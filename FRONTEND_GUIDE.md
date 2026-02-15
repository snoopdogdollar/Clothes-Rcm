# Frontend Integration Guide

Your frontend is now fully connected to the backend API! Here's how everything works.

## 🚀 Quick Start

### 1. Start the API Server
```bash
python api.py
```
The API will run on `http://localhost:8000`

### 2. Open Frontend
Open any of these pages in your browser:
- `frontend/index.html` - Home/Gallery view
- `frontend/wardrobe.html` - Wardrobe management
- `frontend/upload.html` - Upload new items
- `frontend/dressing-room.html` - Outfit builder

## 📁 Files Created

### `frontend/js/api.js`
Central API integration module with all backend communication:
- `uploadItem(file)` - Upload and process image
- `getItems(filters)` - Get items with filtering/pagination
- `getItem(itemId)` - Get single item details
- `updateItem(itemId, data)` - Update item info
- `deleteItem(itemId)` - Delete item
- `getItemImageUrl(itemId, type)` - Get image URL
- `getStatistics()` - Get wardrobe stats

Helper functions:
- `showSuccess(message)` - Toast notification (green)
- `showError(message)` - Toast notification (red)
- `formatConfidence(confidence)` - Format as percentage
- `formatDate(dateString)` - Format date

### `frontend/upload.html`
Complete upload workflow:
1. **Drag & drop or click** to select image
2. **AI Processing** (Segmentation → Classification → Color Extraction)
3. **AI Results Display** with segmented image preview
4. **User Input Form** (Material*, Size*, Brand, Date, Notes)
5. **Save to Wardrobe** or Cancel

Features:
- Real-time file validation (type & size)
- Loading spinner during AI processing
- Beautiful results display with color swatches
- Required fields: Material and Size

### `frontend/index.html` & `frontend/wardrobe.html`
Gallery view with full API integration:
- **Dynamic Loading** - Loads all items from database
- **Search** - Search by brand/notes (500ms debounce)
- **Filters** - Category, Color, Material
- **Item Cards** - Shows image, color, category, material, size, brand
- **View Details** - Modal with full item info
- **Delete** - Delete with confirmation
- **+ Add New** button → Upload page

### `frontend/dressing-room.html`
Outfit builder with real wardrobe items:
- **Wardrobe Sidebar** - Shows first 6 items from your wardrobe
- **Click to Add** - Click item to add to appropriate slot (Top/Bottom/Shoes)
- **Smart Categorization** - Auto-detects which slot based on category:
  - **Tops**: Tshirts, Shirts, Tops, Sweatshirt, Sweaters, Jackets, Blazers
  - **Bottoms**: Jeans, Trousers, Shorts, Track Pants, Skirts, Leggings
  - **Shoes**: Casual Shoes, Sports Shoes, Formal Shoes, Sandals, Flip Flops, Flats, Heels
- **Randomize** - Pick random items for complete outfit
- **Confirm** - Confirm current selection
- **Reset** - Clear all slots
- **Save** - Save outfit combination (feature placeholder)

## 🎯 Features

### Real-Time AI Processing
When uploading:
1. Image uploaded to API
2. U-2-Net segmentation removes background
3. ResNet18 classifier predicts category
4. K-means color extraction analyzes colors
5. Results saved to PostgreSQL
6. User adds material/size details
7. Item appears in wardrobe

### Smart Filtering
- **Search**: Brand, notes (debounced for performance)
- **Category Filter**: Filter by predicted category
- **Color Filter**: Filter by primary color
- **Material Filter**: Filter by user-entered material

### Beautiful UI/UX
- Modern design with Tailwind CSS
- Loading states for all operations
- Toast notifications (success/error)
- Smooth animations and transitions
- Responsive grid layouts
- Modal popups for details

## 🔧 Configuration

### API URL
Change in `frontend/js/api.js` if needed:
```javascript
const API_URL = 'http://localhost:8000';
```

### Categories
Update categories in `dressing-room.html` script if needed:
```javascript
const topCategories = ['Tshirts', 'Shirts', ...];
const bottomCategories = ['Jeans', 'Trousers', ...];
const shoesCategories = ['Casual Shoes', 'Sports Shoes', ...];
```

