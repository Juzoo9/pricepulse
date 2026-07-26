from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, func, select
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    url = Column(String, nullable=False)
    title = Column(String, nullable=False)
    current_price = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    image_url = Column(String, nullable=False)
    parser_type = Column(String, nullable=False)
    threshold = Column(Float, nullable=False, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    price_history = relationship("PriceHistory", back_populates="product")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    product = relationship("Product", back_populates="price_history")


DATABASE_URL = "sqlite+aiosqlite:///pricepulse.db"

engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine, class_=AsyncSession)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def add_product(
    user_id: int,
    url: str,
    title: str,
    price: float,
    currency: str,
    image_url: str,
    parser_type: str,
    threshold: float = 0,
) -> Product:
    async with async_session() as session:
        product = Product(
            user_id=user_id,
            url=url,
            title=title,
            current_price=price,
            currency=currency,
            image_url=image_url,
            parser_type=parser_type,
            threshold=threshold,
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product


async def get_user_products(user_id: int) -> list[Product]:
    async with async_session() as session:
        result = await session.execute(
            select(Product).where(Product.user_id == user_id)
        )
        return list(result.scalars().all())


async def get_all_products() -> list[Product]:
    async with async_session() as session:
        result = await session.execute(select(Product))
        return list(result.scalars().all())


async def update_price(product_id: int, new_price: float):
    async with async_session() as session:
        product = await session.get(Product, product_id)
        if product is None:
            raise ValueError(f"Product with id {product_id} not found")
        product.current_price = new_price
        history = PriceHistory(product_id=product_id, price=new_price)
        session.add(history)
        await session.commit()


async def get_price_history(product_id: int) -> list[tuple]:
    async with async_session() as session:
        result = await session.execute(
            select(PriceHistory)
            .where(PriceHistory.product_id == product_id)
            .order_by(PriceHistory.timestamp)
        )
        rows = result.all()
        return [(row.timestamp, row.price) for row in rows]


async def get_product_by_id(product_id: int) -> Product | None:
    async with async_session() as session:
        return await session.get(Product, product_id)


async def delete_product(product_id: int):
    async with async_session() as session:
        product = await session.get(Product, product_id)
        if product is None:
            raise ValueError(f"Product with id {product_id} not found")
        await session.delete(product)
        await session.commit()


async def get_stats() -> dict:
    async with async_session() as session:
        users_result = await session.execute(select(func.count(Product.user_id.distinct())))
        unique_users = users_result.scalar() or 0

        products_result = await session.execute(select(func.count(Product.id)))
        total_products = products_result.scalar() or 0

        checks_result = await session.execute(select(func.count(PriceHistory.id)))
        total_checks = checks_result.scalar() or 0

    return {
        "unique_users": unique_users,
        "total_products": total_products,
        "total_checks": total_checks,
    }