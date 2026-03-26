# Fashion Wardrobe (Segmentation + Classification + Colors)

FastAPI app that lets you upload clothing photos, removes the background (U-2-Net via `rembg`), classifies the clothing type (ResNet50), extracts dominant colors, and stores everything in PostgreSQL. A simple HTML frontend is included.

## Features

- **Upload → AI pipeline → Save**: segmentation → classification → color extraction → DB
- **Segmentation**: `rembg` (U-2-Net / ISNet variants depending on your config)
- **Classification**: `timm` ResNet50 + custom linear head (uses your `models/clothing_classifier.pth`)
- **Color extraction**: K-means over pixels + named colors
- **Frontend**: simple HTML pages in `frontend/` using `frontend/js/api.js`
- **Admin login (single account)**: credentials in `.env`, token stored in browser localStorage

## Quick start (Windows)

1. Create your env file:
   - Copy `.env.example` → `.env`
   - Set your `DATABASE_URL`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, and `SECRET_KEY`
2. Run setup + start API:
   - Double-click `setup.bat`
3. Open API docs:
   - `http://localhost:8000/docs`

## Run frontend

Because browser CORS rules are stricter when opening files directly, use a tiny local server:

```bash
cd frontend
python -m http.server 3000
```

Then open `http://localhost:3000/login.html`.

## API overview

- **Auth**
  - `POST /api/auth/login` → returns `{ token }`
- **Items**
  - `POST /api/items/upload` (multipart file upload)
  - `GET /api/items`
  - `GET /api/items/{id}`
  - `PUT /api/items/{id}`
  - `DELETE /api/items/{id}`
  - `GET /api/items/{id}/image?type=original|segmented`

## Model files

Place these in `models/`:

- `models/clothing_classifier.pth`
- `models/class_names.json`

## Project layout

```
PROJECT/
├── api.py
├── config.py
├── requirements.txt
├── setup.bat
├── .env.example
├── frontend/
├── utils/
├── models/              # DB models + classifier artifacts (can be split later)
├── data/uploads/        # generated (gitignored)
└── output/              # generated (gitignored)
```

## Notes

- Generated folders like `data/` and `output/` are intentionally **not** committed.
- If you move classifier artifacts into a dedicated folder later (e.g. `ml/`), update the default paths in `utils/classification.py`.
