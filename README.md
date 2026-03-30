# ✈️ Flight Booking Backend — Detailed Project README

A containerized **flight booking backend** built with **FastAPI**, **PostgreSQL**, **Redis**, **MongoDB**, and **Docker Compose**.

This project did **not** start as microservices.
It evolved in stages:

1. **Manual local setup**
2. **Single FastAPI app running with Docker**
3. **Modular monolith**
4. **Microservices with a shared database**

This README explains that full journey, the current architecture, how the services are connected, what each folder does, and all important run/debug commands.

---

# 🌟 Executive Summary

This backend manages:

- user registration and login
- JWT-based authentication
- flight creation and search
- seat-level booking
- private jet booking
- admin activity logs and analytics

The current version is a **microservices-style architecture with a shared PostgreSQL database**.

That means:

- each domain now runs as a separate FastAPI service
- each service has its own container
- services still share common infrastructure
- PostgreSQL stores core transactional data
- Redis supports caching and token/session-like logic
- MongoDB stores logs and analytics

This is a practical transition architecture between a modular monolith and fully independent microservices.

---

# 📜 Project Evolution — From Start to Current Version

## Phase 1 — Pre-Docker Era (Manual Local Setup)

At the very beginning, the project was run locally like a normal FastAPI backend.

Typical flow:

- create virtual environment
- install dependencies
- configure `.env`
- initialize Alembic
- run migrations
- start FastAPI using Uvicorn

### Typical commands used in the early stage

```bash
python -m venv venv
```

```bash
.\venv\Scripts\activate
```

```bash
pip install -r requirements.txt
```

```bash
alembic init alembic
```

```bash
alembic revision --autogenerate -m "Initial tables"
```

```bash
alembic upgrade head
```

```bash
alembic downgrade -1
```

```bash
uvicorn app.main:app --reload
```

In this phase, everything was local and manually managed.

---

## Phase 2 — Dockerized Single-App Backend

After that, the project moved to Docker.

In this stage, the backend still behaved like **one FastAPI application**, but the infrastructure became containerized.

Main benefits gained in this phase:

- same environment on every machine
- easy startup
- PostgreSQL, Redis, and MongoDB started together
- no need to manually configure each dependency every time

At this stage, the system had:

- one API container
- one Postgres container
- one Redis container
- one Mongo container

So the app was still logically one backend, but its infrastructure was much more professional and reproducible.

---

## Phase 3 — Modular Monolith

The next improvement was architectural cleanup.

Instead of keeping all logic mixed in one place, the codebase was organized by domain.

The old structure centered around one `app/` package with separate folders such as:

- `routers/`
- `services/`
- `schemas/`
- `models/`
- `db/`
- `core/`
- `api/dependencies/`

In this stage:

- there was still **one FastAPI app**
- there was still **one API container**
- but the code was much cleaner internally

This is called a **modular monolith**.

### What modular monolith means

It means the app is split into internal modules, but all modules still run together inside one application process.

Example internal domains from your project:

- auth
- flights
- bookings
- private jets
- admin

This stage is very important because it prepares a project for microservices later.

---

## Phase 4 — Current Version: Microservices with Shared Database

Now the project has moved one step further.

Instead of one single FastAPI application including every router, the system now runs as **multiple FastAPI services**:

- `auth-service`
- `flight-service`
- `booking-service`
- `private-jet-service`
- `admin-service`

Each service runs in its **own Docker container** and exposes its **own Swagger docs**.

But this is still a **transition design**, because the services currently share:

- one PostgreSQL database
- one Redis instance
- one MongoDB instance
- one shared code layer for common logic

So this is not yet a strict “database-per-service” architecture.

It is a practical learning and migration step:

> split services first, keep infrastructure shared for now, reduce complexity, then isolate further later if needed.

---

# 🧠 What the Current Architecture Means

The current setup is best described as:

> **Dockerized FastAPI microservices with shared infrastructure and a shared PostgreSQL database**

This means:

- services are separated by business domain
- deployment is separated by container
- routing is separated by service
- docs are separated by service
- but persistent data is still centralized

This is useful because your original booking logic is still tightly connected with flights and seats, so jumping directly to “pure” microservices would make the project much harder to maintain.

---

# 📁 Current Project Structure

