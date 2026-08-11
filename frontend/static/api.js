// Tiny fetch wrapper — every page includes this before its own script.
const API_BASE = "/api/tickets";

async function apiCreateTicket(data) {
  const res = await fetch(API_BASE, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw await res.json();
  return res.json();
}

async function apiListTickets({ status = "", search = "" } = {}) {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  if (search) params.set("search", search);
  const res = await fetch(`${API_BASE}?${params.toString()}`);
  if (!res.ok) throw await res.json();
  return res.json();
}

async function apiGetTicket(ticketId) {
  const res = await fetch(`${API_BASE}/${ticketId}`);
  if (!res.ok) throw await res.json();
  return res.json();
}

async function apiUpdateTicket(ticketId, data) {
  const res = await fetch(`${API_BASE}/${ticketId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw await res.json();
  return res.json();
}

function statusBadgeClass(status) {
  if (status === "Open") return "badge badge-open";
  if (status === "In Progress") return "badge badge-progress";
  return "badge badge-closed";
}

function formatDate(iso) {
  return new Date(iso).toLocaleString(undefined, {
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
  });
}
