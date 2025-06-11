# Deployment Guide: Stopper on Raspberry Pi (Docker + Gunicorn + Nginx)

## 1. Prerequisites
- Raspberry Pi with Raspberry Pi OS (or any Linux)
- Docker installed ([Install Docker on Pi](https://docs.docker.com/engine/install/debian/))
- Nginx installed (`sudo apt install nginx`)
- Git installed

## 2. Clone the Repository
```sh
git clone <your-repo-url>
cd Stopper
```

## 3. Remove Personal/Build Data
- Delete any local data, logs, or files you don't want in the repo (e.g., user data, cache, __pycache__, etc).
- The `.gitignore` file will help prevent accidental commits of these files.

## 4. Build the Docker Image
```sh
make docker-build
```

## 5. Run the Docker Container
```sh
make docker-run
```
- The app will be available on port 8000 inside the container.

## 6. Configure Nginx as a Reverse Proxy
- Edit `/etc/nginx/sites-available/default` (or create a new site config):

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
- Reload Nginx:
```sh
sudo systemctl reload nginx
```

## 7. (Optional) Enable HTTPS
- Use [Let's Encrypt](https://certbot.eff.org/) for a free SSL certificate.

## 8. Stopping and Removing the Container
```sh
docker stop stopper
docker rm stopper
```

## 9. Updating the App
```sh
git pull
make docker-build
make docker-run
```

## 10. Security & Maintenance
- Never commit personal data, secrets, or build artifacts.
- Use `.gitignore` to keep your repo clean.
- Regularly update dependencies and Docker base images.

---

# .gitignore Example
```
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Jupyter Notebook
.ipynb_checkpoints

# pyenv
.python-version

# mypy
.mypy_cache/
.dmypy.json

# VS Code
.vscode/

# Data files
*.db
*.sqlite3
data/

# System files
.DS_Store
Thumbs.db

# Docker
*.pid
*.log

# Environment
.env
.env.*

# Misc
*.swp
``` 