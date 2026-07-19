# Textile Invoice & Billing Management System

A full-stack application for managing customers, products, GST-ready invoices, sales reports, and company settings. Invoices can be downloaded as PDFs with the configured company logo.

## Features

- JWT-protected React dashboard
- Customer and product management
- Invoice creation with CGST, SGST, or IGST calculations
- Invoice history, deletion, and PDF download
- PDF invoices with company details and an optional Base64-encoded logo
- Dashboard metrics, sales reports, GST reports, and CSV export
- Company and bank-detail settings

## Tech stack

| Layer | Technology |
| --- | --- |
| Frontend | React 18, Vite, Material UI, Axios, React Hook Form, Recharts |
| Backend | FastAPI, SQLAlchemy, Pydantic |
| Database | PostgreSQL for deployment; SQLite is available only for local development |
| Authentication | JWT with bcrypt password hashing |
| PDF generation | ReportLab |

## Project structure

```text
.
|-- backend/
|   |-- app/
|   |   |-- api/          # Auth, customers, products, invoices, reports, settings
|   |   |-- auth/         # JWT and password utilities
|   |   |-- database/     # SQLAlchemy session configuration
|   |   |-- models/       # Database models
|   |   |-- pdf/          # Invoice PDF generator
|   |   |-- schemas/      # Pydantic request/response schemas
|   |   `-- main.py       # FastAPI application entry point
|   |-- requirements.txt
|   `-- .env
`-- frontend/
    |-- src/
    |   |-- components/
    |   |-- pages/
    |   `-- services/api.js
    `-- package.json
```

## Prerequisites

- Python 3.10 or later
- Node.js 18 or later
- npm

## Setup and run

### 1. Backend

From the `backend` directory, create and activate a virtual environment, then install dependencies.

```powershell
cd backend
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copy `backend/.env.example` to `backend/.env` and set the values. For local development, `DATABASE_URL=sqlite:///./invoice.db` is supported. For deployment, use the PostgreSQL URL supplied by Supabase or another managed PostgreSQL provider.

```env
DATABASE_URL=postgresql+psycopg2://postgres:password@db.example.supabase.co:5432/postgres
SECRET_KEY=generate-a-long-random-value
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
INITIAL_ADMIN_USERNAME=invoice_admin
INITIAL_ADMIN_PASSWORD=choose-a-strong-password
CORS_ORIGINS=https://your-project.pages.dev
```

Start the API:

```powershell
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`. Interactive API documentation is available at `http://localhost:8000/docs`.

On first startup, the backend creates the administrator configured through `INITIAL_ADMIN_USERNAME` and `INITIAL_ADMIN_PASSWORD`. It does not contain a hard-coded default password.

### 2. Frontend

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the URL shown by Vite, normally `http://localhost:5173`.

By default the frontend connects to `http://localhost:8000/api`. To use a different API address, create `frontend/.env.local`. In Cloudflare Pages, add the same variable in **Settings → Environment variables** before building:

```env
VITE_API_URL=http://localhost:8000/api
```

## Company logo in invoice PDFs

Go to **Settings** and enter a logo as a Base64 data URI, for example:

```text
data:image/png;base64,iVBORw0KGgoAAAANSUhEUg...
```

The logo is displayed in the top-left of the generated invoice PDF. Invalid or unsupported image data is skipped so it does not prevent the PDF from being generated.

## API overview

All endpoints except login require a bearer token in the `Authorization` header.

| Area | Base path | Main operations |
| --- | --- | --- |
| Authentication | `/api/auth` | Login, logout, current user |
| Customers | `/api/customers` | Create, list, update, delete, billing history |
| Products | `/api/products` | Create, list, update, delete |
| Invoices | `/api/invoice` | Create, list, retrieve, delete, download PDF |
| Reports | `/api/reports` | Dashboard, sales, GST, CSV export |
| Settings | `/api/settings/company` | Get and update company details |

### Download an invoice PDF

```text
GET /api/invoice/{invoice_id}/pdf
```

The endpoint returns `application/pdf` with a download filename. When using Swagger, click **Download file** in the response section after executing the request. A normal browser navigation cannot authenticate the request unless it supplies a valid bearer token.

## Useful commands

```powershell
# Frontend production build
cd frontend
npm run build

# Frontend linting
npm run lint

# Backend tests
cd backend
pytest
```

## Security notes

- Never commit `.env`, database files, or real secrets.
- Configure explicit allowed CORS origins before deploying.
- Set unique `INITIAL_ADMIN_USERNAME` and `INITIAL_ADMIN_PASSWORD` values for every shared or production environment.