```bash
flight-booking-backend/
├── alembic/
│   ├── versions/
│   └── __pycache__/
│
├── services/
│   ├── admin-service/
│   │   └── app/
│   │       ├── routers/
│   │       ├── services/
│   │       └── __pycache__/
│   │
│   ├── auth-service/
│   │   └── app/
│   │       ├── routers/
│   │       ├── schemas/
│   │       ├── services/
│   │       └── __pycache__/
│   │
│   ├── booking-service/
│   │   └── app/
│   │       ├── routers/
│   │       ├── schemas/
│   │       ├── services/
│   │       └── __pycache__/
│   │
│   ├── flight-service/
│   │   └── app/
│   │       ├── routers/
│   │       ├── schemas/
│   │       ├── services/
│   │       └── __pycache__/
│   │
│   └── private-jet-service/
│       └── app/
│           ├── routers/
│           ├── schemas/
│           ├── services/
│           └── __pycache__/
│
└── shared/
    ├── core/
    ├── db/
    ├── dependencies/
    ├── models/
    └── __pycache__/
```

---

# 🏗️ High-Level Architecture

## 1. auth-service

Responsible for authentication and user access.

Typical responsibilities:

- register user
- login user
- issue JWT tokens
- refresh token flow
- logout / token invalidation
- check current user
- restrict admin-only access

This service is the entry point for authentication.

---

## 2. flight-service

Responsible for standard flight operations.

Typical responsibilities:

- create flight
- get flights
- search flights
- update flight
- delete flight
- generate and fetch seat data
- cache flight results
- push analytics/logging events

This service owns flight-related behavior.

---

## 3. booking-service

Responsible for standard flight bookings.

Typical responsibilities:

- create booking
- validate flight route destination
- lock selected seat
- prevent double booking
- calculate price
- create booking reference
- fetch a user’s bookings
- cancel a booking
- update seat and seat counts during booking/cancellation

This service currently still reads flight and seat data directly from the shared PostgreSQL database.

That is intentional for the current architecture.

---

## 4. private-jet-service

Responsible for private jet features.

Typical responsibilities:

- create private jet entries
- list private jets
- create private jet bookings
- calculate time-based pricing
- cancel private jet bookings
- mark jet availability

---

## 5. admin-service

Responsible for admin-level operational data.

Typical responsibilities:

- view user activity logs
- inspect flight analytics
- access system-level activity information

MongoDB is mainly used here for logs and analytics retrieval.

---

## 6. shared layer

The `shared/` folder exists because the current services still need common code.

It includes reusable code such as:

- configuration
- JWT/security helpers
- DB connection helpers
- auth dependencies
- shared SQLAlchemy models
- common helper logic used across services

This keeps the new services from duplicating the same foundational code.

---

# 🗄️ Databases and Storage

## PostgreSQL

PostgreSQL is the main transactional database.

It stores structured relational data such as:

- users
- flights
- seats
- bookings
- private jets
- private jet bookings

This is the most important persistence layer for business data.

---

## Redis

Redis is used for speed-focused and short-lived data needs.

Typical uses in this project:

- token/blacklist support
- refresh token session-style handling
- caching flight lists
- invalidating cache after updates or bookings

---

## MongoDB

MongoDB is used for flexible event-style data.

Typical uses in this project:

- user activity logs
- flight analytics
- search/logging-style documents

MongoDB is **not** the main booking database.
It is a logging and analytics layer.

---

# 🧩 Important Models in the Current System

## User
Stores authentication and authorization-related information.

Fields include:

- id
- name
- email
- password
- is_admin

---

## Flight
Stores flight information such as:

- source
- destination
- stops
- segment prices
- business/premium/economy prices
- business/premium/economy seat counts
- airline
- departure/arrival times

---

## Seat
Stores seat-level information linked to a flight.

Fields include:

- flight id
- seat number
- seat type
- booked status

---

## Booking
Stores flight bookings.

Fields include:

- user id
- flight id
- seat id
- seat number
- seat type
- price paid
- passenger name
- destination
- booking reference
- status
- booked at

---

## PrivateJet
Stores private jet information.

Fields include:

- owner id
- name
- description
- price per hour
- availability
- available from / available to

---

## PrivateJetBooking
Stores private jet reservation records.

Fields include:

- user id
- private jet id
- start time
- end time
- price paid
- status
- booked at

---

