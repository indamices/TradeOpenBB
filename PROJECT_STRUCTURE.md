# Project Structure Guide

This document explains the correct file structure for the TradeOpenBB project.

## ✅ Correct Structure

```
TradeOpenBB/                    # GitHub repository root
├── render.yaml                 # ⚠️ MUST be in root for Render to detect
├── .gitignore
├── README.md
├── package.json
├── vite.config.ts
├── docker-compose.yml
│
├── backend/                    # Backend API
│   ├── Dockerfile
│   ├── main.py
│   ├── requirements.txt
│   └── ...
│
├── components/                 # React components
├── services/                   # Frontend services
├── docs/                       # Documentation
└── scripts/                    # Utility scripts
```

## ⚠️ Important Notes

### Render Deployment

1. **`render.yaml` MUST be in the repository root**
   - Render automatically looks for `render.yaml` in the root directory
   - If it's in a subdirectory, Render won't find it

2. **Path Configuration in render.yaml**
   - `dockerfilePath: ./backend/Dockerfile` (relative to root)
   - `dockerContext: ./backend` (relative to root)
   - `buildCommand: npm install && npm run build` (runs in root)
   - `staticPublishPath: ./dist` (relative to root)

### GitHub Repository Structure

When you push to GitHub, the structure should be:

```
https://github.com/indamices/TradeOpenBB/
├── render.yaml          ← Render looks here
├── backend/
├── components/
└── ...
```

**NOT**:
```
https://github.com/indamices/TradeOpenBB/
└── openbb/              ← ❌ Wrong! Render won't find render.yaml
    ├── render.yaml
    └── ...
```

## 🔧 If You Have Wrong Structure

If your GitHub repository has files in an `openbb/` subdirectory:

### Option 1: Manual Service Creation (Recommended)

1. In Render Dashboard, click "New +" → "Web Service"
2. Set **Root Directory** to `openbb`
3. Set **Dockerfile Path** to `backend/Dockerfile` (relative to openbb)
4. Configure other settings normally

### Option 2: Fix GitHub Structure

1. Ensure `render.yaml` is in repository root
2. Re-push to GitHub
3. Use Blueprint deployment

## 📁 Directory Purposes

- **`backend/`**: FastAPI backend code
- **`components/`**: React UI components
- **`services/`**: Frontend API services
- **`docs/`**: Documentation files
- **`scripts/`**: Utility scripts (PowerShell, Python)
- **Root**: Configuration files, entry points

## ✅ Verification Checklist

Before deploying, verify:

- [ ] `render.yaml` exists in repository root
- [ ] `backend/Dockerfile` exists
- [ ] `package.json` exists in root
- [ ] `vite.config.ts` exists in root
- [ ] All paths in `render.yaml` are relative to root
- [ ] GitHub repository structure matches local structure

## 🚀 Deployment Steps

1. **Verify local structure** (this file)
2. **Push to GitHub** (ensure structure matches)
3. **Deploy on Render** using Blueprint or manual service creation
4. **Check logs** if deployment fails

---

For detailed deployment instructions, see [docs/RENDER_QUICK_START.md](docs/RENDER_QUICK_START.md)
