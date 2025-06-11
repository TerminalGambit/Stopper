# Stopper: Habit Tracking and Behavior Monitoring App

## Overview
Stopper is a local-first, modular habit tracking app with journaling and AI-enhanced feedback. All data is stored locally in JSON files for privacy.

## Setup
1. Ensure you have Python 3.8+ installed.
2. Install dependencies:
   ```bash
   pip install flask
   ```
3. Run the app:
   ```bash
   make run
   ```

## Features (MVP)
- Add and view habits
- Dashboard overview
- Local JSON storage

## Project Structure
- `app.py`: Main Flask app
- `data/habits.json`: Local data storage
- `Makefile`: Run commands
- `app/templates/`: HTML templates

## License
MIT

## Deployment (Raspberry Pi: Docker + Gunicorn + Nginx)

### Stack
- **Nginx**: Reverse proxy, serves static files, handles HTTPS
- **Gunicorn**: WSGI server for Flask
- **Docker**: Containerizes the app for easy deployment

### Quick Start
1. **Build the Docker image:**
   ```sh
   docker build -t stopper-app .
   ```
2. **Run the container:**
   ```sh
   docker run -d --name stopper -p 8000:8000 stopper-app
   ```
3. **Set up Nginx** (on the Pi, outside Docker) to reverse proxy to `localhost:8000`.

### Nginx Example Config
```
server {
    listen 80;
    server_name your-pi-ip-or-domain;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Notes
- The Flask app runs with Gunicorn inside Docker on port 8000.
- Nginx listens on port 80 and proxies requests to the Docker container.
- For HTTPS, use [Let's Encrypt](https://certbot.eff.org/) with Nginx. 