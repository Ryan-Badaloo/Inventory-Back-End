import os
from dotenv import load_dotenv
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, Float, DateTime, Date, Enum, ForeignKey, text
from sqlalchemy.sql import func
from datetime import datetime, timedelta, timezone, date
from pydantic import BaseModel
from typing import List, Optional
from fastapi import Form

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
    model = Column(String(255), nullable=True)
    serial_number = Column(String(255), nullable=True)
    inventory_number = Column(String(255), nullable=True)
    delivery_date = Column(Date, nullable=True)
    deployment_date = Column(Date, nullable=True)
    bos_date = Column(Date, nullable=True)
    supplier_name = Column(String(255), nullable=True)
    device_cost = Column(Integer, nullable=True)
    status_id = Column(Integer, ForeignKey("system_status.status_id", ondelete="SET NULL"), nullable=True)
    parish_id = Column(Integer, ForeignKey("parish.parish_id", ondelete="SET NULL"), nullable=True)
    division_id = Column(Integer, ForeignKey("division.division_id", ondelete="SET NULL"), nullable=True)
    location_id = Column(Integer, ForeignKey("location.location_id", ondelete="SET NULL"), nullable=True)
    ltype_id = Column(Integer, ForeignKey("location_type.ltype_id", ondelete="SET NULL"), nullable=True)
    branch_id = Column(Integer, ForeignKey("branch.branch_id", ondelete="SET NULL"), nullable=True)
    client_id = Column(Integer, ForeignKey("clients.client_id", ondelete="SET NULL"), nullable=True)
    added_by = Column(String(255), nullable=True)
    last_updated_by = Column(String(255), nullable=True)
    repaired_date = Column(Date, nullable=True)
    repaired_by = Column(String(255), nullable=True)
    bos_by = Column(String(255), nullable=True)
    deployed_by = Column(String(255), nullable=True)
    return_date = Column(Date, nullable=True)
    assigned_on = Column(Date, nullable=True)
    unassigned_on = Column(Date, nullable=True)

class DeviceFiles(Base):
    __tablename__ = "device_files"

    file_id = Column(Integer, primary_key=True, index=True)
    
    devices_id = Column(
        Integer,
        ForeignKey("devices.devices_id", ondelete="CASCADE"),
        nullable=False
    )

    file_name = Column(String(255), nullable=False)

    file_path = Column(String(500), nullable=False)

    uploaded_at = Column(DateTime, default=datetime.utcnow)
    

class SystemStatus(Base):
    __tablename__ = "system_status"

    status_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    status_description = Column(String(255), nullable=True)

class CPUTypes(Base):
    __tablename__ = "cpu_type"

    cpu_type_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cpu_type_description = Column(String(255), nullable=True)

class FormFactors(Base):
    __tablename__ = "form_factor"

    form_factor_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    form_factor_description = Column(String(255), nullable=True)

class RaidTypes(Base):
    __tablename__ = "raid_type"

    raid_type_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    raid_type_description = Column(String(255), nullable=True)

class ConnectionTypes(Base):
    __tablename__ = "connection_type"

    ctype_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ctype_description = Column(String(255), nullable=True)

class SpeakerTypes(Base):
    __tablename__ = "speaker_type"

    speaker_type_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    speaker_type_description = Column(String(255), nullable=True)

class MonitorTypes(Base):
    __tablename__ = "monitor_type"

    monitor_type_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    monitor_type_description = Column(String(255), nullable=True)

class MonitorFunctions(Base):
    __tablename__ = "monitor_function"

    monitor_function_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    monitor_function_description = Column(String(255), nullable=True)

class MeetingRooms(Base):
    __tablename__ = "meeting_room"

    meeting_room_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    meeting_room_description = Column(String(255), nullable=True)

class CRAVEquipmentTypes(Base):
    __tablename__ = "crav_equipment_type"

    crav_equipment_type_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    crav_equipment_type_description = Column(String(255), nullable=True)

class BagTypes(Base):
    __tablename__ = "bag_type"

    bag_type_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    bag_type_description = Column(String(255), nullable=True)

