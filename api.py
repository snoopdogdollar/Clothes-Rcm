"""
FastAPI REST API for Fashion Wardrobe Application
Provides endpoints for uploading, managing, and retrieving clothing items
"""

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from pathlib import Path
from datetime import date
import shutil
from pydantic import BaseModel

# Import models and database
from models.item import ClothingItem, ItemColor
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
    brand: Optional[str] = None
    purchase_date: Optional[date] = None
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

# ==================== API Endpoints ====================

@app.get("/")
def root():
    """API root endpoint"""
    return {
        "message": "Fashion Wardrobe API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "POST /api/items/upload",
            "list": "GET /api/items",
            "get": "GET /api/items/{item_id}",
            "update": "PUT /api/items/{item_id}",
            "delete": "DELETE /api/items/{item_id}",
            "image": "GET /api/items/{item_id}/image"
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
            confidence=confidence,
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
            "confidence": float(confidence),
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
    Update item with user-provided data (material, size, brand, etc.)
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
    if item_data.brand is not None:
        item.brand = item_data.brand
    if item_data.purchase_date is not None:
        item.purchase_date = item_data.purchase_date
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
