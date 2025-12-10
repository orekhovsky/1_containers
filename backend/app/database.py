import os
import logging
from datetime import datetime
from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Integer,
    String,
    DateTime,
    text,
    insert,
    select,
    func,
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

# === Логирование ===
LOG_DIR = os.getenv("LOG_DIR")
os.makedirs(LOG_DIR, exist_ok=True)
logger = logging.getLogger("database")
if not logger.handlers:
    handler = logging.FileHandler(f"{LOG_DIR}/database.log")
    handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(levelname)s - [%(name)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# === Конфигурация БД ===
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    postgres_user = os.getenv("POSTGRES_USER", "app")
    postgres_password = os.getenv("POSTGRES_PASSWORD", "app")
    postgres_host = os.getenv("POSTGRES_HOST", "db")
    postgres_port = os.getenv("POSTGRES_PORT", "5432")
    postgres_db = os.getenv("POSTGRES_DB", "urls")
    DATABASE_URL = f"postgresql+asyncpg://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"
    logger.info(f"Constructed DATABASE_URL from components: postgresql+asyncpg://{postgres_user}:***@{postgres_host}:{postgres_port}/{postgres_db}")
else:
    masked_url = DATABASE_URL.split("@")[0].split(":")[0] + ":***@" + "@".join(DATABASE_URL.split("@")[1:])
    logger.info(f"Using DATABASE_URL from environment: {masked_url}")

# === Схема БД ===
logger.info("Initializing database schema...")
metadata = MetaData()
short_links = Table(
    "short_links",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("short_code", String(32), unique=True, nullable=False, index=True),
    Column("original_url", String(2048), nullable=False),
    Column("created_at", DateTime, nullable=False, server_default=text("now()")),
)

# === Подключение к БД ===
logger.info("Creating database engine...")
engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)
logger.info("Database engine created successfully")


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session


async def create_short_link(short_code: str, original_url: str) -> bool:
    logger.debug(f"Attempting to create short_link: {short_code} -> {original_url}")
    async with AsyncSessionLocal() as session:
        try:
            await session.execute(
                insert(short_links).values(
                    short_code=short_code,
                    original_url=original_url,
                    created_at=datetime.utcnow(),
                )
            )
            await session.commit()
            logger.info(f"Successfully created short_link in database: {short_code} -> {original_url}")
            return True
        except IntegrityError as e:
            await session.rollback()
            logger.warning(f"IntegrityError: short_code {short_code} already exists in database")
            return False
        except Exception as e:
            logger.error(f"Error creating short_link {short_code}: {str(e)}")
            await session.rollback()
            raise


async def get_original_url(short_code: str) -> str | None:
    logger.debug(f"Querying database for short_code: {short_code}")
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(short_links.c.original_url).where(
                    short_links.c.short_code == short_code
                )
            )
            row = result.first()
            if row:
                logger.info(f"Found original_url for short_code {short_code}: {row[0]}")
                return row[0]
            else:
                logger.warning(f"Short_code not found in database: {short_code}")
                return None
        except Exception as e:
            logger.error(f"Error querying database for short_code {short_code}: {str(e)}")
            raise


async def count_links() -> int:
    logger.debug("Counting total links in database")
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(func.count()).select_from(short_links)
            )
            count = result.scalar_one()
            logger.info(f"Total links in database: {count}")
            return count
        except Exception as e:
            logger.error(f"Error counting links: {str(e)}")
            raise


async def get_short_code_by_url(original_url: str) -> str | None:
    logger.debug(f"Querying database for original_url: {original_url}")
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(short_links.c.short_code).where(
                    short_links.c.original_url == original_url
                )
            )
            row = result.first()
            if row:
                logger.info(f"Found short_code for original_url {original_url}: {row[0]}")
                return row[0]
            else:
                logger.debug(f"Original_url not found in database: {original_url}")
                return None
        except Exception as e:
            logger.error(f"Error querying database for original_url {original_url}: {str(e)}")
            raise