# 🔐 Security and Authentication

The project uses JWT-based authentication.

## Main security ideas

- passwords are hashed before storage
- login returns access token and refresh token
- refresh token handling is supported
- token validation is reused by multiple services
- admin-only endpoints are protected using admin checks

## Authentication flow

1. user logs in using `auth-service`
2. auth-service validates credentials using PostgreSQL
3. auth-service generates JWT tokens
4. tokens are returned to the client
5. client sends access token to other services in the `Authorization` header
6. other services validate the token using shared auth/security code

### Authorization header example

```bash
Authorization: Bearer <access_token>
```

---

# 🔄 How the Services Are Connected

Even though the services are separated, they are still connected in a few important ways.

## 1. Through Docker Compose

Docker Compose starts all service containers together.

So one command starts:

- auth-service
- flight-service
- booking-service
- private-jet-service
- admin-service
- postgres
- redis
- mongo

---

## 2. Through Shared Infrastructure

All services still use the same:

- PostgreSQL
- Redis
- MongoDB
- shared environment variables
- shared auth/config/model layer

---

## 3. Through Business Data Relationships

Example:

- booking-service creates bookings
- booking-service also reads flights and seats
- flight-service manages seat generation and flight data
- admin-service reads analytics data written to MongoDB

This is why the system is called a **shared-database microservices setup**.

---

# ✈️ Example Request Flow — Standard Flight Booking

To understand the architecture better, here is what happens during a normal flight booking.

## Step-by-step booking flow

1. User logs in through auth-service
2. Auth-service returns JWT access token
3. User calls booking-service with bearer token
4. Booking-service validates token through shared auth logic
5. Booking-service fetches the target flight from PostgreSQL
6. Booking-service checks the requested passenger destination against allowed route points
7. Booking-service locks the seat row
8. Booking-service checks whether the seat exists and is already booked or not
9. Booking-service calculates price for the selected destination and seat class
10. Booking-service creates booking row
11. Booking-service marks seat as booked
12. Booking-service updates class seat counts on the flight
13. Booking-service clears cached flight data from Redis
14. Booking-service writes activity log information to MongoDB
15. Response is returned with booking details

This is one reason the project still uses a shared database in the current stage: booking logic is still tightly connected to flight and seat tables.

---

# 🛠️ Environment Variables

Example `.env`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:kashi@postgres:5432/flight
ADMIN_EMAIL=nishant@admin.com
SECRET_KEY=supersecretkey
MONGO_URL=mongodb://mongo:27017
REDIS_URL=redis://redis:6379/0
```

## Meaning of each variable

### `DATABASE_URL`
Async PostgreSQL connection string used by the services.

### `ADMIN_EMAIL`
Admin bootstrap/reference email used by your auth/admin logic.

### `SECRET_KEY`
Used for JWT signing.

### `MONGO_URL`
MongoDB connection string for logs and analytics.

### `REDIS_URL`
Redis connection string for token/cache usage.

---

# 🔌 Port Mapping

Each FastAPI service runs internally on port `8000` inside its own container.

But on your machine, each service is mapped to a different host port.

| Service | Internal Docker Port | External Host Port |
|--------|----------------------:|-------------------:|
| auth-service | 8000 | 8001 |
| flight-service | 8000 | 8002 |
| booking-service | 8000 | 8003 |
| private-jet-service | 8000 | 8004 |
| admin-service | 8000 | 8005 |
| PostgreSQL | 5432 | 5433 |
| Redis | 6379 | 6380 |
| MongoDB | 27017 | 27018 |

This keeps the services separated while avoiding local port conflicts.

---

# 🚀 How to Run the Current Project

## Start all services

```bash
docker compose up --build
```

## Start all services in background

```bash
docker compose up -d --build
```

## Stop all services

```bash
docker compose down
```

## Stop all services and remove orphan containers

```bash
docker compose down --remove-orphans
```

## Stop all services and delete volumes

```bash
docker compose down -v
```

Use `-v` carefully because it removes persistent stored data from Docker volumes.

---

# 📘 Swagger Documentation URLs

Each service has its own docs now.

- Auth Service → `http://localhost:8001/docs`
- Flight Service → `http://localhost:8002/docs`
- Booking Service → `http://localhost:8003/docs`
- Private Jet Service → `http://localhost:8004/docs`
- Admin Service → `http://localhost:8005/docs`

