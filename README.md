# FDA Drug Label Search v2

A fast, research-oriented web app for searching and analyzing U.S. FDA drug label data. Built with React + FastAPI on top of the public [OpenFDA](https://open.fda.gov/) API — no database required, all data is fetched live.

Designed for researchers and clinicians working with drug labels, especially psychiatric drug classes (antipsychotics, antidepressants, mood stabilizers).

---

## Features

| Feature | Description |
|---------|-------------|
| **Single drug search** | Look up any generic drug name; extracts key indications, metadata, and shows the most recent label |
| **Batch query** | Search multiple drugs at once with configurable rate limiting and preset lists (antipsychotics, antidepressants, mood stabilizers) |
| **CSV export** | Download batch results as CSV |
| **Label analysis** | View all historical label versions for a drug, classified as *active / likely active / outdated* with a visual timeline |
| **Indication search** | Reverse lookup — find all FDA-labeled drugs that mention a specific indication (e.g. "schizophrenia"), with live streaming progress |
| **AI summaries** | Optional structured indication summaries via OpenAI, DeepSeek, or Gemini |

---

## Quick start

```bash
# Install all dependencies (frontend + backend)
npm run setup

# Start both frontend and backend
npm run dev
```

- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000

---

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 · TypeScript · Vite · Tailwind CSS · React Router 6 · TanStack Query 5 |
| Backend | FastAPI · Python 3 · Uvicorn · httpx · pandas |
| Data source | [OpenFDA drug/label API](https://open.fda.gov/apis/drug/label/) (no key required) |
| Infra (optional) | Docker · docker-compose · nginx |

---

## Project structure

```
fda_v2/
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── SearchPage.tsx          # Single drug search
│       │   ├── BatchQueryPage.tsx      # Multi-drug batch
│       │   ├── LabelAnalysisPage.tsx   # Label version timeline
│       │   └── IndicationSearchPage.tsx # Reverse indication lookup
│       ├── services/api.ts             # API client
│       └── types/index.ts
├── backend/
│   ├── main.py                         # All API logic (~1300 lines)
│   ├── uk_scraper.py                   # Standalone UK eMC scraper (not mounted)
│   └── requirements.txt
├── docker-compose.yml
├── Makefile
└── .env.example
```

---

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/drugs/search/{drug}` | Single drug — best label + extracted indications |
| `GET` | `/api/drugs/search/{drug}/stream` | SSE stream with progress events |
| `POST` | `/api/drugs/batch` | Batch search `{ drugs[], rate_limit_delay? }` |
| `GET` | `/api/drugs/lists` | Preset drug name lists |
| `GET` | `/api/drugs/analyze-labels/{drug}` | All label versions + active/outdated classification |
| `GET` | `/api/indications/search/{term}/stream` | SSE indication search with live logs |
| `POST` | `/api/export/csv` | Export results as CSV download |

```bash
# Quick sanity checks
curl http://localhost:8000/
curl http://localhost:8000/api/drugs/search/risperidone
curl -X POST http://localhost:8000/api/drugs/batch \
  -H "Content-Type: application/json" \
  -d '{"drugs": ["risperidone", "olanzapine"], "rate_limit_delay": 0.3}'
```

---

## Optional AI summaries

Set one of these in `backend/.env` to enable structured indication summaries:

```env
GEMINI_API_KEY=...
OPENAI_API_KEY=...
DEEPSEEK_API_KEY=...
```

The provider is selected automatically in priority order: OpenAI → DeepSeek → Gemini. Override the model with `AI_MODEL` (e.g. `models/gemini-1.5-pro-latest`).

---

## Docker

```bash
docker-compose up         # builds and starts all services
docker-compose up --build # force rebuild
```

Services: `frontend` (nginx, port 80), `backend` (uvicorn, port 8000), `postgres`, `redis`.

> PostgreSQL and Redis are configured in docker-compose but not yet connected to the application logic — reserved for future persistence and caching.

---

## Label status heuristics

The label analysis endpoint classifies each label version using `effective_time` and `version`:

| Status | Condition |
|--------|-----------|
| **active** | ≤ 730 days old and latest version for its `set_id` |
| **likely active** | ≤ 1825 days old |
| **outdated** | older than 1825 days or superseded by a newer version |
| **unknown** | missing or unparseable date |

---

## Environment variables

See `.env.example` for all available variables. The only required one for the app to function is none — OpenFDA requires no API key.
