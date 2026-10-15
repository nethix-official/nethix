NETHIX 1.0 SETUP

1. Keep your current Cloudflare Pages project. Upload the new index.html to the same GitHub repo.
2. Deploy app.py and requirements.txt on a Python web host (e.g. Render). Build command: pip install -r requirements.txt ; Start command: gunicorn --workers 1 --threads 2 --timeout 180 app:app
3. Set environment variable FRONTEND_ORIGIN to the exact origin of your Cloudflare site, e.g. https://YOUR-SITE.pages.dev (no trailing slash).
4. Copy the real backend URL, e.g. https://YOUR-BACKEND.onrender.com. In index.html replace https://YOUR-BACKEND.onrender.com with that real URL. Commit changes.
5. Test an eligible public video you own/have permission to save. Check browser Downloads (not necessarily Gallery).

Limits: Not all platforms/videos work; private/login/DRM videos not supported. Host may prohibit this use or impose bandwidth/time limits. Do not publish this demo at scale without authentication, per-IP rate limits, abuse monitoring, and hosting-policy review.