---

# 🧪 Suggested Testing Order

After starting the project, test in this order:

1. register or login in auth-service
2. copy the access token
3. open flight-service and test flights list/search
4. open booking-service and create a booking
5. open private-jet-service and test jet listing/booking
6. open admin-service and inspect logs/analytics

This order helps because the other services depend on valid authentication.

---

# 🧬 Alembic Migrations

The project still uses a shared PostgreSQL database, so migrations are still managed centrally.

## Generate a migration

```bash
alembic revision --autogenerate -m "your message"
```

## Apply latest migration

```bash
alembic upgrade head
```

## Roll back one migration

```bash
alembic downgrade -1
```

## Important note

Because the current architecture still shares models and one DB, migration handling remains centralized instead of per service.

---

# 💾 Data Persistence and Portability

Docker volumes are used so your database data survives container restarts.

This means:

- stopping a container does not delete your DB by default
- rebuilding containers does not automatically erase all data
- `docker compose down -v` removes persistent stored volume data

## Historical initial-load example

When loading an old SQL dump into Dockerized Postgres, the style of command used is:

```bash
"C:\Program Files\PostgreSQL\18\bin\psql" -U postgres -p 5433 -d flight < my_old_flight_data.sql
```

This uses the external host port `5433`, which forwards to internal PostgreSQL port `5432`.

---

# 🔍 Monitoring and Debugging

## See all running containers

```bash
docker ps
```

## See full stack logs

```bash
docker compose logs -f
```

## Service-specific logs

```bash
docker compose logs -f auth-service
```

```bash
docker compose logs -f flight-service
```

```bash
docker compose logs -f booking-service
```

```bash
docker compose logs -f private-jet-service
```

```bash
docker compose logs -f admin-service
```

## Infrastructure-specific logs

```bash
docker compose logs -f postgres
```

```bash
docker compose logs -f redis
```

```bash
docker compose logs -f mongo
```

### What these logs help you see

- Postgres logs show DB activity and SQL-level issues
- Redis logs help in token/cache debugging
- Mongo logs help inspect analytics/log write activity
- Service logs show Python import errors, auth problems, route errors, and runtime exceptions

---

# 🧪 Historical Command Reference

This section helps explain the full journey of the project.

## Old manual local commands

```bash
python -m venv venv
```

```bash
.\venv\Scripts\activate
```

```bash
pip install -r requirements.txt
```

```bash
uvicorn app.main:app --reload
```

---

## Old single-app Docker style

```bash
docker compose up -d
```

```bash
docker compose up --build
```

```bash
docker compose restart api
```

```bash
docker compose down
```

```bash
docker compose down -v
```

This was from the stage where one API container handled all routers together.

---

## Current microservices Docker style

```bash
docker compose up --build
```

```bash
docker compose up -d --build
```

```bash
docker compose down
```

```bash
docker compose down --remove-orphans
```

```bash
docker compose down -v
```

If an old monolith container is still running accidentally, `--remove-orphans` is especially useful.

---

# ⚠️ Current Design Choice and Limitation

This project is intentionally using:

- multiple FastAPI services
- one shared PostgreSQL database

This is good for your current learning and migration stage.

But it also means:

- services are not fully isolated yet
- booking-service still depends on flight/seat data directly
- shared models are still needed
- migrations are still centralized

So this is not yet “final pure microservices.”

It is a **strong intermediate architecture**.

---

# ✅ Why This Architecture Is Useful

This structure is useful because it gives you:

- service-level separation
- independent Swagger docs
- cleaner domain ownership
- easier future scaling
- easier learning of real-world service boundaries
- Docker-based deployment per service
- a practical path from monolith to microservices without breaking everything at once

---

# 📌 Final Summary

This project started as a simple manually run FastAPI backend.
Then it became a Dockerized single-app backend.
Then it was cleaned up into a modular monolith.
Now it runs as a **microservices-style system** with five separated FastAPI services:

- auth-service
- flight-service
- booking-service
- private-jet-service
- admin-service

These services are connected through shared infrastructure:

- PostgreSQL for business data
- Redis for token/cache support
- MongoDB for logs and analytics
- shared core/dependency/model code

This makes the project a practical, real-world transition from a monolith toward more advanced service-based backend architecture.
