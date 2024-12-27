from werkzeug.security import generate_password_hash
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app import User, Base  # Import User model and Base from your app

# Set up your database connection
engine = create_engine("postgresql://weather_app_u8d1_user:tZSPLEC3S0ch50Ugd6uQWJygDN6Po0rg@dpg-ctltsidumphs73dbr9h0-a.oregon-postgres.render.com:5432/weather_app_u8d1")

Session = sessionmaker(bind=engine)
session = Session()

# Fetch all users and update passwords if needed
users = session.query(User).all()
for user in users:
    if not user.password.startswith("pbkdf2:sha256"):  # Check if already hashed
        user.password = generate_password_hash(user.password, method='pbkdf2:sha256', salt_length=8)
        print(f"Updated password for user: {user.username}")
        session.commit()

print("Password updates completed.")
