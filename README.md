# Jobt AI Career Coach Platform

**Enterprise Platform for AI-Powered Career Development**

---

## 📋 Project Overview

**Jobt AI Career Coach** is an enterprise platform designed to empower professionals and job seekers with AI-driven simulations of real-world career challenges. This full-stack application focuses initially on realistic interview practice with personalized feedback to build user competence and confidence.

### 🎯 MVP Value Proposition
> *"Users can practice text-based job interviews with a realistic AI, receive helpful, automated feedback, and track their performance improvement over time."*

## 🏗️ Repository Structure
first-jobt-repo/
├── backend/ # FastAPI Backend Service
│ ├── README.md # Backend-specific documentation
│ └── [FastAPI application structure]
├── frontend/ # Frontend Application (Coming Soon)
│ └── [To be populated]
├── docs/ # Project documentation
├── .gitignore
└── README.md # This file

text

---

## 🚀 Current Implementation Status

### ✅ **Phase 1: Backend MVP (Completed)**
The backend service is fully implemented with the following core capabilities:

| Component | Status | Description |
|-----------|--------|-------------|
| **Authentication** | ✅ Complete | Secure JWT-based authentication with OAuth2 scheme |
| **User Management** | ✅ Complete | User profiles with role-based access control (User/Admin) |
| **Subscription System** | ✅ Complete | Four-tier model with automatic trial on registration |
| **Job Categories** | ✅ Complete | 10+ pre-seeded categories with industry classification |
| **Database Models** | ✅ Complete | All required models for interviews and feedback |
| **API Documentation** | ✅ Complete | Interactive Swagger UI and ReDoc endpoints |

### 🔄 **Phase 2: Frontend Development (In Planning)**
Frontend development is scheduled to begin following backend stabilization.

---

## 🎯 Core Features

### 1. **AI Interview Simulation**
- Real-time text-based interviews with AI acting as interviewer
- Dynamic questions tailored to selected job roles
- Conversation history persistence for continuity and analysis

### 2. **Automated Performance Feedback**
- **Relevance Score**: Semantic comparison with expected answer models
- **Confidence Indication**: Analysis of hesitation words and sentiment
- **Positivity Tone**: Sentiment polarity evaluation
- **Key Strengths/Weaknesses**: AI-generated actionable guidance

### 3. **User Progress Tracking**
- Interview history with timestamps and final scores
- Score trend visualization over multiple sessions
- Skill improvement metrics

### 4. **Administration Controls**
- System usage metrics dashboard
- Job category and question set management
- User management and access control

---

## 🛠️ Technical Architecture

### Backend Stack
| Layer | Technology | Purpose |
|-------|------------|---------|
| **API Framework** | FastAPI (Python 3.11+) | High-performance async API service |
| **Database** | PostgreSQL 14+ | Primary data storage with JSONB support |
| **ORM** | SQLAlchemy 2.0 | Async database operations |
| **Authentication** | JWT (python-jose) | Secure token-based authentication |
| **AI Integration** | OpenAI API | Conversational AI for interviews |
| **Migrations** | Alembic | Database schema management |

### Frontend Stack *(Planned)*
| Layer | Technology | Purpose |
|-------|------------|---------|
| **Framework** | Next.js | Server-side rendering & dynamic UI |
| **Language** | TypeScript | Type-safe development |
| **Styling** | Tailwind CSS | Responsive design system |
| **State Management** | React Context/Redux | Application state management |

---

## 📁 Backend Service

The backend is a FastAPI application located in the `/backend` directory.

```markdown
# Jobt AI Career Coach

Internal enterprise platform for AI-powered career coaching, interview preparation, and professional development simulations.

**Status**: Active Development – MVP Phase (Target Launch: January 2026)  
**Confidentiality Notice**: This repository contains proprietary and confidential information. Access is restricted to authorized team members only.

## Quick Start (Backend)

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your credentials (see example below)

# Initialize database
alembic upgrade head
python scripts/seed_categories.py

# Start development server
python run_server.py
```

