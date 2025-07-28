# CTF Checker Manager 🏳️
![Docker Support](https://img.shields.io/badge/docker-supported-blue)
![Python Version](https://img.shields.io/badge/python-3.11+-green)
![License](https://img.shields.io/badge/license-MIT-blue)

## About the project ⚙️
CTF Checker Manager is a Flask-based web application designed for monitoring CTF (Capture The Flag) challenge checkers with automated periodic execution. The system has been updated to remove authentication requirements, making it publicly accessible for all users to upload and monitor challenge checkers.

The site now supports public access - no registration or login required. Simply visit the dashboard to upload and monitor challenge checkers that verify CTF services and their flags.

## How to run 🛠️
Clone the project and go inside the project directory
```bash
git clone <repository-url>
cd ctf-checker-manager
```

### Docker Deployment (Recommended)
Inside the project's main directory can be found the `docker-compose.yml` file along with a `Dockerfile` which can be used to build the project inside Docker with PostgreSQL database.
```bash
docker-compose up --build
```

Alternatively, use the build script:
```bash
./build-docker.sh
```

### Local Development
It's also possible to run the site on the local machine by starting the Flask app directly.
```bash
pip install -r docker-requirements.txt
cd src
python main.py
```

## Set environmental variables 🌐
The application uses environment variables for configuration that can be set in your shell or Docker environment:

```bash
# Database configuration
export DATABASE_URL="postgresql://user:password@localhost:5432/ctf_checker"

# Session management
export SESSION_SECRET="your-secret-key-here"

# Challenge environment (available to checker scripts)
export URL="http://challenge.example.com"
export HOST="challenge.example.com"
export PORT="8080"
```

## Features ✨

- **Public Access**: No authentication required - anyone can add and manage checkers
- **Automated Execution**: Checkers run every minute automatically in isolated environments
- **Real-time Dashboard**: Live status updates with execution history and statistics
- **Flag Validation**: Automatic verification of expected flags with pattern matching
- **Docker Support**: Complete containerization with PostgreSQL database
- **Responsive UI**: Modern Bootstrap-based interface with Replit dark theme
- **Process Isolation**: Secure subprocess execution with timeout limits
- **Comprehensive Logging**: Detailed execution logs and error reporting

## Usage 📋

1. **Dashboard**: Visit the main page to see all checkers and their real-time status
2. **Add Checker**: Upload a Python script that validates a CTF challenge
3. **Monitor Results**: View execution history, success rates, and detailed logs
4. **Set Expected Flag**: Configure the expected output for automatic validation

### Checker Script Requirements

Your checker script should:
- Be written in Python 3
- Print the flag to stdout when successful
- Exit with code 0 for success, non-zero for failure
- Complete execution within 30 seconds
- Use environment variables for configuration

### Example Checker Script

```python
#!/usr/bin/env python3

import os
import requests
from pwn import *
import logging
logging.disable()

# Web challenge configuration
URL = os.environ.get("URL", "http://example.challs.todo.it")
if URL.endswith("/"):
   URL = URL[:-1]

# TCP challenge configuration
HOST = os.environ.get("HOST", "example.challs.todo.it")
PORT = int(os.environ.get("PORT", 34001))

# Perform the check and print the flag
try:
    response = requests.get(f"{URL}/flag", timeout=10)
    if response.status_code == 200:
        print("flag{example_flag_here}")
        exit(0)
except Exception as e:
    print(f"Error: {e}")
    exit(1)
```

## Project Structure 📁

```
├── src/                    # Python application code
│   ├── app.py             # Flask application setup
│   ├── main.py            # Application entry point
│   ├── models.py          # Database models
│   ├── routes.py          # HTTP routes
│   ├── scheduler.py       # Background task scheduler
│   └── checker_runner.py  # Checker execution engine
├── templates/             # HTML templates
├── static/               # CSS and JavaScript files
├── uploads/              # Uploaded checker scripts
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose setup
├── docker-requirements.txt # Python dependencies
└── build-docker.sh       # Docker build script
```

## API Endpoints 🔌

- `GET /` - Redirects to dashboard
- `GET /dashboard` - Main dashboard with checker status
- `GET /add_checker` - Form to add new checker
- `POST /add_checker` - Submit new checker
- `GET /toggle_checker/<id>` - Enable/disable checker
- `GET /delete_checker/<id>` - Delete checker
- `GET /api/checker_status` - JSON API for real-time status updates

## Docker Configuration 🐳

The application includes complete Docker support with:

- **Multi-stage build** for optimized image size
- **PostgreSQL database** with persistent volumes
- **Environment variable** configuration
- **Non-root user** execution for security
- **Health checks** for container monitoring

### Environment Variables in Docker

The `docker-compose.yml` file configures:
- `DATABASE_URL`: PostgreSQL connection string
- `SESSION_SECRET`: Randomly generated session key
- `URL`, `HOST`, `PORT`: Challenge configuration for checkers

## License

This project is licensed under the MIT License.