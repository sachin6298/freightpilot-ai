# FreightPilot AI

**A PayPal-powered AI copilot for freight procurement, quote comparison, and payment-risk review.**

Developed for the **PayPal AI Hackathon 2026**.

---

## Architecture Overview

- **Frontend:** React 18, TypeScript, Vite (Port `5173`)
- **Backend:** Python 3.11+, FastAPI, Pydantic v2, Uvicorn (Port `8000`)
- **Payments:** PayPal Orders v2 REST API + JavaScript SDK (Sandbox Mode)
- **AI:** Grounded AI Copilot adapter with deterministic risk scoring fallback
- **Storage:** SQLite local database (`freightpilot.db`)

---

## Repository Layout

```text
freightpilot-ai/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py         # Pydantic v2 application settings
│   │   └── main.py           # FastAPI app and /health endpoint
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_health.py    # Health check unit tests
│   ├── requirements.txt      # Python dependencies
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.tsx           # Connectivity verification & UI dashboard
│   │   ├── index.css         # Modern design system
│   │   ├── main.tsx          # React application entry
│   │   └── vite-env.d.ts
│   ├── index.html
│   ├── package.json          # Node dependencies and build scripts
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── .env.example
├── docs/                     # Full project specification documents
├── AGENT_RULES.md            # Permanent development rules
├── .env.example              # Root environment template
├── .gitignore
├── LICENSE                   # Open-source MIT License
└── README.md
```

---

## Quick Start (Windows PowerShell)

### Prerequisites
- **Python 3.11+** (tested on 3.12.10)
- **Node.js LTS** (tested on v24.22.1 with npm 11.17.0)

### 1. Backend Setup
Open a terminal in the project root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run tests to verify the backend:
```powershell
pytest
```

Start the FastAPI server:
```powershell
uvicorn app.main:app --reload --port 8000
```
Backend API will be available at:
- Health check: `http://localhost:8000/health`
- Interactive Swagger docs: `http://localhost:8000/docs`

---

### 2. Frontend Setup
Open a second terminal in the project root:

```powershell
cd frontend
npm install
```

Build the production bundle:
```powershell
npm run build
```

Start the Vite development server:
```powershell
npm run dev
```
Open your browser at `http://localhost:5173` to view the application.

---

## Environment Configuration

- **Backend:** Copy `backend/.env.example` to `backend/.env`. Secrets (`PAYPAL_CLIENT_SECRET`, `AI_API_KEY`) remain strictly on the backend.
- **Frontend:** Copy `frontend/.env.example` to `frontend/.env.local`. Configure `VITE_API_BASE_URL` (defaults to `http://localhost:8000`).

---

## Project Status

- **Milestone 1 (Complete):** Core application foundations, FastAPI backend with `/health` and CORS, React + TypeScript + Vite frontend with live backend connectivity testing, automated test suite, and environment configuration.
- **Next Milestone:** Milestone 2 (Data models, SQLite persistence, and Quote Comparison UI).
