# Changelog

All notable changes to Jobt AI Career Coach will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

# Changelog

All notable changes to Jobt AI Career Coach will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.3.0] - 2026-01-15

### ✨ Major Update - Admin Dashboard & Email Operations

This release enables full system operations with a comprehensive admin dashboard for user management and a robust email notification system. It also includes critical stability fixes for the interview engine.

### Added

#### Admin Dashboard (Phase 2A)
- **User Management**
  - `GET /api/v1/admin/users` - Paginated user list with email/name search
  - `GET /api/v1/admin/users/{id}` - Detailed user profile & activity view
  - `PATCH /api/v1/admin/users/{id}/status` - Ban/Unban user capabilities
- **System Analytics**
  - `GET /api/v1/admin/stats` - Platform-wide metrics (Total Users, Active Sessions, Revenue)
- **Security**
  - Rigid `admin` role enforcement on all admin routes

#### Email Service (Phase 2B)
- **SMTP Integration**
  - Robust `EmailService` using `aiosmtplib`
  - Gmail SMTP support with App Password authentication
  - HTML & Plain text multipart email support
- **Automated Notifications**
  - **Welcome Email**: Sent automatically on registration
  - **Password Reset**: Secure token link via email

### Fixed (Critical)

#### Interview Engine
- **Session Termination**: Fixed infinite loop where interviews exceeded question limits (e.g., 5/5). Now strictly auto-terminates.
- **Time Tracking**: Fixed "Null" or frozen timer by correcting timezone-naive vs. aware datetime calculations.
- **AI Personality**: Adjusted system prompts to be friendlier and less robotic, especially for "Beginner" difficulty.
- **OpenAI Integration**: Fixed `400 Bad Request` by properly mapping internal `interviewer` role to `assistant` for API consistency.

#### System Stability
- **Database Connection**: Fixed `connect() got an unexpected keyword argument` crashes for Neon/Supabase by stripping unsupported `sslmode` and `channel_binding` parameters.
- **Data Persistence**: Fixed `conversation_history` not saving by resolving SQLAlchemy in-place JSON mutation detection.
- **API Errors**: 
  - Fixed `500 Internal Server Error` on message sending (missing schema fields).
  - Fixed `500 Internal Server Error` on interview listing (Lazy loading/`joinedload` fix).

---

## [1.1.0] - 2025-12-14

### 🎯 Major Update - Interview System Complete!

This release adds the **core MVP feature** - AI-powered interview simulation with GPT-4 integration. Users can now practice real interviews with AI feedback.

### Added

#### Interview System (Core Feature)
- **Interview Session Management**
  - Start new interview sessions with job category selection
  - Real-time conversation flow with AI interviewer
  - Dynamic question generation based on user responses
  - Session timeout handling (30-minute inactivity)
  - Session status tracking (in_progress, completed, abandoned)
  - Interview history with pagination
  - Duration tracking and token usage monitoring

- **OpenAI GPT-4 Integration**
  - Async OpenAI client with retry logic
  - First question generation with user context
  - Follow-up question generation based on conversation
  - Adaptive difficulty (beginner: 5Q, intermediate: 7Q, advanced: 10Q)
  - AI interviewer personality system
  - Comprehensive feedback generation
  - Token usage tracking for cost control
  - Support for both GPT-4 and GPT-3.5-Turbo

- **AI Interviewer System**
  - Professional, friendly interviewer personality
  - Context-aware questioning
  - STAR method coaching prompts
  - Industry-specific interview styles
  - Behavioral and technical question templates
  - African job market context awareness
  - Natural conversation flow

- **Subscription Integration**
  - Automatic limit checking before interview start
  - Usage counter incrementation
  - Monthly limit enforcement (5 interviews for free tier)
  - Remaining interviews calculation
  - Trial period management

- **Interview API Endpoints**
  - `POST /api/v1/interviews/start` - Start interview session
  - `POST /api/v1/interviews/{id}/message` - Send response, get next question
  - `POST /api/v1/interviews/{id}/end` - Complete interview and generate feedback
  - `GET /api/v1/interviews/{id}` - View session details
  - `GET /api/v1/interviews` - List interview history (paginated)

- **Feedback Generation**
  - AI-powered performance analysis
  - Scoring system (overall, relevance, confidence, positivity)
  - Strength identification with specific examples
  - Weakness analysis with improvement areas
  - Actionable tips for next interview
  - Filler word detection and counting
  - Response length analysis
  - Summary generation

#### Category System Enhancement
- **CategoryService** - Complete business logic layer
  - CRUD operations with validation
  - Industry-based filtering
  - Soft delete and hard delete options
  - Dependency checking before deletion
  - Category statistics and analytics
  - Question count tracking

