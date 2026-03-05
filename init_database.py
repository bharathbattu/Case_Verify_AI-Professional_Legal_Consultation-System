"""
Simple database initialization script for Phase 3.3
Creates tables and admin user with secure credential management
"""
import os
import sys
import secrets
import string
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.abspath('.'))

from database.connection import engine, SessionLocal
from database.models import Base, User
import bcrypt


def generate_secure_password(length: int = 16) -> str:
    """Generate a cryptographically secure random password"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def validate_password_strength(password: str) -> bool:
    """Validate minimum password complexity requirements"""
    if len(password) < 8:
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    return has_upper and has_lower and has_digit


def init_database():
    """Initialize database tables and create admin user"""
    try:
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("\u2705 Database tables created successfully")
        
        # Create session
        db = SessionLocal()
        
        try:
            # Check if admin user already exists
            existing_admin = db.query(User).filter(User.username == "admin").first()
            
            if not existing_admin:
                print("Creating default admin user...")
                
                # Read password from environment variable or generate a secure one
                password = os.environ.get("ADMIN_PASSWORD", "")
                generated = False
                
                if not password:
                    password = generate_secure_password()
                    generated = True
                    print("\u26a0\ufe0f  No ADMIN_PASSWORD env var set. Generated a secure random password.")
                elif not validate_password_strength(password):
                    print("\u274c ADMIN_PASSWORD does not meet complexity requirements:")
                    print("   - Minimum 8 characters")
                    print("   - At least one uppercase letter")
                    print("   - At least one lowercase letter")
                    print("   - At least one digit")
                    return False
                
                # Hash the password
                salt = bcrypt.gensalt()
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
                
                # Read admin email from env or use default
                admin_email = os.environ.get("ADMIN_EMAIL", "admin@caseverify.ai")
                
                # Create admin user
                admin_user = User(
                    username="admin",
                    email=admin_email,
                    hashed_password=hashed_password.decode('utf-8'),
                    role="admin",
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                
                db.add(admin_user)
                db.commit()
                print("\u2705 Default admin user created")
                print(f"   Username: admin")
                print(f"   Email: {admin_email}")
                if generated:
                    print(f"   Password: {password}")
                    print("   \u26a0\ufe0f  SAVE THIS PASSWORD NOW. It will not be shown again.")
                    print("   \u26a0\ufe0f  Change it immediately after first login.")
                else:
                    print("   Password: [set from ADMIN_PASSWORD env var]")
            else:
                print("\u2705 Admin user already exists")
                
        except Exception as e:
            print(f"\u274c Error creating admin user: {e}")
            db.rollback()
        finally:
            db.close()
            
        print("\n\ud83c\udf89 Phase 3.3 Database Initialization Complete!")
        print("\nNext steps:")
        print("1. Run: streamlit run app.py")
        print("2. Navigate to User Management tab")
        print("3. Login with the admin credentials shown above")
        print("4. Test case creation and export features")
        
    except Exception as e:
        print(f"\u274c Database initialization failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    init_database()
