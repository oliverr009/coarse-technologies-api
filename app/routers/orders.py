from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.models import Order, OrderItem, Product, OrderStatus
from app.schemas import (
    OrderCreate, OrderUpdate, OrderResponse, OrderListResponse,
    DashboardResponse, DashboardStats, RecentOrderItem, OrderStatusCount
)
from app.routers.auth import get_current_user, get_admin_user
from app.models import User

router = APIRouter()

STATUS_COLORS = {
    "pending": "#FFA500",
    "confirmed": "#4CAF50",
    "processing": "#2196F3",
    "shipped": "#9C27B0",
    "delivered": "#008000",
    "cancelled": "#F44336"
}

@router.post("", response_model=OrderResponse)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    total_amount = 0
    order_items = []
    
    for item in order.items:
        product = db.query(Product).filter(
            Product.id == item.product_id,
            Product.is_active == 1
        ).first()
        
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        
        if product.stock_quantity < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {product.name}. Available: {product.stock_quantity}"
            )
        
        product.stock_quantity -= item.quantity
        subtotal = product.price * item.quantity
        total_amount += subtotal
        
        order_items.append({
            "product_id": item.product_id,
            "quantity": item.quantity,
            "unit_price": product.price,
            "subtotal": subtotal
        })
    
    db_order = Order(
        customer_email=order.customer_email,
        customer_name=order.customer_name,
        customer_phone=order.customer_phone,
        shipping_address=order.shipping_address,
        city=order.city,
        postal_code=order.postal_code,
        total_amount=total_amount,
        currency="KES",
        status=OrderStatus.PENDING.value,
        notes=order.notes
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    for item_data in order_items:
        db_item = OrderItem(order_id=db_order.id, **item_data)
        db.add(db_item)
    
    db.commit()
    db.refresh(db_order)
    return db_order

@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    total_orders = db.query(Order).count()
    orders_today = db.query(Order).filter(Order.created_at >= today).count()
    pending_orders = db.query(Order).filter(Order.status == OrderStatus.PENDING.value).count()
    confirmed_orders = db.query(Order).filter(Order.status == OrderStatus.CONFIRMED.value).count()
    delivered_orders = db.query(Order).filter(Order.status == OrderStatus.DELIVERED.value).count()
    
    total_revenue = db.query(func.sum(Order.total_amount)).filter(
        Order.status != OrderStatus.CANCELLED.value
    ).scalar() or 0.0
    
    yesterday = today - timedelta(days=1)
    today_revenue = db.query(func.sum(Order.total_amount)).filter(
        Order.created_at >= today,
        Order.status != OrderStatus.CANCELLED.value
    ).scalar() or 0.0
    
    yesterday_revenue = db.query(func.sum(Order.total_amount)).filter(
        Order.created_at >= yesterday,
        Order.created_at < today,
        Order.status != OrderStatus.CANCELLED.value
    ).scalar() or 0.0
    
    revenue_change = None
    if yesterday_revenue > 0:
        revenue_change = round(((today_revenue - yesterday_revenue) / yesterday_revenue) * 100, 1)
    
    recent = db.query(
        Order.id,
        Order.customer_name,
        Order.customer_email,
        Order.total_amount,
        Order.currency,
        Order.status,
        Order.created_at,
        func.count(OrderItem.id).label("item_count")
    ).join(OrderItem).group_by(Order.id).order_by(Order.created_at.desc()).limit(5).all()
    
    recent_orders = [
        RecentOrderItem(
            id=r.id,
            customer_name=r.customer_name,
            customer_email=r.customer_email,
            total_amount=r.total_amount,
            currency=r.currency or "KES",
            status=r.status,
            item_count=r.item_count,
            created_at=r.created_at
        ) for r in recent
    ]
    
    status_counts = db.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
    status_breakdown = [
        OrderStatusCount(
            status=status,
            count=count,
            color=STATUS_COLORS.get(status, "#999999")
        ) for status, count in status_counts
    ]
    
    return DashboardResponse(
        stats=DashboardStats(
            total_orders=total_orders,
            orders_today=orders_today,
            pending_orders=pending_orders,
            confirmed_orders=confirmed_orders,
            delivered_orders=delivered_orders,
            total_revenue=round(total_revenue, 2),
            currency="KES",
            revenue_change_percent=revenue_change
        ),
        recent_orders=recent_orders,
        status_breakdown=status_breakdown
    )

@router.get("", response_model=List[OrderListResponse])
def list_orders(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    customer_email: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    query = db.query(
        Order.id,
        Order.customer_email,
        Order.customer_name,
        Order.total_amount,
        Order.currency,
        Order.status,
        Order.tracking_number,
        Order.created_at,
        func.count(OrderItem.id).label("item_count")
    ).join(OrderItem).group_by(Order.id)
    
    if status:
        query = query.filter(Order.status == status)
    if customer_email:
        query = query.filter(Order.customer_email.ilike(f"%{customer_email}%"))
    if date_from:
        query = query.filter(Order.created_at >= date_from)
    if date_to:
        query = query.filter(Order.created_at <= date_to)
    
    results = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        OrderListResponse(
            id=r.id,
            customer_email=r.customer_email,
            customer_name=r.customer_name,
            total_amount=r.total_amount,
            currency=r.currency or "KES",
            status=r.status,
            tracking_number=r.tracking_number,
            created_at=r.created_at,
            item_count=r.item_count
        ) for r in results
    ]

@router.get("/my-orders", response_model=List[OrderListResponse])
def get_my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    orders = db.query(Order).filter(Order.user_id == current_user.id).all()
    return orders

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if not current_user.is_admin and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return order

@router.put("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int,
    order_update: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    new_status = order_update.status.value if hasattr(order_update.status, 'value') else order_update.status
    
    if new_status == OrderStatus.CONFIRMED.value and db_order.status != OrderStatus.CONFIRMED.value:
        db_order.confirmed_at = datetime.utcnow()
    elif new_status == OrderStatus.SHIPPED.value and db_order.status != OrderStatus.SHIPPED.value:
        db_order.shipped_at = datetime.utcnow()
    elif new_status == OrderStatus.DELIVERED.value and db_order.status != OrderStatus.DELIVERED.value:
        db_order.delivered_at = datetime.utcnow()
    
    if order_update.status:
        db_order.status = new_status
    if order_update.tracking_number is not None:
        db_order.tracking_number = order_update.tracking_number
    if order_update.notes is not None:
        db_order.notes = order_update.notes
    
    db.commit()
    db.refresh(db_order)
    return db_order

@router.get("/{order_id}/track")
def track_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {
        "order_id": order.id,
        "status": order.status,
        "tracking_number": order.tracking_number,
        "estimated_delivery": None,
        "last_updated": order.updated_at,
        "timeline": [
            {"status": "Order Placed", "date": order.created_at, "completed": True},
            {"status": "Confirmed", "date": order.confirmed_at, "completed": order.confirmed_at is not None},
            {"status": "Shipped", "date": order.shipped_at, "completed": order.shipped_at is not None},
            {"status": "Delivered", "date": order.delivered_at, "completed": order.delivered_at is not None},
        ],
        "items": [
            {
                "product_name": item.product.name if item.product else "Unknown",
                "quantity": item.quantity,
                "price": item.unit_price
            } for item in order.items
        ]
    }

@router.post("/{order_id}/confirm")
def confirm_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.status != OrderStatus.PENDING.value:
        raise HTTPException(status_code=400, detail=f"Cannot confirm order with status: {order.status}")
    
    order.status = OrderStatus.CONFIRMED.value
    order.confirmed_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Order confirmed", "order_id": order.id, "confirmed_at": order.confirmed_at}
