from app.config import settings

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )


"""
jpbt/
├── alembic/                          # Database migrations
│   ├── versions/
│   ├── script.py.mako
│   └── env.py
│
├── app/
│   ├── main.py                       # FastAPI entry point
│   ├── config.py                     # Environment variables and settings
│   ├── constants.py                  # All constants
│   │
│   ├── core/                         # Security, DB connections, middleware
│   │   ├── __init__.py
│   │   ├── security.py               # JWT authentication, password hashing
│   │   ├── oauth2.py                 # Authentication and user access control
│   │   ├── database.py               # Async database setup (SQLAlchemy + Supabase)
│   │   └── middleware.py             # CORS, logging, tenant isolation middleware
│   │
│   ├── models/                       # SQLAlchemy Database Models
│   │   ├── __init__.py
│   │   └── ...
│   │
│   ├── schemas/                      # Pydantic Models (Request/Response)
│   │   ├── __init__.py
│   │   └── ...
│   │
│   ├── services/                     # Business Logic Layer
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── interview_service.py
│   │   ├── feedback_service.py
│   │   ├── openai_service.py         # AI integration
│   │   ├── analytics_service.py      # Score calculations
│   │   └── email_service.py          # Notifications
│   │
│   ├── logs/
│   │   └── ...
│   │
│   ├── prompts/                       # ystem prompts as Python files
│   │   ├── ...
│   │   └── ...
│   │
│   ├── routers/                      # API Endpoints
│   │   ├── __init__.py
│   │   └── ...
│   │
│   └── utils/                        # Utilities and helpers
│       ├── __init__.py
│       ├── network.py                # Network resilience utilities
│       └── ...
│
├── tests/                            # Test suite (None is done yet here)
│   ├── __init__.py
│   ├── test_auth.py
│   └── ...
│
├── scripts/
│
├── requirements.txt                  # Python dependencies
├── .env.example                      # Environment variables template
├── .env                              # Environment variables (gitignored)
├── .gitignore                        
├── CHANGELOG.md                      
├── ROADMAP.md                      
├── alembic.ini                       # Migration settings
├── pyproject.toml                      
├── Dockerfile                        # Container configuration
├── run_server.py                     # Runs the server direct calling uvicorn.run("app.main:app", host="127.0.0.1", port=8010, reload=True)
└── README.md                         # Project documentation
"""