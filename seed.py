from decimal import Decimal

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.bouquet import Bouquet
from app.models.category import Category
from app.models.enums import BouquetStatus, ShopStatus, UserRole
from app.models.review import Review
from app.models.shop import Shop
from app.models.user import User
from app.services.review_service import ReviewService
from app.services.user_service import UserService
from app.utils.formatters import normalize_phone_uz


def seed_admin(db) -> User:
    admin_name = "Admin"
    admin_email = "admin@example.com"
    admin_password = "admin123"

    service = UserService(db)
    existing_admin = service.get_by_email(admin_email)
    if existing_admin is not None:
        print(f"Admin already exists: {admin_email}")
        return existing_admin

    admin = service.create_admin(admin_name, admin_email, admin_password)
    print(f"Admin created: {admin_email}")
    return admin


def get_or_create_owner(db, payload: dict) -> User:
    owner = db.execute(select(User).where(User.email == payload["email"])).scalar_one_or_none()
    if owner:
        owner.full_name = payload["full_name"]
        owner.phone = normalize_phone_uz(payload["phone"])
        owner.roles = list(dict.fromkeys([*(owner.roles or []), UserRole.OWNER, UserRole.CUSTOMER]))
        owner.is_active = True
        db.add(owner)
        db.commit()
        db.refresh(owner)
        return owner

    owner = User(
        full_name=payload["full_name"],
        email=payload["email"],
        phone=normalize_phone_uz(payload["phone"]),
        password_hash=hash_password(payload.get("password", "owner123")),
        roles=[UserRole.OWNER, UserRole.CUSTOMER],
        is_active=True,
    )
    db.add(owner)
    db.commit()
    db.refresh(owner)
    print(f"Owner created: {owner.email}")
    return owner


