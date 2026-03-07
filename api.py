"""
FastAPI REST API for Fashion Wardrobe Application
Provides endpoints for uploading, managing, and retrieving clothing items
"""

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from pathlib import Path
import shutil
import hashlib
import random
from collections import Counter
from pydantic import BaseModel

# Import models and database
from models.item import ClothingItem, ItemColor, Outfit, OutfitFeedback
from utils.database import get_db, init_db
from config import Config

# Import AI pipeline
from utils.segmentation import segment_image
from utils.classification import classify_clothing
from utils.color_extraction import extract_colors_simple
from PIL import Image
import numpy as np

# Initialize FastAPI app
app = FastAPI(
    title="Fashion Wardrobe API",
    description="API for clothing segmentation, classification, and wardrobe management",
    version="1.0.0"
)

# CORS middleware (allow frontend to call API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    """Initialize database tables when API starts"""
    init_db()
    print("✓ API server started")

# ==================== Pydantic Models (Request/Response) ====================

class ItemUpdateRequest(BaseModel):
    """Request model for updating item data"""
    material: Optional[str] = None
    size: Optional[str] = None
    notes: Optional[str] = None

class ItemResponse(BaseModel):
    """Response model for single item"""
    id: int
    filename: str
    category: Optional[str]
    confidence: Optional[float]
    primary_color: Optional[str]
    palette_type: Optional[str]
    material: Optional[str]
    size: Optional[str]
    brand: Optional[str]
    colors: List[dict]

class LoginRequest(BaseModel):
    """Request model for login"""
    username: str
    password: str

class OutfitCreateRequest(BaseModel):
    """Request model for saving an outfit"""
    name: Optional[str] = None
    top_id: Optional[int] = None
    bottom_id: Optional[int] = None
    shoes_id: Optional[int] = None

class OutfitUpdateRequest(BaseModel):
    """Request model for updating an outfit"""
    name: Optional[str] = None

class FeedbackRequest(BaseModel):
    """Request model for outfit feedback"""
    top_id: Optional[int] = None
    bottom_id: Optional[int] = None
    shoes_id: Optional[int] = None
    rating: int  # +1 liked, -1 disliked

# ==================== Auth (Option A: single admin) ====================

def _get_admin_token() -> str:
    """Return token to give to client on successful login (from .env or derived)."""
    token = getattr(Config, 'ADMIN_TOKEN', None)
    if token and str(token).strip():
        return str(token).strip()
    return hashlib.sha256(
        (Config.SECRET_KEY + Config.ADMIN_USERNAME).encode()
    ).hexdigest()

@app.post("/api/auth/login")
def login(data: LoginRequest):
    """
    Login with admin username and password.
    Credentials are stored in .env (ADMIN_USERNAME, ADMIN_PASSWORD).
    Returns a token to store in localStorage.
    """
    if data.username != Config.ADMIN_USERNAME or data.password != Config.ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail='Invalid username or password')
    return {
        'success': True,
        'token': _get_admin_token(),
        'message': 'Login successful'
    }

@app.get("/api/auth/me")
def auth_me(authorization: Optional[str] = Header(None)):
    """Check if current token is valid."""
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Not authenticated')
    token = authorization.replace('Bearer ', '', 1).strip()
    if token != _get_admin_token():
        raise HTTPException(status_code=401, detail='Invalid token')
    return {'logged_in': True, 'username': Config.ADMIN_USERNAME}

# ==================== API Endpoints ====================

