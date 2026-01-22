import os
from dotenv import load_dotenv
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, Float, DateTime, Date, Enum
from sqlalchemy import ForeignKey
from datetime import datetime, timedelta, timezone, date
from pydantic import BaseModel
from typing import List, Optional

load_dotenv()

db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Users(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    firstname = Column(String(255), nullable=True)
    lastname = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, nullable=True)
    password = Column(String, nullable=True)
    role_id = Column(Integer, nullable=True)
    active = Column(Boolean, nullable=True)
    date_created = Column(Date, nullable=True)
    last_updated = Column(Date, nullable=True)

class Clients(Base):
    __tablename__ = "clients"

    client_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    firstname = Column(String(255), nullable=True)
    lastname = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, nullable=True)
    phone_number = Column(String(255), nullable=True)
    position = Column(String(255), nullable=True)
    devices_id = Column(Integer, nullable=True)
    parish_id = Column(Integer, nullable=True)
    location_id = Column(Integer, nullable=True)
    ltype_id = Column(Integer, nullable=True)
    division_id = Column(Integer, nullable=True)
    date_created = Column(Date, nullable=True)
    last_updated = Column(Date, nullable=True)
    added_by = Column(String(255), nullable=True)


class Devices(Base):
    __tablename__ = "devices"

    devices_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category = Column(String(255), nullable=True)
    brand = Column(String(255), nullable=True)
    model = Column(String(255), unique=True, nullable=True)
    serial_number = Column(String(255), nullable=True)
    inventory_number = Column(String(255), nullable=True)
    delivery_date = Column(Date, nullable=True)
    deployment_date = Column(Date, nullable=True)
    status_id = Column(Integer, ForeignKey("system_status.status_id"), nullable=True)
    division_id = Column(Integer, ForeignKey("division.division_id"), nullable=True)
    client_id = Column(Integer, nullable=True)
    added_by = Column(String(255), nullable=True)
    last_updated_by = Column(String(255), nullable=True)
    repaired_date = Column(Date, nullable=True)
    repaired_by = Column(String(255), nullable=True)
    bos_date = Column(Date, nullable=True)
    bos_by = Column(String(255), nullable=True)
    deployed_by = Column(String(255), nullable=True)
    assigned_on = Column(Date, nullable=True)
    unassigned_on = Column(Date, nullable=True)

    comments = relationship("Comments", back_populates="device", cascade="all, delete-orphan", passive_deletes=True)

class SystemStatus(Base):
    __tablename__ = "system_status"

    status_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    status_description = Column(String(255), nullable=True)

class CPUTypes(Base):
    __tablename__ = "cpu_type"

    cpu_type_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cpu_type_description = Column(String(255), nullable=True)

class ConnectionTypes(Base):
    __tablename__ = "connection_type"

    ctype_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ctype_description = Column(String(255), nullable=True)


class Divisions(Base):
    __tablename__ = "division"

    division_id = Column(Integer, primary_key=True, index=True)
    division_name = Column(String(255), nullable=True)
    location_id = Column(Integer, ForeignKey("location.location_id"))
    added_by = Column(String(255), nullable=True)
    date_added = Column(Date, nullable=True)
    devices_id = Column(Integer)

class Comments(Base):
    __tablename__ = "comments"

    comment_id = Column(Integer, primary_key=True, index=True)
    devices_id = Column(Integer, ForeignKey(Devices.devices_id, ondelete="CASCADE"), nullable=False)
    comment_value = Column(Text)

    device = relationship(Devices, back_populates="comments")


class Laptops(Base):
    __tablename__ = "laptop"

    laptop_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cpu_type_id = Column(Integer, nullable=False)
    hard_disk_capacity = Column(String(255), nullable=True)
    memory_capacity = Column(String(255), nullable=True)
    processor_speed = Column(String(255), nullable=True)
    processor_type = Column(String(255), nullable=True)
    computer_name = Column(String(255), nullable=True)
    mac_address = Column(String(255), nullable=True)
    operating_system = Column(String(255), nullable=True)
    microsoft_office_version = Column(String(255), nullable=True)
    antivirus = Column(String(255), nullable=True)
    pdf_reader = Column(String(255), nullable=True)
    warranty_start_date = Column(Date, nullable=True)
    warranty_end_date = Column(Date, nullable=True)
    return_date = Column(Date, nullable=True)
    devices_id = Column(Integer, ForeignKey("devices.devices_id"))

    device = relationship("Devices", backref="laptop", uselist=False)


class Tablets(Base):
    __tablename__ = "tablet"

    tablet_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    imei_number = Column(String(255), nullable=True)
    operating_system = Column(String(255), nullable=True)
    version = Column(String(255), nullable=True)
    hard_disk_capacity = Column(String(255), nullable=True)
    memory_capacity = Column(String(255), nullable=True)
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
    ip_address = Column(String(255), nullable=True)
    feature_id = Column(Integer, nullable=True)
    connection_type_id = Column(Integer, nullable=True)
    devices_id = Column(Integer, ForeignKey("devices.devices_id"))

    device = relationship("Devices", backref="printer", uselist=False)

class PrinterFeatures(Base):
    __tablename__ = "printer_feature"

    feature_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    feature_description = Column(String(255), nullable=True)


class CRAVEquipments(Base):
    __tablename__ = "conference_room_av_equipment"

    cr_equipment_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=True)
    ip_address = Column(String(255), nullable=True)
    mac_address = Column(String(255), nullable=True)
    devices_id = Column(Integer, ForeignKey("devices.devices_id"))

    device = relationship("Devices", backref="conference_room_av_equipment", uselist=False)

class Locations(Base):
    __tablename__ = "location"

    location_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    location_name = Column(String(255), nullable=True)
    parish_id = Column(Integer, ForeignKey("parish.parish_id"))
    added_by = Column(String(255), nullable=True)
    date_added = Column(Date, nullable=True)
    ltype_id = Column(Integer, nullable=True)

class LocationTypes(Base):
    __tablename__ = "location_type"

    ltype_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ltype_name = Column(String(255), nullable=True)



class Parishes(Base):
    __tablename__ = "parish"

    parish_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    parish_name = Column(String(255), nullable=True)

class Roles(Base):
    __tablename__ = "roles"

    role_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    role_name = Column(String(255), nullable=True)
    description = Column(String(255), nullable=True)




# Pydantic Models #####################################################################################

class CreateUserRequest(BaseModel):
    firstname: str
    lastname: str
    email: str
    password: str
    role_id: int

class CreateClientRequest(BaseModel):
    firstname: str
    lastname: str
    email: str
    phone_number: str
    position: str
    division_id: int

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
    inventory_number: str | None = None
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

class StatusCreate(BaseModel):
    status: str

class DivisionCreate(BaseModel):
    division: str

class CPUTypeCreate(BaseModel):
    cpu_type: str

class ConnectionTypeCreate(BaseModel):
    ctype: str

class PrinterFeatureCreate(BaseModel):
    printer_feature: str

class CommentCreate(BaseModel):
    id: int
    comment: str

class FilterRequest(BaseModel):
    locations: Optional[List[str]] = None
    parishes: Optional[List[str]] = None
    statuses: Optional[List[str]] = None
    components: Optional[List[str]] = None

class FilterRequest(BaseModel):
    locations: Optional[List[str]] = None
    parishes: Optional[List[str]] = None
    statuses: Optional[List[str]] = None
    components: Optional[List[str]] = None

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class ChangeUserPasswordRequest(BaseModel):
    email: str
    new_password: str

class UpdateStatusRequest(BaseModel):
    serial_number: str
    new_status: int



