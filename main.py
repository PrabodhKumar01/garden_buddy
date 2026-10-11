"""
GardenBuddy Root ASGI Entrypoint.

Exposes `app` at the root module level so that deployments using
either `uvicorn main:app` or `uvicorn app.main:app` start seamlessly.
"""

import os
import sys

try:
    from app.main import app
except Exception as exc:
    import traceback
    traceback.print_exc(file=sys.stderr)
    raise exc

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
