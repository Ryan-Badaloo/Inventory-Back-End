import os
import logging
from datetime import datetime, timedelta, date
from contextlib import asynccontextmanager
from typing import Union, Any, Optional, List, Annotated, Dict
from passlib.context import CryptContext
from jose import jwt, JWTError
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, DateTime, Date, text, or_, and_, desc, func
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

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))
ORGIN = os.getenv('ORGIN')
USERNAME = os.getenv('DEFAULT_USERNAME')
PASSWORD = os.getenv('DEFAULT_PASSWORD')

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

# This function creates a defualt use in database
def defualt_user():

    db:Session = SessionLocal()
    bcrypt_context = CryptContext(schemes=['bcrypt'])

    try:

        defualt_user = db.query(Users).filter(Users.email == USERNAME).first()

        if not defualt_user:
            logging.info("Creating defualt user ...")

            user = Users(
                firstname = "ICT",
                lastname = "DEV",
                email = USERNAME,
                password = bcrypt_context.hash(PASSWORD),
                role_id = 1,
                active = True,
                date_created = date.today(),
                last_updated = None,
            )

            db.add(user)
            db.commit()
            db.refresh(user)

            logging.info("Ddefualt user added.")
        else:
            logging.info("Defualt user already exists.")

    except Exception as e:
        logging.error(f"Error in creating defualt user: {str(e)}")
    finally:
        db.close()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

origins = [ ORGIN ]

@asynccontextmanager
async def lifespan(application: FastAPI):
    logging.info("Application start up ...")
    defualt_user()
    yield
    logging.info("Application shutting down")

