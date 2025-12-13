# Changelog

All notable changes to Jobt AI Career Coach will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- Interview session management with OpenAI integration
- AI-powered feedback generation
- User analytics and progress tracking
- Payment integration with Paystack
- Admin dashboard with system metrics

---

## [1.0.0] - 2025-12-13

### 🎉 Initial MVP Release

This is the first production-ready release of Jobt AI Career Coach, focusing on core authentication, user management, and job category features.

### Added

#### Core Infrastructure
- FastAPI application setup with async support
- PostgreSQL database with SQLAlchemy ORM
- Alembic database migrations
- Environment-based configuration system
- Comprehensive error handling and logging
- CORS middleware for frontend integration
- Request timing and monitoring
- Health check endpoints

#### Authentication & Security
- User registration with email/password
- Secure JWT-based authentication
- Access token and refresh token system
- Password reset flow (request and confirm)
- Password strength validation (uppercase, digit, 8+ chars)
- Role-based access control (User, Admin)
- HTTPBearer and OAuth2PasswordBearer schemes
- Bcrypt password hashing
- Token expiration handling

#### User Management
- User profile creation and updates
- User role management (user, admin)
- Account activation/deactivation
- Last login tracking
- Profile fields:
  - Email, full name, phone
  - Current job title
  - Target job role
  - Years of experience

#### Subscription System
- Four-tier subscription model:
  - Free: 5 interviews/month (30-day trial)
  - Starter: 20 interviews/month (₦3,500/month)
  - Pro: Unlimited interviews (₦8,500/month)
  - Enterprise: Custom pricing and features
- Automatic trial subscription on registration
- Usage tracking (interviews per month)
- Subscription status management (trial, active, expired, cancelled)
- Feature flags for plan-specific capabilities
- Monthly usage reset mechanism
- Paystack integration preparation

#### Job Categories
- Complete CRUD operations for job categories
- 10 pre-seeded categories:
  - Software Engineer
  - Product Manager
  - Data Analyst
  - Sales Representative
  - Marketing Manager
  - Customer Success Manager
  - UI/UX Designer
  - Project Manager
  - Human Resources Manager
  - Financial Analyst
- Industry-based filtering
- Active/inactive status management
- Soft delete and hard delete options
- Category statistics and analytics
- Question count tracking
- 40+ pre-seeded interview questions across categories

#### API Documentation
- Interactive Swagger UI at `/docs`
- ReDoc documentation at `/redoc`
- OpenAPI 3.0 schema at `/openapi.json`
- Comprehensive endpoint descriptions
- Request/response examples
- Authentication documentation

#### Database Models
- User model with authentication fields
- PasswordReset model for secure token management
- Subscription model with usage tracking
- JobCategory model with industry classification
- QuestionTemplate model with difficulty levels
- InterviewSession model (structure ready)
- InterviewFeedback model (structure ready)
- SystemMetrics model for admin analytics
- BaseModel with UUID primary keys and timestamps

#### API Endpoints

**Authentication (`/api/v1/auth`)**
- `POST /register` - User registration with trial subscription
- `POST /login` - Email/password authentication
- `POST /login/swagger` - OAuth2-compatible login
- `POST /refresh` - Refresh access token
- `GET /me` - Get current user profile
- `PATCH /me` - Update user profile
- `POST /change-password` - Change password
- `POST /password-reset/request` - Request password reset
- `POST /password-reset/confirm` - Confirm password reset
- `POST /logout` - Logout (client-side token deletion)

**Job Categories (`/api/v1/categories`)**
- `GET /categories` - List all categories (public)
- `GET /categories/industries` - List unique industries (public)
- `GET /categories/stats` - Category statistics (public)
- `GET /categories/{id}` - Get category details (public)
- `GET /categories/{id}/detail` - Get category with statistics (public)
- `POST /categories` - Create category (admin only)
- `PUT /categories/{id}` - Update category (admin only)
- `DELETE /categories/{id}` - Delete category (admin only)
- `PATCH /categories/{id}/activate` - Activate category (admin only)
- `PATCH /categories/{id}/deactivate` - Deactivate category (admin only)

**System (`/`)**
- `GET /` - API root information
- `GET /health` - Health check with database status
- `GET /ping` - Simple ping endpoint
- `GET /info` - Detailed API information

#### Development Tools
- Seeding script for job categories and questions
- Database clear utility (with confirmation)
- Migration management with Alembic
- Comprehensive logging system
- Development server script
- Environment variable templates

#### Documentation
- Comprehensive README.md with:
  - Project overview
  - Quick start guide
  - Installation instructions
  - API documentation
  - Configuration guide
  - Usage examples
  - Troubleshooting
- Detailed ROADMAP.md with quarterly milestones
- CHANGELOG.md (this file)
- pyproject.toml for modern Python packaging

