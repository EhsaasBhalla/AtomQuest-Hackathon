# Continuous Deployment Hosting Guide (Vercel + Railway)

This guide walks you through deploying your AtomQuest Performance Portal for free. By connecting your GitHub repository to these platforms, **any changes you push to GitHub will automatically build and deploy to your live websites within seconds!**

## Step 1: Prepare Your GitHub Repository
Both Vercel and Railway use GitHub to trigger automatic updates. 
1. Open your terminal in `e:\New folder` and commit all your current files:
   ```bash
   git add .
   git commit -m "Initial commit for hackathon"
   git push origin main
   ```
2. Make sure both your `frontend/` and `backend/` folders are in this single repository.

---

## Step 2: Host the Frontend on Vercel
Vercel is the creator of Next.js and the absolute best place to host Vue/Vite applications. It provides a free global edge network and **never sleeps**.

1. Go to [Vercel.com](https://vercel.com/) and sign up using your GitHub account.
2. Click **Add New** > **Project**.
3. Import your GitHub repository.
4. **Important Configurations:**
   - **Framework Preset**: Select `Vite` (or Vue.js).
   - **Root Directory**: Click "Edit" and select your `frontend` folder (since your code isn't in the absolute root).
   - **Build Command**: Leave as `npm run build` (default).
   - **Output Directory**: Leave as `dist` (default).
5. Expand **Environment Variables**:
   - Add `VITE_API_URL` and set the value to your *future* backend URL (e.g., `https://your-railway-app.up.railway.app/api`). If you don't have the backend URL yet, you can skip this and add it later in the Vercel Settings -> Environment Variables tab.
6. Click **Deploy**.

> [!NOTE]
> **Automatic Updates:** Whenever you make a change to your frontend code locally and run `git push`, Vercel will instantly detect it, rebuild your Vue app, and push it live!

---

## Step 3: Host the Backend & SQLite on Railway
Railway is perfect for Flask and SQLite because it offers persistent disks on its free tier ($5/mo credit), meaning your SQLite database will survive server restarts.

1. Go to [Railway.app](https://railway.app/) and sign up with GitHub.
2. Click **New Project** > **Deploy from GitHub repo**.
3. Select your repository.
4. Go to your new service's **Settings**:
   - **Root Directory**: Change this to `/backend`.
   - **Start Command**: Railway will auto-detect Python, but it's safest to explicitly set the start command to: `gunicorn -w 1 -b 0.0.0.0:$PORT "run:app"`
5. Go to the **Variables** tab and add your environment variables:
   - `SECRET_KEY=your-secret-key`
   - `JWT_SECRET_KEY=your-jwt-secret-key`
   - `REDIS_URL=rediss://default:gQAAAAAAAfhGAAIgcDI5MTNmZWY5ZTliZTY0NWNjODFjMTVmZTYwMzI4NzQ4Nw@knowing-gnat-129094.upstash.io:6379`
6. **Critical: Add a Persistent Volume for SQLite!**
   - Go to the **Volumes** tab.
   - Click **Create Volume**.
   - Set the Mount Path to `/app/instance`. (This ensures that the `goaltracker.db` file created by Flask isn't deleted when Railway pushes a new update).

> [!TIP]
> **Automatic Updates:** Just like Vercel, anytime you run `git push origin main`, Railway will intercept the webhook, shut down your old backend, spin up a new one with your updated Python code, and re-attach your SQLite volume automatically!

---

## The Workflow for Future Changes
Once both are deployed, your development workflow becomes incredibly simple:
1. You make changes to your code on your local computer.
2. You test them locally.
3. You run `git add .`, `git commit -m "my update"`, and `git push`.
4. Grab a cup of coffee. In 60 seconds, your live production website will be updated automatically.
