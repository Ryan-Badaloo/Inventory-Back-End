from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, DateTime, Date, Enum
from sqlalchemy import ForeignKey
from datetime import datetime, timedelta, timezone, date
from pydantic import BaseModel


# Database Section
# URL_DATABASE = "postgresql+psycopg2://postgres:password@localhost:5432/Test_DB"
URL_DATABASE = "postgresql+psycopg2://admin:Pass0rd1@172.16.0.4:5434/computer_inventory"
engine = create_engine(URL_DATABASE)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Users(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    firstname = Column(String(255), nullable=False)
    lastname = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String, nullable=False)
    role_id = Column(Integer, nullable=True)
    active = Column(Boolean, nullable=True)
    date_created = Column(Date, nullable=True)
    last_updated = Column(Date, nullable=True)

class Devices(Base):
    __tablename__ = "devices"

    devices_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category = Column(String(255), nullable=False)
    brand = Column(String(255), nullable=False)
    model = Column(String(255), unique=True, nullable=False)
    serial_number = Column(String, nullable=False)
    inventory_number = Column(Integer, nullable=True)
    delivery_date = Column(Date, nullable=True)
    deployment_date = Column(Date, nullable=True)
    status_id = Column(Integer, nullable=True)
    division_id = Column(Integer, nullable=True)

class Laptops(Base):
    __tablename__ = "laptop"

    laptop_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cpu_type_id = Column(Integer, nullable=False)
    hard_disk_capacity = Column(String(255), nullable=False)
    memory_capacity = Column(String(255), nullable=False)
    processor_speed = Column(String(255), nullable=False)
    processor_type = Column(String(255), nullable=False)
    computer_name = Column(String(255), nullable=False)
    mac_address = Column(String(255), nullable=False)
    operating_system = Column(String(255), nullable=False)
    microsoft_office_version = Column(String(255), nullable=False)
    antivirus = Column(String(255), nullable=False)
    pdf_reader = Column(String(255), nullable=False)
    warranty_start_date = Column(Date, nullable=True)
    warranty_end_date = Column(Date, nullable=True)
    return_date = Column(Date, nullable=True)
    devices_id = Column(Integer, ForeignKey("devices.devices_id"))

    device = relationship("Devices", backref="laptop", uselist=False)


class Tablets(Base):
    __tablename__ = "tablet"

    tablet_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    imei_number = Column(String(255), nullable=False)
    operating_system = Column(String(255), nullable=False)
    version = Column(String(255), nullable=False)
    hard_disk_capacity = Column(String(255), nullable=False)
    memory_capacity = Column(String(255), nullable=False)
    warranty_start_date = Column(Date, nullable=True)
    warranty_end_date = Column(Date, nullable=True)
    return_date = Column(Date, nullable=True)
    devices_id = Column(Integer, ForeignKey("devices.devices_id"))

    device = relationship("Devices", backref="tablet", uselist=False)


class MouseKeyboards(Base):
    __tablename__ = "mouse_keyboard"

    mouse_keyboard_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    connection_type_id = Column(Integer, nullable=False)
    devices_id = Column(Integer, ForeignKey("devices.devices_id"))

    device = relationship("Devices", backref="mouse_keyboard", uselist=False)


class Printers(Base):
    __tablename__ = "printer"

    printer_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ip_address = Column(String(255), nullable=False)
    feature_id = Column(Integer, nullable=False)
    connection_type_id = Column(Integer, nullable=False)
    devices_id = Column(Integer, ForeignKey("devices.devices_id"))

    device = relationship("Devices", backref="printer", uselist=False)

class CRAVEquipments(Base):
    __tablename__ = "conference_room_av_equipment"

    cr_equipment_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    ip_address = Column(String(255), nullable=False)
    mac_address = Column(String(255), nullable=False)
    devices_id = Column(Integer, ForeignKey("devices.devices_id"))

    device = relationship("Devices", backref="conference_room_av_equipment", uselist=False)



# Pydantic Models #####################################################################################

class CreateUserRequest(BaseModel):
    firstname: str
    lastname: str
    email: str
    password: str
    role_id: int
    active: bool
    date_created: date
    last_updated: date

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class DeviceRequest(BaseModel):
    category: str | None = None
    brand: str | None = None
    model: str | None = None
    serial_number: str | None = None
    inventory_number: int | None = None
    delivery_date: date | None = None
    deployment_date: date | None = None
    status_id: int | None = None
    division_id: int | None = None

class LaptopRequest(DeviceRequest):
    cpu_type_id: int | None = None
    hard_disk_capacity: str | None = None
    memory_capacity: str | None = None
    processor_speed: str | None = None
    processor_type: str | None = None
    computer_name: str | None = None
    mac_address: str | None = None
    operating_system: str | None = None
    microsoft_office_version: str | None = None
    antivirus: str | None = None
    pdf_reader: str | None = None
    warranty_start_date: date | None = None
    warranty_end_date: date | None = None
    return_date: date | None = None


class TabletRequest(DeviceRequest):
    imei_number: str | None = None
    operating_system: str | None = None
    version: str | None = None
    hard_disk_capacity: str | None = None
    memory_capacity: str | None = None
    warranty_start_date: date | None = None
    warranty_end_date: date | None = None
    return_date: date | None = None

class MouseKeyboardRequest(DeviceRequest):
    connection_type_id: int | None = None


class PrinterRequest(DeviceRequest):
    ip_address: str | None = None
    feature_id: int | None = None
    connection_type_id: int | None = None


class CRAVEquipmentRequest(DeviceRequest):
    name: str | None = None
    ip_address: str | None = None
    mac_address: str | None = None