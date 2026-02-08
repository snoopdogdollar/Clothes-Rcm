# 🚀 PostgreSQL Integration - Setup Guide

## ✅ What Was Created

### **New Files:**
1. **`.env`** - Environment variables (configure your password here!)
2. **`.env.example`** - Template for .env
3. **`config.py`** - Application configuration
4. **`api.py`** - FastAPI REST API server (470+ lines)
5. **`utils/database.py`** - Database connection management
6. **`models/item.py`** - SQLAlchemy ORM models
7. **`models/__init__.py`** - Model exports
8. **`test_api_setup.py`** - Setup verification script
9. **`README_API.md`** - Complete API documentation
10. **`SETUP_GUIDE.md`** - This file!

### **Updated Files:**
- **`requirements.txt`** - Added PostgreSQL & FastAPI packages

### **New Folders:**
- **`data/uploads/`** - For uploaded images
- **`models/`** - For database models

---

## 🔧 Installation Steps

### **Step 1: Update Your `.env` File**

Open `.env` and replace `your_password_here` with your actual PostgreSQL password:

```env
DATABASE_URL=postgresql://giaphuc:YOUR_ACTUAL_PASSWORD@localhost:5432/fashion_wardrobe
```

### **Step 2: Install New Dependencies**

```bash
# Activate virtual environment first
venv\Scripts\activate

# Install new packages
pip install -r requirements.txt
```

This installs:
- `psycopg2-binary` - PostgreSQL adapter
- `SQLAlchemy` - ORM for database
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `python-multipart` - File upload support
- `python-dotenv` - Environment variables

### **Step 3: Verify Setup**

Run the test script:

```bash
python test_api_setup.py
```

This checks:
- ✅ All packages installed
- ✅ `.env` file configured
- ✅ Folders exist
- ✅ Can connect to PostgreSQL
- ✅ Models import correctly

If any tests fail, follow the instructions shown.

### **Step 4: Create Database Tables**

The tables will be created automatically when you start the API, but you can also create them manually:

```bash
python -c "from utils.database import init_db; init_db()"
```

### **Step 5: Start API Server**

```bash
python api.py
```

Or using uvicorn:

```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

You should see:

```
✓ Database tables initialized
✓ API server started
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### **Step 6: Test the API**

Open your browser:
- **API Root:** http://localhost:8000
- **Interactive Docs:** http://localhost:8000/docs (Swagger UI)
- **Alternative Docs:** http://localhost:8000/redoc

---

## 📡 Quick API Test

### Using the Browser (Swagger UI)

1. Go to http://localhost:8000/docs
2. Click on **POST /api/items/upload**
3. Click "Try it out"
4. Choose an image file
5. Click "Execute"
6. See the results!

### Using curl (Command Line)

```bash
# Upload an image
curl -X POST "http://localhost:8000/api/items/upload" \
  -F "file=@input/your_image.jpg"

# Get all items
curl "http://localhost:8000/api/items"

# Get single item
curl "http://localhost:8000/api/items/1"
```

---

## 🎯 How It Works

### **Complete Flow:**

```
1. User uploads image through frontend
   ↓
2. Frontend sends POST to /api/items/upload
   ↓
3. API runs AI pipeline:
   - Segmentation (U-2-Net)
   - Classification (ResNet18)
   - Color Extraction (K-means)
   ↓
4. API saves to PostgreSQL:
   - clothing_items table (main data)
   - item_colors table (multiple colors)
   ↓
5. API returns item_id + results to frontend
   ↓
6. Frontend shows results + form for user input
   ↓
7. User fills: Material="Cotton", Size="M", etc.
   ↓
8. Frontend sends PUT to /api/items/{id}
   ↓
9. API updates database
   ↓
10. Frontend shows success, redirects to wardrobe view
```

---

## 📊 Database Schema

### **clothing_items** table:
- AI Results: category, confidence, primary_color, palette_type
- User Data: material, size, brand, purchase_date, notes
- File Paths: original_image_path, segmented_image_path
- Timestamps: created_at, updated_at

### **item_colors** table:
- Foreign key to clothing_items
- color_name, color_hex, color_rgb (JSON)
- percentage (how much of the item is this color)

---

## 🔌 Frontend Integration

### **HTML Example:**

```html
<input type="file" id="imageInput" accept="image/*">
<button onclick="uploadImage()">Upload</button>

<script>
async function uploadImage() {
    const file = document.getElementById('imageInput').files[0];
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch('http://localhost:8000/api/items/upload', {
        method: 'POST',
        body: formData
    });
    
    const data = await response.json();
    console.log('Item ID:', data.item_id);
    console.log('Category:', data.category);
    console.log('Primary Color:', data.primary_color);
    
    // Now show form to add material, size, etc.
    showUpdateForm(data.item_id);
}

async function updateItem(itemId, material, size) {
    const response = await fetch(`http://localhost:8000/api/items/${itemId}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({material, size})
    });
    
    const data = await response.json();
    console.log('Updated!', data);
}
</script>
```

---

## 🐛 Troubleshooting

### **"Connection refused" or "Could not connect to server"**

**Problem:** PostgreSQL is not running

**Solution:**
```bash
# Windows - Start PostgreSQL service
net start postgresql-x64-18

# Check if running
pg_isready
```

### **"password authentication failed for user"**

**Problem:** Wrong password in `.env`

**Solution:**
1. Check your password is correct
2. Update `.env` file
3. Restart API server

### **"database 'fashion_wardrobe' does not exist"**

**Problem:** Database not created yet

**Solution:**
```bash
psql -U giaphuc
CREATE DATABASE fashion_wardrobe;
\q
```

### **"ModuleNotFoundError: No module named 'psycopg2'"**

**Problem:** Packages not installed

**Solution:**
```bash
pip install -r requirements.txt
```

### **"Port 8000 is already in use"**

**Problem:** Another process using port 8000

**Solution:**
```bash
# Option 1: Change port in .env
API_PORT=8001

# Option 2: Kill process using port 8000 (Windows)
netstat -ano | findstr :8000
taskkill /PID <process_id> /F
```

---

## 📚 Next Steps

### **Phase 1: Backend (Done ✓)**
- ✅ PostgreSQL setup
- ✅ Database schema created
- ✅ API endpoints implemented
- ✅ AI pipeline integrated

### **Phase 2: Frontend (Your Next Task)**
- Build upload UI
- Display AI results
- Add form for user inputs (material, size, brand)
- Create wardrobe view (list all items)
- Add search/filter functionality
- Item detail page

### **Phase 3: Advanced Features**
- User authentication (login/signup)
- Outfit builder (combine multiple items)
- Wear tracking (mark when item was worn)
- Statistics dashboard
- Export/import wardrobe data
- Mobile app

---

## 📖 Documentation

- **API Endpoints:** See `README_API.md`
- **Database Models:** See `models/item.py`
- **Configuration:** See `config.py`
- **Environment Setup:** See `.env.example`

---

## 💡 Tips

1. **Use Swagger UI** at http://localhost:8000/docs for testing
2. **Check database** with pgAdmin or psql
3. **Monitor API logs** in terminal for debugging
4. **Keep .env secure** - never commit to git
5. **Backup database** regularly in production

---

## 🎉 You're All Set!

Your fashion wardrobe app now has:
- ✅ AI-powered segmentation & classification
- ✅ Advanced color extraction (150+ colors)
- ✅ PostgreSQL database storage
- ✅ RESTful API (5 endpoints)
- ✅ Complete data management (CRUD)

**Start the API and test it out:**

```bash
python api.py
```

Then open http://localhost:8000/docs

Happy coding! 🚀
