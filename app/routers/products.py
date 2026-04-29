from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid

from app.database import get_db
from app.models import Product, User
from app.schemas import ProductCreate, ProductUpdate, ProductResponse
from app.routers.auth import get_admin_user, get_current_user

router = APIRouter()

# =========================
# IMAGE UPLOAD (ADD THIS)
# =========================
@router.post("/upload-images")
async def upload_images(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    uploaded_urls = []
    upload_dir = "uploads/products"
    os.makedirs(upload_dir, exist_ok=True)

    for file in files:
        file_ext = file.filename.split(".")[-1]
        file_name = f"{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(upload_dir, file_name)

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        uploaded_urls.append(f"/uploads/products/{file_name}")

    return {"image_urls": uploaded_urls}


# =========================
# PRODUCTS
# =========================

@router.get("", response_model=List[ProductResponse])
def list_products(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Product).filter(Product.is_active == 1)
    
    if category:
        query = query.filter(Product.category == category)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    
    return query.offset(skip).limit(limit).all()


@router.get("/categories", response_model=List[str])
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Product.category).distinct().filter(Product.category != None).all()
    return [c[0] for c in categories]


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id, Product.is_active == 1).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = product_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db_product.is_active = False
    db.commit()
    return {"message": "Product deleted successfully"}


@router.post("/{product_id}/restock")
def restock_product(
    product_id: int,
    quantity: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product.stock_quantity += quantity
    db.commit()
    return {"message": f"Restocked {quantity} units", "new_stock": product.stock_quantity}
