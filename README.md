# Crypto Flow

Crypto Flow is a backend-oriented data pipeline project for ingesting cryptocurrency market data from the Binance API, transforming it into a normalized structure, and exposing processed data through a FastAPI application.

The project is intentionally split into two concerns:

- **`worker/`**: ingestion and transformation pipeline
- **`app/`**: HTTP API, domain logic, persistence, and application services

This separation keeps collection concerns away from the API layer and follows a simple but scalable architectural direction for data-driven systems.

## Project Status

**Current version: `v0.1`**

Implemented:

- Worker ingestion pipeline (requests + pandas)
- Data normalization and logging
- Multi-symbol ingestion
- File-based persistence (Excel)

Planned:

- PostgreSQL persistence (SQLAlchemy)
- FastAPI endpoints for data access
- Docker-based environment
- CI/CD pipeline

## Why this architecture?

This project is designed as a small data platform rather than a single-script API.

### Architectural decisions

#### 1. Worker and API are separated

The ingestion process lives in `worker/`, outside the FastAPI domain modules.

**Why?**
Because data collection and HTTP serving are different responsibilities:

- the **worker** pulls external data, transforms it, and persists it
- the **API** exposes already-processed data to clients

This separation reduces coupling and makes future scaling easier.  
Real-world analogy: the worker is the **factory line**, while FastAPI is the **storefront**.

#### 2. Layered backend structure inside `app/`

The FastAPI application follows a layered design:

- `api/`: routes and dependencies
- `core/`: configuration, logging, constants, database setup
- `models/`: persistence models
- `repositories/`: database access
- `schemas/`: request/response DTOs
- `services/`: business rules

**Why?**
This keeps transport concerns, business rules, and data access isolated.  
Trade-off: slightly more folders and ceremony now, but much better maintainability as the project grows.

#### 3. `requests` + `pandas` in the worker

The ingestion code uses:

- `requests` for external HTTP communication
- `pandas` is excellent for schema normalization, transformation steps, and quick data concatenation for historical storage.

**Why?**

- `requests` is simple and stable for scheduled ingestion jobs
- `pandas` is excellent for schema normalization and transformation steps

Trade-off:

- simpler than async/event-driven ingestion
- less scalable than a queue-based pipeline
- but easier to reason about and debug at this stage

#### 4. Temporary file persistence before database persistence

The worker currently writes transformed data to `data/trades.xlsx`.

**Why?**
This is a bootstrap strategy:

- validate extraction
- validate transformation
- inspect output quickly
- reduce moving parts early

Trade-off:

- Excel is useful for validation and demos
- PostgreSQL is the correct target for querying, indexing, and API exposure

#### 5. Docker as environment boundary

Docker is part of the intended architecture because the project is moving toward:

- reproducible local development
- isolated services
- database containerization
- CI/CD validation

This matters because backend systems rarely live as raw scripts only; they live inside a broader operational environment.

## Architecture Diagram

```mermaid
flowchart LR
    A[Binance REST API] --> B[Worker: trade_pipeline.py]
    B --> C[Transform with Pandas]
    C --> D[Temporary Output: trades.xlsx]

    subgraph Current v0.1
        B
        C
        D
    end

    C -. planned .-> E[(PostgreSQL)]
    E -. planned .-> F[FastAPI Backend]
    F -. planned .-> G[Clients / Consumers]

    subgraph Target Backend
        E
        F
        G
    end
