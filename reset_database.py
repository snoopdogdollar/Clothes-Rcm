"""
Reset database tables (drop all and recreate with correct schema)
WARNING: This will delete all existing data!
"""

from utils.database import drop_all_tables, init_db

print("⚠️  WARNING: This will delete all data in the database!")
response = input("Are you sure you want to continue? (yes/no): ")

if response.lower() == 'yes':
    print("\n🗑️  Dropping all tables...")
    drop_all_tables()
    print("✓ Tables dropped")
    
    print("\n📊 Creating tables with new schema...")
    init_db()
    print("✓ Tables created successfully")
    
    print("\n🎉 Database reset complete!")
    print("You can now start the API and upload items.")
else:
    print("❌ Operation cancelled")
