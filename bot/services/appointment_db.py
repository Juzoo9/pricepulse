from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Time, select
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.database import Base, async_session


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String, default="")
    duration = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    appointments = relationship("Appointment", back_populates="service")


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, unique=True, nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    appointments = relationship("Appointment", back_populates="client")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    appointment_date = Column(Date, nullable=False)
    appointment_time = Column(Time, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    client = relationship("Client", back_populates="appointments")
    service = relationship("Service", back_populates="appointments")


WORK_START = 9
WORK_END = 18
SLOT_DURATION = 60


async def get_active_services() -> list[Service]:
    async with async_session() as session:
        result = await session.execute(
            select(Service).where(Service.is_active == True)
        )
        return list(result.scalars().all())


async def get_service_by_id(service_id: int) -> Service | None:
    async with async_session() as session:
        return await session.get(Service, service_id)


async def get_or_create_client(user_id: int, name: str, phone: str = "") -> Client:
    async with async_session() as session:
        result = await session.execute(
            select(Client).where(Client.user_id == user_id)
        )
        client = result.scalar_one_or_none()
        if client:
            if name:
                client.name = name
            if phone:
                client.phone = phone
            await session.commit()
            await session.refresh(client)
            return client
        client = Client(user_id=user_id, name=name, phone=phone)
        session.add(client)
        await session.commit()
        await session.refresh(client)
        return client


async def create_appointment(
    client_id: int, service_id: int, appointment_date: date, appointment_time: time
) -> Appointment:
    async with async_session() as session:
        appointment = Appointment(
            client_id=client_id,
            service_id=service_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            status="confirmed",
        )
        session.add(appointment)
        await session.commit()
        await session.refresh(appointment)
        return appointment


async def get_available_slots(target_date: date) -> list[time]:
    async with async_session() as session:
        result = await session.execute(
            select(Appointment.appointment_time)
            .where(
                Appointment.appointment_date == target_date,
                Appointment.status.in_(["pending", "confirmed"]),
            )
        )
        booked = {row[0] for row in result.all()}

    slots = []
    for hour in range(WORK_START, WORK_END):
        slot = time(hour, 0)
        if slot not in booked:
            slots.append(slot)
    return slots


async def get_client_appointments(user_id: int) -> list[Appointment]:
    async with async_session() as session:
        result = await session.execute(
            select(Appointment)
            .join(Client)
            .where(
                Client.user_id == user_id,
                Appointment.status.in_(["pending", "confirmed"]),
            )
            .order_by(Appointment.appointment_date, Appointment.appointment_time)
        )
        return list(result.scalars().all())


async def get_appointment_by_id(appointment_id: int) -> Appointment | None:
    async with async_session() as session:
        return await session.get(Appointment, appointment_id)


async def cancel_appointment(appointment_id: int, user_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(
            select(Appointment)
            .join(Client)
            .where(
                Appointment.id == appointment_id,
                Client.user_id == user_id,
            )
        )
        appointment = result.scalar_one_or_none()
        if appointment is None:
            return False
        appointment.status = "cancelled"
        await session.commit()
        return True


async def get_all_appointments(status: str | None = None) -> list[Appointment]:
    async with async_session() as session:
        query = select(Appointment).order_by(Appointment.appointment_date, Appointment.appointment_time)
        if status:
            query = query.where(Appointment.status == status)
        result = await session.execute(query)
        return list(result.scalars().all())


async def update_appointment_status(appointment_id: int, status: str) -> bool:
    async with async_session() as session:
        appointment = await session.get(Appointment, appointment_id)
        if appointment is None:
            return False
        appointment.status = status
        await session.commit()
        return True


async def add_service(name: str, description: str, duration: int, price: float) -> Service:
    async with async_session() as session:
        service = Service(
            name=name,
            description=description,
            duration=duration,
            price=price,
        )
        session.add(service)
        await session.commit()
        await session.refresh(service)
        return service


async def get_appointment_stats() -> dict:
    async with async_session() as session:
        from sqlalchemy import func
        confirmed = await session.execute(
            select(func.count(Appointment.id)).where(Appointment.status == "confirmed")
        )
        pending = await session.execute(
            select(func.count(Appointment.id)).where(Appointment.status == "pending")
        )
        cancelled = await session.execute(
            select(func.count(Appointment.id)).where(Appointment.status == "cancelled")
        )
        clients_count = await session.execute(select(func.count(Client.id)))
        services_count = await session.execute(
            select(func.count(Service.id)).where(Service.is_active == True)
        )
    return {
        "confirmed": confirmed.scalar() or 0,
        "pending": pending.scalar() or 0,
        "cancelled": cancelled.scalar() or 0,
        "clients": clients_count.scalar() or 0,
        "services": services_count.scalar() or 0,
    }