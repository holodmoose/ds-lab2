import inspect
import sys
import uuid
from fastapi import FastAPI, HTTPException, Depends, Path
from sqlalchemy import (
    TIMESTAMP,
    CheckConstraint,
    ForeignKey,
    create_engine,
    Column,
    Integer,
    String,
    UUID,
)
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base, relationship
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

app = FastAPI(title="Bonus API")


class PrivilegeDb(Base):
    __tablename__ = "privilege"

    id = Column(Integer, primary_key=True)
    username = Column(String(80), nullable=False, unique=True)
    status = Column(String(80), nullable=False, default="BRONZE")
    balance = Column(Integer, nullable=True, default=0)

    __table_args__ = (
        CheckConstraint(
            "status IN ('BRONZE', 'SILVER', 'GOLD')", name="privilege_status_check"
        ),
    )

    history = relationship(
        "PrivilegeHistoryDb", back_populates="privilege", cascade="all, delete"
    )


class PrivilegeHistoryDb(Base):
    __tablename__ = "privilege_history"

    id = Column(Integer, primary_key=True)
    privilege_id = Column(Integer, ForeignKey("privilege.id"))
    ticket_uid = Column(UUID(as_uuid=True), nullable=False)
    datetime = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    balance_diff = Column(Integer, nullable=False)
    operation_type = Column(String(20), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "operation_type IN ('FILL_IN_BALANCE', 'DEBIT_THE_ACCOUNT')",
            name="privilege_operation_type_check",
        ),
    )

    privilege = relationship("PrivilegeDb", back_populates="history")


# --------------------- #
# FastAPI App
# --------------------- #
app = FastAPI(title="Privilege Service", version="1.0")


# --------------------- #
# Dependency
# --------------------- #
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/privilege/{username}", response_model=Privilege)
def get_privilege_by_username(username: str, db: Session = Depends(get_db)):
    privilege = db.query(PrivilegeDb).filter(PrivilegeDb.username == username).first()
    if not privilege:
        raise HTTPException(status_code=404, detail="Privilege not found for this user")
    return privilege


@app.get("/privilege/{username}/history", response_model=List[PrivilegeHistory])
def get_privilege_history_by_username(username: str, db: Session = Depends(get_db)):
    privilege = db.query(PrivilegeDb).filter(PrivilegeDb.username == username).first()
    if not privilege:
        raise HTTPException(status_code=404, detail="Privilege not found for this user")

    history = (
        db.query(PrivilegeHistoryDb)
        .filter(PrivilegeHistoryDb.privilege_id == privilege.id)
        .order_by(PrivilegeHistoryDb.datetime.desc())
        .all()
    )

    return history


@app.get(
    "/privilege/{username}/history/{ticket_uid}",
    response_model=PrivilegeHistory,
)
def get_specific_history_entry(
    username: str,
    ticket_uid: uuid.UUID = Path(..., description="UUID билета"),
    db: Session = Depends(get_db),
):
    privilege = db.query(PrivilegeDb).filter(PrivilegeDb.username == username).first()
    if not privilege:
        raise HTTPException(status_code=404, detail="Privilege not found for this user")

    history_entry = (
        db.query(PrivilegeHistory)
        .filter(
            PrivilegeHistory.privilege_id == privilege.id,
            PrivilegeHistory.ticket_uid == ticket_uid,
        )
        .first()
    )

    if not history_entry:
        raise HTTPException(status_code=404, detail="History entry not found")

    return history_entry


@app.get("/manage/health", status_code=201)
def health():
    pass
