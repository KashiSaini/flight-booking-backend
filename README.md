✈️ Flight Booking & Search Engine (FastAPI + Docker)

🌟 Executive Summary
A high-performance, containerized backend system designed for flight management. This project demonstrates a hybrid database approach using PostgreSQL for transactional integrity (Users/Bookings), MongoDB for high-volume logging (Search History), and Redis for sub-millisecond session caching.



📁 Project Directory Structure

```bash
flight-booking-backend/
├── alembic/                    # Database migration scripts
├── app/
│   ├── api/
│   │   └── dependencies/       # Shared FastAPI dependencies
│   ├── core/                   # App configuration and security helpers
│   ├── db/                     # PostgreSQL, MongoDB, and Redis setup
│   ├── models/                 # SQLAlchemy models
│   ├── routers/                # Route modules for auth, flights, bookings, admin, and private jets
│   ├── schemas/                # Pydantic request/response schemas
│   ├── services/               # Business logic layer
│   ├── main.py                 # FastAPI application entry point
│   └── __init__.py
├── tools/                      # Development helper scripts
├── .dockerignore
├── .env
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── README.md
└── requirements.txt
```



🏗️ System Architecture
The system uses a Containerized Micro-Service Architecture.

API Layer: FastAPI (Python 3.11) with Asynchronous SQLAlchemy.

SQL Layer: PostgreSQL 15 (Alpine) for relational data.

NoSQL Layer: MongoDB for search telemetry and logs.

Cache Layer: Redis for JWT token blacklisting and session storage.



🛠️ Complete Developer Log & Commands

1. The Pre-Docker Era (Manual Setup)
Before moving to containers, the project was initialized locally:

Python Setup: Created a virtual environment using python -m venv venv.

Dependencies: Managed via requirements.txt including fastapi, uvicorn, sqlalchemy, asyncpg, motor, and redis.

Manual Migrations: Initialized Alembic with alembic init alembic to track schema changes.
        Generate Migration: alembic revision --autogenerate -m "Initial tables"
        Apply Migration: alembic upgrade head
        Revert Migration: alembic downgrade -1

Virtual Environment Activation: .\venv\Scripts\activate
Local Server Start: uvicorn app.main:app --reload


2. The Docker Infrastructure (The Current Build)
The project now runs entirely on Docker to ensure environment parity.

Core Management Commands:

Full Deployment: docker compose up -d ~ Starts all 4 services in the background, Then use the terminal for typing as well. Can use this to individually start a specific container.

Service Sync: docker compose up --build ~ Use this when changing requirements.txt or Dockerfile.

Code Refresh: docker compose restart api ~ Restarts the Python server without stopping databases.

Stop Everything: docker compose down ~ Stops all running services

Clean Slate: docker compose down -v ~ Removes containers AND permanent volumes (use with caution!).

To avoid conflicts with local Windows services, we use a "Two-Lane" port system:
Service            Internal (Docker)            External (Windows)
FastAPI API             8000                            8000
PostgreSQL              5432                            5433
MongoDB                 27017                           27018
Redis                   6379                            6380



🔒 Security & Authentication

JWT Implementation: Uses JWT Token with Password Bearer tokens.

Password Hashing: Implemented passlib with bcrypt for secure user credential storage.

Session Caching: Redis (Port 6380) handles token expiration to prevent unauthorized access after logout.



📊 Data Persistence & Portability

To keep data safe during container updates, we implemented Docker Volumes.

The "Initial Load" Procedure
If you are setting this up for the first time, you must migrate your local SQL dump into the Docker volume:

Bash
"C:\Program Files\PostgreSQL\18\bin\psql" -U postgres -p 5433 -d flight < my_old_flight_data.sql
Note: Port 5433 is the external bridge to the internal Postgres port 5432.



🔍 Monitoring & Debugging

To watch the interaction between the API and the databases in real-time, use these "Log Spies":

Target	Command	Expected Output
Full Stack	docker compose logs -f	 Combined stream of all services.
SQL Queries	docker compose logs -f postgres	Shows user lookups and flight bookings.
Cache Hits	docker compose logs -f redis	Shows token verification activity.
Search Logs	docker compose logs -f mongo	Shows NoSQL document insertions.
