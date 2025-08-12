from passlib.context import CryptContext
import os
from datetime import datetime, timedelta
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
ACCESS_TOKEN_EXPIRE_MINUTES = 1

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


def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def add_device(db: Session, device: DeviceRequest):
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
        )

        db.add(device_section)
        db.commit()
        db.refresh(device_section)
        return (device_section)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    

def add_laptop(db: Session, laptop: LaptopRequest):
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
        return (device_section)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))



def add_tablet(db: Session, tablet: TabletRequest):
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
        return (tablet_section)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    

def add_mouse_keyboard(db: Session, mouse_keyboard: MouseKeyboardRequest):
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
        return (mouse_keyboard_section)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    

def add_printer(db: Session, printer: PrinterRequest):
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
        return (printer_section)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    

def add_crav_equipment(db: Session, crav_equipment: CRAVEquipmentRequest):
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
        return (crav_section)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))



# THIS IS THE SECTION THAT DEFINES API'S ####################################################################

@app.post("/create-user", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, user_model: CreateUserRequest):
    db_user = get_user(db, user_model.email)
    if db_user:
        raise HTTPException(status_code=400, detail="User already exists")
    user = Users(
            firstname = user_model.firstname,
            lastname = user_model.lastname,
            email = user_model.email,
            password = pwd_context.hash(user_model.password),
            role_id = user_model.role_id,
            active = user_model.active,
            date_created = user_model.date_created,
            last_updated = user_model.last_updated,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User created successfully"}


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
def add_device_view(device: DeviceRequest, db: Session=Depends(get_db)):
    return add_device(db, device)

@app.post('/add-laptop/', response_model=DeviceRequest)
def add_laptop_view(laptop: LaptopRequest, db: Session=Depends(get_db)):
    return add_laptop(db, laptop)

@app.post('/add-tablet/', response_model=DeviceRequest)
def add_tablet_view(tablet: TabletRequest, db: Session=Depends(get_db)):
    return add_tablet(db, tablet)

@app.post('/add-mouse-keyboard/', response_model=DeviceRequest)
def add_mouse_keyboard_view(mouse_keyboard: MouseKeyboardRequest, db: Session=Depends(get_db)):
    return add_mouse_keyboard(db, mouse_keyboard)

@app.post('/add-printer/', response_model=DeviceRequest)
def add_printer_view(printer: PrinterRequest, db: Session=Depends(get_db)):
    return add_printer(db, printer)

@app.post('/add-crav-equipment/', response_model=DeviceRequest)
def add_crav_equipment_view(crav_equipment: CRAVEquipmentRequest, db: Session=Depends(get_db)):
    return add_crav_equipment(db, crav_equipment)
