"""
Simple database initialization script for Phase 3.3
Creates tables and admin user without Streamlit dependencies
"""
import os
import sys
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.abspath('.'))

from database.connection import engine, SessionLocal
from database.models import Base, User
import bcrypt

def init_database():
    """Initialize database tables and create admin user"""
    try:
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        
        # Create session
        db = SessionLocal()
        
        try:
            # Check if admin user already exists
            existing_admin = db.query(User).filter(User.username == "admin").first()
            
            if not existing_admin:
                print("Creating default admin user...")
                
                # Hash the password
                password = "admin123"
                salt = bcrypt.gensalt()
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
                
                # Create admin user
                admin_user = User(
                    username="admin",
                    email="admin@caseverify.ai",
                    hashed_password=hashed_password.decode('utf-8'),
                    role="admin",
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                
                db.add(admin_user)
                db.commit()
                print("✅ Default admin user created")
                print("   Username: admin")
                print("   Password: admin123")
                print("   Email: admin@caseverify.ai")
            else:
                print("✅ Admin user already exists")
                
        except Exception as e:
            print(f"❌ Error creating admin user: {e}")
            db.rollback()
        finally:
            db.close()
            
        print("\n🎉 Phase 3.3 Database Initialization Complete!")
        print("\nNext steps:")
        print("1. Run: streamlit run app.py")
        print("2. Navigate to User Management tab")
        print("3. Login with admin/admin123")
        print("4. Test case creation and export features")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    init_database()
