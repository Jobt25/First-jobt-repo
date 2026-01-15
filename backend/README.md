# 🎯 Jobt AI Career Coach

> AI-powered interview practice platform helping professionals ace their next job interview

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)

## 📖 Overview

Jobt AI is a comprehensive interview preparation platform that uses artificial intelligence to simulate real-world job interviews, provide detailed feedback, and track your progress over time. Whether you're a fresh graduate or an experienced professional looking to switch roles, Jobt AI helps you practice, improve, and land your dream job.

### ✨ Key Features

- 🤖 **AI-Powered Interviews** - Realistic interview simulations powered by GPT-4
- 📊 **Detailed Feedback** - Comprehensive analysis of your responses including:
  - Relevance scoring
  - Confidence assessment
  - Communication quality
  - Actionable improvement tips
- 📈 **Progress Tracking** - Monitor your improvement over time with analytics
- 🎯 **Industry-Specific** - Tailored questions for 10+ job categories
- 💼 **Subscription Plans** - Flexible pricing for individuals and teams
- 🌍 **African Market Focus** - Payment via Paystack (NGN, GHS, KES, ZAR)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 14+
- OpenAI API key
- Paystack account (for payments)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/jobt-ai.git
cd jobt-ai
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your credentials
```

5. **Create database**
```bash
createdb jobt_db
```

6. **Run migrations**
```bash
alembic upgrade head
```

7. **Seed initial data**
```bash
python scripts/seed_categories.py
```

8. **Start the server**
```bash
python run_server.py
```

The API will be available at `http://localhost:8010`

📚 **API Documentation:** `http://localhost:8010/docs`

---

## 🏗️ Project Structure

```
jobt-ai/
├── app/
│   ├── core/              # Core functionality (security, database)
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic schemas (*_schema.py)
│   ├── routers/           # API endpoints (*_route.py)
│   │   └── api/v1/
│   ├── services/          # Business logic
│   ├── prompts/           # AI prompt templates
│   └── utils/             # Helper functions
├── alembic/               # Database migrations
├── scripts/               # Utility scripts
├── tests/                 # Test suite
├── .env                   # Environment variables (not in git)
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Application
APP_NAME=Jobt AI Career Coach
VERSION=1.0.0
DEBUG=True

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/jobt_db

# Security
SECRET_KEY=your-secret-key-here  # Generate with: openssl rand -hex 32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# OpenAI
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=1000

# Paystack
PAYSTACK_SECRET_KEY=sk_test_your_paystack_secret
PAYSTACK_PUBLIC_KEY=pk_test_your_paystack_public

# Subscription
FREE_TIER_MONTHLY_LIMIT=5
TRIAL_PERIOD_DAYS=30

# Frontend
FRONTEND_URL=http://localhost:3000
```

---

## 📦 Tech Stack

### Backend
- **FastAPI** - Modern, fast web framework
- **SQLAlchemy** - Async ORM
- **PostgreSQL** - Primary database
- **Alembic** - Database migrations
- **Pydantic** - Data validation

### AI & Services
- **OpenAI GPT-4** - Interview simulation
- **Paystack** - Payment processing
- **JWT** - Authentication

### Development
- **pytest** - Testing framework
- **Black** - Code formatting
- **mypy** - Type checking

---

## 🎓 Usage

### 1. Register an Account

```bash
curl -X POST http://localhost:8010/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe",
    "current_job_title": "Junior Developer",
    "target_job_role": "Senior Developer"
  }'
```

**Response:** Access token + 30-day free trial with 5 interviews

### 2. Browse Job Categories

```bash
curl http://localhost:8010/api/v1/categories
```

### 3. Start an Interview

```bash
curl -X POST http://localhost:8010/api/v1/interviews/start \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "category_id": "uuid-here",
    "difficulty": "intermediate"
  }'
```

### 4. Get Feedback

After completing the interview, receive detailed AI-powered feedback on your performance.

---

## 💰 Pricing

### Free Plan
- ✅ 5 interviews per month
- ✅ Basic feedback
- ✅ Progress tracking
- ✅ 30-day trial

### Starter Plan - ₦3,500/month
- ✅ 20 interviews per month
- ✅ Advanced feedback
- ✅ Detailed analytics
- ✅ Custom scenarios

### Pro Plan - ₦8,500/month
- ✅ Unlimited interviews
- ✅ Priority support
- ✅ Video practice (coming soon)
- ✅ Export transcripts

### Enterprise - Custom Pricing
- ✅ Team management
- ✅ HR analytics
- ✅ Custom AI training
- ✅ White-label option

---

## 🧪 Testing

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=app --cov-report=html
```

### Run specific test file
```bash
pytest tests/test_auth.py -v
```

---

## 📊 API Documentation

### Interactive Documentation
- **Swagger UI:** http://localhost:8010/docs
- **ReDoc:** http://localhost:8010/redoc

### Key Endpoints

#### Authentication
- `POST /api/v1/auth/register` - Create account
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token
- `GET /api/v1/auth/me` - Get profile

#### Job Categories
- `GET /api/v1/categories` - List categories
- `GET /api/v1/categories/{id}` - Get category details
- `POST /api/v1/categories` - Create category (admin)

#### Interviews (Coming Soon)
- `POST /api/v1/interviews/start` - Start interview
- `POST /api/v1/interviews/{id}/message` - Send response
- `POST /api/v1/interviews/{id}/end` - End interview
- `GET /api/v1/interviews` - List history

#### Subscriptions (Coming Soon)
- `GET /api/v1/subscriptions/me` - Get subscription
- `POST /api/v1/subscriptions/upgrade` - Upgrade plan
- `POST /api/v1/subscriptions/cancel` - Cancel subscription

---

## 🐛 Troubleshooting

### Database Connection Error
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Verify connection
psql -U your_user -d jobt_db
```

### Migration Issues
```bash
# Reset migrations
alembic downgrade base
alembic upgrade head
```

### OpenAI Rate Limits
- Monitor usage in OpenAI dashboard
- Implement exponential backoff
- Consider caching responses

---

## 📝 License



---

## 👥 Team

**Backend Lead:** Micheal Olorundare  
**Email:** mehselleva@gmail.com  
**Location:** Ilorin Kwara State, Nigeria

---

## 🙏 Acknowledgments

- OpenAI for GPT-4 API
- FastAPI community
- Paystack for payment infrastructure
- All early users

---

## 🔗 Links

- **Website:** https://jobt.ai
- **Documentation:** https://docs.jobt.ai
- **API Status:** https://status.jobt.ai
- **Support:** support@jobt.ai

---

## 🗺️ Roadmap

See [ROADMAP.md](ROADMAP.md) for detailed feature timeline.

## 🎯 What's Next (Phase 2 - Planned)

### Payments & Admin (Jan 2026)
- 💳 **Paystack Integration** - Secure payments and subscription handling
- 👥 **Admin Dashboard** - User management and system metrics
- 📧 **Email Notifications** - Transactional emails and alerts

---

## 📈 Status

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Tests](https://img.shields.io/badge/tests-pass-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-70%25-green)

**Current Version:** 1.2.0 (Phase 1 Complete)  
**Last Updated:** January 14, 2026  
**Status:** 🟢 Active Development

---

**Made with ❤️ in Nigeria for African professionals**