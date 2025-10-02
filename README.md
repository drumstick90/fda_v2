# FDA Data Search v2

Minimal, fast FDA drug data search with a React frontend and FastAPI backend.

## Minimal Quick Start

```bash
# From project root
npm run setup
npm run dev

# If 3000 is busy, Vite will serve on 3001 (use the URL it prints)
# Backend: http://localhost:8000
# Frontend: http://localhost:3000 or http://localhost:3001
```

API quick checks:
- Root: `GET http://localhost:8000/` → `{ "status": "active" }`
- Single: `GET http://localhost:8000/api/drugs/search/risperidone`
- Batch: `POST http://localhost:8000/api/drugs/batch` with `{ "drugs": ["risperidone"], "rate_limit_delay": 0.3 }`

Dev notes:
- Frontend uses Vite proxy: requests to `/api/*` are forwarded to `http://localhost:8000`.

## Current features
- Single-drug search (OpenFDA label endpoint)
- Batch query with rate limiting
- CSV export
- Extracted “Key Indications” derived from `indications_and_usage`
- Preset lists endpoint for quick batch population

## Stack
- Frontend: React + TypeScript + Vite + Tailwind CSS
- Backend: FastAPI + Python

## Project structure

```
fda_v2/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── types/
│   └── Dockerfile
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```