class BagFabricTypes(Base):
    __tablename__ = "bag_fabric_type"

    bag_fabric_type_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    bag_fabric_type_description = Column(String(255), nullable=True)

class Comments(Base):
    __tablename__ = "comments"

    comment_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    devices_id = Column(Integer, ForeignKey("devices.devices_id", ondelete="CASCADE"), nullable=False)
    comment_value = Column(Text)

    created_at = Column(
        DateTime, 
        server_default=text("DATE_TRUNC('second', TIMEZONE('America/Jamaica', CURRENT_TIMESTAMP))"), 
        nullable=False
    )



class Laptops(Base):
    __tablename__ = "laptop"

    laptop_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hard_disk_capacity = Column(String(255), nullable=True)
    memory_capacity = Column(String(255), nullable=True)
    warranty_start_date = Column(Date, nullable=True)
    warranty_end_date = Column(Date, nullable=True)
    mac_address = Column(String(255), nullable=True)
    manufactured_date = Column(Date, nullable=True)
    memory_type = Column(String(255), nullable=True)
    operating_system = Column(String(255), nullable=True)
    cpu_type_id = Column(Integer, ForeignKey("cpu_type.cpu_type_id", ondelete="SET NULL"), nullable=True)
    processor_speed = Column(String(255), nullable=True)
    processor_type = Column(String(255), nullable=True)
    computer_name = Column(String(255), nullable=True)
    microsoft_office_version = Column(String(255), nullable=True)
    antivirus = Column(String(255), nullable=True)
    pdf_reader = Column(String(255), nullable=True)
    devices_id = Column(Integer, ForeignKey("devices.devices_id", ondelete="CASCADE"), nullable=True)

class Desktops(Base):
    __tablename__ = "desktop"

    desktop_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hard_disk_capacity = Column(String(255), nullable=True)
    memory_capacity = Column(String(255), nullable=True)
    warranty_start_date = Column(Date, nullable=True)
    warranty_end_date = Column(Date, nullable=True)
    mac_address = Column(String(255), nullable=True)
    manufactured_date = Column(Date, nullable=True)
    memory_type = Column(String(255), nullable=True)
    operating_system = Column(String(255), nullable=True)
    cpu_type_id = Column(Integer, ForeignKey("cpu_type.cpu_type_id", ondelete="SET NULL"), nullable=True)
    processor_speed = Column(String(255), nullable=True)
    processor_type = Column(String(255), nullable=True)
    computer_name = Column(String(255), nullable=True)
    microsoft_office_version = Column(String(255), nullable=True)
    antivirus = Column(String(255), nullable=True)
    form_factor_id = Column(Integer, ForeignKey("form_factor.form_factor_id", ondelete="SET NULL"), nullable=True)
    pdf_reader = Column(String(255), nullable=True)
    devices_id = Column(Integer, ForeignKey("devices.devices_id", ondelete="CASCADE"), nullable=True)

class Servers(Base):
    __tablename__ = "server"

    server_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hard_disk_capacity = Column(String(255), nullable=True)
    memory_capacity = Column(String(255), nullable=True)
    warranty_start_date = Column(Date, nullable=True)
    warranty_end_date = Column(Date, nullable=True)
    mac_address = Column(String(255), nullable=True)
    manufactured_date = Column(Date, nullable=True)
    memory_type = Column(String(255), nullable=True)
    operating_system = Column(String(255), nullable=True)
    cpu_type_id = Column(Integer, ForeignKey("cpu_type.cpu_type_id", ondelete="SET NULL"), nullable=True)
    processor_speed = Column(String(255), nullable=True)
    processor_type = Column(String(255), nullable=True)
    computer_name = Column(String(255), nullable=True)
    microsoft_office_version = Column(String(255), nullable=True)
    antivirus = Column(String(255), nullable=True)
    form_factor_id = Column(Integer, ForeignKey("form_factor.form_factor_id", ondelete="SET NULL"), nullable=True)
    raid_type_id = Column(Integer, ForeignKey("raid_type.raid_type_id", ondelete="SET NULL"), nullable=True)
    number_of_hard_drives = Column(Integer, nullable=True)
    number_of_power_supplies = Column(Integer, nullable=True)
    pdf_reader = Column(String(255), nullable=True)
    devices_id = Column(Integer, ForeignKey("devices.devices_id", ondelete="CASCADE"), nullable=True)


