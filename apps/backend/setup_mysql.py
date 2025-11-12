#!/usr/bin/env python
"""
Script to initialize MySQL database for local testing.
Creates schema and runs migrations.

Usage: python setup_mysql.py
"""
import sys
from pathlib import Path

# Add the app directory to the path so we can import the models
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from app.models import Base
from app.core.config import settings

def create_database():
    """Create database if it doesn't exist."""
    # Connect to MySQL without specifying a database
    engine_url = f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}"
    engine = create_engine(engine_url)
    
    with engine.connect() as connection:
        # Check if database exists
        result = connection.execute(
            text(f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{settings.MYSQL_DB}'")
        )
        if not result.fetchone():
            print(f"📦 Creating database '{settings.MYSQL_DB}'...")
            connection.execute(text(f"CREATE DATABASE {settings.MYSQL_DB}"))
            connection.commit()
            print(f"✅ Database '{settings.MYSQL_DB}' created successfully!")
        else:
            print(f"✅ Database '{settings.MYSQL_DB}' already exists.")
    
    engine.dispose()

def create_tables():
    """Create all tables using SQLAlchemy models."""
    print(f"\n📊 Connecting to {settings.database_url.split('@')[1]}...")
    engine = create_engine(settings.database_url, echo=False)
    
    # Create all tables
    print("📋 Creating tables...")
    Base.metadata.create_all(engine)
    print("✅ All tables created successfully!")
    
    # List created tables
    with engine.connect() as connection:
        result = connection.execute(
            text(f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{settings.MYSQL_DB}'")
        )
        tables = [row[0] for row in result.fetchall()]
        if tables:
            print(f"\n📋 Tables in '{settings.MYSQL_DB}':")
            for table in sorted(tables):
                print(f"   ✓ {table}")
    
    engine.dispose()

def verify_connection():
    """Verify database connection."""
    print("\n🔍 Verifying connection...")
    try:
        engine = create_engine(settings.database_url)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
        engine.dispose()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🗄️  MySQL Database Setup")
    print("=" * 60)
    print("\n📍 Configuration:")
    print(f"   Host: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}")
    print(f"   User: {settings.MYSQL_USER}")
    print(f"   Database: {settings.MYSQL_DB}")
    
    try:
        # Step 1: Verify initial connection to MySQL
        print("\n⏳ Step 1: Verifying MySQL connection...")
        engine_url = f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}"
        engine = create_engine(engine_url, connect_args={"connect_timeout": 5})
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        engine.dispose()
        print("✅ MySQL is running and accessible!")
        
        # Step 2: Create database
        print("\n⏳ Step 2: Creating database...")
        create_database()
        
        # Step 3: Create tables
        print("\n⏳ Step 3: Creating tables...")
        create_tables()
        
        # Step 4: Verify final connection
        print("\n⏳ Step 4: Final verification...")
        if verify_connection():
            print("\n" + "=" * 60)
            print("✅ Setup completed successfully!")
            print("=" * 60)
            print("\nYou can now run:")
            print("  python -m pytest tests/ -v")
            print("  alembic upgrade head")
            print("  python app/main.py")
        else:
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        print("\nMake sure MySQL is running:")
        print("  • MySQL service is started")
        print("  • Credentials are correct (root:1234@localhost)")
        print("  • You can connect using: mysql -h localhost -u root -p1234")
        sys.exit(1)
