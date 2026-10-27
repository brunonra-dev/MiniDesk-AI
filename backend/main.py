from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field

import database


class TicketCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    description: str = Field(min_length=1, max_length=5000)


class Ticket(BaseModel):
    id: int
    description: str
    category: str | None
    priority: str | None
    summary: str | None


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield


app = FastAPI(title="MiniDesk AI", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/tickets", response_model=Ticket, status_code=201)
def create_ticket(ticket: TicketCreate):
    return database.create_ticket(ticket.description)


@app.get("/tickets", response_model=list[Ticket])
def list_tickets():
    return database.list_tickets()
