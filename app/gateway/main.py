from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import datetime
import uuid
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from common import *
from services import *

FLIGHTS_SERVICE_URL = os.getenv("FLIGHTS_SERVICE_URL")
TICKETS_SERVICE_URL = os.getenv("TICKETS_SERVICE_URL")
PRIVILEGES_SERVICE_URL = os.getenv("PRIVILEGES_SERVICE_URL")

if FLIGHTS_SERVICE_URL is None:
    raise RuntimeError("missing FLIGHTS_SERVICE_URL")
if TICKETS_SERVICE_URL is None:
    raise RuntimeError("missing TICKETS_SERVICE_URL")
if PRIVILEGES_SERVICE_URL is None:
    raise RuntimeError("missing PRIVILEGES_SERVICE_URL")

flights_service = FlightsService(FLIGHTS_SERVICE_URL)
tickets_service = TicketsService(TICKETS_SERVICE_URL)
privliges_service = PrivilegesService(PRIVILEGES_SERVICE_URL)


# FastAPI app
app = FastAPI(title="App API", root_path="/api/v1")


class TicketBuyBody(BaseModel):
    flightNumber: str
    price: int
    paidFromBalance: bool


def error_response(msg, code):
    return JSONResponse(
        content=ErrorResponse(message=msg).model_dump(), status_code=code
    )


@app.get("/flights", response_model=PaginationResponse)
def get_flights(page: int = None, size: int = None):
    return flights_service.get_all(page, size)


@app.get("/tickets")
def get_tickets(x_user_name: str = Header()) -> List[TicketResponse]:
    privilege = privliges_service.get_user_privelge(x_user_name)
    if privilege is None:
        return error_response("Пользователь не найден", 404)
    return tickets_service.get_user_tickets(x_user_name)


@app.get("/me")
def get_user(x_user_name: str = Header()) -> UserInfoResponse | ErrorResponse:
    privilege = privliges_service.get_user_privelge(x_user_name)
    if privilege is None:
        return error_response("Пользователь не найден", 404)
    tickets = tickets_service.get_user_tickets(x_user_name)
    return UserInfoResponse(
        tickets=tickets,
        privilege=PrivilegeShortInfo(
            balance=privilege.balance, status=privilege.status
        ),
    )


@app.get("/tickets/{ticket_uid}")
def get_ticket(
    ticket_uid: int, x_user_name: str = Header()
) -> TicketResponse | ErrorResponse:
    ticket = tickets_service.get_ticket(ticket_uid)
    if ticket is None:
        return error_response("Билет не найден", 404)
    if ticket.username != x_user_name:
        return error_response("Билет не пренадлежит пользователю", 403)
    flight = flights_service.get_flight_by_number(ticket.flight_number)
    if flight is None:
        return error_response("Перелет не найден", 404)

    resp = TicketResponse(
        ticketUid=ticket.ticket_uuid,
        flightNumber=ticket.flight_number,
        fromAirport=flight.fromAirport,
        toAirport=flight.toAirport,
        date=flight.date,
        price=ticket.price,
        status=ticket.status,
    )
    return resp


@app.post("/tickets")
def buy_ticket(
    body: TicketPurchaseRequest, x_user_name: str = Header()
) -> TicketPurchaseResponse | ValidationErrorResponse:
    flight = flights_service.get_flight_by_number(body.flightNumber)
    if flight is None:
        return ValidationErrorResponse(message="Ошибка валидации данных")

    priv = privliges_service.get_user_privelge(x_user_name)
    if priv is None:
        return ValidationErrorResponse(message="Пользователь не существует")

    ticket_uid = uuid.uuid4()

    paid_by_money = flight.price
    paid_by_bonus = 0
    if body.paidFromBalance:
        money = min(priv.balance, flight.price)
        paid_by_bonus = money
        paid_by_money = flight.price - paid_by_bonus
        privliges_service.pay_with_bonus(
            body.flightNumber, ticket_uid, priv.id, paid_by_bonus
        )
    else:
        privliges_service.add_bonus(
            body.flightNumber, ticket_uid, priv.id, paid_by_money // 10
        )

    now = datetime.datetime.now()
    priv = privliges_service.get_user_privelge(x_user_name)
    tickets_service.create_ticket(
        ticket_uid, x_user_name, flight.flightNumber, paid_by_money
    )
    return TicketPurchaseResponse(
        ticket_uid,
        body.flightNumber,
        flight.fromAirport,
        flight.toAirport,
        now,
        flight.price,
        paid_by_money,
        paid_by_bonus,
        "PAID",
        PrivilegeShortInfo(balance=priv.balance, status=priv.status),
    )


@app.delete("/tickets/{ticket_uid}")
def return_ticket(ticket_uid, x_user_name: str = Header()) -> None | ErrorResponse:
    ticket = tickets_service.get_ticket(ticket_uid)
    if ticket is None:
        return ErrorResponse(message="Билет не существует")
    if ticket.username != x_user_name:
        return ErrorResponse(message="Билет не принадлежит пользователю")
    if ticket.status != "PAID":
        return ErrorResponse(message="Билет не может быть отменен")
    privliges_service.rollback_transaction(x_user_name, ticket_uid)
    tickets_service.delete_ticket(ticket_uid)


@app.get("/privilege")
def get_privilege(x_user_name: str = Header()) -> PrivilegeInfoResponse:
    a = privliges_service.get_user_privelge(x_user_name)
    b = privliges_service.get_user_privelge_history(x_user_name)
    return PrivilegeInfoResponse(balance=a.balance, status=a.status, history=b)
