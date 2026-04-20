# Deployment Guide for Cortex Flow HR System

## 1. What this setup does
- `requirements.txt` lists the Python packages you need.
- `Procfile` tells Render and other hosts how to start the app with `gunicorn`.
- `runtime.txt` pins the Python version.
- `main.py` now uses `PORT` and `HOST` environment variables, so it works on cloud services.
- `.gitignore` avoids uploading your virtual environment, SQLite database, and cache files.

## 2. Test locally first
1. Activate your virtual environment:
   - `& ".\.venv\Scripts\Activate.ps1"`
2. Install requirements:
   - `python -m pip install -r requirements.txt`
3. Run the app locally:
   - `python main.py`
4. Open in browser:
   - `http://localhost:5000`

## 3. Prepare GitHub repository
1. Open a terminal in this project folder.
2. Initialize Git:
   - `git init`
3. Add files:
   - `git add .`
4. Commit:
   - `git commit -m "Initial Flask app deployment setup"`
5. Create a GitHub repository on GitHub.com.
6. Link the remote repository:
   - `git remote add origin https://github.com/<your-username>/<repo-name>.git`
7. Push to GitHub:
   - `git branch -M main`
   - `git push -u origin main`

## 4. Deploy to Render (recommended)
1. Go to https://render.com and sign up or log in.
2. Click **New** → **Web Service**.
3. Connect your GitHub account and select your repository.
4. Use these settings:
   - Environment: `Python`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn main:app`
   - Region: choose the nearest region to your users.
5. Click **Create Web Service**.
6. Wait for the deploy to finish, then open the provided URL.

### Notes for Render
- Render sets `PORT` automatically, so your app will start correctly.
- If the app fails to start, check the Render deploy logs.
- Your app will stay online while the service is running.

## 5. What happens after deployment
- The app will run from Render, so you do not need to keep your laptop on.
- The public URL from Render is what users will open.
- The SQLite file `cortexflow.db` will be created on the server and stored inside the project folder.

## 6. Security reminder
- Change the admin password after deployment.
- Do not commit any secret keys or passwords to GitHub.
- If you want, I can help you add a simple admin password change page or secure the database further.
