import inspect
import sys
from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import os

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

app = FastAPI(title="Flight API")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Airport(Base):
    __tablename__ = "airport"

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    city = Column(String(255))
    country = Column(String(255))

    # Relationships
    departures = relationship(
        "Flight", back_populates="from_airport", foreign_keys="Flight.from_airport_id"
    )
    arrivals = relationship(
        "Flight", back_populates="to_airport", foreign_keys="Flight.to_airport_id"
    )


class Flight(Base):
    __tablename__ = "flight"

    id = Column(Integer, primary_key=True)
    flight_number = Column(String(20), nullable=False)
    datetime = Column(TIMESTAMP(timezone=True))
    from_airport_id = Column(Integer, ForeignKey("airport.id"))
    to_airport_id = Column(Integer, ForeignKey("airport.id"))
    price = Column(Integer, nullable=False)

    # Relationships
    from_airport = relationship(
        "Airport", foreign_keys=[from_airport_id], back_populates="departures"
    )
    to_airport = relationship(
        "Airport", foreign_keys=[to_airport_id], back_populates="arrivals"
    )


def flight_to_response(flight: Flight) -> FlightResponse:
    from_airport = f"{flight.from_airport.country}, {flight.from_airport.name}"
    to_airport = f"{flight.to_airport.country}, {flight.to_airport.name}"

    return FlightResponse(
        flightNumber=flight.flight_number,
        fromAirport=from_airport,
        toAirport=to_airport,
        date=flight.datetime.isoformat(),
        price=flight.price,
    )


@app.get("/flights", response_model=PaginationResponse)
def get_all_flights(
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(
        10, ge=1, le=100, description="Количество элементов на странице"
    ),
    db: Session = Depends(get_db),
):
    offset = (page - 1) * page_size

    total = db.query(Flight).count()
    flights = db.query(Flight).offset(offset).limit(page_size).all()

    response_items = [flight_to_response(f) for f in flights]

    return PaginationResponse(
        page=page,
        pageSize=page_size,
        totalElements=total,
        items=response_items,
    )


@app.get("/flights/{flight_number}", response_model=FlightResponse)
def get_flight_by_number(flight_number: str, db: Session = Depends(get_db)):
    flight = db.query(Flight).filter(Flight.flight_number == flight_number).first()

    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")

    return flight_to_response(flight)


@app.get("/manage/health", status_code=201)
def health():
    pass
