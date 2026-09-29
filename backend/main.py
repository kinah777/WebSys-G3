import sys
from pathlib import Path
import uvicorn

# Ensure the backend directory is in sys.path so 'app' is importable when launched from anywhere
_backend_dir = Path(__file__).resolve().parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

if __name__ == "__main__":
    uvicorn.run("app.api:app", host="127.0.0.1", port=8000, reload=True)