- **Category API Endpoints** (10 routes)
  - `GET /api/v1/categories` - List categories (public, paginated)
  - `GET /api/v1/categories/industries` - Get unique industries
  - `GET /api/v1/categories/stats` - Category statistics
  - `GET /api/v1/categories/{id}` - Get category details
  - `GET /api/v1/categories/{id}/detail` - Category with statistics
  - `POST /api/v1/categories` - Create category (admin)
  - `PUT /api/v1/categories/{id}` - Update category (admin)
  - `DELETE /api/v1/categories/{id}` - Delete category (admin)
  - `PATCH /api/v1/categories/{id}/activate` - Activate category (admin)
  - `PATCH /api/v1/categories/{id}/deactivate` - Deactivate category (admin)

- **Seed Data**
  - 10 pre-configured job categories with descriptions
  - 40+ interview questions across categories
  - Multiple difficulty levels per category
  - Expected keywords for each question
  - Automated seeding script with clear/reseed options

#### Project Structure Improvements
- **Prompts Directory** - System prompts as code
  - Interviewer personality configurations
  - Question generation templates
  - Feedback generation prompts
  - Difficulty-specific guidance
  - Behavioral and technical question templates

- **Service Layer Pattern**
  - CategoryService for job category operations
  - InterviewService for session management
  - OpenAIService for AI integration
  - Clean separation of concerns
  - Reusable business logic

### Changed

#### OpenAI Integration
- **Migrated to OpenAI v1.x API** (Breaking change from v0.x)
  - Updated from `openai.ChatCompletion.create()` to async client
  - Changed error handling (`openai.error` → direct imports)
  - Improved async/await patterns
  - Better error messages and retry logic

#### Configuration
- Added OpenAI settings to config
  - `OPENAI_API_KEY` - API authentication
  - `OPENAI_MODEL` - Model selection (gpt-4 or gpt-3.5-turbo)
  - `OPENAI_MAX_TOKENS` - Token limit per request
  - `MAX_SESSION_DURATION` - Interview timeout (30 minutes)

#### Documentation
- Added comprehensive integration guides
  - Category service setup instructions
  - Interview system integration steps
  - OpenAI API cost estimates
  - Testing procedures with examples
  - Troubleshooting guides

### Fixed
- **OpenAI API compatibility** with v1.x library
  - Fixed `AttributeError: module 'openai' has no attribute 'error'`
  - Fixed `APIRemovedInV1` error with ChatCompletion
  - Updated to use AsyncOpenAI client
  - Fixed exception handling for rate limits

### Technical Details

#### Dependencies
- OpenAI library v1.x support (async client)
- Continued use of FastAPI async patterns
- PostgreSQL JSONB for conversation storage
- Efficient token usage tracking

#### Performance
- Async OpenAI calls (non-blocking)
- JSONB for flexible conversation storage
- Optimized database queries with indexes
- Request timing middleware for monitoring

#### Security
- Session ownership verification
- Subscription limit enforcement
- Token usage monitoring
- Rate limit protection with exponential backoff

### Cost Optimization
- Token tracking per session
- Support for GPT-3.5-Turbo (12x cheaper than GPT-4)
- Cost estimates provided in documentation
- Monthly cost projections for different scales

**Estimated Costs:**
- GPT-3.5-Turbo: ~$0.002/interview ($10/month for 1000 users × 5 interviews)
- GPT-4: ~$0.024/interview ($120/month for 1000 users × 5 interviews)
- **Recommendation**: Use GPT-3.5-Turbo for MVP

---

## [1.2.0] - 2026-01-14

### 🚀 Major Update - Feedback & Analytics Complete!

This release fulfills the promise of Phase 1 by implementing the complete feedback loop and analytics dashboard. Users can now see detailed performance breakdowns and track their progress over time.

### Added

#### Feedback Service (Complete)
- **Comprehensive Feedback Generation**
  - Real-time filler word counting from user audio/text
  - Average response length tracking
  - Improvement rate calculation (% change)
  - Common strengths & weaknesses aggregation
  - Smart actionable tips generation
- **New Endpoints**
  - `GET /api/v1/feedback/{session_id}` - Detailed feedback view
  - `GET /api/v1/feedback/summary` - User's lifetime summary
  - `GET /api/v1/feedback/history` - Paginated feedback history
  - `POST /api/v1/feedback/compare` - Compare multiple sessions side-by-side

#### Analytics Service (Complete)
- **Progress Tracking System**
  - Time-series data visualization (7d, 30d, 90d, All)
  - Score breakdown by interview category
  - Usage statistics (total time, streak, interview count)
  - Category performance comparison (Best vs Worst)
- **New Endpoints**
  - `GET /api/v1/analytics/progress` - Progress trends
  - `GET /api/v1/analytics/breakdown` - Category scores
  - `GET /api/v1/analytics/statistics` - User stats
  - `GET /api/v1/analytics/comparison` - Performance insight

#### API Infrastructure
- **New Routers**
  - `feedback_route.py`: 4 new endpoints
  - `analytics_route.py`: 4 new endpoints
