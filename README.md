# SmartBooks — AI-Powered Business Finance Manager

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![Django](https://img.shields.io/badge/Django-4.x-green?style=flat-square&logo=django)
![DRF](https://img.shields.io/badge/DRF-3.x-red?style=flat-square)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue?style=flat-square&logo=postgresql)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

> A production-ready SaaS finance management platform for small businesses — built with Django REST Framework, featuring an AI-powered expense categorization engine, invoice management with PDF generation, and a real-time financial dashboard.

---

## 📌 What is SmartBooks?

SmartBooks helps small businesses manage their finances digitally. Instead of using Excel sheets or paper registers, business owners can:

- Create and send **professional invoices** to clients
- Track **business expenses** with AI auto-categorization
- Monitor **cash flow** through a real-time dashboard
- Get **automatic overdue alerts** for unpaid invoices
- Download **PDF invoices** to share with clients

---

## ✨ Features

### 🔐 Authentication & Multi-Tenancy
- Email-based JWT authentication (register, login, logout)
- Token refresh and blacklisting for secure logout
- Email verification system
- **Multi-tenant architecture** — every business has fully isolated data
- Business profile management (name, logo, currency, tax number)

### 🧾 Invoice Management
- Create invoices with multiple line items
- Auto-generated invoice numbers (`INV-2024-0001` format)
- Automatic financial calculations (subtotal, tax, discount, total)
- Status machine: `Draft → Sent → Paid / Cancelled`
- Overdue detection — auto-flags invoices past due date
- **PDF generation** — download professional invoice PDFs
- Filter by status, client, date range

### 💸 Expense Tracking
- Log expenses with title, amount, vendor, payment method
- **AI auto-categorization** — no manual tagging needed
- Confidence scoring on AI predictions
- 10 built-in default categories
- Custom category creation per business
- Filter by category, date range
- Spending analytics by category and month

### 🤖 AI Engine
- NLP-based expense categorizer using keyword matching + fuzzy similarity
- Supports categories: Software, Office Supplies, Travel, Food, Utilities, Salaries, Marketing, Equipment, Professional Services, Miscellaneous
- Returns confidence score with every prediction
- Standalone `/ai-categorize/` endpoint for frontend suggestions

### 📊 Dashboard API
- Total revenue, expenses, and net profit
- Month-over-month revenue growth percentage
- Outstanding and overdue invoice amounts
- Revenue and expenses by month (last 6 months chart data)
- Top 5 expense categories
- Recent activity feed (last 5 invoices and expenses)

### 👥 Client Management
- Full CRUD for business clients
- Search by name, email, company
- Safety guard — cannot delete clients with existing invoices
- Per-client invoice and outstanding amount tracking

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend Framework | Django 4.x, Django REST Framework |
| Authentication | JWT via SimpleJWT |
| AI / NLP | Custom keyword + fuzzy matching engine |
| Database | PostgreSQL |
| PDF Generation | WeasyPrint |
| API Documentation | drf-spectacular (Swagger UI) |
| Storage | Django Media Files |

---

## 📁 Project Structure

```
smartbooks/
├── apps/
│   ├── accounts/           # Auth, users, business profiles
│   │   ├── models.py       # User, BusinessProfile, EmailVerificationToken
│   │   ├── serializers.py  # Register, Profile, BusinessProfile serializers
│   │   ├── views.py        # Register, Login, Profile, ChangePassword views
│   │   └── urls.py
│   ├── invoices/           # Invoice management + dashboard
│   │   ├── models.py       # Invoice, InvoiceItem
│   │   ├── serializers.py  # Invoice + InvoiceItem serializers
│   │   ├── views.py        # CRUD, Status, PDF, Dashboard views
│   │   ├── dashboard.py    # Dashboard data aggregation logic
│   │   ├── utils.py        # Invoice number generator
│   │   └── urls.py
│   ├── expenses/           # Expense tracking
│   │   ├── models.py       # Expense, ExpenseCategory
│   │   ├── serializers.py
│   │   ├── views.py        # CRUD, Stats, AI categorize views
│   │   ├── fixtures/       # Default expense categories
│   │   └── urls.py
│   ├── clients/            # Client management
│   │   ├── models.py       # Client model
│   │   ├── serializers.py
│   │   ├── views.py        # CRUD, Stats views
│   │   └── urls.py
│   └── ai_engine/          # AI categorization engine
│       └── categorizer.py  # NLP keyword + fuzzy matching logic
├── config/
│   ├── settings/
│   │   ├── base.py         # Shared settings
│   │   ├── development.py  # Dev-specific settings
│   │   └── production.py   # Production settings
│   ├── urls.py
│   ├── celery.py
│   └── wsgi.py
├── templates/
│   └── invoices/
│       └── invoice_pdf.html  # PDF invoice template
├── .env.example
├── .gitignore
├── manage.py
└── requirements.txt
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL
- Git

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/smartbooks.git
cd smartbooks

# 2. Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Open .env and fill in your database credentials and email settings

# 5. Create PostgreSQL database
# In psql or pgAdmin: CREATE DATABASE smartbooks_db;

# 6. Run migrations
python manage.py migrate

# 7. Load default expense categories
python manage.py loaddata apps/expenses/fixtures/default_categories.json

# 8. Create superuser (for admin panel)
python manage.py createsuperuser

# 9. Start the server
python manage.py runserver
```

Visit `http://localhost:8000/api/docs/` for the interactive Swagger documentation.

---

## 🔑 Environment Variables

Create a `.env` file in the root directory based on `.env.example`:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=smartbooks_db
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=youremail@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
```

> **Note:** For Gmail, generate an App Password from your Google Account settings. Never commit your real `.env` file to GitHub.

---

## 📡 API Endpoints

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/accounts/register/` | Register new business account |
| POST | `/api/accounts/login/` | Login and receive JWT tokens |
| POST | `/api/accounts/token/refresh/` | Refresh access token |
| POST | `/api/accounts/logout/` | Logout and blacklist token |
| GET | `/api/accounts/verify-email/` | Verify email address |
| GET/PUT | `/api/accounts/profile/` | Get or update user profile |
| GET/PUT | `/api/accounts/business/` | Get or update business profile |
| POST | `/api/accounts/change-password/` | Change password |

### Clients
| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/api/clients/` | List clients / Create client |
| GET/PUT/DELETE | `/api/clients/{id}/` | Client detail, update, delete |
| GET | `/api/clients/stats/` | Client statistics |

### Invoices
| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/api/invoices/` | List invoices / Create invoice |
| GET/PUT/DELETE | `/api/invoices/{id}/` | Invoice detail, update, delete |
| POST | `/api/invoices/{id}/status/` | Update invoice status |
| GET | `/api/invoices/{id}/pdf/` | Download invoice as PDF |
| GET | `/api/invoices/stats/` | Invoice statistics |

### Expenses
| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/api/expenses/` | List expenses / Create expense |
| GET/PUT/DELETE | `/api/expenses/{id}/` | Expense detail, update, delete |
| POST | `/api/expenses/ai-categorize/` | AI category prediction |
| GET | `/api/expenses/stats/` | Spending analytics |
| GET/POST | `/api/expenses/categories/` | List / create categories |

### Dashboard
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/dashboard/` | Full financial summary |

---

## 🤖 AI Expense Categorizer

The AI engine automatically categorizes expenses without any external API or ML model — making it fast, free, and offline-capable.

**How it works:**

1. Takes the expense title and description as input
2. Preprocesses text (lowercase, removes special characters)
3. Matches against keyword dictionary for each category
4. Uses fuzzy string similarity for typo tolerance
5. Returns the best matching category with a confidence score

**Example:**

```json
POST /api/expenses/ai-categorize/
{
    "title": "Bought a Dell laptop",
    "description": "For development work"
}

Response:
{
    "suggested_category": "Equipment & Hardware",
    "confidence": 0.87,
    "confidence_percent": "87%",
    "method": "keyword"
}
```

If no category is provided when creating an expense, the AI categorizes it automatically.

---

## 📊 Dashboard Response Example

```json
GET /api/dashboard/

{
    "summary": {
        "total_revenue": 150000,
        "revenue_this_month": 55000,
        "revenue_growth_percent": 66.7,
        "outstanding_amount": 75000,
        "overdue_amount": 25000,
        "total_expenses": 45000,
        "net_profit": 105000
    },
    "invoices": {
        "breakdown": [
            { "status": "paid", "count": 3, "total": 150000 },
            { "status": "overdue", "count": 1, "total": 25000 }
        ],
        "overdue_list": [...]
    },
    "charts": {
        "revenue_by_month": [...],
        "expenses_by_month": [...],
        "top_expense_categories": [...]
    },
    "recent_activity": {
        "invoices": [...],
        "expenses": [...]
    }
}
```

---

## 🔒 Security Features

- JWT authentication with short-lived access tokens (1 hour)
- Refresh token rotation and blacklisting on logout
- Multi-tenant isolation — users can only access their own data
- Password validation enforced on registration and change
- Environment variables for all sensitive credentials
- `.env` excluded from version control via `.gitignore`

---

## 🧠 Key Design Decisions

**Why custom User model?**
Django recommends always using a custom user model at project start. Using email instead of username is more user-friendly and industry standard.

**Why multi-tenant architecture?**
Every query is filtered by `business` (the tenant). This means User A can never access User B's data — even if they guess an ID. This is production SaaS thinking, not tutorial thinking.

**Why split settings?**
Separating `base.py`, `development.py`, and `production.py` is industry standard. It prevents accidentally running debug mode in production and keeps environment-specific config clean.

**Why store calculated totals?**
Invoice `subtotal`, `tax_amount`, and `total_amount` are stored in the database rather than calculated on every read. This makes dashboard queries fast — especially when aggregating across hundreds of invoices.

---

## 📄 License

This project is licensed under the MIT License.

---

## 👨‍💻 Author

**Muhammad Bilal Khan**  
Software Engineer | Python & Django Developer  
BS Software Engineering — COMSATS University Islamabad

[![GitHub](https://img.shields.io/badge/GitHub-M--B--Khan-black?style=flat-square&logo=github)](https://github.com/M-B-Khan)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?style=flat-square&logo=linkedin)](https://linkedin.com/in/muhammad-bilal-k-163651111)

---

> Built as a portfolio project to demonstrate production-quality Django REST API development, multi-tenant SaaS architecture, and AI/NLP integration.
