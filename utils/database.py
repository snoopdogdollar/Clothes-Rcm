"""
Database connection and session management using SQLAlchemy
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from config import Config

# Create database engine
engine = create_engine(
    Config.DATABASE_URL,
    echo=Config.DEBUG,  # Log SQL queries in debug mode
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=10,  # Connection pool size
    max_overflow=20  # Max overflow connections
)

# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

# Base class for all models
Base = declarative_base()

def get_db():
    """
    Dependency function to get database session.
    Use with FastAPI Depends() to inject database session into endpoints.
    
    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            items = db.query(ClothingItem).all()
            return items
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initialize database tables.
    Creates all tables defined in models if they don't exist.
    
    Call this once when starting the application.
    """
    from models.item import ClothingItem, ItemColor, Outfit, OutfitFeedback  # Import models
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables initialized")

def drop_all_tables():
    """
    Drop all tables (use with caution!).
    Only use in development for resetting database.
    """
    if Config.DEBUG:
        Base.metadata.drop_all(bind=engine)
        print("⚠ All tables dropped")
    else:
        raise Exception("Cannot drop tables in production mode")
