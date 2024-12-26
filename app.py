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
engine = create_engine(f"postgresql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}")
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
    icon = Column(String)  # Add icon to cache
    timestamp = Column(DateTime, default=datetime.utcnow)

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
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful.', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])  # Hash password
        new_user = User(username=username, password=password)
        session.add(new_user)
        session.commit()
        flash('Registration successful. Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def home():
    weather = None
    test_text = "Welcome to Ben's Weather App!"

    if request.method == 'POST':
        city = request.form.get('city')
        if city:
            cache = session.query(WeatherCache).filter_by(city=city).first()
            if cache and cache.timestamp > datetime.utcnow() - timedelta(seconds=30):
                weather = {
                    'city': cache.city,
                    'temperature': cache.temperature,
                    'description': cache.description,
                    'icon': cache.icon,  # Use cached icon
                }
            else:
                api_key = '8697703eabb9caac81bf8df7d1d650dc'
                url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={api_key}"
                response = requests.get(url)

                if response.status_code == 200:
                    data = response.json()
                    weather = {
                        'city': city,
                        'temperature': data['main']['temp'],
                        'description': data['weather'][0]['description'],
                        'icon': data['weather'][0]['icon'],  # Fetch icon code
                    }
                    if cache:
                        cache.temperature = data['main']['temp']
                        cache.description = data['weather'][0]['description']
                        cache.icon = data['weather'][0]['icon']  # Update icon in cache
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