class Tablets(Base):
    __tablename__ = "tablet"

    tablet_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hard_disk_capacity = Column(String(255), nullable=True)
    memory_capacity = Column(String(255), nullable=True)
    warranty_start_date = Column(Date, nullable=True)
    warranty_end_date = Column(Date, nullable=True)
    device_size = Column(String(255), nullable=True)
    operating_system = Column(String(255), nullable=True)
    imei_number = Column(String(255), nullable=True)
    version = Column(String(255), nullable=True)
    
    devices_id = Column(Integer, ForeignKey("devices.devices_id", ondelete="CASCADE"), nullable=True)

class Bags(Base):
    __tablename__ = "bag"

    bag_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    bag_type_id = Column(Integer, ForeignKey("bag_type.bag_type_id", ondelete="SET NULL"), nullable=True)
    bag_brand = Column(String(255), nullable=True)
    bag_model = Column(String, nullable=True)
    bag_ministry_number = Column(String, nullable=True)
    bag_fabric_type_id = Column(Integer, ForeignKey("bag_fabric_type.bag_fabric_type_id", ondelete="SET NULL"), nullable=True)
    bag_delivery_date = Column(Date, nullable=True)
    bag_assignment_date = Column(Date, nullable=True)
    bag_status_id = Column(Integer, ForeignKey("system_status.status_id", ondelete="SET NULL"), nullable=True)
    bag_bos_date = Column(Date, nullable=True)
    
    devices_id = Column(Integer, ForeignKey("devices.devices_id", ondelete="CASCADE"), nullable=True)

class Adapters(Base):
    __tablename__ = "adapter"

    adapter_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    adapter_serial_number = Column(String(255), nullable=True)
    adapter_brand = Column(String(255), nullable=True)
    adapter_model = Column(String, nullable=True)
    adapter_ministry_number = Column(String, nullable=True)
    adapter_delivery_date = Column(Date, nullable=True)
    adapter_assignment_date = Column(Date, nullable=True)
    adapter_status_id = Column(Integer, ForeignKey("system_status.status_id", ondelete="SET NULL"), nullable=True)
    adapter_bos_date = Column(Date, nullable=True)
    
    devices_id = Column(Integer, ForeignKey("devices.devices_id", ondelete="CASCADE"), nullable=True)


class MouseKeyboards(Base):
    __tablename__ = "mouse_keyboard"

    mouse_keyboard_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    connection_type_id = Column(Integer, ForeignKey("connection_type.ctype_id", ondelete="SET NULL"), nullable=False)
    devices_id = Column(Integer, ForeignKey("devices.devices_id", ondelete="CASCADE"), nullable=True)

class Scanners(Base):
    __tablename__ = "scanner"

    scanner_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    mac_address = Column(String(255), nullable=True)
    ip_address = Column(String(255), nullable=True)
    connection_type_id = Column(Integer, nullable=False)
    devices_id = Column(Integer, ForeignKey("devices.devices_id", ondelete="CASCADE"), nullable=True)

class SurgeProtectors(Base):
    __tablename__ = "surge_protector"

    surge_protector_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    number_of_outlets = Column(Integer, nullable=False)
    devices_id = Column(Integer, ForeignKey("devices.devices_id", ondelete="CASCADE"), nullable=True)

class UPS(Base):
    __tablename__ = "ups"

    ups_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    number_of_outlets = Column(Integer, nullable=False)
    devices_id = Column(Integer, ForeignKey("devices.devices_id", ondelete="CASCADE"), nullable=True)

class Speakers(Base):
    __tablename__ = "speaker"

    speaker_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    number_of_speakers = Column(Integer, nullable=False)
    speaker_type_id = Column(Integer, ForeignKey("speaker_type.speaker_type_id", ondelete="SET NULL"), nullable=True)
    devices_id = Column(Integer, ForeignKey("devices.devices_id", ondelete="CASCADE"), nullable=True)