@app.get("/")
def root():
    """API root endpoint"""
    return {
        "message": "Fashion Wardrobe API",
        "version": "1.0.0",
        "endpoints": {
            "auth_login": "POST /api/auth/login",
            "auth_me": "GET /api/auth/me",
            "upload": "POST /api/items/upload",
            "list": "GET /api/items",
            "get": "GET /api/items/{item_id}",
            "update": "PUT /api/items/{item_id}",
            "delete": "DELETE /api/items/{item_id}",
            "image": "GET /api/items/{item_id}/image",
            "outfits_create": "POST /api/outfits",
            "outfits_list": "GET /api/outfits",
            "outfits_get": "GET /api/outfits/{outfit_id}",
            "outfits_update": "PUT /api/outfits/{outfit_id}",
            "outfits_delete": "DELETE /api/outfits/{outfit_id}",
            "feedback_record": "POST /api/feedback",
            "feedback_suggest": "GET /api/feedback/suggest"
        }
    }

@app.post("/api/items/upload")
async def upload_item(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and process a clothing image
    
    Steps:
    1. Save uploaded image
    2. Run AI pipeline (segmentation, classification, color extraction)
    3. Save results to database
    4. Return item details
    """
    try:
        # Validate file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in Config.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not allowed. Allowed: {Config.ALLOWED_EXTENSIONS}"
            )
        
        # Save uploaded file
        upload_path = Config.get_upload_path(file.filename)
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"Processing: {file.filename}")
        
        # Load image
        input_image = Image.open(upload_path)
        if input_image.mode != 'RGB':
            input_image = input_image.convert('RGB')
        
        # Step 1: Segmentation
        print("  Segmenting...")
        segmented_image = segment_image(input_image)
        
        # Step 2: Classification
        print("  Classifying...")
        category, confidence, top3 = classify_clothing(segmented_image)
        
        # Step 3: Color Extraction
        print("  Extracting colors...")
        color_info = extract_colors_simple(segmented_image, num_colors=3)
        
        # Save segmented image
        primary_color = color_info.get('primary_color', 'Unknown')
        output_filename = f"{primary_color}-{category}-{Path(file.filename).stem}.png"
        output_path = Config.get_output_path(output_filename)
        segmented_image.save(output_path, 'PNG')
        
        # Create database entry
        new_item = ClothingItem(
            filename=file.filename,
            original_image_path=str(upload_path),
            segmented_image_path=str(output_path),
            category=category,
            primary_color=primary_color,
            palette_type=color_info.get('palette_type', 'Unknown')
        )
        
        db.add(new_item)
        db.flush()  # Get the ID without committing
        
        # Add colors
        for color in color_info.get('colors', []):
            item_color = ItemColor(
                item_id=new_item.id,
                color_name=color['name'],
                color_hex=color['hex'],
                color_rgb=color['rgb'],
                percentage=color['percentage']
            )
            db.add(item_color)
        
        db.commit()
        db.refresh(new_item)
        
        print(f"✓ Saved to database: Item ID {new_item.id}")
        
        return {
            "success": True,
            "item_id": new_item.id,
            "filename": file.filename,
            "category": category,
            "primary_color": primary_color,
            "palette_type": color_info.get('palette_type'),
            "colors": color_info.get('colors', []),
            "segmented_image": str(output_path)
        }
        
    except Exception as e:
        db.rollback()
        print(f"Error processing upload: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/items/{item_id}")
def update_item(
    item_id: int,
    item_data: ItemUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update item with user-provided data (material, size, notes)
    """
    # Find item
    item = db.query(ClothingItem).filter(ClothingItem.id == item_id).first()
    
    if not item:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    
    # Update fields (only if provided)
    if item_data.material is not None:
        item.material = item_data.material
    if item_data.size is not None:
        item.size = item_data.size
    if item_data.notes is not None:
        item.notes = item_data.notes
    
    db.commit()
    db.refresh(item)
    
    return {
        "success": True,
        "item_id": item.id,
        "message": "Item updated successfully",
        "item": item.to_dict()
    }

@app.get("/api/items")
def get_items(
    category: Optional[str] = Query(None, description="Filter by category"),
    category_group: Optional[str] = Query(
        None,
        description="Comma-separated list of categories (used for UI groups like TOPS/BOTTOMS/FOOTWEAR)",
    ),
    color: Optional[str] = Query(None, description="Filter by primary color"),
    material: Optional[str] = Query(None, description="Filter by material"),
    size: Optional[str] = Query(None, description="Filter by size"),
    search: Optional[str] = Query(None, description="Search in brand/notes"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get list of all clothing items with filtering and pagination
    """
    query = db.query(ClothingItem)
    
    # Apply filters
    if category:
        query = query.filter(ClothingItem.category == category)
    if category_group:
        categories = [c.strip() for c in category_group.split(",") if c.strip()]
        if categories:
            query = query.filter(ClothingItem.category.in_(categories))
    if color:
        query = query.filter(ClothingItem.primary_color.ilike(f"%{color}%"))
    if material:
        query = query.filter(ClothingItem.material.ilike(f"%{material}%"))
    if size:
        query = query.filter(ClothingItem.size == size)
    if search:
        query = query.filter(
            or_(
                ClothingItem.brand.ilike(f"%{search}%"),
                ClothingItem.notes.ilike(f"%{search}%")
            )
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * limit
    items = query.order_by(ClothingItem.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit,
        "items": [item.to_dict(include_colors=False) for item in items]
    }

@app.get("/api/items/{item_id}")
def get_item(item_id: int, db: Session = Depends(get_db)):
    """
    Get details of a single item including all colors
    """
    item = db.query(ClothingItem).filter(ClothingItem.id == item_id).first()
    
    if not item:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    
    return item.to_dict(include_colors=True)

@app.delete("/api/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    """
    Delete a clothing item (also deletes related colors via CASCADE)
    """
    item = db.query(ClothingItem).filter(ClothingItem.id == item_id).first()
    
    if not item:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    
    # Optionally delete image files
    try:
        if item.original_image_path and Path(item.original_image_path).exists():
            Path(item.original_image_path).unlink()
        if item.segmented_image_path and Path(item.segmented_image_path).exists():
            Path(item.segmented_image_path).unlink()
    except Exception as e:
        print(f"Warning: Could not delete image files: {e}")
    
    db.delete(item)
    db.commit()
    
    return {
        "success": True,
        "message": f"Item {item_id} deleted successfully",
        "deleted_id": item_id
    }

@app.get("/api/items/{item_id}/image")
def get_item_image(
    item_id: int,
    type: str = Query("segmented", regex="^(original|segmented)$"),
    db: Session = Depends(get_db)
):
    """
    Get item image file (original or segmented)
    """
    item = db.query(ClothingItem).filter(ClothingItem.id == item_id).first()
    
    if not item:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    
    image_path = item.segmented_image_path if type == "segmented" else item.original_image_path
    
    if not image_path or not Path(image_path).exists():
        raise HTTPException(status_code=404, detail=f"Image file not found")
    
    return FileResponse(image_path)

# ==================== Outfit Endpoints ====================

@app.post("/api/outfits")
def create_outfit(data: OutfitCreateRequest, db: Session = Depends(get_db)):
    """Save a new outfit combination."""
    if not data.top_id and not data.bottom_id and not data.shoes_id:
        raise HTTPException(status_code=400, detail="Outfit must have at least one item")

    outfit = Outfit(
        name=data.name,
        top_id=data.top_id,
        bottom_id=data.bottom_id,
        shoes_id=data.shoes_id,
    )
    db.add(outfit)
    db.commit()
    db.refresh(outfit)
    return {"success": True, "outfit": outfit.to_dict()}


@app.get("/api/outfits")
def list_outfits(db: Session = Depends(get_db)):
    """List all saved outfits (newest first)."""
    outfits = db.query(Outfit).order_by(Outfit.created_at.desc()).all()
    return {"total": len(outfits), "outfits": [o.to_dict() for o in outfits]}


@app.get("/api/outfits/{outfit_id}")
def get_outfit(outfit_id: int, db: Session = Depends(get_db)):
    """Get a single outfit by ID."""
    outfit = db.query(Outfit).filter(Outfit.id == outfit_id).first()
    if not outfit:
        raise HTTPException(status_code=404, detail=f"Outfit {outfit_id} not found")
    return outfit.to_dict()


@app.put("/api/outfits/{outfit_id}")
def update_outfit(outfit_id: int, data: OutfitUpdateRequest, db: Session = Depends(get_db)):
    """Update an outfit (e.g. rename)."""
    outfit = db.query(Outfit).filter(Outfit.id == outfit_id).first()
    if not outfit:
        raise HTTPException(status_code=404, detail=f"Outfit {outfit_id} not found")
    if data.name is not None:
        outfit.name = data.name.strip() or None
    db.commit()
    db.refresh(outfit)
    return {"success": True, "outfit": outfit.to_dict()}


@app.delete("/api/outfits/{outfit_id}")
def delete_outfit(outfit_id: int, db: Session = Depends(get_db)):
    """Delete a saved outfit."""
    outfit = db.query(Outfit).filter(Outfit.id == outfit_id).first()
    if not outfit:
        raise HTTPException(status_code=404, detail=f"Outfit {outfit_id} not found")
    db.delete(outfit)
    db.commit()
    return {"success": True, "message": f"Outfit {outfit_id} deleted", "deleted_id": outfit_id}


# ==================== Feedback & Recommendation ====================

SLOT_CATEGORIES = {
    "top": ["t-shirt", "shirt", "polo", "long_sleeve", "hoodie", "sweater", "jacket", "denim_jacket", "leather_jacket"],
    "bottom": ["jeans", "trousers", "shorts", "jorts", "cargo"],
    "shoes": ["casual_shoe", "formal_shoe", "sport shoes"],
}
MIN_FEEDBACK_FOR_LEARNING = 3


@app.post("/api/feedback")
def record_feedback(data: FeedbackRequest, db: Session = Depends(get_db)):
    """Record +1 (liked) or -1 (disliked) feedback for an outfit combination."""
    if data.rating not in (1, -1):
        raise HTTPException(status_code=400, detail="rating must be 1 or -1")
    if not data.top_id and not data.bottom_id and not data.shoes_id:
        raise HTTPException(status_code=400, detail="At least one item required")

    def _attr(item_id, attr):
        if not item_id:
            return None
        item = db.query(ClothingItem).filter(ClothingItem.id == item_id).first()
        return getattr(item, attr, None) if item else None

    fb = OutfitFeedback(
        rating=data.rating,
        top_id=data.top_id,
        bottom_id=data.bottom_id,
        shoes_id=data.shoes_id,
        top_category=_attr(data.top_id, "category"),
        top_color=_attr(data.top_id, "primary_color"),
        top_material=_attr(data.top_id, "material"),
        bottom_category=_attr(data.bottom_id, "category"),
        bottom_color=_attr(data.bottom_id, "primary_color"),
        bottom_material=_attr(data.bottom_id, "material"),
        shoes_category=_attr(data.shoes_id, "category"),
        shoes_color=_attr(data.shoes_id, "primary_color"),
        shoes_material=_attr(data.shoes_id, "material"),
    )
    db.add(fb)
    db.commit()
    total = db.query(OutfitFeedback).count()
    return {"success": True, "feedback_id": fb.id, "total_feedback": total}


@app.get("/api/feedback/suggest")
def suggest_outfit(db: Session = Depends(get_db)):
    """Return a smart outfit suggestion scored by past feedback."""
    all_items = db.query(ClothingItem).all()
    tops = [i for i in all_items if i.category in SLOT_CATEGORIES["top"]]
    bottoms = [i for i in all_items if i.category in SLOT_CATEGORIES["bottom"]]
    shoes = [i for i in all_items if i.category in SLOT_CATEGORIES["shoes"]]

    if not tops and not bottoms and not shoes:
        raise HTTPException(status_code=404, detail="No items to build an outfit")

    feedbacks = db.query(OutfitFeedback).all()

    # Not enough feedback — pure random
    if len(feedbacks) < MIN_FEEDBACK_FOR_LEARNING:
        return _random_outfit(tops, bottoms, shoes)

    # Build pattern scores from feedback history
    cat_combos: Counter = Counter()     # ("Tshirts","Jeans","Casual Shoes") → net score
    color_combos: Counter = Counter()   # ("Black","Blue","White") → net score
    mat_combos: Counter = Counter()     # ("Cotton","Denim",None) → net score
    item_scores: Counter = Counter()    # item_id → net score

    for fb in feedbacks:
        r = fb.rating
        cat_combos[(fb.top_category, fb.bottom_category, fb.shoes_category)] += r
        color_combos[(fb.top_color, fb.bottom_color, fb.shoes_color)] += r
        mat_combos[(fb.top_material, fb.bottom_material, fb.shoes_material)] += r
        if fb.top_id:
            item_scores[fb.top_id] += r
        if fb.bottom_id:
            item_scores[fb.bottom_id] += r
        if fb.shoes_id:
            item_scores[fb.shoes_id] += r

    # Generate candidates and score them
    num_candidates = min(30, max(5, len(tops) * len(bottoms) * len(shoes) if tops and bottoms and shoes else 10))
    candidates = []
    for _ in range(num_candidates):
        t = random.choice(tops) if tops else None
        b = random.choice(bottoms) if bottoms else None
        s = random.choice(shoes) if shoes else None
        score = _score_combo(t, b, s, cat_combos, color_combos, mat_combos, item_scores)
        candidates.append((score, t, b, s))

    candidates.sort(key=lambda x: x[0], reverse=True)
    _, best_t, best_b, best_s = candidates[0]

    return {
        "top": best_t.to_dict(include_colors=False) if best_t else None,
        "bottom": best_b.to_dict(include_colors=False) if best_b else None,
        "shoes": best_s.to_dict(include_colors=False) if best_s else None,
    }


def _random_outfit(tops, bottoms, shoes):
    return {
        "top": random.choice(tops).to_dict(include_colors=False) if tops else None,
        "bottom": random.choice(bottoms).to_dict(include_colors=False) if bottoms else None,
        "shoes": random.choice(shoes).to_dict(include_colors=False) if shoes else None,
    }


def _score_combo(t, b, s, cat_combos, color_combos, mat_combos, item_scores):
    tc = t.category if t else None
    bc = b.category if b else None
    sc = s.category if s else None

    score = 0.0
    score += cat_combos.get((tc, bc, sc), 0) * 3
    score += color_combos.get(
        (t.primary_color if t else None, b.primary_color if b else None, s.primary_color if s else None), 0
    ) * 2
    score += mat_combos.get(
        (t.material if t else None, b.material if b else None, s.material if s else None), 0
    ) * 1.5
    if t:
        score += item_scores.get(t.id, 0)
    if b:
        score += item_scores.get(b.id, 0)
    if s:
        score += item_scores.get(s.id, 0)
    score += random.uniform(0, 1.5)
    return score


# ==================== Statistics Endpoints (Bonus) ====================

@app.get("/api/stats")
def get_statistics(db: Session = Depends(get_db)):
    """
    Get wardrobe statistics
    """
    from sqlalchemy import func
    
    total_items = db.query(ClothingItem).count()
    
    # Category breakdown
    category_stats = db.query(
        ClothingItem.category,
        func.count(ClothingItem.id).label('count')
    ).group_by(ClothingItem.category).all()
    
    # Color breakdown
    color_stats = db.query(
        ClothingItem.primary_color,
        func.count(ClothingItem.id).label('count')
    ).group_by(ClothingItem.primary_color).all()
    
    return {
        "total_items": total_items,
        "by_category": [{"category": cat, "count": count} for cat, count in category_stats],
        "by_color": [{"color": color, "count": count} for color, count in color_stats]
    }

# Run with: uvicorn api:app --reload --host 0.0.0.0 --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=Config.API_HOST, port=Config.API_PORT)
