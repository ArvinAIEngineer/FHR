from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List
from collections import Counter
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# In-memory ticket storage
tickets = []
ticket_id_counter = 1

# ----- API MODEL -----
class Ticket(BaseModel):
    title: str
    description: str
    priority: str
    category: str

# ----- API ENDPOINTS -----
@app.post("/api/tickets", response_model=dict)
def create_ticket(ticket: Ticket):
    global ticket_id_counter
    new_ticket = { "id": ticket_id_counter, **ticket.dict() }
    tickets.append(new_ticket)
    ticket_id_counter += 1
    print("DEBUG: Tickets ->", tickets)  # Debug log
    return new_ticket

@app.get("/api/tickets", response_model=List[dict])
def list_tickets():
    return tickets

@app.get("/api/tickets/{ticket_id}", response_model=dict)
def get_ticket(ticket_id: int):
    for t in tickets:
        if t["id"] == ticket_id:
            return t
    return {"error": "Ticket not found"}

# ----- UI ROUTES -----
@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    total = len(tickets)
    by_priority = Counter([t["priority"] for t in tickets])
    by_category = Counter([t["category"] for t in tickets])
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "total": total,
        "by_priority": by_priority,
        "by_category": by_category
    })

@app.get("/tickets", response_class=HTMLResponse)
def tickets_list(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "tickets": tickets})

@app.post("/submit", response_class=HTMLResponse)
def submit_ticket(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    priority: str = Form(...),
    category: str = Form(...)
):
    global ticket_id_counter
    new_ticket = {
        "id": ticket_id_counter,
        "title": title,
        "description": description,
        "priority": priority,
        "category": category,
    }
    tickets.append(new_ticket)
    ticket_id_counter += 1
    print("DEBUG: Tickets ->", tickets)  # Debug log
    return RedirectResponse("/tickets", status_code=302)

@app.get("/ticket/{ticket_id}", response_class=HTMLResponse)
def ticket_detail(request: Request, ticket_id: int):
    for t in tickets:
        if t["id"] == ticket_id:
            return templates.TemplateResponse("ticket.html", {"request": request, "ticket": t})
    return HTMLResponse("<h1>Ticket not found</h1>", status_code=404)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