#### Code Quality
- Type hints throughout codebase
- Pydantic schemas for request/response validation
- Structured logging with log levels
- Error handling with HTTPException
- Database transaction management
- Async/await patterns
- Service layer architecture
- Clean separation of concerns

### Security Features
- End-to-end password encryption
- JWT token signature verification
- Token expiration validation
- SQL injection protection (SQLAlchemy ORM)
- XSS protection (Pydantic validation)
- CORS configuration
- Rate limiting preparation
- Secure password reset tokens (24-hour expiration)

### Technical Details
- **Framework:** FastAPI 0.104+
- **Database:** PostgreSQL with asyncpg
- **ORM:** SQLAlchemy 2.0 (async)
- **Migrations:** Alembic
- **Authentication:** JWT (python-jose)
- **Password Hashing:** bcrypt (passlib)
- **Validation:** Pydantic v2
- **Python Version:** 3.11+

### Developer Experience
- Clear project structure
- Naming conventions (`*_schema.py`, `*_route.py`)
- Comprehensive docstrings
- Request/response examples
- Swagger UI for testing
- Environment-based configuration
- Hot reload in development

---

## [0.2.0] - 2025-12-10

### Added
- Database models and schemas
- Authentication system foundation
- Subscription model structure

### Changed
- Refactored security module
- Split oauth2 from security functions
- Updated project structure

---

## [0.1.0] - 2025-12-03

### Added
- Initial project setup
- Basic FastAPI application
- Database configuration
- Project structure

---

## Release Notes

### Version 1.0.0 Highlights

This release marks the official MVP (Minimum Viable Product) launch of Jobt AI Career Coach. The platform is now ready for:

- ✅ User registration and authentication
- ✅ Subscription management (4 tiers)
- ✅ Job category browsing
- ✅ Admin operations

**What's Coming Next:**
- Interview simulation with OpenAI
- AI-powered feedback generation
- Progress analytics
- Payment integration (Paystack)
- Admin dashboard

**Stability:** Production-ready
- All authentication flows tested
- Database migrations stable
- API documentation complete
- Error handling comprehensive

**Known Limitations:**
- Interview features not yet implemented
- Email notifications log to console
- Payment integration pending
- Admin dashboard basic

**System Requirements:**
- Python 3.11+
- PostgreSQL 14+
- 2GB RAM minimum
- OpenAI API key
- Paystack account (for payments)

**For Developers:**
- Comprehensive API docs at `/docs`
- Seeding script for test data
- Clear service layer patterns
- Type hints throughout

**For Users:**
- Smooth registration flow
- 30-day free trial (5 interviews)
- Clear subscription tiers
- 10+ job categories ready

---

## Migration Guide

### From v0.x to v1.0

1. **Update environment variables:**
   ```bash
   # Add new required variables
   OPENAI_API_KEY=your-key
   PAYSTACK_SECRET_KEY=your-key
   FREE_TIER_MONTHLY_LIMIT=5
   TRIAL_PERIOD_DAYS=30
   ```

2. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

3. **Seed job categories:**
   ```bash
   python scripts/seed_categories.py
   ```

4. **Update API calls:**
   - Token now includes `refresh_token`
   - Profile endpoints moved to `/auth/me`
   - Categories are now public endpoints

---

## Deprecations

### v1.0.0
- None (initial release)

### Future Deprecations
- `/auth/login/swagger` will be merged with `/auth/login` in v2.0

---

## Security Updates

### v1.0.0
- Implemented JWT token system
- Added password strength validation
- Secured admin endpoints with RBAC
- Added password reset token expiration
- Implemented soft delete for categories

---

## Performance Improvements

### v1.0.0
- Async database operations throughout
- Optimized category queries with filters
- Request timing middleware
- Efficient pagination support

---

## Bug Fixes

### v1.0.0
- None (initial release)

---

## Breaking Changes

### v1.0.0
- None (initial release)

---

## Contributors

### v1.0.0
- **Micheal Olorundare** - Backend Lead, Core Development
- Claude AI - Architecture & Code Generation Support

---

## Links

- **Repository:** https://github.com/yourusername/jobt-ai
- **Documentation:** https://docs.jobt.ai
- **Website:** https://jobt.ai
- **Support:** support@jobt.ai

---

## Notes

### Release Strategy
- **Semantic Versioning:** MAJOR.MINOR.PATCH
  - MAJOR: Breaking changes
  - MINOR: New features (backward compatible)
  - PATCH: Bug fixes

### Release Cycle
- **Major releases:** Quarterly
- **Minor releases:** Monthly
- **Patch releases:** As needed

### Support Policy
- **Latest version:** Full support
- **Previous major:** Security updates only
- **Older versions:** No support

---

*For detailed feature information, see [ROADMAP.md](ROADMAP.md)*  
*For project overview, see [README.md](README.md)*