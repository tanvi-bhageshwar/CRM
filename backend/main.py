from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import get_connection, init_db
from models import (
    Note,
    TicketCreate,
    TicketCreateResponse,
    TicketDetail,
    TicketSummary,
    TicketUpdate,
    TicketUpdateResponse,
)

app = FastAPI(title="Support CRM API")

# Wide-open CORS is fine for an assessment project served from one origin;
# tighten this to your real frontend domain before using it for anything else.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_summary(row) -> TicketSummary:
    return TicketSummary(
        ticket_id=row["ticket_id"],
        customer_name=row["customer_name"],
        subject=row["subject"],
        status=row["status"],
        created_at=row["created_at"],
    )


# ---------------------------------------------------------------------------
# 1. POST /api/tickets — create a ticket
# ---------------------------------------------------------------------------
@app.post("/api/tickets", response_model=TicketCreateResponse, status_code=201)
def create_ticket(payload: TicketCreate):
    conn = get_connection()
    cur = conn.cursor()

    # Insert first to get the autoincrement id, then derive the human-facing
    # ticket_id from it (TKT-001, TKT-002, ...) — guaranteed unique for free.
    now = _now()
    cur.execute(
        """
        INSERT INTO tickets (ticket_id, customer_name, customer_email, subject,
                              description, status, created_at, updated_at)
        VALUES ('', ?, ?, ?, ?, 'Open', ?, ?)
        """,
        (payload.customer_name, payload.customer_email, payload.subject,
         payload.description, now, now),
    )
    new_id = cur.lastrowid
    ticket_id = f"TKT-{new_id:03d}"
    cur.execute("UPDATE tickets SET ticket_id = ? WHERE id = ?", (ticket_id, new_id))
    conn.commit()
    conn.close()

    return TicketCreateResponse(ticket_id=ticket_id, created_at=now)


# ---------------------------------------------------------------------------
# 2 & 3. GET /api/tickets — list, with optional status filter + text search
# ---------------------------------------------------------------------------
@app.get("/api/tickets", response_model=list[TicketSummary])
def list_tickets(
    status: str | None = Query(default=None),
    search: str | None = Query(default=None),
):
    conn = get_connection()
    sql = "SELECT * FROM tickets WHERE 1=1"
    params: list[str] = []

    if status:
        sql += " AND status = ?"
        params.append(status)

    if search:
        like = f"%{search}%"
        sql += """ AND (customer_name LIKE ? OR customer_email LIKE ?
                        OR ticket_id LIKE ? OR description LIKE ?)"""
        params.extend([like, like, like, like])

    sql += " ORDER BY created_at DESC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()

    return [_row_to_summary(r) for r in rows]


# ---------------------------------------------------------------------------
# 4. GET /api/tickets/{ticket_id} — full detail + notes
# ---------------------------------------------------------------------------
@app.get("/api/tickets/{ticket_id}", response_model=TicketDetail)
def get_ticket(ticket_id: str):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,)
    ).fetchone()

    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Ticket not found")

    note_rows = conn.execute(
        "SELECT note_text, created_at FROM notes WHERE ticket_id = ? ORDER BY created_at ASC",
        (ticket_id,),
    ).fetchall()
    conn.close()

    return TicketDetail(
        ticket_id=row["ticket_id"],
        customer_name=row["customer_name"],
        customer_email=row["customer_email"],
        subject=row["subject"],
        description=row["description"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        notes=[Note(note_text=n["note_text"], created_at=n["created_at"]) for n in note_rows],
    )


# ---------------------------------------------------------------------------
# 5. PUT /api/tickets/{ticket_id} — update status and/or add a note
# ---------------------------------------------------------------------------
@app.put("/api/tickets/{ticket_id}", response_model=TicketUpdateResponse)
def update_ticket(ticket_id: str, payload: TicketUpdate):
    conn = get_connection()
    row = conn.execute(
        "SELECT id FROM tickets WHERE ticket_id = ?", (ticket_id,)
    ).fetchone()
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Ticket not found")

    now = _now()

    if payload.status is not None:
        conn.execute(
            "UPDATE tickets SET status = ?, updated_at = ? WHERE ticket_id = ?",
            (payload.status, now, ticket_id),
        )

    if payload.notes:
        conn.execute(
            "INSERT INTO notes (ticket_id, note_text, created_at) VALUES (?, ?, ?)",
            (ticket_id, payload.notes, now),
        )
        # Adding a note counts as activity on the ticket too.
        conn.execute(
            "UPDATE tickets SET updated_at = ? WHERE ticket_id = ?", (now, ticket_id)
        )

    conn.commit()
    conn.close()

    return TicketUpdateResponse(success=True, updated_at=now)


# ---------------------------------------------------------------------------
# Serve the frontend (static files) from the same app/deployment
# ---------------------------------------------------------------------------
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
