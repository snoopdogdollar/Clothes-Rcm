"""
Test script to verify PostgreSQL integration is set up correctly
Run this before starting the API to check everything is configured
"""

import sys
from pathlib import Path

def test_imports():
    """Test if all required packages are installed"""
    print("Testing imports...")
    
    try:
        import psycopg2
        print("  ✓ psycopg2 installed")
    except ImportError:
        print("  ✗ psycopg2 NOT installed - run: pip install psycopg2-binary")
        return False
    
    try:
        import sqlalchemy
        print("  ✓ SQLAlchemy installed")
    except ImportError:
        print("  ✗ SQLAlchemy NOT installed - run: pip install SQLAlchemy")
        return False
    
    try:
        import fastapi
        print("  ✓ FastAPI installed")
    except ImportError:
        print("  ✗ FastAPI NOT installed - run: pip install fastapi")
        return False
    
    try:
        import uvicorn
        print("  ✓ Uvicorn installed")
    except ImportError:
        print("  ✗ Uvicorn NOT installed - run: pip install uvicorn[standard]")
        return False
    
    try:
        from dotenv import load_dotenv
        print("  ✓ python-dotenv installed")
    except ImportError:
        print("  ✗ python-dotenv NOT installed - run: pip install python-dotenv")
        return False
    
    return True

def test_config():
    """Test if .env file exists and is configured"""
    print("\nTesting configuration...")
    
    env_file = Path(".env")
    if not env_file.exists():
        print("  ✗ .env file NOT found")
        print("    → Copy .env.example to .env and update your password")
        return False
    
    print("  ✓ .env file exists")
    
    # Check if password is still placeholder
    with open(env_file) as f:
        content = f.read()
        if "your_password_here" in content:
            print("  ⚠ WARNING: .env still has placeholder password")
            print("    → Edit .env and replace 'your_password_here' with your actual password")
            return False
    
    print("  ✓ .env appears to be configured")
    return True

def test_database_connection():
    """Test if can connect to PostgreSQL"""
    print("\nTesting database connection...")
    
    try:
        from config import Config
        from sqlalchemy import create_engine, text
        
        print(f"  Connecting to: {Config.DATABASE_URL.split('@')[1]}")  # Hide password
        
        engine = create_engine(Config.DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"  ✓ Connected to PostgreSQL")
            print(f"    Version: {version.split(',')[0]}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Connection failed: {e}")
        print("\n  Troubleshooting:")
        print("    1. Is PostgreSQL running? Check with: pg_isready")
        print("    2. Is password correct in .env file?")
        print("    3. Does database 'fashion_wardrobe' exist?")
        print("       Create it: psql -U giaphuc -c 'CREATE DATABASE fashion_wardrobe;'")
        return False

def test_folders():
    """Test if required folders exist"""
    print("\nTesting folder structure...")
    
    folders = [
        Path("data/uploads"),
        Path("output"),
        Path("models"),
        Path("utils")
    ]
    
    all_exist = True
    for folder in folders:
        if folder.exists():
            print(f"  ✓ {folder}/ exists")
        else:
            print(f"  ✗ {folder}/ NOT found")
            folder.mkdir(parents=True, exist_ok=True)
            print(f"    → Created {folder}/")
    
    return True

def test_models():
    """Test if can import models"""
    print("\nTesting models...")
    
    try:
        from models.item import ClothingItem, ItemColor
        print("  ✓ Models imported successfully")
        return True
    except Exception as e:
        print(f"  ✗ Failed to import models: {e}")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("PostgreSQL Integration Setup Test")
    print("="*60 + "\n")
    
    tests = [
        ("Package Installation", test_imports),
        ("Configuration", test_config),
        ("Folder Structure", test_folders),
        ("Models", test_models),
        ("Database Connection", test_database_connection),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n  ✗ Test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8s} {name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 All tests passed! You're ready to start the API server.")
        print("\nNext steps:")
        print("  1. Start API: python api.py")
        print("  2. Open browser: http://localhost:8000/docs")
        print("  3. Test upload endpoint with an image")
    else:
        print("\n⚠ Some tests failed. Fix the issues above before starting API.")
        sys.exit(1)

if __name__ == "__main__":
    main()
