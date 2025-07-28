# Checker Site 🏳️
![GitHub License](https://img.shields.io/github/license/PascalCTF/CTF-Checker)
![GitHub Issues](https://img.shields.io/github/issues/PascalCTF/CTF-Checker)
![GitHub Pull Requests](https://img.shields.io/github/issues-pr/PascalCTF/CTF-Checker)

## About the project ⚙️
CTF-Checker is a python based site made for the [`PascalCTF`](https://github.com/PascalCTF) cybersecurity event to check the status of the online services and their flags.

The site now supports user accounts. Create an account via the `/register` page and log in to access the dashboard where you can upload and monitor challenge checkers.

## How to run 🛠️
Clone the project and go inside the project directory
```
git clone https://github.com/PascalCTF/CTF-Checker.git
cd CTF-Checker
```

Inside the project's main directory can be found the `docker-compose.yml` file  along with a `Dockerfile` which can be used to build the project inside a docker.
```
docker compose up --build
```

It's also possible to run the site inside the local machine by starting the flask main app.
```
pip3 install -r requirements.txt
python3 main.py
```

## Set environmental variables 🌐
The whole site uses a MySQL database whose variable are set by the `.env` file that can be found inside the main directory.