class OtherEquipments(Base):
    __tablename__ = "other_equipment"

    other_equipment_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    equipment_type = Column(String(255), nullable=True)
    devices_id = Column(Integer, ForeignKey("devices.devices_id", ondelete="CASCADE"), nullable=True)


class Printers(Base):
    __tablename__ = "printer"

    printer_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ip_address = Column(String(255), nullable=True)
    feature_id = Column(Integer, nullable=True)
    connection_type_id = Column(Integer, nullable=True)
    devices_id = Column(Integer, ForeignKey("devices.devices_id", ondelete="CASCADE"))

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
    meeting_room_id = Column(Integer, ForeignKey("meeting_room.meeting_room_id", ondelete="SET NULL"))
    crav_equipment_type_id = Column(Integer, ForeignKey("crav_equipment_type.crav_equipment_type_id", ondelete="SET NULL"))
    devices_id = Column(Integer, ForeignKey("devices.devices_id", ondelete="CASCADE"))

    device = relationship("Devices", backref="conference_room_av_equipment", uselist=False)

class NetworkSwitches(Base):
    __tablename__ = "network_switch"

    network_switch_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    warranty_start_date = Column(Date, nullable=True)
    warranty_end_date = Column(Date, nullable=True)
    mac_address = Column(String(255), nullable=True)
    number_of_ports = Column(Integer, nullable=True)
    device_size = Column(String(255), nullable=True)
    firmware_type = Column(String(255), nullable=True)
    firmware_version = Column(String(255), nullable=True)
    device_name = Column(String(255), nullable=True)
    manufactured_date = Column(Date, nullable=True)
    physical_location = Column(String(255), nullable=True)
    devices_id = Column(Integer, ForeignKey("devices.devices_id", ondelete="CASCADE"))

    device = relationship("Devices", backref="network_switch", uselist=False)

class Monitors(Base):
    __tablename__ = "monitor"

    monitor_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    warranty_start_date = Column(Date, nullable=True)
    warranty_end_date = Column(Date, nullable=True)
    manufactured_date = Column(Date, nullable=True)
    monitor_size = Column(String(255), nullable=True)
    monitor_type_id = Column(Integer, ForeignKey("monitor_type.monitor_type_id", ondelete="SET NULL"))
    monitor_function_id = Column(Integer, ForeignKey("monitor_function.monitor_function_id", ondelete="SET NULL"))

    devices_id = Column(Integer, ForeignKey("devices.devices_id", ondelete="CASCADE"))

    device = relationship("Devices", backref="monitor", uselist=False)

# class DivisionLocation(Base):
#     __tablename__ = "division_location"

#     division_id = Column(Integer, ForeignKey("division.division_id", ondelete="CASCADE"), primary_key=True)
#     location_id = Column(Integer, ForeignKey("location.location_id", ondelete="CASCADE"), primary_key=True)

#     added_by = Column(String(255), nullable=True)
#     date_added = Column(Date, nullable=True)


class Divisions(Base):
    __tablename__ = "division"

    division_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    division_name = Column(String(255), nullable=False)
    added_by = Column(String(255), nullable=True)
    date_added = Column(Date, nullable=True)

class Branches(Base):
    __tablename__ = "branch"

    branch_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    branch_name = Column(String(255), nullable=False)
    division_id = Column(Integer, ForeignKey("division.division_id", ondelete="CASCADE"))
    added_by = Column(String(255), nullable=True)
    date_added = Column(Date, nullable=True)

class Locations(Base):
    __tablename__ = "location"

    location_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    location_name = Column(String(255), nullable=False)
    parish_id = Column(Integer, ForeignKey("parish.parish_id", ondelete="CASCADE"))
    added_by = Column(String(255), nullable=True)
    date_added = Column(Date, nullable=True)

