# 🚀 SmartSpend Production Deployment Guide

Deploy your app for **free** using **Vercel** (frontend) + **Render** (backend + database).

---

## Architecture Overview

```
┌─────────────────┐     HTTPS      ┌──────────────────┐     PostgreSQL    ┌─────────────────┐
│   Vercel (Free)  │ ─────────────→ │  Render (Free)    │ ───────────────→ │  Render DB       │
│   React Frontend │                │  FastAPI Backend   │                  │  PostgreSQL      │
└─────────────────┘                └──────────────────┘     Redis         ┌─────────────────┐
                                                          ───────────────→│  Upstash (Free)  │
                                                                          │  Redis           │
                                                                          └─────────────────┘
```

---

## Step 1: Push Code to GitHub

If you haven't already, create a GitHub repo and push your code:

```bash
cd C:\Storage\Projects\SmartSpend
git init
git add .
git commit -m "Initial commit - SmartSpend AI"
git remote add origin https://github.com/YOUR_USERNAME/SmartSpend.git
git branch -M main
git push -u origin main
```

> ⚠️ **IMPORTANT:** Make sure `.env` is in `.gitignore`! Never push secrets to GitHub.

---

## Step 2: Set Up PostgreSQL on Render

1. Go to [render.com](https://render.com) → Sign up (free)
2. Click **New → PostgreSQL**
3. Configure:
   - **Name:** `smartspend-db`
   - **Region:** Pick closest to your users (e.g., Oregon or Singapore)
   - **Plan:** Free
4. Click **Create Database**
5. Copy the **Internal Database URL** (looks like `postgresql://user:pass@host/dbname`)
6. For the backend env var, **replace** `postgresql://` with `postgresql+asyncpg://`

```
# Example: What Render gives you
postgresql://smartspend_user:abc123@dpg-xyz.oregon-postgres.render.com/smartspend_db

# What you put in DATABASE_URL (add +asyncpg)
postgresql+asyncpg://smartspend_user:abc123@dpg-xyz.oregon-postgres.render.com/smartspend_db
```

---

## Step 3: Set Up Free Redis (Upstash)

1. Go to [upstash.com](https://upstash.com) → Sign up (free)
2. Click **Create Database** → Choose a region → Create
3. Copy the **Redis URL** (starts with `rediss://...`)

---

## Step 4: Deploy Backend on Render

### 4a. Create a `render.yaml` (Optional - for auto-deploy)

Or simply use the Render dashboard:

### 4b. Dashboard Deploy

1. Go to [render.com](https://render.com) → **New → Web Service**
2. Connect your GitHub repo
3. Configure:
   - **Name:** `smartspend-api`
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free

4. **Add Environment Variables** (Settings → Environment):

| Variable | Value |
|---|---|
| `APP_ENV` | `production` |
| `SECRET_KEY` | *(generate a new one: `python -c "import secrets; print(secrets.token_hex(32))"`)* |
| `ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` |
| `DATABASE_URL` | `postgresql+asyncpg://...` *(from Step 2)* |
| `REDIS_URL` | `rediss://...` *(from Step 3)* |
| `GEMINI_API_KEY` | *(your Google Gemini API key)* |
| `GEMINI_MODEL` | `gemini-2.5-flash` |
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `465` |
| `SMTP_USER` | *(your Gmail address)* |
| `SMTP_PASSWORD` | *(your Gmail App Password)* |
| `ALLOWED_ORIGINS` | `https://your-app.vercel.app` *(update after Step 5)* |
| `GOOGLE_CLIENT_ID` | *(your OAuth client ID if using Google login)* |
| `GOOGLE_CLIENT_SECRET` | *(your OAuth secret)* |
| `GOOGLE_REDIRECT_URI` | `https://smartspend-api.onrender.com/api/v1/auth/google/callback` |

5. Click **Create Web Service**
6. Wait for the build to complete (~3-5 minutes)
7. Note your backend URL: `https://smartspend-api.onrender.com`

> 💡 **Note:** Free Render instances spin down after 15 minutes of inactivity. The first request after sleep takes ~30s to wake up. This is normal for the free tier.

---

## Step 5: Deploy Frontend on Vercel

1. Go to [vercel.com](https://vercel.com) → Sign up with GitHub
2. Click **Add New → Project** → Import your `SmartSpend` repo
3. Configure:
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`

4. **Add Environment Variable:**

| Variable | Value |
|---|---|
| `VITE_API_URL` | `https://smartspend-api.onrender.com/api/v1` |

5. Click **Deploy**
6. Your app will be live at: `https://smartspend-xxx.vercel.app`

### 5a. Update Backend CORS

After deployment, go back to Render and update:
```
ALLOWED_ORIGINS=https://your-app.vercel.app,https://smartspend-xxx.vercel.app
```

---

## Step 6: Run Database Migrations

After the backend is running, you need to initialize the database. SSH into Render or use the **Shell** tab:

1. Go to your Render web service → **Shell** tab
2. Run:
```bash
alembic upgrade head
```

If you don't have Alembic migrations set up, the app's startup event should auto-create tables. Verify by hitting:
```
https://smartspend-api.onrender.com/api/v1/categories
```

---

## Step 7: Seed Demo Data (Optional)

To seed the demo accounts on production, use Render's Shell:

```bash
python seed_mock_data.py
python seed_insights_demo.py
```

---

## 🔄 How to Deploy New Changes

### Frontend (Vercel) — Automatic!
```bash
git add .
git commit -m "feat: your changes"
git push origin main
```
Vercel auto-detects the push and redeploys in ~30 seconds. ✅

### Backend (Render) — Also Automatic!
Same process — Render watches your `main` branch and auto-deploys on push.

### Manual Redeploy
If auto-deploy isn't working:
- **Vercel:** Dashboard → Project → Deployments → **Redeploy**
- **Render:** Dashboard → Service → **Manual Deploy → Deploy latest commit**

---

## 🛡️ Production Checklist

Before going live, verify these:

- [ ] **Generate a new `SECRET_KEY`** — don't use the dev one
- [ ] **Remove dev credentials** from `.env` before pushing
- [ ] **`.gitignore` includes:** `.env`, `venv/`, `__pycache__/`, `node_modules/`
- [ ] **CORS is configured** with your Vercel domain
- [ ] **Google OAuth redirect URI** updated to production URL
- [ ] **SMTP credentials** are working
- [ ] **Gemini API key** has production quota

---

## 📁 Required .gitignore Files

### `backend/.gitignore`
```
venv/
__pycache__/
*.pyc
.env
*.db
.pytest_cache/
```

### `frontend/.gitignore`
```
node_modules/
dist/
.env
.env.local
```

### Root `.gitignore`
```
.env
*.pyc
__pycache__/
node_modules/
dist/
venv/
.DS_Store
```

---

## 🔧 Troubleshooting

| Issue | Fix |
|---|---|
| Backend takes 30s to respond | Free Render tier sleeps after 15min inactivity — first request wakes it |
| CORS errors in browser | Add your Vercel URL to `ALLOWED_ORIGINS` in Render env vars |
| Database connection fails | Ensure you used `postgresql+asyncpg://` (not plain `postgresql://`) |
| Frontend shows "Network Error" | Check `VITE_API_URL` is set correctly in Vercel env vars |
| OTP emails not sending | Verify SMTP credentials; Gmail needs App Passwords enabled |
| Google Login redirect fails | Update `GOOGLE_REDIRECT_URI` to your Render URL |

---

## 💰 Cost Summary

| Service | Tier | Cost |
|---|---|---|
| Vercel (Frontend) | Hobby | **Free** |
| Render (Backend) | Free | **Free** |
| Render (PostgreSQL) | Free | **Free** (90 days, then $7/mo) |
| Upstash (Redis) | Free | **Free** (10k commands/day) |
| **Total** | | **$0/month** |

> After 90 days, Render's free PostgreSQL expires. You can migrate to [Supabase](https://supabase.com) (free forever, 500MB) or [Neon](https://neon.tech) (free forever, 512MB) as alternatives.
