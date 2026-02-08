# Fashion Wardrobe API Documentation

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Database

Edit `.env` file and set your PostgreSQL password:

```env
DATABASE_URL=postgresql://giaphuc:YOUR_PASSWORD@localhost:5432/fashion_wardrobe
```

### 3. Create Database

Open PostgreSQL (psql) and run:

```sql
CREATE DATABASE fashion_wardrobe;
```

Or if you already created it, you're good to go!

### 4. Start API Server

```bash
python api.py
```

Or using uvicorn directly:

```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

API will be available at: http://localhost:8000

Interactive API docs: http://localhost:8000/docs

---

## 📡 API Endpoints

### 1. Upload & Process Image

**Endpoint:** `POST /api/items/upload`

**Description:** Upload clothing image, run AI pipeline, save to database

**Request:**
```javascript
// Using FormData (JavaScript)
const formData = new FormData();
formData.append('file', imageFile);

fetch('http://localhost:8000/api/items/upload', {
  method: 'POST',
  body: formData
})
```

**Response:**
```json
{
  "success": true,
  "item_id": 1,
  "filename": "shirt.jpg",
  "category": "Tshirts",
  "confidence": 0.8945,
  "primary_color": "Navy Blue",
  "palette_type": "Cool Palette",
  "colors": [
    {"name": "Navy Blue", "hex": "#001f3f", "rgb": {"r": 0, "g": 31, "b": 63}, "percentage": 67.3}
  ]
}
```

---

### 2. Update Item Data

**Endpoint:** `PUT /api/items/{item_id}`

**Description:** Add user-provided data (material, size, brand, etc.)

**Request:**
```javascript
fetch('http://localhost:8000/api/items/1', {
  method: 'PUT',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    material: "Cotton",
    size: "M",
    brand: "Nike",
    purchase_date: "2024-01-15",
    notes: "Gift from mom"
  })
})
```

**Response:**
```json
{
  "success": true,
  "item_id": 1,
  "message": "Item updated successfully"
}
```

---

### 3. Get All Items

**Endpoint:** `GET /api/items`

**Query Parameters:**
- `category` - Filter by category (e.g., "Tshirts")
- `color` - Filter by color (e.g., "Blue")
- `material` - Filter by material
- `size` - Filter by size
- `search` - Search in brand/notes
- `page` - Page number (default: 1)
- `limit` - Items per page (default: 20)

**Examples:**
```
GET /api/items
GET /api/items?category=Tshirts
GET /api/items?color=Blue&size=M
GET /api/items?search=Nike&page=1&limit=10
```

**Response:**
```json
{
  "total": 45,
  "page": 1,
  "limit": 20,
  "total_pages": 3,
  "items": [
    {
      "id": 1,
      "filename": "shirt1.jpg",
      "category": "Tshirts",
      "primary_color": "Navy Blue",
      "material": "Cotton",
      "size": "M"
    }
  ]
}
```

---

### 4. Get Single Item

**Endpoint:** `GET /api/items/{item_id}`

**Example:**
```
GET /api/items/1
```

**Response:**
```json
{
  "id": 1,
  "filename": "shirt1.jpg",
  "category": "Tshirts",
  "confidence": 0.8945,
  "primary_color": "Navy Blue",
  "colors": [
    {"color_name": "Navy Blue", "hex": "#001f3f", "percentage": 67.3},
    {"color_name": "White", "hex": "#ffffff", "percentage": 21.5"}
  ],
  "material": "Cotton",
  "size": "M",
  "brand": "Nike"
}
```

---

### 5. Delete Item

**Endpoint:** `DELETE /api/items/{item_id}`

**Example:**
```
DELETE /api/items/1
```

**Response:**
```json
{
  "success": true,
  "message": "Item 1 deleted successfully",
  "deleted_id": 1
}
```

---

### 6. Get Item Image

**Endpoint:** `GET /api/items/{item_id}/image`

**Query Parameters:**
- `type` - "original" or "segmented" (default: "segmented")

**Examples:**
```
GET /api/items/1/image?type=segmented
GET /api/items/1/image?type=original
```

Returns the image file directly.

---

### 7. Get Statistics (Bonus)

**Endpoint:** `GET /api/stats`

**Response:**
```json
{
  "total_items": 45,
  "by_category": [
    {"category": "Tshirts", "count": 15},
    {"category": "Jeans", "count": 10"}
  ],
  "by_color": [
    {"color": "Navy Blue", "count": 8},
    {"color": "Black", "count": 12"}
  ]
}
```

---

## 🔧 Frontend Integration Example

### HTML + JavaScript

```html
<!DOCTYPE html>
<html>
<head>
    <title>Fashion Wardrobe</title>
</head>
<body>
    <h1>Upload Clothing Item</h1>
    
    <input type="file" id="fileInput" accept="image/*">
    <button onclick="uploadImage()">Upload</button>
    
    <div id="results"></div>
    
    <script>
        async function uploadImage() {
            const fileInput = document.getElementById('fileInput');
            const file = fileInput.files[0];
            
            if (!file) {
                alert('Please select a file');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await fetch('http://localhost:8000/api/items/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                document.getElementById('results').innerHTML = `
                    <h2>Results:</h2>
                    <p>Category: ${data.category}</p>
                    <p>Confidence: ${(data.confidence * 100).toFixed(1)}%</p>
                    <p>Primary Color: ${data.primary_color}</p>
                    <p>Item ID: ${data.item_id}</p>
                `;
                
                // Now show form to add material, size, etc.
                showUpdateForm(data.item_id);
                
            } catch (error) {
                console.error('Error:', error);
                alert('Upload failed: ' + error.message);
            }
        }
        
        function showUpdateForm(itemId) {
            // Show form to update item with material, size, etc.
            // Then call PUT /api/items/{itemId}
        }
    </script>
</body>
</html>
```

---

## 🧪 Testing API

### Using curl

```bash
# Upload image
curl -X POST "http://localhost:8000/api/items/upload" \
  -F "file=@/path/to/image.jpg"

# Get all items
curl "http://localhost:8000/api/items"

# Get single item
curl "http://localhost:8000/api/items/1"

# Update item
curl -X PUT "http://localhost:8000/api/items/1" \
  -H "Content-Type: application/json" \
  -d '{"material":"Cotton","size":"M"}'

# Delete item
curl -X DELETE "http://localhost:8000/api/items/1"
```

### Using Python requests

```python
import requests

# Upload
files = {'file': open('image.jpg', 'rb')}
response = requests.post('http://localhost:8000/api/items/upload', files=files)
print(response.json())

# Update
data = {'material': 'Cotton', 'size': 'M'}
response = requests.put('http://localhost:8000/api/items/1', json=data)
print(response.json())
```

---

## 📁 File Structure

```
PROJECT/
├── api.py                     # FastAPI server (NEW)
├── config.py                  # Configuration (NEW)
├── .env                       # Environment variables (NEW)
├── app.py                     # Original batch processing
├── requirements.txt           # Updated with new packages
├── models/
│   ├── __init__.py           # Model exports (NEW)
│   └── item.py               # SQLAlchemy models (NEW)
├── utils/
│   ├── database.py           # Database connection (NEW)
│   ├── segmentation.py
│   ├── classification.py
│   └── color_extraction.py
├── data/
│   └── uploads/              # Uploaded images (NEW)
└── output/                   # Segmented images
```

---

## 🛠️ Troubleshooting

### Database connection failed
- Check PostgreSQL is running: `pg_isready`
- Verify password in `.env` file
- Ensure database exists: `psql -l`

### ModuleNotFoundError
- Install dependencies: `pip install -r requirements.txt`
- Activate virtual environment first

### Port already in use
- Change port in `.env`: `API_PORT=8001`
- Or kill process: `netstat -ano | findstr :8000`

---

## 📚 Next Steps

1. ✅ Test API with Postman or curl
2. ✅ Build frontend UI (HTML/React/Vue)
3. ✅ Add authentication (JWT tokens)
4. ✅ Add outfit builder feature
5. ✅ Deploy to production (Heroku, AWS, etc.)
