from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from app.models import OrderStatus

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    is_admin: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock_quantity: int = 0
    category: Optional[str] = None
    sku: Optional[str] = None
    image_url: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock_quantity: Optional[int] = None
    category: Optional[str] = None
    sku: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None

class ProductResponse(ProductBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    subtotal: float
    product: Optional[ProductResponse]
    
    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    customer_email: EmailStr
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    shipping_address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    items: List[OrderItemCreate]
    notes: Optional[str] = None

class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    tracking_number: Optional[str] = None
    notes: Optional[str] = None

class OrderResponse(BaseModel):
    id: int
    user_id: Optional[int]
    customer_email: str
    customer_name: Optional[str]
    customer_phone: Optional[str]
    shipping_address: Optional[str]
    city: Optional[str]
    postal_code: Optional[str]
    total_amount: float
    currency: str
    status: str
    tracking_number: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    confirmed_at: Optional[datetime]
    shipped_at: Optional[datetime]
    delivered_at: Optional[datetime]
    items: List[OrderItemResponse]
    
    class Config:
        from_attributes = True

class OrderListResponse(BaseModel):
    id: int
    customer_email: str
    customer_name: Optional[str]
    total_amount: float
    currency: str
    status: str
    tracking_number: Optional[str]
    created_at: datetime
    item_count: int
    
    class Config:
        from_attributes = True

class DashboardStats(BaseModel):
    total_orders: int
    orders_today: int
    pending_orders: int
    confirmed_orders: int
    delivered_orders: int
    total_revenue: float
    currency: str
    revenue_change_percent: Optional[float] = None

class RecentOrderItem(BaseModel):
    id: int
    customer_name: Optional[str]
    customer_email: str
    total_amount: float
    currency: str
    status: str
    item_count: int
    created_at: datetime

class OrderStatusCount(BaseModel):
    status: str
    count: int
    color: str

class DashboardResponse(BaseModel):
    stats: DashboardStats
    recent_orders: List[RecentOrderItem]
    status_breakdown: List[OrderStatusCount]
