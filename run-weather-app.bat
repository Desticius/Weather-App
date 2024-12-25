@echo off
echo Rebuilding the Docker image...
docker build -t weather-app .

echo Running the Docker container...
docker run -p 5000:5000 weather-app
