# Pose Tracker — Render deployment package

This Flask app supports **Upload Photo** and **Upload Video** pose tracking. The Live Camera option is removed.

## Deploy on Render

1. Upload this folder to a GitHub repository (the files in this folder must be at the repository root).
2. In Render, choose **New → Web Service**, connect the repository, and select the Python runtime.
3. Set:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app --workers 1 --threads 4 --timeout 180`
4. Deploy. Render provides an `onrender.com` URL when the build succeeds.

Python is pinned to 3.11 for dependency compatibility. `opencv-python-headless` is used for server hosting (no desktop GUI dependencies).

## Run locally

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000.

## Hosting notes

- Video uploads are saved in the app's `uploads/` folder. On ephemeral hosting, files may be removed when the service restarts or redeploys; process videos promptly or configure persistent storage if you need long-term retention.
- Pose processing uses CPU and can be slow for large videos. Start with short, smaller videos.
