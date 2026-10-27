from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

import database
import gemini


class TicketCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    description: str = Field(min_length=1, max_length=5000)


class Ticket(BaseModel):
    id: int
    description: str
    category: str | None
    priority: str | None
    summary: str | None


class GeminiTestResult(BaseModel):
    model: str
    text: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield


app = FastAPI(title="MiniDesk AI", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/tickets", response_model=Ticket, status_code=201)
def create_ticket(ticket: TicketCreate):
    return database.create_ticket(ticket.description)


@app.get("/tickets", response_model=list[Ticket])
def list_tickets():
    return database.list_tickets()


@app.post("/tickets/{ticket_id}/analyze", response_model=Ticket)
def analyze_ticket(ticket_id: int):
    ticket = database.get_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="No se encontró la solicitud.")
    try:
        analysis = gemini.analyze_description(ticket["description"])
    except gemini.GeminiError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from None
    updated = database.update_analysis(
        ticket_id, analysis.category, analysis.priority, analysis.summary
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="No se encontró la solicitud.")
    return updated


@app.post("/gemini/test", response_model=GeminiTestResult)
def test_gemini():
    try:
        return gemini.test_connection()
    except gemini.GeminiError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from None
