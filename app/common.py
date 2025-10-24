import uuid
from pydantic import BaseModel
from typing import List
import datetime
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from enum import Enum


class Ticket(BaseModel):
    id: int
    ticket_uuid: str
    username: str
    flight_number: str
    price: int
    status: str

    class Config:
        orm_mode = True


class Flight(BaseModel):
    id: int
    flight_number: str
    datetime: datetime
    from_airport_id: int
    to_airport_id: int
    price: int

    class Config:
        orm_mode = True


class Airport(BaseModel):
    id: int
    name: str
    city: str
    country: str

    class Config:
        orm_mode = True


class Privilege(BaseModel):
    id: int
    username: str
    status: str
    balance: int

    class Config:
        orm_mode = True


class PrivilegeHistory(BaseModel):
    id: int
    privilege_id: int
    ticket_uid: str
    datetime: datetime
    balance_diff: int
    operation_type: str

    class Config:
        orm_mode = True


# -------------------- ENUMS --------------------


class TicketStatus(str, Enum):
    PAID = "PAID"
    CANCELED = "CANCELED"


class PrivilegeStatus(str, Enum):
    BRONZE = "BRONZE"
    SILVER = "SILVER"
    GOLD = "GOLD"


class OperationType(str, Enum):
    FILL_IN_BALANCE = "FILL_IN_BALANCE"
    DEBIT_THE_ACCOUNT = "DEBIT_THE_ACCOUNT"
    FILLED_BY_MONEY = "FILLED_BY_MONEY"


# -------------------- CORE MODELS --------------------


class FlightResponse(BaseModel):
    flightNumber: str = Field(..., description="Номер полета")
    fromAirport: str = Field(..., description="Страна и аэропорт отправления")
    toAirport: str = Field(..., description="Страна и аэропорт прибытия")
    date: str = Field(..., description="Дата и время вылета (ISO 8601 формат)")
    price: int = Field(..., description="Стоимость")


class PaginationResponse(BaseModel):
    page: int = Field(..., description="Номер страницы")
    pageSize: int = Field(..., description="Количество элементов на странице")
    totalElements: int = Field(..., description="Общее количество элементов")
    items: List[FlightResponse] = Field(..., description="Список рейсов")


class TicketResponse(BaseModel):
    ticketUid: str = Field(..., description="UUID билета")
    flightNumber: str = Field(..., description="Номер полета")
    fromAirport: str = Field(..., description="Страна и аэропорт отправления")
    toAirport: str = Field(..., description="Страна и аэропорт прибытия")
    date: str = Field(..., description="Дата и время вылета (ISO 8601 формат)")
    price: int = Field(..., description="Стоимость")
    status: TicketStatus = Field(..., description="Статус билета")


class PrivilegeShortInfo(BaseModel):
    balance: int = Field(..., description="Баланс бонусного счета")
    status: PrivilegeStatus = Field(..., description="Статус в бонусной программе")


class BalanceHistory(BaseModel):
    date: datetime = Field(..., description="Дата и время операции (ISO 8601)")
    ticketUid: str = Field(..., description="UUID билета по которому была операция")
    balanceDiff: int = Field(..., description="Изменение баланса")
    operationType: OperationType = Field(..., description="Тип операции")


class PrivilegeInfoResponse(BaseModel):
    balance: int = Field(..., description="Баланс бонусного счета")
    status: PrivilegeStatus = Field(..., description="Статус в бонусной программе")
    history: List[BalanceHistory] = Field(..., description="История изменения баланса")


class UserInfoResponse(BaseModel):
    tickets: List[TicketResponse] = Field(
        ..., description="Информация о билетах пользователя"
    )
    privilege: PrivilegeShortInfo = Field(
        ..., description="Информация о бонусной программе"
    )


class TicketPurchaseRequest(BaseModel):
    flightNumber: str = Field(..., description="Номер полета")
    price: int = Field(..., description="Стоимость")
    paidFromBalance: bool = Field(
        ..., description="Списание бонусных баллов при покупке"
    )


class TicketPurchaseResponse(BaseModel):
    ticketUid: str = Field(..., description="UUID билета")
    flightNumber: str = Field(..., description="Номер полета")
    fromAirport: str = Field(..., description="Страна и аэропорт отправления")
    toAirport: str = Field(..., description="Страна и аэропорт прибытия")
    date: str = Field(..., description="Дата и время вылета (ISO 8601 формат)")
    price: int = Field(..., description="Стоимость")
    paidByMoney: int = Field(..., description="Сумма оплаченная деньгами")
    paidByBonuses: int = Field(..., description="Сумма оплаченная бонусами")
    status: TicketStatus = Field(..., description="Статус билета")
    privilege: PrivilegeShortInfo = Field(
        ..., description="Информация о бонусной программе"
    )


# -------------------- ERROR MODELS --------------------


class ErrorDescription(BaseModel):
    field: str
    error: str


class ErrorResponse(BaseModel):
    message: str = Field(..., description="Информация об ошибке")


class ValidationErrorResponse(BaseModel):
    message: str = Field(..., description="Информация об ошибке")
    errors: List[ErrorDescription] = Field(
        ..., description="Массив полей с описанием ошибки"
    )


class TicketCreateRequest(BaseModel):
    ticketUid: uuid.UUID = Field(..., description="UUID билета")
    username: str = Field(..., description="Имя пользователя")
    flightNumber: str = Field(..., description="Номер рейса")
    price: int = Field(..., description="Стоимость билета")
