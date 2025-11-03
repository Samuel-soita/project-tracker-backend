# project-tracker-backend

Backend API for the Project Tracker app, built with Flask, PostgreSQL, and SQLAlchemy.


## Table of Contents

- [Technologies](#technologies)
- [Features](#features)
- [Setup & Installation](#setup--installation)
- [Environment Variables](#environment-variables)
- [Database Migrations](#database-migrations)
- [Running the Server](#running-the-server)
- [API Endpoints](#api-endpoints)
- [Contributing](#contributing)


## Technologies

- Python 3.12
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- Flask-CORS
- PostgreSQL
- Alembic (for migrations)
- PyJWT (JWT authentication)
- pyotp (Two-Factor Authentication)
- qrcode (2FA QR code generation)



## Features

- User authentication (login/signup)
- Role-based access (Admin, Student)
- Two-Factor Authentication (2FA)
- Project,Cohort,class and task management
- PostgreSQL database integration
- Database migrations with Alembic


## Setup & Installation

1. Clone the repository:

git clone <repo_url>
cd project-tracker-backend

2. Create Virtual Environment

-python -m venv venv
-source venv/bin/activate   # Windows: venv\Scripts\activate
-pip install -r requirements.txt
-pip install -r requirements.txt
-flask db upgrade

4.Database Migrations
-flask db init       
-flask db migrate -m 
-flask db upgrade
-flask db downgrade  

5.Running the Server
-flask run

## License
-MIT License. See LICENSE for details

## Contributors

-Samuel Soita

-Shelmith

-Ashley

-David

-Said