class LocationTypes(Base):
    __tablename__ = "location_type"

    ltype_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ltype_name = Column(String(255), nullable=False)



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

    category: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None

    serial_number: Optional[str] = None
    inventory_number: Optional[str] = None

    delivery_date: Optional[date] = None
    deployment_date: Optional[date] = None
    bos_date: Optional[date] = None

    supplier_name: Optional[str] = None
    device_cost: Optional[int] = None

    status_id: Optional[int] = None
    parish_id: Optional[int] = None
    ltype_id: Optional[int] = None
    branch_id: Optional[int] = None
    division_id: Optional[int] = None
    location_id: Optional[int] = None

    comment: Optional[str] = None

    @classmethod
    def as_form(

        cls,

        category: Optional[str] = Form(None),
        brand: Optional[str] = Form(None),
        model: Optional[str] = Form(None),

        serial_number: Optional[str] = Form(None),
        inventory_number: Optional[str] = Form(None),

        delivery_date: Optional[date] = Form(None),
        deployment_date: Optional[date] = Form(None),
        bos_date: Optional[date] = Form(None),

        supplier_name: Optional[str] = Form(None),
        device_cost: Optional[int] = Form(None),

        status_id: Optional[int] = Form(None),
        division_id: Optional[int] = Form(None),
        parish_id: Optional[int] = Form(None),
        ltype_id: Optional[int] = Form(None),
        location_id: Optional[int] = Form(None),
        branch_id: Optional[int] = Form(None),

        comment: Optional[str] = Form(None)

    ):

        return cls(

            category=category,
            brand=brand,
            model=model,

            serial_number=serial_number,
            inventory_number=inventory_number,

            delivery_date=delivery_date,
            deployment_date=deployment_date,
            bos_date=bos_date,

            supplier_name=supplier_name,
            device_cost=device_cost,

            status_id=status_id,
            division_id=division_id,
            location_id=location_id,
            parish_id=parish_id,
            ltype_id=ltype_id,
            branch_id=branch_id,

            comment=comment
        )

class LaptopRequest(DeviceRequest):
    hard_disk_capacity: str | None = None
    memory_capacity: str | None = None
    warranty_start_date: date | None = None
    warranty_end_date: date | None = None
    return_date: date | None = None
    mac_address: str | None = None
    manufactured_date: date | None = None
    memory_type: str | None = None
    operating_system: str | None = None
    cpu_type_id: int | None = None
    processor_speed: str | None = None
    processor_type: str | None = None
    computer_name: str | None = None
    microsoft_office_version: str | None = None
    antivirus: str | None = None
    pdf_reader: str | None = None
    


