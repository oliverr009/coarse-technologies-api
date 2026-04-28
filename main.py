from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import products, orders, auth
from app.seed import seed_products
from app.database import SessionLocal
import uvicorn
import os

Base.metadata.create_all(bind=engine)

db = SessionLocal()
try:
    seed_products(db)
finally:
    db.close()

app = FastAPI(
    title="Coarse Technologies API",
    description="E-commerce backend for product creation and order tracking",
    version="2.0.0"
)

frontend_url = os.getenv("FRONTEND_URL", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url] if frontend_url != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])

@app.get("/")
def root():
    return {"message": "Coarse Technologies API", "docs": "/docs", "dashboard": "/api/orders/dashboard", "health": "/health"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "2.0.0"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
