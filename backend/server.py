from fastapi import FastAPI, APIRouter, HTTPException, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Urban Bites API", version="0.1.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ------------- Utils -------------

def now_utc_iso():
    return datetime.now(timezone.utc).isoformat()


def new_id() -> str:
    return str(uuid.uuid4())


async def ensure_indexes():
    await db.products.create_index("categories")
    await db.products.create_index("name")
    await db.products.create_index("_id")
    await db.orders.create_index("_id")
    await db.coupons.create_index("code", unique=True)


# ------------- Data Models -------------

class Image(BaseModel):
    url: str
    alt: Optional[str] = None


class Variant(BaseModel):
    variant_id: str = Field(default_factory=new_id)
    name: str
    price_delta: float = 0.0


class AddOn(BaseModel):
    add_on_id: str = Field(default_factory=new_id)
    name: str
    price_delta: float = 0.0


class Product(BaseModel):
    product_id: str = Field(default_factory=new_id)
    name: str
    description: Optional[str] = None
    base_price: float
    categories: List[str] = []  # category slugs
    images: List[Image] = []
    availability: Optional[Dict[str, Any]] = None
    variants: List[Variant] = []
    add_ons: List[AddOn] = []

    def to_mongo(self) -> dict:
        d = self.model_dump()
        d["_id"] = d.pop("product_id")
        return d


class Coupon(BaseModel):
    coupon_id: str = Field(default_factory=new_id)
    code: str
    discount_type: str  # percent | fixed
    amount: float
    min_order_value: float = 0.0
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    usage_limit: Optional[int] = None

    def to_mongo(self) -> dict:
        d = self.model_dump()
        d["_id"] = d.pop("coupon_id")
        return d


class OrderItem(BaseModel):
    product_id: str
    product_name: str
    variant_id: Optional[str] = None
    variant_name: Optional[str] = None
    quantity: int
    unit_price: float
    add_on_ids: List[str] = []
    add_ons: List[Dict[str, Any]] = []
    line_total: float


class Address(BaseModel):
    street: str
    city: str
    postal_code: str
    instructions: Optional[str] = None


class Order(BaseModel):
    order_id: str = Field(default_factory=new_id)
    user_info: Dict[str, Any]
    cart_snapshot: Dict[str, Any]
    payment_status: str = "pending"  # pending/paid/failed (payments disabled in MVP)
    fulfillment_type: str  # pickup/delivery
    delivery_address: Optional[Address] = None
    pickup_location: Optional[str] = None
    order_status: str = "received"  # received→preparing→ready→completed
    totals: Dict[str, float]
    timestamps: Dict[str, str] = Field(default_factory=lambda: {"created_at": now_utc_iso(), "updated_at": now_utc_iso()})

    def to_mongo(self) -> dict:
        d = self.model_dump()
        d["_id"] = d.pop("order_id")
        return d


# ------------- Seed Data -------------

HERO_IMG = {
    "url": "https://images.unsplash.com/photo-1482049016688-2d3e1b311543?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2Mzl8MHwxfHNlYXJjaHwxfHxmb29kfGVufDB8fHx8MTc1NDY3MTUwNHww&ixlib=rb-4.1.0&q=85",
    "alt": "Urban Bites hero",
}
BURGER1 = {
    "url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDF8MHwxfHNlYXJjaHwxfHxidXJnZXJ8ZW58MHx8fHwxNzU0NjcyNzQ2fDA&ixlib=rb-4.1.0&q=85",
    "alt": "Gourmet burger",
}
BURGER2 = {
    "url": "https://images.unsplash.com/photo-1550547660-d9450f859349?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDF8MHwxfHNlYXJjaHwyfHxidXJnZXJ8ZW58MHx8fHwxNzU0NjcyNzQ2fDA&ixlib=rb-4.1.0&q=85",
    "alt": "Burger dark background",
}
COFFEE1 = {
    "url": "https://images.unsplash.com/photo-1509042239860-f550ce710b93?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzd8MHwxfHNlYXJjaHw0fHxjb2ZmZWV8ZW58MHx8fHwxNzU0NjcyNzUyfDA&ixlib=rb-4.1.0&q=85",
    "alt": "Latte art",
}
COFFEE2 = {
    "url": "https://images.pexels.com/photos/312418/pexels-photo-312418.jpeg",
    "alt": "Coffee professional",
}


