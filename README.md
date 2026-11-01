# ⚡ NSE Market Intelligence & Algorithmic Trading Platform

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Pytest](https://img.shields.io/badge/Pytest-100%25_Passing-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)](https://pytest.org/)

An enterprise-grade, full-stack financial technology platform engineered for real-time market data ingestion, quantitative technical analysis (Fibonacci Pivots, Bollinger Bands, 50/200-day EMAs), algorithmic trade signal generation, and automated multi-channel alert dispatching.

Designed and architected following production software engineering patterns: **Layered 3-Tier Architecture**, **Async REST APIs (FastAPI)**, **Relational Persistence (SQLAlchemy ORM with PostgreSQL & SQLite)**, **Automated Testing Suite (`pytest`)**, **Containerization (Docker & Docker Compose)**, and **Interactive Web Dashboard**.

---

## 🏛️ System Architecture

```mermaid
graph TD
    subgraph Market Ingestion Layer
        NSE[NSE Historical & Real-time Feeds]
        KITE[Zerodha Kite Connect API]
        SCR[Screener.in Financial Fundamentals]
    end

    subgraph Core Application Layer
        MF[Market Feed Adapter / Retries]
        TE[Technical Indicator Engine\n(Pivots, Bollinger Bands, EMAs)]
        SE[Algorithmic Signal Engine]
        AI[Google Gemini AI Rationale Synthesis]
    end

    subgraph Data & Persistence Layer
        DB[(SQLAlchemy ORM\nSQLite / PostgreSQL)]
        SR[Scan Runs Table]
        SM[Stock Metrics Table]
        TS[Trade Signals Table]
        AL[Alert Logs Table]
        ALog[API Audit Logs Table]
    end

    subgraph Presentation & Client Layer
        API[FastAPI Async REST Layer]
        DOCS[Swagger / OpenAPI Documentation]
        DASH[Web Trading Terminal UI]
        TG[Telegram Bot Channel Dispatch]
    end

    NSE --> MF
    KITE --> MF
    SCR --> MF
    MF --> TE
    TE --> SE
    SE --> AI
    SE --> DB
    TE --> DB
    DB --> SR
    DB --> SM
    DB --> TS
    DB --> AL
    DB --> ALog
    DB --> API
    API --> DOCS
    API --> DASH
    SE --> TG
```

---

## 🎯 Opus Software Developer JD Mapping

This project was built to address and demonstrate competence across all core pillars of the **Opus Software Developer / Technical Engineer** role:

| Opus Requirement | Implementation in this Platform |
| :--- | :--- |
| **Application Engineering & Architecture** | Modular, decoupled 3-tier architecture with distinct domain services, data models, repositories, and presentation controllers. |
| **REST APIs & APIfication** | Async OpenAPI 3.0 / Swagger documentation, Pydantic v2 schema validation, standardized status codes, query filtering, and request pagination. |
| **Database & ORM Proficiency** | Relational schemas, foreign-key constraints, cascading deletes, query optimization, connection pooling, and multi-dialect compatibility (SQLite/PostgreSQL). |
| **Quality Engineering (QE) & Testing** | Comprehensive automated `pytest` suite with in-memory test database fixtures, unit tests for mathematical models, and API integration tests. |
| **Cloud & DevOps (Docker)** | Multi-stage, minimal `Dockerfile` with non-root security standards and multi-container `docker-compose.yml` with health checks. |
| **Observability & Health Monitoring** | Deep `/health` probe verifying database roundtrip latency, broker connection state, and system uptime. |
| **Financial Services / FinTech Domain** | Real-time equity analysis, market session phase state machine (Pre-open, Regular, Post-market), Fibonacci pivots, Bollinger Band standard deviation. |

---

## 📂 Project Structure

```
Algo-trading-suite-main/
│
├── app/                         # Enterprise Application Core
│   ├── api/                     # REST API Routing
│   │   └── v1/
│   │       ├── api.py           # Unified APIRouter aggregator
│   │       └── endpoints/
│   │           ├── health.py    # Deep health check & observability
│   │           ├── market.py    # NSE market session & live quote endpoints
│   │           ├── scanner.py   # Universe scans & metrics querying
│   │           ├── signals.py   # Algorithmic trade signals feed
│   │           └── alerts.py    # Outbound alert dispatch audit
│   ├── core/                    # Core Configuration & Cross-Cutting Concerns
│   │   ├── config.py            # Pydantic BaseSettings management (.env)
│   │   ├── logging.py           # Structured logging with leveled filters
│   │   └── security.py          # API key verification & sliding-window rate limiting
│   ├── database/                # Database Layer
│   │   ├── base.py              # Declarative ORM base
│   │   └── session.py           # Engine lifecycle, sessionmaker, init_db()
│   ├── models/                  # SQLAlchemy Relational Models
│   │   ├── scan_result.py       # ScanRun & StockMetric tables
│   │   ├── signal.py            # TradeSignal records
│   │   ├── alert.py             # AlertLog audit table
│   │   └── audit_log.py         # API request latency audit log
│   ├── schemas/                 # Pydantic Schemas (Data Transfer Objects)
│   │   ├── health.py            # System health contract
│   │   ├── market.py            # Quote, pivots, Bollinger Bands, and EMAs
│   │   └── scanner.py           # Scan requests, results, and signal models
│   ├── services/                # Pure Business Logic & Domain Services
│   │   ├── technical_engine.py  # Pure mathematical functions (Pivots, BB, EMA)
│   │   ├── scanner_service.py   # Universe scanner orchestrator
│   │   ├── signal_service.py    # Multi-factor signal evaluation
│   │   └── alert_service.py     # Notification dispatcher & throttling
│   └── integrations/            # External Integration Adapters
│       ├── market_feed.py       # Market data adapter with exponential retry backoff
│       ├── kite_client.py       # Zerodha Kite Connect broker adapter
│       ├── telegram_client.py   # Telegram Bot API client
│       └── gemini_ai.py         # Google Gemini AI reasoning engine
│
├── frontend/                    # Web Trading Dashboard
│   ├── index.html               # Modern financial terminal layout
│   └── static/
│       ├── css/style.css        # Glassmorphic dark theme
│       └── js/dashboard.js      # Real-time API consumption & reactive tables
│
├── tests/                       # Automated Test Suite (Pytest)
│   ├── conftest.py              # In-memory SQLite DB fixtures & FastAPI TestClient
│   ├── test_indicators.py       # Math verification (Fibonacci pivots, BB, EMA)
│   ├── test_database.py         # Relational database CRUD & constraints
│   ├── test_api.py              # API endpoint status & schema integration tests
│   └── test_scanner.py          # End-to-end scanner pipeline test with mocks
│
├── Dockerfile                   # Multi-stage production container build
├── docker-compose.yml           # Full-stack orchestrator (FastAPI + PostgreSQL)
├── requirements.txt             # Project dependencies
├── pytest.ini                   # Pytest testpath & pythonpath configuration
├── .env.example                 # Documented environment variables template
└── legacy/                      # Standalone trading bots & scripts (fully preserved)
    ├── free_market_scanner.py   # Direct console scanner
    ├── telegram_bot.py          # Polling Telegram bot
    ├── app.py                   # Streamlit UI
    └── 01_EQFNO.py              # F&O scanner
```

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.11+
- Git

### 1. Local Environment Setup

```bash
# Clone the repository
git clone https://github.com/your-username/Algo-trading-suite.git
cd Algo-trading-suite

# Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create your local environment file
copy .env.example .env   # Windows
# or: cp .env.example .env # Linux/macOS
```

### 2. Run the Automated Test Suite

```bash
python -m pytest tests/ -v
```

Expected Output:
```
============================= test session starts =============================
tests/test_api.py::test_health_endpoint PASSED                           [  6%]
tests/test_api.py::test_market_status_endpoint PASSED                    [ 12%]
tests/test_api.py::test_get_signals_endpoint PASSED                      [ 18%]
tests/test_api.py::test_get_scanner_results_empty PASSED                 [ 25%]
tests/test_api.py::test_get_scanner_results_seeded PASSED                [ 31%]
tests/test_database.py::test_create_scan_run_with_metrics PASSED         [ 37%]
tests/test_database.py::test_trade_signal_lifecycle PASSED               [ 43%]
tests/test_database.py::test_alert_log_persistence PASSED                [ 50%]
tests/test_indicators.py::test_fibonacci_pivot_hierarchy PASSED          [ 56%]
tests/test_indicators.py::test_fibonacci_pivot_invalid_inputs PASSED     [ 62%]
tests/test_indicators.py::test_bollinger_bands_breakout PASSED           [ 68%]
tests/test_indicators.py::test_bollinger_bands_oversold PASSED           [ 75%]
tests/test_indicators.py::test_bollinger_bands_insufficient_data PASSED  [ 81%]
tests/test_indicators.py::test_ema_calculation PASSED                    [ 87%]
tests/test_indicators.py::test_trend_evaluation PASSED                   [ 93%]
tests/test_scanner.py::test_scanner_service_mock_run PASSED              [100%]
======================== 16 passed in 0.72s ========================
```

### 3. Start the Application & Web Dashboard

```bash
uvicorn app.main:app --reload --port 8000
```

- **Web Dashboard**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Deep Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 🐳 Running with Docker & Docker Compose

Deploy the complete multi-container stack (FastAPI Backend + PostgreSQL Database) in a single command:

```bash
docker-compose up --build -d
```

The application automatically checks PostgreSQL health before bootstrapping the database schema.

---

## 📡 REST API Reference

| Method | Path | Summary | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Deep Health Check | Returns overall health, DB roundtrip latency, Telegram & broker status |
| `GET` | `/api/v1/market/status` | Market Session Status | Returns NSE session state (Pre-open, Regular, Closed) & benchmark indices |
| `GET` | `/api/v1/market/quote/{sym}` | In-depth Stock Quote | Real-time quote, Fibonacci Pivots, Bollinger Bands, and EMAs |
| `POST` | `/api/v1/scanner/run` | Trigger Market Scan | Executes scan over NIFTY 50 universe, saves run to DB, triggers signals |
| `GET` | `/api/v1/scanner/results` | Query Scan Results | Returns filterable and paginated stock metrics from the latest scan |
| `GET` | `/api/v1/scanner/runs` | List Scan Runs | Historical scan audit log with durations and breakout counts |
| `GET` | `/api/v1/signals` | Trade Signals Feed | Algorithmically scored setups with entry, targets, and AI rationales |
| `GET` | `/api/v1/alerts` | Alert History | Outbound notification delivery log and audit trail |

---

## 📊 Database Schema (Relational Models)

```
┌──────────────┐         1:N         ┌───────────────────┐
│  scan_runs   │────────────────────<│   stock_metrics   │
├──────────────┤                     ├───────────────────┤
│ id (PK)      │                     │ id (PK)           │
│ created_at   │                     │ scan_run_id (FK)  │
│ universe     │                     │ symbol            │
│ total_stocks │                     │ ltp               │
│ breakouts    │                     │ change_pct        │
│ oversold     │                     │ bb_upper/lower    │
│ duration_sec │                     │ pivot_p, r1..r3   │
│ status       │                     │ dema_50, dema_200 │
└──────────────┘                     └───────────────────┘

┌───────────────────┐               ┌───────────────────┐
│   trade_signals   │               │    alert_logs     │
├───────────────────┤               ├───────────────────┤
│ id (PK)           │               │ id (PK)           │
│ symbol            │               │ symbol            │
│ signal_type       │               │ channel (TELEGRAM)│
│ price, target, SL │               │ message           │
│ confidence        │               │ status (SENT)     │
│ rationale         │               │ created_at        │
└───────────────────┘               └───────────────────┘
```

---

## 💼 Interview Talking Points (Opus Placement)

When discussing this project during your Opus technical interview:

1. **"Walk me through the architecture of your application."**
   > *"I engineered a modular 3-tier financial system in Python. The presentation tier features an async REST API built with FastAPI and a modern web dashboard. The business layer isolates pure mathematical calculations like Fibonacci Pivots and Bollinger Bands into a deterministic technical engine. The data tier uses SQLAlchemy with connection pooling and support for both SQLite for instant testing and PostgreSQL for containerized production."*

2. **"How do you ensure reliability and testing?"**
   > *"I follow strict Quality Engineering principles. I decoupled the indicator math from network I/O, allowing 100% test coverage using `pytest`. I created fixtures with in-memory database transactions that rollback after each test, and mocked external market feeds so our integration tests run deterministically in under a second."*

3. **"How did you handle error handling, observability, and debugging?"**
   > *"I implemented exponential backoff retry wrappers on the market feed adapter to absorb transient network drops. For observability, I developed a deep `/health` endpoint that queries the database to measure live roundtrip latency in milliseconds and verifies broker session validity, as well as an audit-logging HTTP middleware measuring request-response durations."*
