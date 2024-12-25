from flask import Flask, render_template, request
import requests
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os  # Add this line to import the os module

app = Flask(__name__)

# Database setup
Base = declarative_base()
import os

engine = create_engine(f"postgresql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}")
Session = sessionmaker(bind=engine)
session = Session()

class WeatherCache(Base):
    __tablename__ = 'weather_cache'
    id = Column(Integer, primary_key=True)
    city = Column(String, unique=True)
    temperature = Column(Float)
    description = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

@app.route('/', methods=['GET', 'POST'])
def home():
    weather = None  # Initialize weather variable
    test_text = "Caching Enabled"

    if request.method == 'POST':
        city = request.form.get('city')
        if city:
            # Check cache
            print(f"Checking cache for {city}...")
            cache = session.query(WeatherCache).filter_by(city=city).first()
            if cache and cache.timestamp > datetime.utcnow() - timedelta(seconds=30):
                print(f"Cache hit for {city}. Using cached data.")
                # Use cached data
                weather = {
                    'city': cache.city,
                    'temperature': cache.temperature,
                    'description': cache.description,
                }
            else:
                print(f"Cache miss for {city}. Fetching new data.")
                # Fetch new data
                api_key = '8697703eabb9caac81bf8df7d1d650dc'
                url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={api_key}"
                response = requests.get(url)

                if response.status_code == 200:
                    data = response.json()
                    weather = {
                        'city': city,
                        'temperature': data['main']['temp'],
                        'description': data['weather'][0]['description'],
                    }
                    # Update or add cache
                    if cache:
                        print(f"Updating cache for {city}.")
                        cache.temperature = data['main']['temp']
                        cache.description = data['weather'][0]['description']
                        cache.timestamp = datetime.utcnow()
                    else:
                        print(f"Adding new cache entry for {city}.")
                        new_cache = WeatherCache(
                            city=city,
                            temperature=data['main']['temp'],
                            description=data['weather'][0]['description']
                        )
                        session.add(new_cache)
                    session.commit()
    return render_template('index.html', weather=weather, test_text=test_text)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Default to 5000 if PORT is not set
    app.run(debug=True, host='0.0.0.0', port=port)