### API Access (Local Development)
- Base URL: http://localhost:8010
- Interactive Docs (Swagger UI): http://localhost:8010/docs
- Alternative Docs (ReDoc): http://localhost:8010/redoc

### Example `.env` Configuration

```env
# Core Application
APP_NAME="Jobt AI Career Coach"
DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/jobt_db"
SECRET_KEY="your-secure-secret-key"

# AI Integration
OPENAI_API_KEY="sk-your-openai-api-key"

# Security
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALGORITHM="HS256"
```

## 🔮 Product Roadmap

### Phase 1: MVP Launch (Target: January 2026)
- ✅ Backend API complete
- 🔄 Frontend application development
- 🔄 Full interview simulation flow
- 🔄 Integration testing

### Phase 2: Enhanced Features (Post-MVP)
- Video interview capability with real-time analysis
- Advanced scenarios (salary negotiation, workplace simulations)
- Gamification elements and achievement systems
- Corporate HR dashboards and team analytics
- Third-party integrations (LinkedIn, calendar systems)

### Phase 3: Enterprise Scaling (Future)
- Multi-tenant architecture for corporate clients
- Advanced analytics and reporting
- Custom AI model training
- White-label deployment options

## 👥 Team & Development

### Backend Team
- **Lead Developer**: Micheal Olorundare  
  Focus: API architecture, database design, security implementation

### Frontend Team
- **Position**: Open / To be filled  
  Focus: User interface, interactive elements, mobile-responsive design

### Collaboration Practices
- **API Contracts**: Defined via OpenAPI/Swagger documentation
- **Version Control**: Feature branching workflow with mandatory pull requests
- **Communication**: Regular sync meetings for integration alignment

## 📄 Documentation

| Document                  | Location                        | Purpose                                      |
|---------------------------|---------------------------------|----------------------------------------------|
| Backend Guide             | `/backend/README.md`            | Complete backend setup and API reference     |
| API Documentation         | http://localhost:8010/docs      | Interactive API testing and reference        |
| Product Requirements      | `docs/PRD.pdf`                  | Full product specifications                  |
| MVP Scope                 | `docs/MVP_Scope.docx`           | Minimum viable product definition            |
| Changelog                 | `CHANGELOG.md`                  | Version history and release notes            |

## 🔒 Security & Compliance

### Data Protection
- End-to-end encryption for sensitive communications
- Secure password hashing using bcrypt
- JWT tokens with expiration and strict validation

### Access Control
- Role-based access control (RBAC) on all endpoints
- Principle of least privilege enforced
- Audit logging for administrative operations

### Compliance Readiness
- GDPR/CCPA-compliant data handling patterns
- Anonymous aggregation for benchmarking
- Secure storage and transmission (TLS)

## 📈 Success Metrics

### User Engagement
- Weekly Active Users (WAU)
- Average session duration
- Feature adoption rates

### Product Effectiveness
- Pre/post-practice skill improvement scores
- User satisfaction (NPS/CSAT)
- Feedback quality ratings

### Technical Performance
- API response times: < 200ms (p95)
- System uptime target: 99.9%
- Error rate target: < 0.1%

## 🐛 Support & Troubleshooting

### Common Issues
- **Database Connection**: Ensure PostgreSQL service is running and credentials are correct
- **Migration Errors**: Reset with `alembic downgrade base && alembic upgrade head`
- **Environment Variables**: Verify `.env` file exists and contains valid values

### Development Support
- Backend issues → Contact backend team
- Frontend issues → Contact frontend team
- Integration issues → Review API contracts and interactive docs

## 📬 Contact

**Project Lead**: Micheal Olorundare  
**Repository**: Company Internal Git Repository  
**Status**: Active Development – MVP Phase

This is an internal enterprise platform. All code, documentation, and intellectual property are proprietary and confidential.