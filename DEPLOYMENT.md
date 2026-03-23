# 🚀 SmartSpend Production Deployment Guide

Deploy for **free** using **Vercel** (frontend) + **Render** (backend via Docker) + **Upstash** (Redis).

---

## Step 1: Push Code to GitHub

```bash
cd C:\Storage\Projects\SmartSpend
git init
git add .
git commit -m "Initial commit - SmartSpend AI"
git remote add origin https://github.com/YOUR_USERNAME/SmartSpend.git
git branch -M main
git push -u origin main
```

> ⚠️ Make sure `.env` is in `.gitignore` — never push secrets.

---

## Step 2: Set Up PostgreSQL on Render

1. [render.com](https://render.com) → **New → PostgreSQL**
2. Name: `smartspend-db`, Plan: **Free**, Create
3. Copy the **Internal Database URL**
4. **Prepend** `+asyncpg` to the scheme:

```
# Render gives you:
postgresql://user:pass@host/dbname

# You need (add +asyncpg):
postgresql+asyncpg://user:pass@host/dbname
```

---

## Step 3: Set Up Free Redis (Upstash)

1. [upstash.com](https://upstash.com) → Create Database → Choose region
2. Your Redis URL needs the `rediss://` scheme (double-s for TLS)

Extract just the URL part (drop the `redis-cli --tls -u` prefix):
```
rediss://default:YOUR_PASSWORD@your-host.upstash.io:6379
```
> Note: Use `rediss://` (with double-s) for Upstash since it requires TLS.

---

## Step 4: Deploy Backend on Render (Docker)

Render uses Docker to build your backend. The `Dockerfile` is already in `backend/`.

1. [render.com](https://render.com) → **New → Web Service**
2. Connect your GitHub repo
3. Fill in the fields you see:

| Field | Value |
|---|---|
| **Name** | `smartspend-api` |
| **Docker Build Context Directory** | `backend/` |
| **Dockerfile Path** | `backend/Dockerfile` |
| **Docker Command** | *(leave empty — Dockerfile CMD handles it)* |
| **Pre-Deploy Command** | *(leave empty)* |
| **Auto-Deploy** | `On Commit` |

4. Scroll up to **Environment Variables** and add these:

| Variable | Value |
|---|---|
| `APP_ENV` | `production` |
| `SECRET_KEY` | *(generate: `python -c "import secrets; print(secrets.token_hex(32))"`)* |
| `ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` |
| `DATABASE_URL` | `postgresql+asyncpg://smartspend_db_d0hd_user:u5LwEXsf6omm0fqUYTs9Ny2nz7yJ3aIr@dpg-d70nnqv5gffc7391u0p0-a/smartspend_db_d0hd` |
| `REDIS_URL` | `rediss://default:gQAAAAAAAUGlAAIncDJjZmNkODE3Yzg2MmI0MTczYWRlZDIyNDQ5OTVlMWNjOHAyODIzNDE@advanced-dogfish-82341.upstash.io:6379` |
| `GEMINI_API_KEY` | *(your Gemini key)* |
| `GEMINI_MODEL` | `gemini-2.5-flash` |
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `465` |
| `SMTP_USER` | *(your Gmail)* |
| `SMTP_PASSWORD` | *(your Gmail App Password)* |
| `ALLOWED_ORIGINS` | `https://your-app.vercel.app` *(update after Step 5)* |
| `FRONTEND_URL` | `https://your-app.vercel.app` *(update after Step 5)* |
| `GOOGLE_CLIENT_ID` | *(your OAuth client ID)* |
| `GOOGLE_CLIENT_SECRET` | *(your OAuth secret)* |
| `GOOGLE_REDIRECT_URI` | `https://smartspend-api.onrender.com/api/v1/auth/google/callback` |

5. Click **Deploy Web Service**
6. Wait ~5 minutes for the Docker image to build
7. Your backend URL: `https://smartspend-api.onrender.com`

---

## Step 5: Deploy Frontend on Vercel

1. [vercel.com](https://vercel.com) → Sign up with GitHub
2. **Add New → Project** → Import your `SmartSpend` repo
3. Configure:

| Field | Value |
|---|---|
| **Framework Preset** | Vite |
| **Root Directory** | `frontend` |
| **Build Command** | `npm run build` |
| **Output Directory** | `dist` |

4. **Environment Variable:**

| Variable | Value |
|---|---|
| `VITE_API_URL` | `https://smartspend-api.onrender.com/api/v1` |

5. Click **Deploy**

### After Deploy — Update Backend CORS

Go back to Render → your service → **Environment** → update:
```
ALLOWED_ORIGINS=https://your-app.vercel.app
```

---

## Step 6: Seed Demo Data (Optional)

In Render → your service → **Shell** tab:
```bash
python seed_mock_data.py
python seed_insights_demo.py
```

---

## 🔄 Deploying New Changes

```bash
git add .
git commit -m "feat: your changes"
git push origin main
```

Both **Vercel** and **Render** auto-deploy on push. Zero manual steps.

**Manual redeploy:** Dashboard → Service → **Manual Deploy** / **Redeploy**

---

## 🛡️ Production Checklist

- [ ] Generate new `SECRET_KEY` for production
- [ ] `.env` is in `.gitignore`
- [ ] CORS configured with Vercel domain
- [ ] Google OAuth redirect URI updated
- [ ] Test login, voice input, and receipt upload

---

## 🔧 Troubleshooting

| Issue | Fix |
|---|---|
| Backend takes 30s | Free tier sleeps after 15min inactivity |
| CORS errors | Add Vercel URL to `ALLOWED_ORIGINS` |
| DB connection fails | Use `postgresql+asyncpg://` not `postgresql://` |
| Redis connection fails | Use `rediss://` (double-s) for Upstash TLS |
| Frontend "Network Error" | Check `VITE_API_URL` in Vercel env vars |

---

## 💰 Cost: $0/month

| Service | Tier | Cost |
|---|---|---|
| Vercel (Frontend) | Hobby | Free |
| Render (Backend) | Free | Free |
| Render (PostgreSQL) | Free | Free (90 days, then $7/mo) |
| Upstash (Redis) | Free | Free (10k commands/day) |

> After 90 days, swap to [Neon](https://neon.tech) or [Supabase](https://supabase.com) for free-forever PostgreSQL.