app = FastAPI(
    title="Computer Inventory Backend",
    description="This application contains the backend logic to create, edit, manage and get data related to the Computer Inventory.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
async def create_user(user_model: CreateUserRequest, db: Session=Depends(get_db)):
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

@app.post("/change-password/", status_code=status.HTTP_200_OK)
async def change_password(password_set: ChangePasswordRequest, current_user: user_dependency, db: Session=Depends(get_db)):
    user = db.query(Users).filter(Users.email == current_user.email).first()

    if user:
        if verify_password(password_set.old_password, user.password):
            new_hashed_password = get_password_hash(password_set.new_password)
            user.password = new_hashed_password
            db.commit()
            db.refresh(user)
            return {"message": "Password updated successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect password"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    

@app.post("/change-user-password/", status_code=status.HTTP_200_OK)
async def change_user_password(user_password_set: ChangeUserPasswordRequest, current_user: user_dependency, db: Session=Depends(get_db)):
    user = db.query(Users).filter(Users.email == user_password_set.email).first()

    if user:
        new_hashed_password = get_password_hash(user_password_set.new_password)
        user.password = new_hashed_password
        db.commit()
        db.refresh(user)
        return {"message": "Password updated successfully"}
    
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


@app.delete('/delete-user/')
def delete_user_view(first_name: str, last_name: str, email: str, current_user: user_dependency, db: Session=Depends(get_db)):
    deleted = db.query(Users).filter(Users.firstname == first_name, Users.lastname == last_name, Users.email == email).delete()
    db.commit()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User has been deleted"}




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

@app.post('/add-laptop/')
def add_laptop_view(laptop: LaptopRequest, current_user: user_dependency, db: Session=Depends(get_db)):
    try:
        serialExists = db.query(Devices).filter(Devices.serial_number == laptop.serial_number).first()
        inventoryExists = db.query(Devices).filter(Devices.inventory_number == laptop.inventory_number).first()


        if serialExists:
            return "Serial Found"
        elif inventoryExists:
            return "Inventory Found"        
        else:
            device_section = Devices(
                category = laptop.category,
                brand = laptop.brand,
                model = laptop.model,
                serial_number = laptop.serial_number,
                inventory_number = laptop.inventory_number,
                delivery_date = laptop.delivery_date,
                deployment_date = laptop.deployment_date,
                bos_date = laptop.bos_date,
                supplier_name = laptop.supplier_name,
                device_cost = laptop.device_cost,
                status_id = laptop.status_id,
                division_id = laptop.division_id,
                location_id = laptop.location_id,
                added_by = current_user.firstname + " " + current_user.lastname,
            )

            db.add(device_section)
            db.flush()

            laptop_section = Laptops(
                
                
                hard_disk_capacity = laptop.hard_disk_capacity,
                memory_capacity = laptop.memory_capacity,
                warranty_start_date = laptop.warranty_start_date,
                warranty_end_date = laptop.warranty_end_date,
                return_date = laptop.return_date,
                mac_address = laptop.mac_address,
                manufactured_date = laptop.manufactured_date,
                memory_type = laptop.memory_type,
                operating_system = laptop.operating_system,
                cpu_type_id = laptop.cpu_type_id,
                processor_speed = laptop.processor_speed,
                processor_type = laptop.processor_type,
                computer_name = laptop.computer_name,
                microsoft_office_version = laptop.microsoft_office_version,
                antivirus = laptop.antivirus,
                pdf_reader = laptop.pdf_reader,
                
                devices_id = device_section.devices_id,
            )

            db.add(laptop_section)

            comment_section = Comments(
                devices_id = device_section.devices_id,
                comment_value = laptop.comment,
            )

            db.add(comment_section)

            db.commit()
            db.refresh(laptop_section)
            return {"message": "Laptop Has Been Added"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post('/add-desktop/')
def add_desktop_view(desktop: DesktopRequest, current_user: user_dependency, db: Session=Depends(get_db)):
    try:
        serialExists = db.query(Devices).filter(Devices.serial_number == desktop.serial_number).first()
        inventoryExists = db.query(Devices).filter(Devices.inventory_number == desktop.inventory_number).first()


        if serialExists:
            return "Serial Found"
        elif inventoryExists:
            return "Inventory Found"        
        else:
            device_section = Devices(
                category = desktop.category,
                brand = desktop.brand,
                model = desktop.model,
                serial_number = desktop.serial_number,
                inventory_number = desktop.inventory_number,
                delivery_date = desktop.delivery_date,
                deployment_date = desktop.deployment_date,
                bos_date = desktop.bos_date,
                supplier_name = desktop.supplier_name,
                device_cost = desktop.device_cost,
                status_id = desktop.status_id,
                division_id = desktop.division_id,
                location_id = desktop.location_id,
                added_by = current_user.firstname + " " + current_user.lastname,
            )

            db.add(device_section)
            db.flush()

            desktop_section = Desktops(
                
                
                hard_disk_capacity = desktop.hard_disk_capacity,
                memory_capacity = desktop.memory_capacity,
                warranty_start_date = desktop.warranty_start_date,
                warranty_end_date = desktop.warranty_end_date,
                return_date = desktop.return_date,
                mac_address = desktop.mac_address,
                manufactured_date = desktop.manufactured_date,
                memory_type = desktop.memory_type,
                operating_system = desktop.operating_system,
                cpu_type_id = desktop.cpu_type_id,
                processor_speed = desktop.processor_speed,
                processor_type = desktop.processor_type,
                computer_name = desktop.computer_name,
                microsoft_office_version = desktop.microsoft_office_version,
                antivirus = desktop.antivirus,
                form_factor_id = desktop.form_factor_id,
                pdf_reader = desktop.pdf_reader,
                
                devices_id = device_section.devices_id,
            )

            db.add(desktop_section)

            comment_section = Comments(
                devices_id = device_section.devices_id,
                comment_value = desktop.comment,
            )

            db.add(comment_section)

            db.commit()
            db.refresh(desktop_section)
            return {"message": "Desktop Has Been Added"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post('/add-server/')
def add_server_view(server: ServerRequest, current_user: user_dependency, db: Session=Depends(get_db)):
    try:
        serialExists = db.query(Devices).filter(Devices.serial_number == server.serial_number).first()
        inventoryExists = db.query(Devices).filter(Devices.inventory_number == server.inventory_number).first()


        if serialExists:
            return "Serial Found"
        elif inventoryExists:
            return "Inventory Found"        
        else:
            device_section = Devices(
                category = server.category,
                brand = server.brand,
                model = server.model,
                serial_number = server.serial_number,
                inventory_number = server.inventory_number,
                delivery_date = server.delivery_date,
                deployment_date = server.deployment_date,
                bos_date = server.bos_date,
                supplier_name = server.supplier_name,
                device_cost = server.device_cost,
                status_id = server.status_id,
                division_id = server.division_id,
                location_id = server.location_id,
                added_by = current_user.firstname + " " + current_user.lastname,
            )

            db.add(device_section)
            db.flush()

            server_section = Servers(
                
                
                hard_disk_capacity = server.hard_disk_capacity,
                memory_capacity = server.memory_capacity,
                warranty_start_date = server.warranty_start_date,
                warranty_end_date = server.warranty_end_date,
                return_date = server.return_date,
                mac_address = server.mac_address,
                manufactured_date = server.manufactured_date,
                memory_type = server.memory_type,
                operating_system = server.operating_system,
                cpu_type_id = server.cpu_type_id,
                processor_speed = server.processor_speed,
                processor_type = server.processor_type,
                computer_name = server.computer_name,
                microsoft_office_version = server.microsoft_office_version,
                antivirus = server.antivirus,
                form_factor_id = server.form_factor_id,
                raid_type_id = server.raid_type_id,
                number_of_hard_drives = server.number_of_hard_drives,
                number_of_power_supplies = server.number_of_power_supplies,
                pdf_reader = server.pdf_reader,
                
                devices_id = device_section.devices_id,
            )

            db.add(server_section)

            comment_section = Comments(
                devices_id = device_section.devices_id,
                comment_value = server.comment,
            )

            db.add(comment_section)

            db.commit()
            db.refresh(server_section)
            return {"message": "Server Has Been Added"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post('/add-tablet/')
def add_tablet_view(tablet: TabletRequest, current_user: user_dependency, db: Session=Depends(get_db)):
    try:

        serialExists = db.query(Devices).filter(Devices.serial_number == tablet.serial_number).first()
        inventoryExists = db.query(Devices).filter(Devices.inventory_number == tablet.inventory_number).first()


        if serialExists:
            return "Serial Found"
        elif inventoryExists:
            return "Inventory Found"  
        else:
            device_section = Devices(
                    category = tablet.category,
                    brand = tablet.brand,
                    model = tablet.model,
                    serial_number = tablet.serial_number,
                    inventory_number = tablet.inventory_number,
                    delivery_date = tablet.delivery_date,
                    deployment_date = tablet.deployment_date,
                    bos_date = tablet.bos_date,
                    supplier_name = tablet.supplier_name,
                    device_cost = tablet.device_cost,
                    status_id = tablet.status_id,
                    division_id = tablet.division_id,
                    location_id = tablet.location_id,
                    added_by = current_user.firstname + " " + current_user.lastname,
            )

            db.add(device_section)
            db.flush()

            tablet_section = Tablets(
                
                hard_disk_capacity = tablet.hard_disk_capacity,
                memory_capacity = tablet.memory_capacity,
                warranty_start_date = tablet.warranty_start_date,
                warranty_end_date = tablet.warranty_end_date,
                return_date = tablet.return_date,
                device_size = tablet.device_size,
                operating_system = tablet.operating_system,
                imei_number = tablet.imei_number,
                version = tablet.version,

                devices_id = device_section.devices_id,
            )

            db.add(tablet_section)

            comment_section = Comments(
                devices_id = device_section.devices_id,
                comment_value = tablet.comment,
            )

            db.add(comment_section)

            db.commit()
            db.refresh(tablet_section)
            return {"message": "Tablet Has Been Added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post('/add-mouse-keyboard/')
def add_mouse_keyboard_view(mouse_keyboard: MouseKeyboardRequest, current_user: user_dependency, db: Session=Depends(get_db)):
    try:

        serialExists = db.query(Devices).filter(Devices.serial_number == mouse_keyboard.serial_number).first()
        inventoryExists = db.query(Devices).filter(Devices.inventory_number == mouse_keyboard.inventory_number).first()


        if serialExists:
            return "Serial Found"
        elif inventoryExists:
            return "Inventory Found"  
        else:
            device_section = Devices(
                    category = mouse_keyboard.category,
                    brand = mouse_keyboard.brand,
                    model = mouse_keyboard.model,
                    serial_number = mouse_keyboard.serial_number,
                    inventory_number = mouse_keyboard.inventory_number,
                    delivery_date = mouse_keyboard.delivery_date,
                    deployment_date = mouse_keyboard.deployment_date,
                    bos_date = mouse_keyboard.bos_date,
                    supplier_name = mouse_keyboard.supplier_name,
                    device_cost = mouse_keyboard.device_cost,
                    status_id = mouse_keyboard.status_id,
                    division_id = mouse_keyboard.division_id,
                    location_id = mouse_keyboard.location_id,
                    added_by = current_user.firstname + " " + current_user.lastname,
            )

            db.add(device_section)
            db.flush()

            mouse_keyboard_section = MouseKeyboards(
                connection_type_id = mouse_keyboard.connection_type_id,
                devices_id = device_section.devices_id,
            )

            db.add(mouse_keyboard_section)

            comment_section = Comments(
                devices_id = device_section.devices_id,
                comment_value = mouse_keyboard.comment,
            )

            db.add(comment_section)

            db.commit()
            db.refresh(mouse_keyboard_section)
            return {"message": "Mouse/Keyboard Has Been Added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post('/add-scanner/')
def add_scanner_view(scanner: ScannerRequest, current_user: user_dependency, db: Session=Depends(get_db)):
    try:

        serialExists = db.query(Devices).filter(Devices.serial_number == scanner.serial_number).first()
        inventoryExists = db.query(Devices).filter(Devices.inventory_number == scanner.inventory_number).first()


        if serialExists:
            return "Serial Found"
        elif inventoryExists:
            return "Inventory Found"  
        else:
            device_section = Devices(
                    category = scanner.category,
                    brand = scanner.brand,
                    model = scanner.model,
                    serial_number = scanner.serial_number,
                    inventory_number = scanner.inventory_number,
                    delivery_date = scanner.delivery_date,
                    deployment_date = scanner.deployment_date,
                    bos_date = scanner.bos_date,
                    supplier_name = scanner.supplier_name,
                    device_cost = scanner.device_cost,
                    status_id = scanner.status_id,
                    division_id = scanner.division_id,
                    location_id = scanner.location_id,
                    added_by = current_user.firstname + " " + current_user.lastname,
            )

            db.add(device_section)
            db.flush()

            scanner_section = Scanners(
                mac_address = scanner.mac_address,
                ip_address = scanner.ip_address,
                connection_type_id = scanner.connection_type_id,
                devices_id = device_section.devices_id,
            )

            db.add(scanner_section)

            comment_section = Comments(
                devices_id = device_section.devices_id,
                comment_value = scanner.comment,
            )

            db.add(comment_section)

            db.commit()
            db.refresh(scanner_section)
            return {"message": "Scanner Has Been Added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post('/add-surge-protector/')
def add_surge_protector_view(surge_protector: SurgeProtectorRequest, current_user: user_dependency, db: Session=Depends(get_db)):
    try:

        serialExists = db.query(Devices).filter(Devices.serial_number == surge_protector.serial_number).first()
        inventoryExists = db.query(Devices).filter(Devices.inventory_number == surge_protector.inventory_number).first()


        if serialExists:
            return "Serial Found"
        elif inventoryExists:
            return "Inventory Found"  
        else:
            device_section = Devices(
                    category = surge_protector.category,
                    brand = surge_protector.brand,
                    model = surge_protector.model,
                    serial_number = surge_protector.serial_number,
                    inventory_number = surge_protector.inventory_number,
                    delivery_date = surge_protector.delivery_date,
                    deployment_date = surge_protector.deployment_date,
                    bos_date = surge_protector.bos_date,
                    supplier_name = surge_protector.supplier_name,
                    device_cost = surge_protector.device_cost,
                    status_id = surge_protector.status_id,
                    division_id = surge_protector.division_id,
                    location_id = surge_protector.location_id,
                    added_by = current_user.firstname + " " + current_user.lastname,
            )

            db.add(device_section)
            db.flush()

            surge_protector_section = SurgeProtectors(
                
                number_of_outlets = surge_protector.number_of_outlets,
                devices_id = device_section.devices_id,
            )

            db.add(surge_protector_section)

            comment_section = Comments(
                devices_id = device_section.devices_id,
                comment_value = surge_protector.comment,
            )

            db.add(comment_section)

            db.commit()
            db.refresh(surge_protector_section)
            return {"message": "Surge Protector Has Been Added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post('/add-ups/')
def add_ups_view(ups: UPSRequest, current_user: user_dependency, db: Session=Depends(get_db)):
    try:

        serialExists = db.query(Devices).filter(Devices.serial_number == ups.serial_number).first()
        inventoryExists = db.query(Devices).filter(Devices.inventory_number == ups.inventory_number).first()


        if serialExists:
            return "Serial Found"
        elif inventoryExists:
            return "Inventory Found"  
        else:
            device_section = Devices(
                    category = ups.category,
                    brand = ups.brand,
                    model = ups.model,
                    serial_number = ups.serial_number,
                    inventory_number = ups.inventory_number,
                    delivery_date = ups.delivery_date,
                    deployment_date = ups.deployment_date,
                    bos_date = ups.bos_date,
                    supplier_name = ups.supplier_name,
                    device_cost = ups.device_cost,
                    status_id = ups.status_id,
                    division_id = ups.division_id,
                    location_id = ups.location_id,
                    added_by = current_user.firstname + " " + current_user.lastname,
            )

            db.add(device_section)
            db.flush()

            ups_section = UPS(
                
                number_of_outlets = ups.number_of_outlets,
                return_date = ups.return_date,
                devices_id = device_section.devices_id,
            )

            db.add(ups_section)

            comment_section = Comments(
                devices_id = device_section.devices_id,
                comment_value = ups.comment,
            )

            db.add(comment_section)

            db.commit()
            db.refresh(ups_section)
            return {"message": "UPS Has Been Added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post('/add-speaker/')
def add_speaker_view(speaker: SpeakerRequest, current_user: user_dependency, db: Session=Depends(get_db)):
    try:

        serialExists = db.query(Devices).filter(Devices.serial_number == speaker.serial_number).first()
        inventoryExists = db.query(Devices).filter(Devices.inventory_number == speaker.inventory_number).first()


        if serialExists:
            return "Serial Found"
        elif inventoryExists:
            return "Inventory Found"  
        else:
            device_section = Devices(
                    category = speaker.category,
                    brand = speaker.brand,
                    model = speaker.model,
                    serial_number = speaker.serial_number,
                    inventory_number = speaker.inventory_number,
                    delivery_date = speaker.delivery_date,
                    deployment_date = speaker.deployment_date,
                    bos_date = speaker.bos_date,
                    supplier_name = speaker.supplier_name,
                    device_cost = speaker.device_cost,
                    status_id = speaker.status_id,
                    division_id = speaker.division_id,
                    location_id = speaker.location_id,
                    added_by = current_user.firstname + " " + current_user.lastname,
            )

            db.add(device_section)
            db.flush()

            speaker_section = Speakers(

                return_date = speaker.return_date,
                speaker_type_id = speaker.speaker_type_id,
                number_of_speakers = speaker.number_of_speakers,
                
                devices_id = device_section.devices_id,
            )

            db.add(speaker_section)

            comment_section = Comments(
                devices_id = device_section.devices_id,
                comment_value = speaker.comment,
            )

            db.add(comment_section)

            db.commit()
            db.refresh(speaker_section)
            return {"message": "Speaker Has Been Added"}
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
def get_items_view(current_user: user_dependency, filter: Optional[str] = None, input: Optional[str] = None, db: Session=Depends(get_db)):

    query = (
        db.query(
            Devices, 
            SystemStatus.status_description, 
            Divisions.division_name, 
            Clients.firstname,
            Clients.lastname,
        )
        .outerjoin(SystemStatus, Devices.status_id == SystemStatus.status_id)
        .outerjoin(Divisions, Devices.division_id == Divisions.division_id)
        .outerjoin(Clients, Devices.client_id == Clients.client_id)
    )
    if filter == "Device Type":
        query = query.filter(Devices.category.ilike(f"%{input}%"))

    if filter == "Status":
        query = query.filter(SystemStatus.status_description.ilike(f"%{input}%"))

    if filter == "Division":
        query = query.filter(Divisions.division_name.ilike(f"%{input}%"))

    if filter == "Serial Number":
        query = query.filter(Devices.serial_number.ilike(f"%{input}%"))
        
    if filter == "Delivery Date":
        parsed_date = datetime.strptime(input, "%Y-%m-%d").date()
        query = query.filter(Devices.delivery_date == parsed_date)

    if filter == "Deployment Date":
        parsed_date = datetime.strptime(input, "%Y-%m-%d").date()
        query = query.filter(Devices.deployment_date == parsed_date)

    if filter == "Client":
        query = query.filter(
            or_(
                Clients.firstname.ilike(f"%{input}%"),
                Clients.lastname.ilike(f"%{input}%"),
            )
        )


    rows = query.all()
    result_list = []

    for device, status_description, division_name, firstname, lastname in rows:
        client_name = None
        if firstname or lastname:
            client_name = f"{firstname or ''} {lastname or ''}".strip()
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
            "client_id": device.client_id,
            "client_name": client_name, 
        }
        result_list.append(item)


    return result_list

@app.get('/get-unassigned-items/')
def get__unassigned_items_view(current_user: user_dependency, filter: Optional[str] = None, input: Optional[str] = None, db: Session=Depends(get_db)):

    query = (
        db.query(
            Devices, 
            SystemStatus.status_description, 
            Divisions.division_name, 
            Clients.firstname,
            Clients.lastname,
        )
        .outerjoin(SystemStatus, Devices.status_id == SystemStatus.status_id)
        .outerjoin(Divisions, Devices.division_id == Divisions.division_id)
        .outerjoin(Clients, Devices.client_id == Clients.client_id)
    )

    query = query.filter(Devices.client_id == None)

    if filter == "Device Type":
        query = query.filter(Devices.category.ilike(f"%{input}%"))

    if filter == "Status":
        query = query.filter(SystemStatus.status_description.ilike(f"%{input}%"))

    if filter == "Division":
        query = query.filter(Divisions.division_name.ilike(f"%{input}%"))

    if filter == "Serial Number":
        query = query.filter(Devices.serial_number.ilike(f"%{input}%"))
        
    if filter == "Delivery Date":
        parsed_date = datetime.strptime(input, "%Y-%m-%d").date()
        query = query.filter(Devices.delivery_date == parsed_date)

    if filter == "Deployment Date":
        parsed_date = datetime.strptime(input, "%Y-%m-%d").date()
        query = query.filter(Devices.deployment_date == parsed_date)

    if filter == "Client":
        query = query.filter(
            or_(
                Clients.firstname.ilike(f"%{input}%"),
                Clients.lastname.ilike(f"%{input}%"),
            )
        )


    rows = query.all()
    result_list = []

    for device, status_description, division_name, firstname, lastname in rows:
        client_name = None
        if firstname or lastname:
            client_name = f"{firstname or ''} {lastname or ''}".strip()
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
            "client_id": device.client_id,
            "client_name": client_name, 
        }
        result_list.append(item)


    return result_list

@app.get('/get-assigned-items/')
def get_items_view(current_user: user_dependency, filter: Optional[str] = None, input: Optional[str] = None, db: Session=Depends(get_db)):

    query = (
        db.query(
            Devices, 
            SystemStatus.status_description, 
            Divisions.division_name, 
            Clients.firstname,
            Clients.lastname,
        )
        .outerjoin(SystemStatus, Devices.status_id == SystemStatus.status_id)
        .outerjoin(Divisions, Devices.division_id == Divisions.division_id)
        .outerjoin(Clients, Devices.client_id == Clients.client_id)
    )

    query = query.filter(Devices.client_id != None)

    if filter == "Device Type":
        query = query.filter(Devices.category.ilike(f"%{input}%"))

    if filter == "Status":
        query = query.filter(SystemStatus.status_description.ilike(f"%{input}%"))

    if filter == "Division":
        query = query.filter(Divisions.division_name.ilike(f"%{input}%"))

    if filter == "Serial Number":
        query = query.filter(Devices.serial_number.ilike(f"%{input}%"))
        
    if filter == "Delivery Date":
        parsed_date = datetime.strptime(input, "%Y-%m-%d").date()
        query = query.filter(Devices.delivery_date == parsed_date)

    if filter == "Deployment Date":
        parsed_date = datetime.strptime(input, "%Y-%m-%d").date()
        query = query.filter(Devices.deployment_date == parsed_date)

    if filter == "Client":
        query = query.filter(
            or_(
                Clients.firstname.ilike(f"%{input}%"),
                Clients.lastname.ilike(f"%{input}%"),
                (Clients.firstname + " " + Clients.lastname).ilike(f"%{input}%"),
            )
        )


    rows = query.all()
    result_list = []

    for device, status_description, division_name, firstname, lastname in rows:
        client_name = None
        if firstname or lastname:
            client_name = f"{firstname or ''} {lastname or ''}".strip()
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
            "client_id": device.client_id,
            "client_name": client_name, 
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
        
    else:
        result = (
            db.query(
                Devices,
                SystemStatus.status_description,
                Divisions.division_name,
            )
            .outerjoin(SystemStatus, Devices.status_id == SystemStatus.status_id)
            .outerjoin(Divisions, Devices.division_id == Divisions.division_id)
            .filter(Devices.serial_number == serial_number)
            .first()
        )

        if result:
            device, status_description, division_name = result
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
                }
        else:
            return {"message": "Device not found"}


    return {"message": "Category not supported"}

@app.delete('/delete-item/')
def delete_item_view(current_user: user_dependency, serial_number: str, db: Session=Depends(get_db)):
    deleted = db.query(Devices).filter(Devices.serial_number == serial_number).first()

    if not deleted:
        raise HTTPException(status_code=404, detail="Device not found")
    
    db.delete(deleted)
    db.commit()
    
    return {"message": "Device has been deleted"}

@app.post('/unassign-item/')
def delete_item_view(current_user: user_dependency, serial_number: str, db: Session=Depends(get_db)):
    device = db.query(Devices).filter(Devices.serial_number == serial_number).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    device.client_id = None
    db.commit()

    return {"message": "Device has been unassigned from the client"}



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

@app.delete('/delete-client/')
def delete_client_view(first_name: str, last_name: str, current_user: user_dependency, db: Session=Depends(get_db)):

    deleted = db.query(Clients).filter(Clients.firstname == first_name, Clients.lastname == last_name).delete()
    db.commit()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return {"message": "Client has been deleted"}

@app.get('/get-clients/')
def get_client_view(current_user: user_dependency, name: Optional[str] = None, db: Session=Depends(get_db)):

    if name:
        search = f"%{name.strip()}%"
        query = db.query(Clients).filter((Clients.firstname + " " + Clients.lastname).ilike(search)).all()
        return query
    else:
        return db.query(Clients).all()
    
@app.get('/get-users/')
def get_client_view(current_user: user_dependency, name: Optional[str] = None, db: Session=Depends(get_db)):

    if name:
        search = f"%{name.strip()}%"
        query = db.query(Users).filter((Users.firstname + " " + Users.lastname).ilike(search)).all()
        return query
    else:
        return db.query(Users).all()
    




@app.get('/get-statuses/')
def get_statuses_view(current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(SystemStatus).all()

@app.get('/get-cpu-types/')
def get_cpu_types_view(current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(CPUTypes).all()

@app.get('/get-connection-types/')
def get_connection_types_view(current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(ConnectionTypes).all()

@app.get('/get-printer-features/')
def get_printer_features_view(current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(PrinterFeatures).all()

@app.get('/get-form-factors/')
def get_form_factors_view(current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(FormFactors).all()

@app.get('/get-raid-types/')
def get_raid_types_view(current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(RaidTypes).all()

@app.get('/get-speaker-types/')
def get_speaker_types_view(current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(SpeakerTypes).all()

@app.get('/get-divisions/')
def get_divisions_view(current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(Divisions).all()

@app.get('/get-locations/')
def get_locations_view(current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(Locations).all()

@app.get('/get-parishes/')
def get_parishes_view(current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(Parishes).all()

@app.get('/get-location-types/')
def get_location_types_view(current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(LocationTypes).all()

@app.get('/get-parish-locations/')
def get_parish_locations_view(current_user: user_dependency, db: Session=Depends(get_db), parish_id: Optional[int] = None):

    if parish_id:
        locations = (
            db.query(Locations)
            .join(Parishes, Parishes.parish_id == Locations.parish_id)
            .filter(Parishes.parish_id == parish_id)
            .all()
        )
    else:
        locations = (
            db.query(Locations).all()
        )

    return locations

@app.get('/get-parish-divisions/')
def get_parish_divisions_view(current_user: user_dependency, db: Session=Depends(get_db), parish_id: Optional[int] = None):

    if parish_id:
        divisions = (
            db.query(Divisions)
            .join(DivisionLocation, DivisionLocation.division_id == Divisions.division_id)
            .join(Locations, Locations.location_id == DivisionLocation.location_id)
            .join(Parishes, Parishes.parish_id == Locations.parish_id)
            .filter(Parishes.parish_id == parish_id)
            .all()
        )
    
    else:
        divisions = (
            db.query(Divisions).all()
        )

    return divisions


@app.get('/get-location-parish/')
def get_location_parish_view(current_user: user_dependency, db: Session=Depends(get_db), location_id: Optional[int] = None):

    if location_id:
        parish = (
            db.query(Parishes)
            .join(Locations, Parishes.parish_id == Locations.parish_id)
            .filter(Locations.location_id == location_id)
            .all()
        )
    else:
        parish = (
            db.query(Parishes).all()
        )

    return parish


@app.get('/get-location-division/')
def get_location_parish_view(current_user: user_dependency, db: Session=Depends(get_db), location_id: Optional[int] = None):
    
    if location_id:
        divisions = (
            db.query(Divisions)
            .join(DivisionLocation, DivisionLocation.division_id == Divisions.division_id)
            .join(Locations, Locations.location_id == DivisionLocation.location_id)
            .filter(Locations.location_id == location_id)
            .all()
        )
    else:
        divisions = (
            db.query(Divisions).all()
        )
    
    return divisions


@app.put('/assign-device/')
def assign_device_view(current_user: user_dependency, device_sn: str, client_id: int, db: Session=Depends(get_db)):
    device = db.query(Devices).filter(Devices.serial_number == device_sn).first()

    if device:
        device.client_id = client_id
        device.assigned_on = datetime.now().strftime("%Y-%m-%d")
        db.commit()
        db.refresh(device)
        return {"message": "Device assigned successfully", "item_id": device.devices_id, "client": client_id}
    
    else:
        raise HTTPException(
            status_code=404,
            detail="Device not found"
        )


@app.get('/get-comments/')
def get_comments_view(current_user: user_dependency, devices_id: int, db: Session=Depends(get_db)):
    return db.query(Comments).filter(Comments.devices_id == devices_id).order_by(desc(Comments.comment_id)).all()

@app.post('/add-comments/')
def add_comments_view(comment: CommentCreate, current_user: user_dependency, db: Session=Depends(get_db)):
    try:
        device = db.query(Devices).filter(Devices.devices_id == comment.id).first()
        
        if device:
            new_comment = Comments(
                devices_id = comment.id,
                comment_value = comment.comment,
            )

            db.add(new_comment)
            db.commit()
            db.refresh(new_comment)
            return {"message": "Comment Has Been Added"}
        else:
            return {"message": "Comment Not Found"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    
@app.delete('/delete-comment/')
def delete_comments_view(current_user: user_dependency, id: int, db: Session=Depends(get_db)):
    deleted = db.query(Comments).filter(Comments.comment_id == id).delete()
    db.commit()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return {"message": "comment has been deleted"}



@app.post('/add-status/')
def add_status_view(status: StatusCreate, current_user: user_dependency, db: Session=Depends(get_db)):
    try:
        new_status = SystemStatus(
            status_description = status.status,
        )

        db.add(new_status)
        db.commit()
        db.refresh(new_status)
        return {"message": "Status Has Been Added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post('/add-division/')
def add_division_view(division: DivisionCreate, current_user: user_dependency, db: Session=Depends(get_db)):
    try:
        new_division = Divisions(
            division_name = division.division,
            added_by = current_user.firstname + " " + current_user.lastname,
        )

        db.add(new_division)
        db.commit()
        db.refresh(new_division)
        return {"message": "Division Has Been Added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/delete-status/")
def delete_status_view(
    current_user: user_dependency,
    status: str,
    db: Session = Depends(get_db)
):

    status_record = db.query(SystemStatus).filter(SystemStatus.status_description == status).first()

    if not status_record:
        raise HTTPException(status_code=404, detail="Status not found")

    # Set status to NULL for all devices using this status
    db.query(Devices).filter(Devices.status_id == status_record.status_id).update({Devices.status_id: None})

    db.delete(status_record)
    db.commit()

    return {"message": "Status deleted and devices updated"}

@app.delete("/delete-division/")
def delete_status_view(
    current_user: user_dependency,
    division: str,
    db: Session = Depends(get_db)
):

    division_record = db.query(Divisions).filter(Divisions.division_name == division).first()

    if not division_record:
        raise HTTPException(status_code=404, detail="Division not found")

    # Set status to NULL for all devices using this status
    db.query(Devices).filter(Devices.division_id == division_record.division_id).update({Devices.status_id: None})

    db.delete(division_record)
    db.commit()

    return {"message": "Division deleted and devices updated"}
    


@app.post('/add-cpu-type/')
def add_cpu_type_view(cpu_type: CPUTypeCreate, current_user: user_dependency, db: Session=Depends(get_db)):
    try:
        new_cpu_type = CPUTypes(
            cpu_type_description = cpu_type.cpu_type,
        )

        db.add(new_cpu_type)
        db.commit()
        db.refresh(new_cpu_type)
        return {"message": "CPU Type Has Been Added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    

@app.delete('/delete-cpu-type/')
def delete_status_view(cpu_type: str, current_user: user_dependency, db: Session=Depends(get_db)):
    deleted = db.query(CPUTypes).filter(CPUTypes.cpu_type_description == cpu_type).delete()
    db.commit()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="CPU Type not found")
    
    return {"message": "Cpu Type has been deleted"}


@app.post('/add-connection-type/')
def add_connection_type_view(ctype: ConnectionTypeCreate, current_user: user_dependency, db: Session=Depends(get_db)):
    try:
        new_ctype = ConnectionTypes(
            ctype_description = ctype.ctype,
        )

        db.add(new_ctype)
        db.commit()
        db.refresh(new_ctype)
        return {"message": "Connection Type Has Been Added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    
@app.delete('/delete-connection-type/')
def delete_connection_type_view(current_user: user_dependency, ctype: str, db: Session=Depends(get_db)):
    deleted = db.query(ConnectionTypes).filter(ConnectionTypes.ctype_description == ctype).delete()
    db.commit()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Connection Type not found")
    
    return {"message": "Connection Type has been deleted"}


@app.post('/add-printer-feature/')
def add_printer_feature_view(printer_feature: PrinterFeatureCreate, current_user: user_dependency, db: Session=Depends(get_db)):
    try:
        new_printer_feature = PrinterFeatures(
            feature_description = printer_feature.printer_feature,
        )

        db.add(new_printer_feature)
        db.commit()
        db.refresh(new_printer_feature)
        return {"message": "Printer Feature Has Been Added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    

@app.delete('/delete-printer-feature/')
def delete_printer_feature_view(current_user: user_dependency, printer_feature: str, db: Session=Depends(get_db)):
    deleted = db.query(PrinterFeatures).filter(PrinterFeatures.feature_description == printer_feature).delete()
    db.commit()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Printer Feature not found")
    
    return {"message": "Printer Feature has been deleted"}


@app.get('/get-location-names/')
def get_location_names_view(current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(Locations).all()

@app.get("/get-all-locations/")
def get_all_locations(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Returns a list of all locations, 
    each with the count of devices per category under that location.
    """
    try:
        # Step 1: Get all locations
        locations = db.query(Locations).all()

        results = []

        # Step 2: For each location, count devices by category
        for loc in locations:
            category_counts = (
                db.query(Devices.category, func.count(Devices.devices_id))
                .join(Divisions, Devices.division_id == Divisions.division_id)
                .filter(Divisions.location_id == loc.location_id)
                .group_by(Devices.category)
                .all()
            )

            # Step 3: Format data
            formatted_counts = [
                {"category": category, "count": count} for category, count in category_counts
            ]

            results.append({
                "location_name": loc.location_name,
                "category_counts": formatted_counts
            })

        return results

    except Exception as e:
        print(f"Error fetching location data: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving location data.")
    

@app.get('/get-parish-names/')
def get_parish_names_view(current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(Parishes).all()



@app.get("/filter-delivery-date/")
def filter_delivery_date(date: date, current_user: user_dependency, db: Session = Depends(get_db)):
    query = (
        db.query(
            Devices.devices_id,
            Devices.category,
            Devices.brand,
            Devices.model,
            Devices.serial_number,
            Devices.inventory_number,
            Devices.delivery_date,
            Divisions.division_name,
            SystemStatus.status_description,
        )
        .join(Divisions, Devices.division_id == Divisions.division_id)
        .join(SystemStatus, Devices.status_id == SystemStatus.status_id)
    )

    if date:
        query = query.filter(Devices.delivery_date >= date)

        results = query.all()

    return [
        {
            "devices_id": r.devices_id,
            "category": r.category,
            "brand": r.brand,
            "model": r.model,
            "serial_number": r.serial_number,
            "inventory_number": r.inventory_number,
            "delivery_date": r.delivery_date,
            "status_description": r.status_description,
            "division_name": r.division_name,
        }
        for r in results
    ]


@app.get("/filter-deployment-date/")
def filter_deployment_date(date: date, current_user: user_dependency, db: Session = Depends(get_db)):
    query = (
        db.query(
            Devices.devices_id,
            Devices.category,
            Devices.brand,
            Devices.model,
            Devices.serial_number,
            Devices.inventory_number,
            Devices.deployment_date,
            Divisions.division_name,
            SystemStatus.status_description,
        )
        .join(Divisions, Devices.division_id == Divisions.division_id)
        .join(SystemStatus, Devices.status_id == SystemStatus.status_id)
    )

    if date:
        query = query.filter(Devices.deployment_date >= date)

        results = query.all()

    return [
        {
            "devices_id": r.devices_id,
            "category": r.category,
            "brand": r.brand,
            "model": r.model,
            "serial_number": r.serial_number,
            "inventory_number": r.inventory_number,
            "deployment_date": r.deployment_date,
            "status_description": r.status_description,
            "division_name": r.division_name,
        }
        for r in results
    ]


@app.post("/filter-devices/")
def filter_devices(
    filters: FilterRequest,
    current_user: user_dependency,
    db: Session = Depends(get_db)
):
    query = (
        db.query(
            Devices.devices_id,
            Devices.category,
            Devices.brand,
            Devices.model,
            Devices.serial_number,
            Devices.inventory_number,
            Devices.delivery_date,
            SystemStatus.status_description,
            Locations.location_name,
        )
        .join(SystemStatus, Devices.status_id == SystemStatus.status_id, isouter=True)
        .join(Divisions, Devices.division_id == Divisions.division_id, isouter=True)
        .join(Locations, Divisions.location_id == Locations.location_id, isouter=True)
        .join(Parishes, Locations.parish_id == Parishes.parish_id, isouter=True)
        
    )

    # ✅ Step 3: Apply filters dynamically
    if filters.locations:
        query = query.filter(Locations.location_name.in_(filters.locations))

    if filters.parishes:
        query = query.filter(Parishes.parish_name.in_(filters.parishes))

    if filters.statuses:
        query = query.filter(SystemStatus.status_description.in_(filters.statuses))

    if filters.components:
        query = query.filter(Devices.category.in_(filters.components))

    results = query.all()

    return [
        {
            "devices_id": r.devices_id,
            "category": r.category,
            "brand": r.brand,
            "model": r.model,
            "serial_number": r.serial_number,
            "inventory_number": r.inventory_number,
            "delivery_date": r.delivery_date,
            "status_description": r.status_description,
            "location_name": r.location_name,
        }
        for r in results
    ]

@app.get('/get-items-delivery-date/')
def get_items_delivery_date_view(delivery_date: date, current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(Devices).filter(Devices.delivery_date > delivery_date).all()

@app.get('/filter-being-repaired/')
def filter_being_repaired(current_user: user_dependency, db: Session=Depends(get_db)):
    query = (
        db.query(
            Devices.devices_id,
            Devices.category,
            Devices.brand,
            Devices.model,
            Devices.serial_number,
            Devices.inventory_number,
            Devices.delivery_date,
            Divisions.division_name,
            SystemStatus.status_description,
            Clients.firstname,
            Clients.lastname,
        )
        .outerjoin(Divisions, Devices.division_id == Divisions.division_id)
        .outerjoin(SystemStatus, Devices.status_id == SystemStatus.status_id)
        .outerjoin(Clients, Devices.client_id == Clients.client_id)
    )

    query = query.filter(Devices.status_id == 2)

    results = query.all()

    return [
        {
            "devices_id": r.devices_id,
            "category": r.category,
            "brand": r.brand,
            "model": r.model,
            "serial_number": r.serial_number,
            "inventory_number": r.inventory_number,
            "delivery_date": r.delivery_date,
            "status_description": r.status_description,
            "division_name": r.division_name,
            "client_first_name": r.firstname,
            "client_last_name": r.lastname,
        }
        for r in results
    ]

@app.post("/update-status/", status_code=status.HTTP_201_CREATED)
async def update_status(status_box: UpdateStatusRequest, current_user: user_dependency, db: Session=Depends(get_db)):
    existing_statuses = db.query(SystemStatus.status_id).all()
    existing_statuses = [row[0] for row in existing_statuses]
    device = db.query(Devices).filter(Devices.serial_number == status_box.serial_number).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    elif status_box.new_status not in existing_statuses:
        raise HTTPException(status_code=404, detail="Status not found")
    
    elif device.status_id == status_box.new_status:
        raise HTTPException(status_code=404, detail="Device already has this status")
    
    else:
        if device.status_id == 2 and status_box.new_status == 1:
            device.repaired_date = datetime.now().strftime("%Y-%m-%d")
            device.repaired_by = current_user.firstname + " " + current_user.lastname

        device.status_id = status_box.new_status

        db.commit()
        db.refresh(device)
        return device
    

        
