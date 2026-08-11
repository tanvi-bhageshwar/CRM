# Support desk — customer support ticketing CRM

A small full-stack app for creating, searching, filtering, and updating
customer support tickets. Built for the Datastraw assessment.

## Stack

- **Backend:** Python + FastAPI
- **Database:** SQLite (2 tables: `tickets`, `notes`)
- **Frontend:** Plain HTML/CSS/JS (no build step), served directly by FastAPI
- **Deploy target:** Railway.app

## Folder structure

```
support-crm/
├── backend/
│   ├── main.py            # FastAPI app + all 4 API endpoints + serves frontend
│   ├── database.py        # SQLite connection + schema creation
│   ├── models.py          # Pydantic request/response schemas
│   ├── requirements.txt
│   └── crm.db              # created automatically on first run (gitignored)
├── frontend/
│   ├── index.html         # ticket list, live search, status filter
│   ├── new.html            # create ticket form
│   ├── ticket.html         # ticket detail, status update, notes
│   └── static/
│       ├── style.css
│       └── api.js          # shared fetch helpers
├── .env.example
├── .gitignore
└── README.md
```

## Running locally

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Then open http://localhost:8000 in your browser. The API itself lives under
`/api/tickets` and interactive docs are auto-generated at
http://localhost:8000/docs.

The SQLite database file (`backend/crm.db`) is created automatically on
first startup — no manual migration step needed.

## API reference

| Method | Path                     | Purpose                              |
|--------|--------------------------|---------------------------------------|
| POST   | `/api/tickets`           | Create a ticket                       |
| GET    | `/api/tickets`           | List tickets (`?status=`, `?search=`) |
| GET    | `/api/tickets/{id}`      | Get one ticket + its notes            |
| PUT    | `/api/tickets/{id}`      | Update status and/or add a note       |

## Design notes

- **Ticket IDs** (`TKT-001`, `TKT-002`, ...) are derived from the row's
  autoincrement `id`, so uniqueness is guaranteed by SQLite for free instead
  of hand-rolling a counter.
- **Search** is a single `LIKE`-based query across name, email, ticket ID,
  and description — good enough at this scale; a real production system
  handling "hundreds of tickets a day across multiple channels" would swap
  this for a proper full-text index (e.g. SQLite FTS5 or Postgres `tsvector`)
  once the table grows past a few thousand rows.
- **Notes** are append-only and update the parent ticket's `updated_at`,
  since a note is itself a form of activity on the ticket.
- **Raw `sqlite3` instead of an ORM** — the schema is two tables with one
  foreign key; an ORM would add indirection without adding value here.

## What I'd add with more time

- Ticket assignment to a specific support agent
- Priority levels (Low/Medium/High) with sorting
- Pagination on the ticket list for larger datasets
- Basic auth so only agents can update tickets

## Environment variables

None are strictly required to run the app locally — SQLite needs no
connection string. See `.env.example` for the one optional variable
(port override) if you want it.
