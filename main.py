from passlib.context import CryptContext
import os
from datetime import datetime, timedelta, date
from typing import Union, Any, Optional, List, Annotated
from jose import jwt, JWTError
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, DateTime, Date, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, FastAPI, HTTPException, status, APIRouter
from datetime import datetime, timedelta, timezone, date
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from enum import Enum
from models import *

app = FastAPI()

SECRET_KEY = 'my_secret_key'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES =30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

origins = [
    "http://localhost:5173",  # frontend origin
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]



# THIS IS THE SECTION THAT DEFINES FUNCTIONS #################################################################

async def get_current_user(db: db_dependency, token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        id = payload.get("id")
        firstname = payload.get("firstname")
        lastname = payload.get("lastname")
        if email is None:
            raise credentials_exception
        token_data = TokenData(username=email, )
    except JWTError:
        raise credentials_exception
    user = get_user(db, email=token_data.username)
    if user is  None:
        raise credentials_exception
    return user

user_dependency = Annotated[dict, Depends(get_current_user)]


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user(db, email: str):
    return db.query(Users).filter(Users.email == email).first()

def get_client(db, email: str):
    return db.query(Clients).filter(Clients.email == email).first()


def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user
    



# THIS IS THE SECTION THAT DEFINES API'S ####################################################################

@app.post("/create-user/", status_code=status.HTTP_201_CREATED)
async def create_user(user_model: CreateUserRequest, current_user: user_dependency, db: Session=Depends(get_db)):
    db_user = get_user(db, user_model.email)
    if db_user:
        raise HTTPException(status_code=400, detail="User already exists")
    user = Users(
            firstname = user_model.firstname,
            lastname = user_model.lastname,
            email = user_model.email,
            password = pwd_context.hash(user_model.password),
            role_id = user_model.role_id,
            active = True,
            date_created = date.today(),
            last_updated = None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User created successfully"}



@app.post("/create-client/", status_code=status.HTTP_201_CREATED)
async def create_client(client_model: CreateClientRequest, current_user: user_dependency, db: Session=Depends(get_db)):
    db_client = get_client(db, client_model.email)
    if db_client:
        raise HTTPException(status_code=400, detail="Client already exists")
    client = Clients(
            firstname = client_model.firstname,
            lastname = client_model.lastname,
            email = client_model.email,
            phone_number = client_model.phone_number,
            position = client_model.position,
            division_id = client_model.division_id,
            date_created = date.today(),
            added_by = current_user.firstname + " " + current_user.lastname,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return {"message": "Client created successfully"}





@app.delete('/delete-user/')
def delete_user_view(first_name: str, last_name: str, email: str, current_user: user_dependency, db: Session=Depends(get_db)):
    deleted = db.query(Users).filter(Users.firstname == first_name, Users.lastname == last_name, Users.email == email).delete()
    db.commit()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User has been deleted"}


@app.delete('/delete-client/')
def delete_client_view(first_name: str, last_name: str, current_user: user_dependency, db: Session=Depends(get_db)):
    deleted = db.query(Clients).filter(Clients.firstname == first_name, Clients.lastname == last_name).delete()
    db.commit()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return {"message": "Client has been deleted"}

@app.post("/token")
async def login_for_access_token(db: db_dependency, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "firstname": user.firstname, "lastname": user.lastname, "role": user.role_id}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@app.get("/users/me/", response_model=CreateUserRequest)
async def read_users_me(current_user: user_dependency):
    return current_user

# @app.get("/db-test")
# def test_database_connection(db: Session = Depends(get_db)):
#     try:
#         db.execute(text("SELECT 1"))
#         return JSONResponse(status_code=200, content={"message": "Database connection successful."})
#     except Exception as e:
#         return JSONResponse(status_code=500, content={"message": "Database connection failed.", "error": str(e)})


@app.post('/add-device/', response_model=DeviceRequest)
def add_device_view(device: DeviceRequest, current_user: user_dependency, db: Session=Depends(get_db)):
    try:
        device_section = Devices(
            category = device.category,
            brand = device.brand,
            model = device.model,
            serial_number = device.serial_number,
            inventory_number = device.inventory_number,
            delivery_date = device.delivery_date,
            deployment_date = device.deployment_date,
            status_id = device.status_id,
            division_id = device.division_id,
            added_by = current_user.firstname + " " + current_user.lastname,
        )

        db.add(device_section)
        db.commit()
        db.refresh(device_section)
        return {"message": "Device Has Been Added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post('/add-laptop/', response_model=DeviceRequest)
def add_laptop_view(laptop: LaptopRequest, current_user: user_dependency, db: Session=Depends(get_db)):
    try:
        device_section = Devices(
            category = laptop.category,
            brand = laptop.brand,
            model = laptop.model,
            serial_number = laptop.serial_number,
            inventory_number = laptop.inventory_number,
            delivery_date = laptop.delivery_date,
            deployment_date = laptop.deployment_date,
            status_id = laptop.status_id,
            division_id = laptop.division_id,
            added_by = current_user.firstname + " " + current_user.lastname,
        )

        db.add(device_section)
        db.flush()

        laptop_section = Laptops(
            
            cpu_type_id = laptop.cpu_type_id,
            hard_disk_capacity = laptop.hard_disk_capacity,
            memory_capacity = laptop.memory_capacity,
            processor_speed = laptop.processor_speed,
            processor_type = laptop.processor_type,
            computer_name = laptop.computer_name,
            mac_address = laptop.mac_address,
            operating_system = laptop.operating_system,
            microsoft_office_version = laptop.microsoft_office_version,
            antivirus = laptop.antivirus,
            pdf_reader = laptop.pdf_reader,
            warranty_start_date = laptop.warranty_start_date,
            warranty_end_date = laptop.warranty_end_date,
            return_date = laptop.return_date,
            devices_id = device_section.devices_id,
        )

        db.add(laptop_section)
        db.commit()
        db.refresh(laptop_section)
        return {"message": "Laptop Has Been Added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    

@app.post('/add-tablet/', response_model=DeviceRequest)
def add_tablet_view(tablet: TabletRequest, current_user: user_dependency, db: Session=Depends(get_db)):
    try:
        device_section = Devices(
            category = tablet.category,
            brand = tablet.brand,
            model = tablet.model,
            serial_number = tablet.serial_number,
            inventory_number = tablet.inventory_number,
            delivery_date = tablet.delivery_date,
            deployment_date = tablet.deployment_date,
            status_id = tablet.status_id,
            division_id = tablet.division_id,
            added_by = current_user.firstname + " " + current_user.lastname,
        )

        db.add(device_section)
        db.flush()

        tablet_section = Tablets(
            
            imei_number = tablet.imei_number,
            operating_system = tablet.operating_system,
            version = tablet.version,
            hard_disk_capacity = tablet.hard_disk_capacity,
            memory_capacity = tablet.memory_capacity,
            warranty_start_date = tablet.warranty_start_date,
            warranty_end_date = tablet.warranty_end_date,
            return_date = tablet.return_date,
            devices_id = device_section.devices_id,
        )

        db.add(tablet_section)
        db.commit()
        db.refresh(tablet_section)
        return {"message": "Tablet Has Been Added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post('/add-mouse-keyboard/', response_model=DeviceRequest)
def add_mouse_keyboard_view(mouse_keyboard: MouseKeyboardRequest, current_user: user_dependency, db: Session=Depends(get_db)):
    try:
        device_section = Devices(
            category = mouse_keyboard.category,
            brand = mouse_keyboard.brand,
            model = mouse_keyboard.model,
            serial_number = mouse_keyboard.serial_number,
            inventory_number = mouse_keyboard.inventory_number,
            delivery_date = mouse_keyboard.delivery_date,
            deployment_date = mouse_keyboard.deployment_date,
            status_id = mouse_keyboard.status_id,
            division_id = mouse_keyboard.division_id,
            added_by = current_user.firstname + " " + current_user.lastname,
        )

        db.add(device_section)
        db.flush()

        mouse_keyboard_section = MouseKeyboards(
            connection_type_id = mouse_keyboard.connection_type_id,
            devices_id = device_section.devices_id,
        )

        db.add(mouse_keyboard_section)
        db.commit()
        db.refresh(mouse_keyboard_section)
        return {"message": "Mouse/Keyboard Has Been Added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post('/add-printer/', response_model=DeviceRequest)
def add_printer_view(printer: PrinterRequest, current_user: user_dependency, db: Session=Depends(get_db)):
    try:
        device_section = Devices(
            category = printer.category,
            brand = printer.brand,
            model = printer.model,
            serial_number = printer.serial_number,
            inventory_number = printer.inventory_number,
            delivery_date = printer.delivery_date,
            deployment_date = printer.deployment_date,
            status_id = printer.status_id,
            division_id = printer.division_id,
            added_by = current_user.firstname + " " + current_user.lastname,
        )

        db.add(device_section)
        db.flush()

        printer_section = Printers(
            ip_address = printer.ip_address,
            feature_id = printer.feature_id,
            connection_type_id = printer.connection_type_id,
            devices_id = device_section.devices_id,
        )

        db.add(printer_section)
        db.commit()
        db.refresh(printer_section)
        return {"message": "Printer Has Been Added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post('/add-crav-equipment/', response_model=DeviceRequest)
def add_crav_equipment_view(crav_equipment: CRAVEquipmentRequest, current_user: user_dependency, db: Session=Depends(get_db)):
    try:
        device_section = Devices(
            category = crav_equipment.category,
            brand = crav_equipment.brand,
            model = crav_equipment.model,
            serial_number = crav_equipment.serial_number,
            inventory_number = crav_equipment.inventory_number,
            delivery_date = crav_equipment.delivery_date,
            deployment_date = crav_equipment.deployment_date,
            status_id = crav_equipment.status_id,
            division_id = crav_equipment.division_id,
            added_by = current_user.firstname + " " + current_user.lastname,
        )

        db.add(device_section)
        db.flush()

        crav_section = CRAVEquipments(
            name = crav_equipment.name,
            ip_address = crav_equipment.ip_address,
            mac_address = crav_equipment.mac_address,
            devices_id = device_section.devices_id,
        )

        db.add(crav_section)
        db.commit()
        db.refresh(crav_section)
        return {"message": "CRAV Has Been Added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
 

@app.get('/get-items/')
def get_items_view(current_user: user_dependency, brand: Optional[str] = None, category: Optional[str] = None, db: Session=Depends(get_db)):

    query = db.query(Devices, SystemStatus.status_description, Divisions.division_name).outerjoin(SystemStatus, Devices.status_id == SystemStatus.status_id).outerjoin(Divisions, Devices.division_id == Divisions.division_id)

    if brand:
        query = query.filter(Devices.brand == brand)

    if category:
        query = query.filter(Devices.category == category)

    rows = query.all()
    result_list = []

    for device, status_description, division_name in rows:
        item = {
            "devices_id": device.devices_id,
            "category": device.category,
            "brand": device.brand,
            "model": device.model,
            "serial_number": device.serial_number,
            "inventory_number": device.inventory_number,
            "delivery_date": device.delivery_date,
            "deployment_date": device.deployment_date,
            "status_id": device.status_id,
            "division_id": device.division_id,
            "status_description": status_description,
            "division_name": division_name,
        }
        result_list.append(item)


    return result_list


@app.get('/get-item-sn/')
def get_item_sn_view(serial_number: str, category: str, db: Session=Depends(get_db)):


    if category == "Laptop":

        result = (
            db.query(
                Devices,
                SystemStatus.status_description,
                Divisions.division_name,
                Laptops
            )
            .outerjoin(SystemStatus, Devices.status_id == SystemStatus.status_id)
            .outerjoin(Divisions, Devices.division_id == Divisions.division_id)
            .outerjoin(Laptops, Devices.devices_id == Laptops.devices_id)
            .filter(Devices.serial_number == serial_number)
            .first()
        )

        if result:
            device, status_description, division_name, laptop = result
            return {
                "devices_id": device.devices_id,
                "category": device.category,
                "brand": device.brand,
                "model": device.model,
                "serial_number": device.serial_number,
                "inventory_number": device.inventory_number,
                "delivery_date": device.delivery_date,
                "deployment_date": device.deployment_date,
                "status_id": device.status_id,
                "division_id": device.division_id,
                "status_description": status_description,
                "division_name": division_name,
                "laptop_id": laptop.laptop_id,
                "cpu_type_id": laptop.cpu_type_id,
                "hard_disk_capacity": laptop.hard_disk_capacity,
                "memory_capacity": laptop.memory_capacity,
                "processor_speed": laptop.processor_speed,
                "processor_type": laptop.processor_type,
                "computer_name": laptop.computer_name,
                "mac_address": laptop.mac_address,
                "operating_system": laptop.operating_system,
                "microsoft_office_version": laptop.microsoft_office_version,
                "antivirus": laptop.antivirus,
                "pdf_reader": laptop.pdf_reader,
                "warranty_start_date": laptop.warranty_start_date,
                "warranty_end_date": laptop.warranty_end_date,
                "return_date": laptop.return_date,
                }
        else:
            return {"message": "Device not found"}

    elif category == "Tablet":
        result = (
            db.query(
                Devices,
                SystemStatus.status_description,
                Divisions.division_name,
                Tablets
            )
            .outerjoin(SystemStatus, Devices.status_id == SystemStatus.status_id)
            .outerjoin(Divisions, Devices.division_id == Divisions.division_id)
            .outerjoin(Tablets, Devices.devices_id == Tablets.devices_id)
            .filter(Devices.serial_number == serial_number)
            .first()
        )

        if result:
            device, status_description, division_name, tablet = result
            return {
                "devices_id": device.devices_id,
                "category": device.category,
                "brand": device.brand,
                "model": device.model,
                "serial_number": device.serial_number,
                "inventory_number": device.inventory_number,
                "delivery_date": device.delivery_date,
                "deployment_date": device.deployment_date,
                "status_id": device.status_id,
                "division_id": device.division_id,
                "status_description": status_description,
                "division_name": division_name,
                "tablet_id": tablet.tablet_id,
                "imei_number": tablet.imei_number,
                "operating_system": tablet.operating_system,
                "version": tablet.version,
                "hard_disk_capacity": tablet.hard_disk_capacity,
                "memory_capacity": tablet.memory_capacity,
                "warranty_start_date": tablet.warranty_start_date,
                "warranty_end_date": tablet.warranty_end_date,
                "return_date": tablet.return_date,
                }
        else:
            return {"message": "Device not found"}

    elif (category == "Mouse") or (category == "Keyboard"):
        result = (
            db.query(
                Devices,
                SystemStatus.status_description,
                Divisions.division_name,
                MouseKeyboards
            )
            .outerjoin(SystemStatus, Devices.status_id == SystemStatus.status_id)
            .outerjoin(Divisions, Devices.division_id == Divisions.division_id)
            .outerjoin(MouseKeyboards, Devices.devices_id == MouseKeyboards.devices_id)
            .filter(Devices.serial_number == serial_number)
            .first()
        )

        if result:
            device, status_description, division_name, mouse_keyboard = result
            return {
                "devices_id": device.devices_id,
                "category": device.category,
                "brand": device.brand,
                "model": device.model,
                "serial_number": device.serial_number,
                "inventory_number": device.inventory_number,
                "delivery_date": device.delivery_date,
                "deployment_date": device.deployment_date,
                "status_id": device.status_id,
                "division_id": device.division_id,
                "status_description": status_description,
                "division_name": division_name,
                "mouse_keyboard_id": mouse_keyboard.mouse_keyboard_id,
                "connection_type_id": mouse_keyboard.connection_type_id,
                }
        else:
            return {"message": "Device not found"}
        
    elif category == "Printer":
        result = (
            db.query(
                Devices,
                SystemStatus.status_description,
                Divisions.division_name,
                Printers
            )
            .outerjoin(SystemStatus, Devices.status_id == SystemStatus.status_id)
            .outerjoin(Divisions, Devices.division_id == Divisions.division_id)
            .outerjoin(Printers, Devices.devices_id == Printers.devices_id)
            .filter(Devices.serial_number == serial_number)
            .first()
        )

        if result:
            device, status_description, division_name, printer = result
            return {
                "devices_id": device.devices_id,
                "category": device.category,
                "brand": device.brand,
                "model": device.model,
                "serial_number": device.serial_number,
                "inventory_number": device.inventory_number,
                "delivery_date": device.delivery_date,
                "deployment_date": device.deployment_date,
                "status_id": device.status_id,
                "division_id": device.division_id,
                "status_description": status_description,
                "division_name": division_name,
                "printer_id": printer.printer_id,
                "ip_address": printer.ip_address,
                "feature_id": printer.feature_id,
                "connection_type_id": printer.connection_type_id,
                }
        else:
            return {"message": "Device not found"}
        
    elif category == "CRAV":
        result = (
            db.query(
                Devices,
                SystemStatus.status_description,
                Divisions.division_name,
                CRAVEquipments
            )
            .outerjoin(SystemStatus, Devices.status_id == SystemStatus.status_id)
            .outerjoin(Divisions, Devices.division_id == Divisions.division_id)
            .outerjoin(CRAVEquipments, Devices.devices_id == CRAVEquipments.devices_id)
            .filter(Devices.serial_number == serial_number)
            .first()
        )

        if result:
            device, status_description, division_name, crav = result
            return {
                "devices_id": device.devices_id,
                "category": device.category,
                "brand": device.brand,
                "model": device.model,
                "serial_number": device.serial_number,
                "inventory_number": device.inventory_number,
                "delivery_date": device.delivery_date,
                "deployment_date": device.deployment_date,
                "status_id": device.status_id,
                "division_id": device.division_id,
                "status_description": status_description,
                "division_name": division_name,
                "cr_equipment_id": crav.cr_equipment_id,
                "name": crav.name,
                "ip_address": crav.ip_address,
                "mac_address": crav.mac_address,
                }
        else:
            return {"message": "Device not found"}


    return {"message": "Category not supported"}


@app.delete('/delete-item/')
def delete_item_view(current_user: user_dependency, serial_number: str, db: Session=Depends(get_db)):
    deleted = db.query(Devices).filter(Devices.serial_number == serial_number).delete()
    db.commit()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return {"message": "Device has been deleted"}