class DesktopRequest(DeviceRequest):

    hard_disk_capacity: str | None = None
    memory_capacity: str | None = None

    warranty_start_date: date | None = None
    warranty_end_date: date | None = None

    return_date: date | None = None

    mac_address: str | None = None

    manufactured_date: date | None = None

    memory_type: str | None = None
    operating_system: str | None = None

    cpu_type_id: int | None = None

    processor_speed: str | None = None
    processor_type: str |None = None

    computer_name: str | None = None

    microsoft_office_version: str | None = None

    antivirus: str | None = None

    form_factor_id: int | None = None

    pdf_reader: str | None = None

    @classmethod
    def as_form(

        cls,

        # =========================
        # DeviceRequest fields
        # =========================

        category: str | None = Form(None),
        brand: str | None = Form(None),
        model: str | None = Form(None),

        serial_number: str | None = Form(None),
        inventory_number: str | None = Form(None),

        delivery_date: date | None = Form(None),
        deployment_date: date | None = Form(None),
        bos_date: date | None = Form(None),

        supplier_name: str | None = Form(None),

        device_cost: int | None = Form(None),

        status_id: int | None = Form(None),

        division_id: int | None = Form(None),

        location_id: int | None = Form(None),

        comment: str | None = Form(None),

        # =========================
        # DesktopRequest fields
        # =========================

        hard_disk_capacity: str | None = Form(None),

        memory_capacity: str | None = Form(None),

        warranty_start_date: date | None = Form(None),

        warranty_end_date: date | None = Form(None),

        return_date: date | None = Form(None),

        mac_address: str | None = Form(None),

        manufactured_date: date | None = Form(None),

        memory_type: str | None = Form(None),

        operating_system: str | None = Form(None),

        cpu_type_id: int | None = Form(None),

        processor_speed: str | None = Form(None),

        processor_type: str | None = Form(None),

        computer_name: str | None = Form(None),

        microsoft_office_version: str | None = Form(None),

        antivirus: str | None = Form(None),

        form_factor_id: int | None = Form(None),

        pdf_reader: str | None = Form(None),

    ):

        return cls(

            # =========================
            # DeviceRequest fields
            # =========================

            category=category,
            brand=brand,
            model=model,

            serial_number=serial_number,
            inventory_number=inventory_number,

            delivery_date=delivery_date,
            deployment_date=deployment_date,
            bos_date=bos_date,

            supplier_name=supplier_name,

            device_cost=device_cost,

            status_id=status_id,

            division_id=division_id,

            location_id=location_id,

            comment=comment,

            # =========================
            # DesktopRequest fields
            # =========================

            hard_disk_capacity=hard_disk_capacity,

            memory_capacity=memory_capacity,

            warranty_start_date=warranty_start_date,

            warranty_end_date=warranty_end_date,

            return_date=return_date,

            mac_address=mac_address,

            manufactured_date=manufactured_date,

            memory_type=memory_type,

            operating_system=operating_system,

            cpu_type_id=cpu_type_id,

            processor_speed=processor_speed,

            processor_type=processor_type,

            computer_name=computer_name,

            microsoft_office_version=microsoft_office_version,

            antivirus=antivirus,

            form_factor_id=form_factor_id,

            pdf_reader=pdf_reader,
        )

class ServerRequest(DeviceRequest):
    hard_disk_capacity: str | None = None
    memory_capacity: str | None = None
    warranty_start_date: date | None = None
    warranty_end_date: date | None = None
    return_date: date | None = None
    mac_address: str | None = None
    manufactured_date: date | None = None
    memory_type: str | None = None
    operating_system: str | None = None
    cpu_type_id: int | None = None
    processor_speed: str | None = None
    processor_type: str | None = None
    computer_name: str | None = None
    microsoft_office_version: str | None = None
    antivirus: str | None = None
    form_factor_id: int | None = None
    raid_type_id: int | None = None
    number_of_hard_drives: int | None = None
    number_of_power_supplies: int | None = None
    pdf_reader: str | None = None


class TabletRequest(DeviceRequest):
    hard_disk_capacity: str | None = None
    memory_capacity: str | None = None
    warranty_start_date: date | None = None
    warranty_end_date: date | None = None
    return_date: date | None = None
    device_size: str | None = None
    operating_system: str | None = None
    imei_number: str | None = None
    version: str | None = None

class BagRequest(BaseModel):
    bag_type_id: int | None = None
    bag_brand: str | None = None
    bag_model: str | None = None
    bag_ministry_number: str | None = None
    bag_fabric_type_id: int | None = None
    bag_delivery_date: date | None = None
    bag_assignment_date: date | None = None
    bag_status_id: int | None = None
    bag_bos_date: date | None = None

class AdapterRequest(BaseModel):
    adapter_serial_number: str | None = None
    adapter_brand: str | None = None
    adapter_model: str | None = None
    adapter_ministry_number: str | None = None
    adapter_delivery_date: date | None = None
    adapter_assignment_date: date | None = None
    adapter_status_id: int | None = None
    adapter_bos_date: date | None = None

class AddTabletRequest(BaseModel):
    tablet: TabletRequest
    bag: Optional[BagRequest] = None
    adapter: Optional[AdapterRequest] = None


class MouseKeyboardRequest(DeviceRequest):
    connection_type_id: int | None = None

class ScannerRequest(DeviceRequest):
    mac_address: str | None = None
    ip_address: str | None = None
    connection_type_id: int | None = None

class SurgeProtectorRequest(DeviceRequest):
    number_of_outlets: int | None = None

class UPSRequest(DeviceRequest):
    number_of_outlets: int | None = None
    return_date: date | None = None

