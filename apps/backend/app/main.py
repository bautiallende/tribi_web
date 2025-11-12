import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .api import catalog_router
from .api.auth import router as auth_router
from .api.orders import router as orders_router, payments_router, esims_router
from .api.admin import router as admin_router
from .core.config import settings

load_dotenv()

app = FastAPI(title="Tribi Backend", version="0.1.0")

# CORS middleware with credentials support for cookies
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(catalog_router)
app.include_router(auth_router)
app.include_router(orders_router)
app.include_router(payments_router)
app.include_router(esims_router)
app.include_router(admin_router)


@app.get("/health")
def read_health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
