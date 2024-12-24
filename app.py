from flask import Flask, render_template, request
import requests

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    weather = None  # Initialize weather variable
    test_text = "WEATHERAPP"


    if request.method == 'POST':
        city = request.form.get('city')  # Get city name from form
        if city:
            # OpenWeather API Key
            api_key = '8697703eabb9caac81bf8df7d1d650dc'
            # API request URL
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={api_key}"
            response = requests.get(url)

            # Debugging prints
            print(f"API URL: {url}")  # Show the full API request URL
            print(f"Response Status Code: {response.status_code}")  # Show the HTTP status code
            print(f"Response Data: {response.text}")  # Show the raw response data

            if response.status_code == 200:
                data = response.json()  # Parse JSON response
                weather = {
                    'city': city,
                    'temperature': data['main']['temp'],
                    'description': data['weather'][0]['description'],
                }
            else:
                weather = {'error': f"Could not retrieve weather for {city}. Please try again."}

    return render_template('index.html', weather=weather, test_text=test_text)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Default to 5000 if PORT is not set
    app.run(debug=True, host='0.0.0.0', port=port)