async def seed_menu():
    count = await db.products.count_documents({})
    if count > 0:
        return

    products = [
        Product(
            name="Urban Classic Burger",
            description="Juicy beef patty, cheddar, lettuce, tomato, secret sauce.",
            base_price=8.99,
            categories=["burgers"],
            images=[Image(**BURGER1)],
            availability={"days": "all", "times": "11:00-22:00"},
            variants=[
                Variant(name="Regular", price_delta=0.0),
                Variant(name="Large", price_delta=2.0),
            ],
            add_ons=[
                AddOn(name="Extra Cheese", price_delta=1.0),
                AddOn(name="Bacon", price_delta=1.5),
            ],
        ),
        Product(
            name="Smoky Double Burger",
            description="Double beef, smoked gouda, caramelized onions.",
            base_price=12.5,
            categories=["burgers"],
            images=[Image(**BURGER2)],
            availability={"days": "all", "times": "11:00-22:00"},
            variants=[
                Variant(name="Regular", price_delta=0.0),
                Variant(name="Large", price_delta=2.5),
            ],
            add_ons=[
                AddOn(name="Jalapeño", price_delta=0.8),
                AddOn(name="Truffle Mayo", price_delta=1.2),
            ],
        ),
        Product(
            name="Artisanal Latte",
            description="Hand-pulled espresso with velvety milk.",
            base_price=4.0,
            categories=["coffee"],
            images=[Image(**COFFEE1)],
            availability={"days": "all", "times": "07:00-20:00"},
            variants=[
                Variant(name="8 oz", price_delta=0.0),
                Variant(name="12 oz", price_delta=0.8),
                Variant(name="16 oz", price_delta=1.5),
            ],
            add_ons=[
                AddOn(name="Oat Milk", price_delta=0.5),
                AddOn(name="Extra Shot", price_delta=0.8),
            ],
        ),
        Product(
            name="Cold Brew",
            description="Slow-steeped, smooth and bold.",
            base_price=3.5,
            categories=["coffee"],
            images=[Image(**COFFEE2)],
            availability={"days": "all", "times": "07:00-20:00"},
            variants=[
                Variant(name="12 oz", price_delta=0.0),
                Variant(name="16 oz", price_delta=1.0),
            ],
            add_ons=[
                AddOn(name="Vanilla Syrup", price_delta=0.4),
                AddOn(name="Caramel Syrup", price_delta=0.4),
            ],
        ),
    ]

    # Insert products with _id = product_id
    await db.products.insert_many([p.to_mongo() for p in products])

    # Basic coupons
    coupons = [
        Coupon(code="URBAN10", discount_type="percent", amount=10.0, min_order_value=15.0),
        Coupon(code="WELCOME5", discount_type="fixed", amount=5.0, min_order_value=20.0),
    ]
    await db.coupons.insert_many([c.to_mongo() for c in coupons])

    # App settings
    await db.settings.update_one(
        {"_id": "public"},
        {
            "$set": {
                "brand": {"name": "Urban Bites", "theme": "dark"},
                "tax_rate": 0.08,
                "currency": "USD",
                "payments_enabled": False,
                "restaurant_hours": {"mon_sun": "07:00-22:00"},
            }
        },
        upsert=True,
    )


# ------------- Routers -------------

config_router = APIRouter(prefix="/config", tags=["config"])
menu_router = APIRouter(prefix="/menu", tags=["menu"])
promo_router = APIRouter(prefix="/cart", tags=["cart"])
orders_router = APIRouter(prefix="/orders", tags=["orders"])
payments_router = APIRouter(prefix="/payments", tags=["payments"])  # stub


@config_router.get("/public")
async def get_public_config():
    settings = await db.settings.find_one({"_id": "public"})
    if not settings:
        await seed_menu()
        settings = await db.settings.find_one({"_id": "public"})
    return {
        "brand": settings.get("brand", {"name": "Urban Bites", "theme": "dark"}),
        "currency": settings.get("currency", "USD"),
        "tax_rate": settings.get("tax_rate", 0.0),
        "payments_enabled": settings.get("payments_enabled", False),
        "hero_image": HERO_IMG,
    }


@menu_router.get("/categories")
async def get_categories():
    # Derive category slugs from products
    cursor = db.products.find({}, {"categories": 1})
    cats = set()
    async for doc in cursor:
        for c in doc.get("categories", []):
            cats.add(c)
    categories = [{"slug": c, "name": c.capitalize()} for c in sorted(list(cats))]
    return categories


@menu_router.get("/products")
async def list_products(category: Optional[str] = None, q: Optional[str] = None):
    query: Dict[str, Any] = {}
    if category:
        query["categories"] = category
    if q:
        query["name"] = {"$regex": q, "$options": "i"}
    docs = await db.products.find(query).to_list(500)
    for d in docs:
        d["product_id"] = d.pop("_id")
    return docs


class CouponCheckRequest(BaseModel):
    code: str
    subtotal: float


@promo_router.post("/validate-coupon")
async def validate_coupon(req: CouponCheckRequest):
    code = req.code.strip().upper()
    coupon = await db.coupons.find_one({"code": code})
    if not coupon:
        raise HTTPException(status_code=404, detail="Invalid coupon code")

    if req.subtotal &lt; coupon.get("min_order_value", 0):
        raise HTTPException(status_code=400, detail="Subtotal too low for this coupon")

    discount_amount = 0.0
    if coupon["discount_type"] == "percent":
        discount_amount = round(req.subtotal * (coupon["amount"] / 100.0), 2)
    else:
        discount_amount = round(coupon["amount"], 2)

    return {
        "coupon_id": coupon.get("_id"),
        "code": coupon["code"],
        "discount_type": coupon["discount_type"],
        "amount": coupon["amount"],
        "discount_amount": discount_amount,
    }


