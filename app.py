from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, current_user, login_user, logout_user, login_required, UserMixin
import requests
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database setup
Base = declarative_base()
engine = create_engine(
    "postgresql://weather_app_u8d1_user:tZSPLEC3S0ch50Ugd6uQWJygDN6Po0rg@dpg-ctltsidumphs73dbr9h0-a.oregon-postgres.render.com:5432/weather_app_u8d1"
)
Session = sessionmaker(bind=engine)
session = Session()

# User model with UserMixin
class User(Base, UserMixin):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

# Weather cache model
class WeatherCache(Base):
    __tablename__ = 'weather_cache'
    id = Column(Integer, primary_key=True)
    city = Column(String, unique=True)
    temperature = Column(Float)
    description = Column(String)
    icon = Column(String)  # Icon column added
    timestamp = Column(DateTime, default=datetime.utcnow)

# User profiles
class Profile(Base):
    __tablename__ = 'profiles'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)  # Foreign key to User table
    email = Column(String, unique=True, nullable=False)
    favorite_cities = Column(String)  # Comma-separated list of favorite cities

# Ensure all tables are created
Base.metadata.create_all(engine)

@login_manager.user_loader
def load_user(user_id):
    return session.query(User).get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = session.query(User).filter_by(username=username).first()
        
        if user:
            if check_password_hash(user.password, password):
                login_user(user)
                flash('Login successful.', 'success')
                return redirect(url_for('home'))
            else:
                flash('Incorrect password. Please try again.', 'danger')
        else:
            flash('Username not found. Please try again.', 'danger')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the username already exists
        existing_user = session.query(User).filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('register'))

        # Hash the password and create a new user
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
        new_user = User(username=username, password=hashed_password)
        
        try:
            session.add(new_user)
            session.commit()
            flash('Registration successful. Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            session.rollback()  # Roll back in case of any other database errors
            flash('An error occurred. Please try again.', 'danger')
            print(f"Error during registration: {e}")

    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/profile/<username>/edit', methods=['GET', 'POST'])
@login_required
def edit_profile(username):
    user = session.query(User).filter_by(username=username).first()
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('home'))

    profile = session.query(Profile).filter_by(user_id=user.id).first()

    if request.method == 'POST':
        email = request.form['email']
        favorite_cities = request.form['favorite_cities']

        if profile:
            profile.email = email
            profile.favorite_cities = favorite_cities
        else:
            profile = Profile(user_id=user.id, email=email, favorite_cities=favorite_cities)
            session.add(profile)

        session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile', username=username))

    return render_template('edit_profile.html', user=user, profile=profile)




@app.route('/', methods=['GET', 'POST'])
def home():
    weather = None
    test_text = "Welcome to Ben's Weather App!"

    if request.method == 'POST':
        city = request.form.get('city')
        if city:
            cache = session.query(WeatherCache).filter_by(city=city).first()
            if cache and cache.timestamp > datetime.utcnow() - timedelta(seconds=30):
                # Use cached data
                weather = {
                    'city': cache.city,
                    'temperature': cache.temperature,
                    'description': cache.description,
                    'icon': cache.icon,  # Use cached icon
                }
            else:
                # Fetch data from OpenWeather API
                api_key = os.getenv('OPENWEATHER_API_KEY', 'your-api-key')
                url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid=8697703eabb9caac81bf8df7d1d650dc"
                response = requests.get(url)

                if response.status_code == 200:
                    data = response.json()
                    weather = {
                        'city': city,
                        'temperature': data['main']['temp'],
                        'description': data['weather'][0]['description'],
                        'icon': data['weather'][0]['icon'],  # Fetch icon
                    }
                    # Update or add cache
                    if cache:
                        cache.temperature = data['main']['temp']
                        cache.description = data['weather'][0]['description']
                        cache.icon = data['weather'][0]['icon']
                        cache.timestamp = datetime.utcnow()
                    else:
                        new_cache = WeatherCache(
                            city=city,
                            temperature=data['main']['temp'],
                            description=data['weather'][0]['description'],
                            icon=data['weather'][0]['icon']
                        )
                        session.add(new_cache)
                    session.commit()
    return render_template('index.html', weather=weather, test_text=test_text)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
