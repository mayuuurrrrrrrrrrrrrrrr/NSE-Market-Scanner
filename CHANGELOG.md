# Changelog

All notable changes to the NSE Market Intelligence & Trading Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-09-22

### Added
- **Layered 3-Tier Enterprise Architecture**:
  - `app/api/v1/`: Modular FastAPI endpoints for `/health`, `/market`, `/scanner`, `/signals`, and `/alerts`.
  - `app/services/`: Isolated technical engine (`technical_engine.py`) calculating deterministic Fibonacci Pivots, Bollinger Bands, and EMAs.
  - `app/models/`: SQLAlchemy 2.0 ORM models for `ScanRun`, `StockMetric`, `TradeSignal`, `AlertLog`, and `ApiAuditLog`.
  - `app/database/`: Thread-safe connection pooling, SQLite support for instant testing, and PostgreSQL support for containerized production.
  - `app/integrations/`: Resilient market feed with exponential backoff retries, Kite Connect broker adapter, Telegram alert client, and Google Gemini AI reasoning engine.
- **REST APIs & OpenAPI**:
  - Interactive Swagger UI documentation at `/docs` and ReDoc at `/redoc`.
  - Request/Response validation powered by Pydantic v2 schemas.
  - Sliding-window rate limiting and optional API-Key security middleware.
- **Quality Engineering & Automated Testing**:
  - Comprehensive `pytest` test suite covering mathematical indicator correctness, database relationships, and API contract integration.
  - Transactional database fixtures with rollback for total test isolation.
  - Mock adapters for offline, sub-second execution (0.7s total test suite runtime).
- **Web Trading Terminal Dashboard**:
  - Dark glassmorphic financial UI with real-time benchmark index feeds, scanner radar, breakout badges, and manual scan triggers.
- **DevOps & Containerization**:
  - Multi-stage `Dockerfile` with non-root user execution (`appuser`).
  - `docker-compose.yml` linking FastAPI and PostgreSQL 15 with automated health checks.
- **Observability**:
  - Deep `/health` probe auditing database query latency, broker session status, and uptime.
  - HTTP middleware logging response times and API audit trails into the database.

### Changed
- Refactored monolith scripts into modular domain packages while maintaining complete backward compatibility with existing legacy scripts (`free_market_scanner.py`, `telegram_bot.py`, `01_EQFNO.py`).
