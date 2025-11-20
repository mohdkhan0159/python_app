# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.settings import settings
import urllib.parse

Base = declarative_base()

# ----------------------------------------------------------
# SELECT DATABASE BASED ON ENVIRONMENT
# ----------------------------------------------------------
def build_azure_sql_url():
    """
    Convert standard AZURE_SQL_CONNECTION_STRING into a valid
    SQLAlchemy async connection string using aioodbc.
    """

    raw = settings.AZURE_SQL_CONNECTION_STRING
    if not raw:
        return None

    # Azure SQL typical format:
    # Server=tcp:myserver.database.windows.net,1433;Database=mydb;User ID=user;Password=pass;
    # OR user may provide SQLAlchemy-style URL.

    if raw.startswith("mssql"):
        # User already provided a SQLAlchemy URL
        return raw

    # Otherwise, convert Key Vault–style connection strings
    parts = dict(
        item.split("=", 1)
        for item in raw.replace(";", "&").split("&")
        if "=" in item
    )

    server = parts.get("Server") or parts.get("server")
    database = parts.get("Database") or parts.get("database")
    user = parts.get("User ID") or parts.get("uid") or parts.get("user")
    password = parts.get("Password") or parts.get("pwd")

    if not (server and database and user and password):
        raise ValueError("Invalid Azure SQL connection string format.")

    # remove 'tcp:' prefix
    server = server.replace("tcp:", "")

    # SQLAlchemy async driver (aioodbc)
    password_enc = urllib.parse.quote_plus(password)

    url = (
        f"mssql+aioodbc://{user}:{password_enc}@{server}/{database}"
        "?driver=ODBC+Driver+18+for+SQL+Server"
        "&Encrypt=yes"
        "&TrustServerCertificate=no"
    )

    return url


# ----------------------------------------------------------
# PICK DATABASE URL (LOCAL OR AZURE)
# ----------------------------------------------------------
if settings.ENV in ("production", "prod") and settings.AZURE_SQL_CONNECTION_STRING:
    print("Using Azure SQL")
    DATABASE_URL = build_azure_sql_url()
else:
    print("Using local SQLite")
    DATABASE_URL = settings.DATABASE_URL


# ----------------------------------------------------------
# SQLALCHEMY ENGINE (ASYNC)
# ----------------------------------------------------------
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    future=True,
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
