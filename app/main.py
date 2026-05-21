from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app import models  # noqa: F401
from app.routers import (
    address_router,
    auth_router,
    bouquet_router,
    category_router,
    order_router,
    review_router,
    shop_router,
    upload_router,
    user_router,
)

app = FastAPI(title="Flower Shop API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(address_router)
app.include_router(category_router)
app.include_router(shop_router)
app.include_router(bouquet_router)
app.include_router(order_router)
app.include_router(review_router)
app.include_router(upload_router)

if settings.AUTO_CREATE_TABLES:
    Base.metadata.create_all(bind=engine)


@app.get("/health", tags=["Health"])
def healthcheck():
    return {"status": "ok"}
