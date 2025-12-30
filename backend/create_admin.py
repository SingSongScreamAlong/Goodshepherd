#!/usr/bin/env python3
"""
Create an admin user for Good Shepherd.
Run from project root with PYTHONPATH set.
"""
import sys
import os
from uuid import uuid4
from datetime import datetime

# Ensure we're running from project root with proper PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from sqlalchemy.orm import Session
from backend.core.database import SessionLocal
from backend.core.security import get_password_hash
from backend.models.user import User, Organization, RoleEnum, user_organization

def create_admin_user(
    email: str = "admin@goodshepherd.io",
    password: str = "admin123",
    full_name: str = "System Administrator"
):
    """Create an admin user with default organization."""
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"User {email} already exists")
            return existing_user
        
        # Create default organization
        org = Organization(
            id=uuid4(),
            name="Good Shepherd Operations",
            description="Primary operations organization for World Situational Awareness",
            region_of_interest="Global",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(org)
        db.flush()
        
        # Create admin user
        user = User(
            id=uuid4(),
            email=email,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            is_active=True,
            is_superuser=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(user)
        db.flush()
        
        # Associate user with organization as admin
        db.execute(
            user_organization.insert().values(
                user_id=user.id,
                organization_id=org.id,
                role=RoleEnum.ADMIN,
                created_at=datetime.utcnow()
            )
        )
        
        db.commit()
        
        print(f"✅ Created admin user:")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        print(f"   Organization: {org.name}")
        
        return user
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating admin user: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()
