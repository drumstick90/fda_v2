# FDA Data Search v2 🚀

> Lean, fast FDA drug data search and retrieval platform

## 🎯 Vision
Build the fastest, most intuitive way to search and analyze FDA drug approval data. Think "Google for FDA data" - simple interface, powerful results.

## 🏗️ Architecture

```
fda_v2/
├── frontend/          # React + Vite + TypeScript
├── backend/           # FastAPI + Python
├── shared/            # Shared types and schemas
├── docs/              # API docs and guides
└── docker-compose.yml # One-command deployment
```

## 🚀 Tech Stack

### Frontend
- **React 18** + **TypeScript** - Modern, type-safe UI
- **Vite** - Lightning-fast development
- **Tailwind CSS** - Utility-first styling
- **React Query** - Smart data fetching
- **Recharts** - Beautiful data visualization

### Backend
- **FastAPI** - High-performance Python API
- **PostgreSQL** - Robust data storage
- **Redis** - Caching layer
- **Pydantic** - Data validation
- **SQLAlchemy** - ORM

### DevOps
- **Docker** - Containerization
- **Nginx** - Reverse proxy
- **GitHub Actions** - CI/CD

## 🎨 Key Features

- **Instant Search** - Real-time FDA data search
- **Smart Filters** - Drug type, approval date, company, etc.
- **Data Visualization** - Charts and graphs for trends
- **Export Options** - CSV, JSON, PDF reports
- **API Access** - RESTful API for developers
- **Mobile Responsive** - Works on all devices

## 🔥 MVP Features (Week 1)

1. **Search Interface** - Clean, Google-like search
2. **Basic Filters** - Drug name, company, year
3. **Results Display** - Card-based layout
4. **Detail View** - Complete drug information
5. **Export** - Download search results

## 📊 Data Sources

- FDA Orange Book
- FDA Drug Approvals
- FDA Adverse Events
- Clinical Trials Database

## 🚀 Getting Started

```bash
# Clone and setup (if from git)
git clone <repo>
cd fda_v2

# Option A) Local development (recommended)
npm install
npm run setup

# Start both frontend and backend (concurrently)
npm run dev

# Open the URL printed by Vite
# If port 3000 is busy, Vite will use 3001 automatically
# Example: http://localhost:3001

# Option B) Manual (two terminals)
# Terminal A (backend)
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal B (frontend)
cd frontend
npm install
npm run dev -- --host --port 3000
# If port 3000 is in use, Vite will switch to 3001 and print the new URL

# Option C) Docker (if installed)
docker compose up -d --build
```

### Dev server notes
- Frontend runs on Vite. It will serve the app on `http://localhost:3000` by default, or `http://localhost:3001` if 3000 is already in use.
- During development, the frontend uses a Vite proxy so that requests to `/api/*` are forwarded to the backend at `http://localhost:8000`.
- The backend FastAPI server listens on `http://localhost:8000`.

## 📁 Project Structure

```
fda_v2/
├── frontend/              # React + TypeScript + Tailwind
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # App pages (Home, Search, Batch)
│   │   ├── services/      # API client
│   │   ├── types/         # TypeScript definitions
│   │   └── utils/         # Helper functions
│   ├── package.json
│   └── Dockerfile
├── backend/               # FastAPI + Python
│   ├── main.py           # Main API server (mirrors your script!)
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml     # One-command deployment
└── README.md
```

## 🎯 Key Features Implemented

### ✅ Batch Query (Your Main Use Case)
- **Exact replica** of your antipsychotic script workflow
- Predefined drug lists (antipsychotics, antidepressants, etc.)
- Rate limiting respect for FDA API
- Real-time progress tracking
- CSV export functionality

### ✅ Individual Drug Search
- Single drug lookup with detailed information
- Rich data display (indications, manufacturer, routes, etc.)
- Fast autocomplete and suggestions

### ✅ Modern Architecture
- **Frontend**: React 18 + TypeScript + Tailwind CSS + Vite
- **Backend**: FastAPI + Python (async for performance)
- **Deployment**: Docker + docker-compose
- **API**: RESTful with comprehensive error handling

## 🎯 Success Metrics

- **< 200ms** search response time
- **99.9%** uptime
- **10k+** searches per day
- **< 3 clicks** to find any drug data

---

*Built with ❤️ for faster FDA data access*