class OrderItemInput(BaseModel):
    product_id: str
    variant_id: Optional[str] = None
    quantity: int = 1
    add_on_ids: List[str] = []


class UserInfo(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None


class OrderCreateRequest(BaseModel):
    items: List[OrderItemInput]
    user: UserInfo
    fulfillment_type: str  # pickup | delivery
    delivery_address: Optional[Address] = None
    pickup_location: Optional[str] = None
    tip_amount: float = 0.0
    coupon_code: Optional[str] = None


class OrderCreateResponse(BaseModel):
    order_id: str
    order_status: str
    payment_status: str
    totals: Dict[str, float]


async def price_item(product_doc: dict, variant_id: Optional[str], add_on_ids: List[str]) -> Dict[str, Any]:
    base_price = float(product_doc["base_price"])
    variant_name = None
    unit_price = base_price

    for v in product_doc.get("variants", []):
        if v.get("variant_id") == variant_id:
            unit_price += float(v.get("price_delta", 0))
            variant_name = v.get("name")
            break

    selected_addons: List[Dict[str, Any]] = []
    for a in product_doc.get("add_ons", []):
        if a.get("add_on_id") in add_on_ids:
            unit_price += float(a.get("price_delta", 0))
            selected_addons.append(a)

    return {
        "unit_price": round(unit_price, 2),
        "variant_name": variant_name,
        "selected_addons": selected_addons,
    }


@orders_router.post("/", response_model=OrderCreateResponse)
async def create_order(payload: OrderCreateRequest):
    settings = await db.settings.find_one({"_id": "public"}) or {"tax_rate": 0.0}
    tax_rate = float(settings.get("tax_rate", 0.0))

    # Price items
    order_items: List[OrderItem] = []
    subtotal = 0.0
    for item in payload.items:
        prod = await db.products.find_one({"_id": item.product_id})
        if not prod:
            raise HTTPException(status_code=404, detail=f"Product not found: {item.product_id}")
        priced = await price_item(prod, item.variant_id, item.add_on_ids)
        line_total = round(priced["unit_price"] * item.quantity, 2)
        subtotal = round(subtotal + line_total, 2)
        order_items.append(
            OrderItem(
                product_id=prod["_id"],
                product_name=prod["name"],
                variant_id=item.variant_id,
                variant_name=priced["variant_name"],
                quantity=item.quantity,
                unit_price=priced["unit_price"],
                add_on_ids=item.add_on_ids,
                add_ons=priced["selected_addons"],
                line_total=line_total,
            )
        )

    discount_amount = 0.0
    applied_coupon: Optional[dict] = None
    if payload.coupon_code:
        try:
            validation = await validate_coupon(CouponCheckRequest(code=payload.coupon_code, subtotal=subtotal))
            discount_amount = float(validation["discount_amount"]) if isinstance(validation, dict) else float(validation.discount_amount)  # type: ignore
            applied_coupon = validation if isinstance(validation, dict) else validation.model_dump()  # type: ignore
        except HTTPException:
            pass  # silently ignore invalid coupon

    taxable_amount = max(0.0, subtotal - discount_amount)
    tax_amount = round(taxable_amount * tax_rate, 2)
    total = round(taxable_amount + tax_amount + float(payload.tip_amount or 0.0), 2)

    order = Order(
        user_info=payload.user.model_dump(),
        cart_snapshot={
            "items": [oi.model_dump() for oi in order_items],
            "subtotal": subtotal,
            "discount_amount": discount_amount,
            "tax_amount": tax_amount,
            "tip_amount": float(payload.tip_amount or 0.0),
            "total": total,
            "coupon": applied_coupon,
        },
        fulfillment_type=payload.fulfillment_type,
        delivery_address=payload.delivery_address,
        pickup_location=payload.pickup_location,
        totals={
            "subtotal": subtotal,
            "discount_amount": discount_amount,
            "tax_amount": tax_amount,
            "tip_amount": float(payload.tip_amount or 0.0),
            "total": total,
        },
    )

    doc = order.to_mongo()
    await db.orders.insert_one(doc)

    return OrderCreateResponse(
        order_id=doc["_id"],
        order_status=doc["order_status"],
        payment_status=doc["payment_status"],
        totals=doc["totals"],
    )


@orders_router.get("/{order_id}")
async def get_order(order_id: str):
    doc = await db.orders.find_one({"_id": order_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Order not found")
    doc["order_id"] = doc.pop("_id")
    return doc


@payments_router.get("/providers")
async def payment_providers():
    settings = await db.settings.find_one({"_id": "public"}) or {}
    enabled = settings.get("payments_enabled", False)
    return {"payments_enabled": enabled, "providers": []}


# Legacy demo endpoints retained
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StatusCheckCreate(BaseModel):
    client_name: str


@api_router.get("/")
async def root():
    return {"message": "Hello World"}


@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj


@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]


# Include feature routers
api_router.include_router(config_router)
api_router.include_router(menu_router)
api_router.include_router(promo_router)
api_router.include_router(orders_router)
api_router.include_router(payments_router)

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def on_startup():
    await ensure_indexes()
    await seed_menu()


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()