def get_or_create_customer(db, payload: dict) -> User:
    customer = db.execute(select(User).where(User.email == payload["email"])).scalar_one_or_none()
    if customer:
        customer.full_name = payload["full_name"]
        customer.phone = normalize_phone_uz(payload["phone"]) if payload.get("phone") else None
        customer.roles = [UserRole.CUSTOMER]
        customer.is_active = True
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer

    customer = User(
        full_name=payload["full_name"],
        email=payload["email"],
        phone=normalize_phone_uz(payload["phone"]) if payload.get("phone") else None,
        password_hash=hash_password(payload.get("password", "customer123")),
        roles=[UserRole.CUSTOMER],
        is_active=True,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def get_or_create_shop(db, owner: User, payload: dict) -> Shop:
    shop = db.execute(select(Shop).where(Shop.slug == payload["slug"])).scalar_one_or_none()
    mapped_payload = {
        **payload,
        "owner_id": owner.id,
        "phone": normalize_phone_uz(payload["phone"]),
        "status": ShopStatus.ACTIVE,
    }

    if shop is None:
        shop = Shop(**mapped_payload)
    else:
        for key, value in mapped_payload.items():
            setattr(shop, key, value)

    db.add(shop)
    db.commit()
    db.refresh(shop)
    return shop


def upsert_category(db, payload: dict) -> Category:
    category = db.execute(select(Category).where(Category.slug == payload["slug"])).scalar_one_or_none()
    if category is None:
        category = Category(**payload)
    else:
        for key, value in payload.items():
            setattr(category, key, value)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def upsert_bouquet(
    db,
    shop_map: dict[str, Shop],
    category_map: dict[str, Category],
    payload: dict,
) -> Bouquet:
    shop = shop_map[payload["shop_slug"]]
    bouquet = db.execute(
        select(Bouquet).where(Bouquet.shop_id == shop.id, Bouquet.slug == payload["slug"])
    ).scalar_one_or_none()

    mapped_payload = {
        **payload,
        "shop_id": shop.id,
        "category_id": category_map[payload["category_slug"]].id,
    }
    mapped_payload.pop("shop_slug", None)
    mapped_payload.pop("category_slug", None)

    if bouquet is None:
        bouquet = Bouquet(**mapped_payload)
    else:
        for key, value in mapped_payload.items():
            setattr(bouquet, key, value)

    db.add(bouquet)
    db.commit()
    db.refresh(bouquet)
    return bouquet


def money(value: str) -> Decimal:
    return Decimal(value)


def bouquet_payload(
    shop_slug: str,
    category_slug: str,
    name: str,
    slug: str,
    description: str,
    compound: str,
    price: str,
    old_price: str | None,
    image: str,
    extra_images: list[str],
    size: str,
    stock: int,
) -> dict:
    return {
        "shop_slug": shop_slug,
        "category_slug": category_slug,
        "name": name,
        "slug": slug,
        "description": description,
        "compound": compound,
        "price": money(price),
        "old_price": money(old_price) if old_price else None,
        "image": image,
        "images": [image, *extra_images],
        "size": size,
        "stock": stock,
        "status": BouquetStatus.ACTIVE,
        "rating": Decimal("0.0"),
        "reviews_count": 0,
    }


def seed_reviews(db, shop_map: dict[str, Shop], bouquets: dict[str, Bouquet]) -> None:
    customer_payloads = [
        {"full_name": "Nilufar Karimova", "email": "nilufar.customer@example.com", "phone": "+998 91 220 11 44"},
        {"full_name": "Aziza Mamatova", "email": "aziza.customer@example.com", "phone": "+998 93 540 22 18"},
        {"full_name": "Madina Rasulova", "email": "madina.customer@example.com", "phone": "+998 94 321 55 09"},
        {"full_name": "Sardor Olimov", "email": "sardor.customer@example.com", "phone": "+998 90 618 72 31"},
        {"full_name": "Kamola Tursunova", "email": "kamola.customer@example.com", "phone": "+998 97 404 33 21"},
        {"full_name": "Jasur Rahimov", "email": "jasur.customer@example.com", "phone": "+998 99 876 54 32"},
        {"full_name": "Malika Saidova", "email": "malika.customer@example.com", "phone": "+998 95 118 90 22"},
        {"full_name": "Diyor Bekmurodov", "email": "diyor.customer@example.com", "phone": "+998 90 650 40 10"},
    ]
    customers = [get_or_create_customer(db, payload) for payload in customer_payloads]
    customer_ids = [customer.id for customer in customers]
    shop_ids = [shop.id for shop in shop_map.values()]

    db.query(Review).filter(
        Review.shop_id.in_(shop_ids),
        Review.user_id.in_(customer_ids),
    ).delete(synchronize_session=False)
    db.commit()

    review_texts = [
        "Gullar juda yangi, wrapping ham premium ko'rindi. Sovg'a qilgan odamim juda xursand bo'ldi.",
        "Delivery vaqtida keldi, carddagi yozuv ham chiroyli qilib tayyorlangan.",
        "Ranglari rasmdagidan ham nafisroq. Buket hajmi va sifati narxiga arziydi.",
        "Operator tez javob berdi, buyurtma jarayoni juda qulay bo'ldi.",
        "Buket juda didli yig'ilgan, gullar ertasi kuni ham chiroyli turdi.",
        "Tantanali sovg'a uchun ideal. Packaging, lenta va kompozitsiya juda mos.",
        "Yaqin insonimga yubordim, suratdagidek chiroyli yetib bordi.",
        "Sifati zo'r, faqat bayram kunlari oldindan buyurtma qilish kerak ekan.",
        "Fresh, elegant and neat. I will definitely order again.",
        "Juda muloyim ranglar, ayniqsa pastel bouquetlar juda nozik chiqibdi.",
    ]
    ratings = [5, 5, 5, 4, 5, 4, 5, 5, 5, 4]

    bouquet_items = list(bouquets.values())
    for index, bouquet in enumerate(bouquet_items):
        review_count = 3 if index % 3 == 0 else 2
        for review_index in range(review_count):
            customer = customers[(index + review_index) % len(customers)]
            text = review_texts[(index * 2 + review_index) % len(review_texts)]
            rating = ratings[(index + review_index) % len(ratings)]
            db.add(
                Review(
                    user_id=customer.id,
                    shop_id=bouquet.shop_id,
                    bouquet_id=bouquet.id,
                    rating=rating,
                    text=text,
                    is_verified=review_index == 0,
                    is_approved=True,
                )
            )
    db.commit()

    review_service = ReviewService(db)
    for bouquet in bouquet_items:
        review_service._recalculate_ratings(bouquet.shop_id, bouquet.id)


def seed_catalog(db) -> None:
    owner_payloads = [
        {
            "full_name": "Muslima Boutique Owner",
            "email": "owner@muslima.uz",
            "phone": "+998 90 123 45 67",
            "password": "owner123",
        },
        {
            "full_name": "Lola Garden Owner",
            "email": "owner@lolagarden.uz",
            "phone": "+998 91 444 22 11",
            "password": "owner123",
        },
        {
            "full_name": "Rose Avenue Owner",
            "email": "owner@roseavenue.uz",
            "phone": "+998 93 555 33 22",
            "password": "owner123",
        },
        {
            "full_name": "Bloom House Owner",
            "email": "owner@bloomhouse.uz",
            "phone": "+998 94 777 88 99",
            "password": "owner123",
        },
    ]
    owners = [get_or_create_owner(db, payload) for payload in owner_payloads]

    shop_payloads = [
        {
            "name": "Muslima Flower Boutique",
            "slug": "muslima-boutique",
            "description": "Luxury flower arrangements for romantic evenings, birthdays, weddings, and meaningful everyday surprises.",
            "logo": "https://images.unsplash.com/photo-1525310072745-f49212b5ac6d?auto=format&fit=crop&w=300&q=80",
            "banner": "https://images.unsplash.com/photo-1526045431048-f857369baa09?auto=format&fit=crop&w=1400&q=80",
            "phone": "+998 90 777 66 55",
            "address": "45 Garden Avenue, Tashkent",
            "city": "Tashkent",
            "latitude": "41.311081",
            "longitude": "69.240562",
            "working_hours": "09:00 - 22:00",
            "rating": Decimal("0.0"),
            "reviews_count": 0,
        },
        {
            "name": "Lola Garden Studio",
            "slug": "lola-garden-studio",
            "description": "Soft seasonal bouquets, pastel arrangements, and warm family celebration flowers.",
            "logo": "https://images.unsplash.com/photo-1490750967868-88aa4486c946?auto=format&fit=crop&w=300&q=80",
            "banner": "https://images.unsplash.com/photo-1468327768560-75b778cbb551?auto=format&fit=crop&w=1400&q=80",
            "phone": "+998 91 444 22 11",
            "address": "18 Amir Temur Street, Tashkent",
            "city": "Tashkent",
            "latitude": "41.327546",
            "longitude": "69.281920",
            "working_hours": "08:30 - 21:30",
            "rating": Decimal("0.0"),
            "reviews_count": 0,
        },
        {
            "name": "Rose Avenue",
            "slug": "rose-avenue",
            "description": "Expressive rose boxes, anniversary flowers, and premium romantic arrangements.",
            "logo": "https://images.unsplash.com/photo-1518895949257-7621c3c786d7?auto=format&fit=crop&w=300&q=80",
            "banner": "https://images.unsplash.com/photo-1519378058457-4c29a0a2efac?auto=format&fit=crop&w=1400&q=80",
            "phone": "+998 93 555 33 22",
            "address": "7 Shota Rustaveli Street, Tashkent",
            "city": "Tashkent",
            "latitude": "41.285895",
            "longitude": "69.239891",
            "working_hours": "10:00 - 23:00",
            "rating": Decimal("0.0"),
            "reviews_count": 0,
        },
        {
            "name": "Bloom House Tashkent",
            "slug": "bloom-house-tashkent",
            "description": "Modern floral styling for weddings, get-well gifts, newborn celebrations, and daily bouquets.",
            "logo": "https://images.unsplash.com/photo-1508610048659-a06b669e3321?auto=format&fit=crop&w=300&q=80",
            "banner": "https://images.unsplash.com/photo-1508610048659-a06b669e3321?auto=format&fit=crop&w=1400&q=80",
            "phone": "+998 94 777 88 99",
            "address": "22 Nukus Street, Tashkent",
            "city": "Tashkent",
            "latitude": "41.299496",
            "longitude": "69.272984",
            "working_hours": "09:00 - 22:30",
            "rating": Decimal("0.0"),
            "reviews_count": 0,
        },
    ]
    shop_map = {
        payload["slug"]: get_or_create_shop(db, owners[index], payload)
        for index, payload in enumerate(shop_payloads)
    }

    category_payloads = [
        {"name": "Roses", "slug": "roses", "image": "https://images.unsplash.com/photo-1518895949257-7621c3c786d7?auto=format&fit=crop&w=500&q=80", "is_active": True},
        {"name": "Birthday", "slug": "birthday", "image": "https://images.unsplash.com/photo-1464195244916-405fa0a82545?auto=format&fit=crop&w=500&q=80", "is_active": True},
        {"name": "Anniversary", "slug": "anniversary", "image": "https://images.unsplash.com/photo-1520763185298-1b434c919102?auto=format&fit=crop&w=500&q=80", "is_active": True},
        {"name": "Wedding", "slug": "wedding", "image": "https://images.unsplash.com/photo-1525258946800-98cfd641d0de?auto=format&fit=crop&w=500&q=80", "is_active": True},
        {"name": "New Baby", "slug": "new-baby", "image": "https://images.unsplash.com/photo-1516589091380-5d6017b7c32f?auto=format&fit=crop&w=500&q=80", "is_active": True},
        {"name": "Get Well Soon", "slug": "get-well-soon", "image": "https://images.unsplash.com/photo-1490750967868-88aa4486c946?auto=format&fit=crop&w=500&q=80", "is_active": True},
    ]
    category_map = {
        category_payload["slug"]: upsert_category(db, category_payload)
        for category_payload in category_payloads
    }

    img = {
        "red": "https://images.unsplash.com/photo-1519378058457-4c29a0a2efac?auto=format&fit=crop&w=900&q=80",
        "rose": "https://images.unsplash.com/photo-1518895949257-7621c3c786d7?auto=format&fit=crop&w=900&q=80",
        "pink": "https://images.unsplash.com/photo-1563241527-3004b7be0ffd?auto=format&fit=crop&w=900&q=80",
        "mixed": "https://images.unsplash.com/photo-1526397751294-331021109fbd?auto=format&fit=crop&w=900&q=80",
        "white": "https://images.unsplash.com/photo-1508610048659-a06b669e3321?auto=format&fit=crop&w=900&q=80",
        "baby": "https://images.unsplash.com/photo-1468327768560-75b778cbb551?auto=format&fit=crop&w=900&q=80",
        "yellow": "https://images.unsplash.com/photo-1490750967868-88aa4486c946?auto=format&fit=crop&w=900&q=80",
        "tulip": "https://images.unsplash.com/photo-1520763185298-1b434c919102?auto=format&fit=crop&w=900&q=80",
        "cream": "https://images.unsplash.com/photo-1487530811176-3780de880c2d?auto=format&fit=crop&w=900&q=80",
        "field": "https://images.unsplash.com/photo-1518709779341-56cf4535e94b?auto=format&fit=crop&w=900&q=80",
    }

    bouquet_specs = [
        ("muslima-boutique", "roses", "Red Passion", "red-passion", "Velvety red roses with eucalyptus and a premium satin wrap.", "25 red roses, eucalyptus, hypericum berries", "85.00", "92.00", img["red"], [img["rose"], img["mixed"]], "Large", 14),
        ("muslima-boutique", "birthday", "Blush Romance", "blush-romance", "A joyful pink bouquet designed to brighten birthdays instantly.", "Pink roses, carnations, spray roses, wrapping paper", "78.00", "84.00", img["pink"], [img["yellow"], img["field"]], "Medium", 11),
        ("muslima-boutique", "anniversary", "Pure Love", "pure-love", "A dramatic anniversary arrangement with ruby and blush tones.", "Red roses, pink roses, carnations, ruscus", "92.00", "101.00", img["mixed"], [img["tulip"], img["red"]], "Large", 9),
        ("muslima-boutique", "wedding", "White Whisper", "white-whisper", "Elegant ivory roses curated for graceful wedding moments.", "White roses, lisianthus, baby's breath", "80.00", None, img["white"], [img["cream"], img["baby"]], "Large", 12),
        ("muslima-boutique", "new-baby", "Little Miracle", "little-miracle", "Soft peach and cream flowers for welcoming a newborn.", "Peach roses, white tulips, chamomile, ribbon", "74.00", "79.00", img["baby"], [img["field"], img["cream"]], "Medium", 8),
        ("muslima-boutique", "get-well-soon", "Tender Recovery", "tender-recovery", "Fresh pastel tones created to send warmth and strength.", "Cream roses, hydrangea, chrysanthemums, greenery", "69.00", None, img["yellow"], [img["cream"], img["field"]], "Medium", 16),
        ("lola-garden-studio", "birthday", "Sunlit Joy", "sunlit-joy", "Bright sunflowers and garden greens for cheerful birthdays.", "Sunflowers, solidago, eucalyptus, kraft wrap", "58.00", "65.00", img["yellow"], [img["field"], img["rose"]], "Medium", 18),
        ("lola-garden-studio", "roses", "Garden Rose Mix", "garden-rose-mix", "A soft rose bouquet with garden textures and a light ribbon.", "Garden roses, spray roses, ruscus", "72.00", None, img["rose"], [img["pink"], img["mixed"]], "Medium", 13),
        ("lola-garden-studio", "anniversary", "Velvet Promise", "velvet-promise", "Deep red and mauve blooms for elegant anniversaries.", "Roses, carnations, eucalyptus, velvet ribbon", "88.00", "96.00", img["red"], [img["mixed"], img["rose"]], "Large", 10),
        ("lola-garden-studio", "get-well-soon", "Morning Smile", "morning-smile", "Light yellow flowers that feel fresh, calm, and uplifting.", "Daisies, chrysanthemums, yellow roses", "54.00", None, img["field"], [img["yellow"], img["cream"]], "Small", 22),
        ("lola-garden-studio", "new-baby", "Peach Lullaby", "peach-lullaby", "Peach and cream bouquet for a gentle newborn greeting.", "Peach roses, chamomile, soft greenery", "67.00", "72.00", img["baby"], [img["cream"], img["pink"]], "Medium", 15),
        ("lola-garden-studio", "wedding", "Ivory Garden", "ivory-garden", "A refined white bouquet for intimate bridal styling.", "White roses, lisianthus, eucalyptus", "98.00", None, img["white"], [img["cream"], img["tulip"]], "Large", 7),
        ("rose-avenue", "roses", "Crimson Box", "crimson-box", "Premium red roses arranged in a modern round box.", "31 red roses, box, satin ribbon", "105.00", "118.00", img["red"], [img["rose"], img["mixed"]], "Premium", 6),
        ("rose-avenue", "anniversary", "Moonlit Love", "moonlit-love", "Romantic roses and pale flowers with a luxury evening mood.", "Red roses, white roses, eucalyptus", "96.00", None, img["mixed"], [img["white"], img["red"]], "Large", 8),
        ("rose-avenue", "birthday", "Candy Bloom", "candy-bloom", "Playful pink bouquet for sweet birthday surprises.", "Pink roses, carnations, tulips, ribbon", "63.00", "70.00", img["pink"], [img["tulip"], img["yellow"]], "Medium", 17),
        ("rose-avenue", "wedding", "Pearl Ceremony", "pearl-ceremony", "White roses and airy greens for elegant ceremony styling.", "White roses, baby's breath, ruscus", "115.00", None, img["white"], [img["cream"], img["baby"]], "Premium", 5),
        ("rose-avenue", "roses", "Ruby Classic", "ruby-classic", "Classic red rose bouquet with a clean romantic silhouette.", "19 red roses, eucalyptus, premium wrap", "73.00", None, img["rose"], [img["red"], img["mixed"]], "Medium", 20),
        ("rose-avenue", "get-well-soon", "Soft Comfort", "soft-comfort", "Cream and yellow tones designed to feel warm and calm.", "Cream roses, chamomile, yellow mums", "59.00", None, img["cream"], [img["yellow"], img["field"]], "Small", 19),
        ("bloom-house-tashkent", "wedding", "Snow Veil", "snow-veil", "Minimal white florals for bridal portraits and ceremonies.", "White roses, orchids, baby's breath", "125.00", "140.00", img["white"], [img["cream"], img["tulip"]], "Premium", 4),
        ("bloom-house-tashkent", "birthday", "Rainbow Wish", "rainbow-wish", "Colorful blooms for a lively and memorable birthday.", "Mixed roses, tulips, seasonal greens", "82.00", None, img["mixed"], [img["pink"], img["yellow"]], "Large", 12),
        ("bloom-house-tashkent", "new-baby", "Tiny Angel", "tiny-angel", "Cream and blush flowers wrapped for a newborn celebration.", "Cream roses, peach flowers, satin ribbon", "76.00", "83.00", img["baby"], [img["cream"], img["white"]], "Medium", 9),
        ("bloom-house-tashkent", "anniversary", "Golden Memory", "golden-memory", "Warm yellow and blush arrangement for lasting memories.", "Yellow roses, blush roses, greenery", "79.00", None, img["yellow"], [img["pink"], img["field"]], "Large", 14),
        ("bloom-house-tashkent", "roses", "Rose Atelier", "rose-atelier", "Designer rose bouquet with layered colors and couture wrapping.", "Roses, spray roses, eucalyptus, ribbon", "89.00", "99.00", img["pink"], [img["rose"], img["mixed"]], "Large", 10),
        ("bloom-house-tashkent", "get-well-soon", "Calm Meadow", "calm-meadow", "Fresh meadow-inspired bouquet for thoughtful care.", "Daisies, hydrangea, greenery, kraft wrap", "57.00", None, img["field"], [img["yellow"], img["cream"]], "Medium", 21),
        ("bloom-house-tashkent", "wedding", "Lace Bouquet", "lace-bouquet", "Soft ivory bouquet with delicate textures and graceful volume.", "Ivory roses, lisianthus, gypsophila", "108.00", None, img["cream"], [img["white"], img["baby"]], "Large", 6),
    ]

    bouquets = {}
    for spec in bouquet_specs:
        payload = bouquet_payload(*spec)
        bouquet = upsert_bouquet(db, shop_map, category_map, payload)
        bouquets[f"{payload['shop_slug']}:{bouquet.slug}"] = bouquet

    seed_reviews(db, shop_map, bouquets)

    print(
        f"Seeded {len(shop_payloads)} shops, {len(category_payloads)} categories, "
        f"{len(bouquet_specs)} bouquets and fresh reviews"
    )


def main() -> None:
    db = SessionLocal()
    try:
        seed_admin(db)
        seed_catalog(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