## 📊 Testing

### 1. Upload Test
1. Open `frontend/upload.html`
2. Drop an image or click to browse
3. Wait for AI processing (~5-10 seconds)
4. Check results display correctly
5. Fill material & size (required)
6. Click "Save to Wardrobe"
7. Should redirect to wardrobe page

### 2. Wardrobe Test
1. Open `frontend/wardrobe.html`
2. Should see uploaded items
3. Try search (type in search box)
4. Try filters (dropdowns)
5. Click "View" on item → modal opens
6. Click "Delete" on item → confirmation → deleted

### 3. Dressing Room Test
1. Open `frontend/dressing-room.html`
2. Should see items in sidebar
3. Click item → adds to appropriate slot
4. Click "Randomize" → random outfit
5. Click "Reset" → clears slots
6. Click "Confirm" → shows selection

## 🐛 Troubleshooting

### "Failed to load items"
- **Cause**: API not running or connection failed
- **Fix**: Start API with `python api.py`

### Upload fails
- **Cause**: File too large, wrong format, or API error
- **Check**: 
  - File < 10MB
  - Format: JPG, PNG, WEBP
  - Check API terminal for errors

### No items showing
- **Cause**: Database empty
- **Fix**: Upload at least one item first

### Images not loading
- **Cause**: API not serving images or wrong path
- **Check**: 
  - API running
  - Files exist in `data/uploads/` and `data/outputs/`
  - Check browser console for 404 errors

### CORS errors
- **Cause**: Opening HTML files with `file://` protocol
- **Fix**: Use a local server:
  ```bash
  # Python
  cd frontend
  python -m http.server 3000
  # Then open http://localhost:3000
  ```

## 🎨 Customization

### Colors
Main colors in `<style>` tags:
- Background: `#ffffff` (white)
- Cards: `#D1D1D1` (light gray)
- Item cards: `#e5e5e5` (lighter gray)
- Accent: `#1a1a1a` (black)

### Fonts
Using Inter font from Google Fonts:
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;900&display=swap" rel="stylesheet">
```

### Layout
All pages use Tailwind CSS utility classes. Modify breakpoints:
- `sm:` - 640px+
- `md:` - 768px+
- `lg:` - 1024px+
- `xl:` - 1280px+

## 🚀 Next Steps

### Potential Enhancements
1. **Outfit Saving** - Create `outfits` table and save combinations
2. **Statistics Page** - Show wardrobe analytics (colors, categories, brands)
3. **Favorites** - Mark favorite items
4. **Tags** - Add custom tags to items
5. **Seasons** - Filter by season (Spring, Summer, Fall, Winter)
6. **Occasions** - Add occasion field (Casual, Formal, Party, Sport)
7. **Weather Integration** - Suggest outfits based on weather
8. **Calendar** - Track what you wore each day
9. **Sharing** - Share outfits with friends
10. **Mobile App** - React Native or Flutter app

### Database Schema Additions
Consider adding these columns to `ClothingItem`:
- `favorite` (Boolean)
- `season` (String)
- `occasion` (String)
- `tags` (ARRAY or JSON)
- `times_worn` (Integer)
- `last_worn_date` (DateTime)

Consider creating these tables:
- `outfits` - Save outfit combinations
- `outfit_items` - Many-to-many relationship
- `wardrobe_history` - Track daily outfits

## 📝 Notes

- Toast notifications auto-dismiss after 3 seconds
- Search has 500ms debounce (waits for typing to stop)
- Modal clicks outside to close
- File validation happens client-side first
- All API calls have error handling
- Images use transparent backgrounds from segmentation

## 🎉 You're All Set!

Your fashion wardrobe app is now fully functional with:
✅ AI-powered image processing
✅ Smart categorization and color extraction
✅ PostgreSQL database persistence
✅ Beautiful, modern UI
✅ Full CRUD operations
✅ Outfit builder
✅ Search and filtering

**Start uploading your clothes and building outfits!**
