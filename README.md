# Plain Downloader

FastAPI backend (`main.py`) and static frontend (`index.html`). The backend uses yt-dlp and its installed bgutil PO Token Provider plugin. The separate existing Node bgutil service is still required for YouTube requests.

## Render backend

Deploy this directory as a Docker Web Service. Set the environment variable `BGUTIL_URL` to the base URL of your existing Node provider, for example `https://my-yt-token-provider.onrender.com` (omit `/get_pot`). The default in `main.py` is that same example URL; change the environment variable if your actual service differs. Keep the Node service running with a compatible current bgutil server version.

The Dockerfile installs the Python provider plugin and Deno. It starts Uvicorn on port 8000; configure Render's port accordingly if needed. Configure the frontend's `API_BASE` in `index.html` to the backend's public URL.

## Verify

After deploying, request `/formats?url=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DqSSOa7AjkGs` and inspect backend/provider logs. If player extraction still fails, enable yt-dlp verbose logging for a single request and check the loaded provider, connection errors and YouTube response. A PO token cannot repair an IP block by itself.

Use the downloader only for content you have permission to download.
