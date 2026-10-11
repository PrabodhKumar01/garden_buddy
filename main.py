"""
GardenBuddy Root ASGI Entrypoint.

Exposes `app` at the root module level so that deployments using
either `uvicorn main:app` or `uvicorn app.main:app` start seamlessly.
"""

from app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