- **New Schemas**
  - `FeedbackResponse`, `FeedbackSummary`
  - `ProgressTrends`, `UserStatistics`
  - `CategoryComparison`
- **Testing Suite**
  - Comprehensive `pytest` infrastructure
  - `conftest.py` with async fixtures
  - 30+ tests achieving ~70% coverage
  - Integration tests for full user journey

### Enhanced
#### Interview System
- **Real-time UX Improvements**
  - Progress tracking (Questions X/Y)
  - Timeout warnings (< 5 minutes remaining)
  - Time remaining calculation

### Fixed
- Fixed specific module path issues in testing configuration
- Improved error handling in OpenAI service

---

## 🎯 What's Next (v1.3.0 - Phase 2)

### Immediate Priorities (Jan 2026)

#### 1. Payment Integration (Paystack)
- Subscription upgrade/downgrade flows
- Payment webhook handling
- Billing history & invoice generation

#### 2. Subscription Management
- Feature gating middleware
- Usage limit enforcement improvements
- Plan management endpoints

#### 3. Admin Dashboard
- System health metrics
- User management interface
- Financial analytics

---

## [1.0.0] - 2025-12-13

### 🎉 Initial MVP Release

This is the first production-ready release of Jobt AI Career Coach, focusing on core authentication, user management, and foundation features.

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
- Profile fields (email, name, job titles, experience)

#### Subscription System
- Four-tier subscription model
  - Free: 5 interviews/month (30-day trial)
  - Starter: 20 interviews/month (₦3,500/month)
  - Pro: Unlimited interviews (₦8,500/month)
  - Enterprise: Custom pricing and features
- Automatic trial subscription on registration
- Usage tracking (interviews per month)
- Subscription status management
- Feature flags for plan-specific capabilities
- Monthly usage reset mechanism
- Paystack integration preparation

#### Database Models
- User model with authentication fields
- PasswordReset model for secure token management
- Subscription model with usage tracking
- JobCategory model with industry classification
- QuestionTemplate model with difficulty levels
- InterviewSession model for conversation storage
- InterviewFeedback model for AI-generated feedback
- SystemMetrics model for admin analytics
- BaseModel with UUID primary keys and timestamps

#### API Documentation
- Interactive Swagger UI at `/docs`
- ReDoc documentation at `/redoc`
- OpenAPI 3.0 schema at `/openapi.json`
- Comprehensive endpoint descriptions
- Request/response examples
- Authentication documentation

#### Documentation
- Comprehensive README.md
- Detailed ROADMAP.md with quarterly milestones
- CHANGELOG.md (this file)
- pyproject.toml for modern Python packaging

---

## Release Statistics

### Version 1.1.0 (Current)
- **Total Routes**: 17 (8 auth + 5 interviews + 10 categories + 4 system)
- **Database Tables**: 8
- **Service Classes**: 3 (Auth, Category, Interview, OpenAI)
- **Lines of Code**: ~2,500+
- **Features Complete**: 75% of MVP
- **Integration Status**: OpenAI ✅, Paystack ⏳

### Development Timeline
- **v0.1.0**: Project inception (Dec 3, 2025)
- **v0.2.0**: Database and auth foundation (Dec 10, 2025)
- **v1.0.0**: MVP launch - Auth & Subscriptions (Dec 13, 2025)
- **v1.1.0**: Interview system complete (Dec 14, 2025)
- **v1.2.0**: Feedback & Analytics (Planned: Dec 15-16, 2025)
- **v2.0.0**: Public launch with payments (Planned: Jan 2026)

---

## Migration Notes

### Migrating from v1.0.0 to v1.1.0

1. **Install OpenAI package:**
   ```bash
   pip install openai==1.3.5
   ```

2. **Update environment variables:**
   ```bash
   # Add to .env
   OPENAI_API_KEY=sk-your-key-here
   OPENAI_MODEL=gpt-3.5-turbo
   OPENAI_MAX_TOKENS=1000
   MAX_SESSION_DURATION=1800
   ```

3. **Run database migrations:**
   ```bash
   # Migrations should already be applied if you ran them in v1.0.0
   # Verify:
   alembic current
   ```

4. **Seed job categories:**
   ```bash
   python scripts/seed_categories.py
   ```

5. **Update API integrations:**
   - New interview endpoints available
   - Category endpoints now active
   - Test with Swagger UI at `/docs`

---

## Contributors

### v1.1.0
- **Micheal Olorundare** - Backend Lead, Interview System, OpenAI Integration
- Claude AI - Architecture, Code Generation, Prompt Engineering

### v1.0.0
- **Micheal Olorundare** - Backend Lead, Core Development

---

## Support

- **Documentation**: https://docs.jobt.ai
- **API Status**: https://status.jobt.ai  
- **Email**: support@jobt.ai
- **Issues**: https://github.com/yourusername/jobt-ai/issues

---

*Last Updated: December 14, 2025*  
*Next Release: v1.2.0 (Feedback & Analytics) - December 15-16, 2025*

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