class SpeakerRequest(DeviceRequest):
    return_date: date | None = None
    speaker_type_id: int | None = None
    number_of_speakers: int | None = None

class OtherEquipmentRequest(DeviceRequest):
    equipment_type: str | None = None
    

class PrinterRequest(DeviceRequest):
    return_date: date | None = None
    ip_address: str | None = None
    feature_id: int | None = None
    connection_type_id: int | None = None


class CRAVEquipmentRequest(DeviceRequest):
    name: str | None = None
    ip_address: str | None = None
    mac_address: str | None = None
    meeting_room_id: int | None = None
    crav_equipment_type_id: int | None = None

class NetworkSwitchRequest(DeviceRequest):
    warranty_start_date: date | None = None
    warranty_end_date: date | None = None
    return_date: date | None = None
    mac_address: str | None = None
    number_of_ports: int | None = None
    device_size: str | None = None
    firmware_type: str | None = None
    firmware_version: str | None = None
    device_name: str | None = None
    manufactured_date: date | None = None
    physical_location: str | None = None

class MonitorRequest(DeviceRequest):
    warranty_start_date: date | None = None
    warranty_end_date: date | None = None
    return_date: date | None = None
    manufactured_date: date | None = None
    monitor_size: str | None = None
    monitor_type_id: int | None = None
    monitor_function_id: int | None = None



class StatusCreate(BaseModel):
    status: str

class DivisionCreate(BaseModel):
    division: str
    location: int

class CPUTypeCreate(BaseModel):
    cpu_type: str

class RaidTypeCreate(BaseModel):
    raid_type: str

class ConnectionTypeCreate(BaseModel):
    ctype: str

class PrinterFeatureCreate(BaseModel):
    printer_feature: str

class FormFactorCreate(BaseModel):
    form_factor: str

class MeetingRoomCreate(BaseModel):
    meeting_room: str

class MonitorTypeCreate(BaseModel):
    monitor_type: str

class BagTypeCreate(BaseModel):
    bag_type: str

class BagFabricTypeCreate(BaseModel):
    bag_fabric_type: str

class MonitorFunctionCreate(BaseModel):
    monitor_function: str

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

class UpdatePackage(BaseModel): 
    category: Optional[str]
    brand: Optional[str]
    model: Optional[str]
    serial_number: Optional[str]
    inventory_number: Optional[str]
    delivery_date: Optional[date]
    deployment_date: Optional[date]
    bos_date: Optional[date]
    supplier_name: Optional[str]
    device_cost: Optional[str]
    status_id: Optional[int]
    hard_disk_capacity: Optional[str]
    memory_capacity: Optional[str]
    warranty_start_date: Optional[date]
    warranty_end_date: Optional[date]
    return_date: Optional[date]
    mac_address: Optional[str]
    manufactured_date: Optional[date]
    memory_type: Optional[str]
    operating_system: Optional[str]
    cpu_type_id: Optional[int]
    processor_speed: Optional[str]
    processor_type: Optional[str]
    computer_name: Optional[str]
    ms_office_version: Optional[str]
    antivirus: Optional[str]
    form_factor_id: Optional[int]
    raid_type_id: Optional[int]
    number_hard_drive: Optional[str]
    number_power_supply: Optional[str]
    device_size: Optional[str]
    imei_number: Optional[str]
    version: Optional[str]
    connection_type_id: Optional[int]
    ip_address: Optional[str]
    number_outlets: Optional[str]  
    speaker_type_id: Optional[int]
    number_speakers: Optional[str]
    equipment_type: Optional[str]
    feature_id: Optional[int]
    crav_equipment_type_id: Optional[int]
    name: Optional[str]
    meeting_room_id: Optional[int]
    number_of_ports: Optional[str]
    firmware_type: Optional[str]
    firmware_version: Optional[str]
    device_name: Optional[str]
    size: Optional[str]
    monitor_type_id: Optional[int]
    monitor_function_id: Optional[int]
    

    location_id: Optional[int]
    division_id: Optional[int]



