import uuid
from fastapi import FastAPI, HTTPException, Depends, Path
from sqlalchemy import CheckConstraint, create_engine, Column, Integer, String, UUID
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base
import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from common import *

# Database configuration from environment variables
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_NAME = os.getenv("POSTGRES_DB", "postgres")
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(title="Tickets API")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Ticket(Base):
    __tablename__ = "ticket"

    id = Column(Integer, primary_key=True)
    ticket_uid = Column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4
    )
    username = Column(String(80), nullable=False)
    flight_number = Column(String(20), nullable=False)
    price = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False)

    __table_args__ = (
        CheckConstraint("status IN ('PAID', 'CANCELED')", name="ticket_status_check"),
    )


@app.get("/tickets/{username}", response_model=List[TicketResponse])
def get_tickets_by_user(username: str, db: Session = Depends(get_db)):
    tickets = db.query(Ticket).filter(Ticket.username == username).all()
    return tickets


@app.get("/tickets/{ticket_uid}", response_model=TicketResponse)
def get_ticket_by_uid(
    ticket_uid: uuid.UUID = Path(..., description="UUID билета"),
    db: Session = Depends(get_db),
):
    ticket = db.query(Ticket).filter(Ticket.ticket_uid == ticket_uid).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@app.post("/tickets", response_model=TicketResponse, status_code=201)
def create_ticket(request: TicketCreateRequest, db: Session = Depends(get_db)):
    existing = db.query(Ticket).filter(Ticket.ticket_uid == request.ticketUid).first()
    if existing:
        raise HTTPException(
            status_code=400, detail="Ticket with this UUID already exists"
        )

    new_ticket = Ticket(
        ticket_uid=request.ticketUid,
        username=request.username,
        flight_number=request.flightNumber,
        price=request.price,
        status="PAID",
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    return new_ticket


@app.delete("/tickets/{ticket_uid}", status_code=204)
def delete_ticket(ticket_uid: uuid.UUID, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.ticket_uid == ticket_uid).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    db.delete(ticket)
    db.commit()
    return None


@app.get("/manage/health", status_code=201)
def health():
    pass
