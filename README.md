# Coarse Technologies E-Commerce Backend

FastAPI backend for products, orders, order tracking and admin dashboard.

## Included
- `/api/products` product API
- `/api/orders` order API
- `/api/orders/{order_id}/track` public tracking
- `/api/orders/dashboard` admin stats
- `/health` health check
- `render.yaml` for Render deployment
- sample products auto-seeded so frontend can show products immediately

## Run locally
```bash
pip install -r requirements.txt
python main.py
```

Test:
```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/api/products
http://127.0.0.1:8000/docs
```

## Push to GitHub
```bash
git init
git add .
git commit -m "Coarse Technologies Backend v2"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/coarse-technologies-api.git
git push -u origin main
```
