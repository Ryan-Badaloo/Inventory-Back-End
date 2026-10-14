import os
import logging
import shutil
import uuid
from datetime import datetime, timedelta, date
from contextlib import asynccontextmanager
from typing import Union, Any, Optional, List, Annotated, Dict
from passlib.context import CryptContext
from jose import jwt, JWTError
from sqlalchemy import extract, create_engine, Column, Integer, String, Boolean, Float, DateTime, Date, text, or_, and_, desc, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, FastAPI, HTTPException, status, APIRouter, UploadFile, File
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
        user.last_updated = datetime.now()
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


######################### SECTION FOR ADDING INFORMATION #######################################
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
                parish_id = laptop.parish_id,
                ltype_id = laptop.ltype_id,
                division_id = laptop.division_id,
                location_id = laptop.location_id,
                branch_id = laptop.branch_id,
                added_by = current_user.firstname + " " + current_user.lastname,
            )

            print("Testing the ltype and branch id")
            print(laptop.ltype_id, laptop.branch_id)

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
async def add_desktop_view(desktop: DesktopRequest, current_user: user_dependency, db: Session = Depends(get_db)):
    try:
        print(desktop.parish_id)
        print(desktop.ltype_id)
        print(desktop.branch_id)
        serialExists = db.query(Devices).filter(Devices.serial_number == desktop.serial_number).first()

        inventoryExists = db.query(Devices).filter(Devices.inventory_number == desktop.inventory_number).first()

        if serialExists:

            raise HTTPException(
                status_code=400,
                detail="Serial Number Already Exists"
            )

        elif inventoryExists:

            raise HTTPException(
                status_code=400,
                detail="Inventory Number Already Exists"
            )

        else:
            device_section = Devices(

            category=desktop.category,
            brand=desktop.brand,
            model=desktop.model,

            serial_number=desktop.serial_number,
            inventory_number=desktop.inventory_number,

            delivery_date=desktop.delivery_date,
            deployment_date=desktop.deployment_date,
            bos_date=desktop.bos_date,

            supplier_name=desktop.supplier_name,
            device_cost=desktop.device_cost,

            status_id=desktop.status_id,
            parish_id = desktop.parish_id,
            ltype_id = desktop.ltype_id,
            division_id = desktop.division_id,
            location_id = desktop.location_id,
            branch_id = desktop.branch_id,

            added_by=current_user.firstname + " " + current_user.lastname,
        )


        db.add(device_section)

        # Generates devices_id before commit
        db.flush()

        desktop_section = Desktops(

            hard_disk_capacity=desktop.hard_disk_capacity,
            memory_capacity=desktop.memory_capacity,

            warranty_start_date=desktop.warranty_start_date,
            warranty_end_date=desktop.warranty_end_date,

            return_date=desktop.return_date,

            mac_address=desktop.mac_address,
            manufactured_date=desktop.manufactured_date,

            memory_type=desktop.memory_type,
            operating_system=desktop.operating_system,

            cpu_type_id=desktop.cpu_type_id,

            processor_speed=desktop.processor_speed,
            processor_type=desktop.processor_type,

            computer_name=desktop.computer_name,

            microsoft_office_version=desktop.microsoft_office_version,

            antivirus=desktop.antivirus,

            form_factor_id=desktop.form_factor_id,

            pdf_reader=desktop.pdf_reader,

            devices_id=device_section.devices_id,
        )

        db.add(desktop_section)


        if desktop.comment:

            comment_section = Comments(

                devices_id=device_section.devices_id,

                comment_value=desktop.comment,
            )

            db.add(comment_section)


        db.commit()

        db.refresh(desktop_section)

        return {

            "message": "Desktop Has Been Added",

            "device_id": device_section.devices_id
        }

    except HTTPException:

        db.rollback()

        raise

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    
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
                parish_id = server.parish_id,
                ltype_id = server.ltype_id,
                division_id = server.division_id,
                location_id = server.location_id,
                branch_id = server.branch_id,
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
def add_tablet_view(data: AddTabletRequest, current_user: user_dependency, db: Session=Depends(get_db)):
    try:

        serialExists = db.query(Devices).filter(Devices.serial_number == data.tablet.serial_number).first()
        inventoryExists = db.query(Devices).filter(Devices.inventory_number == data.tablet.inventory_number).first()


        if serialExists:
            return "Serial Found"
        elif inventoryExists:
            return "Inventory Found"  
        else:
            device_section = Devices(
                    category = data.tablet.category,
                    brand = data.tablet.brand,
                    model = data.tablet.model,
                    serial_number = data.tablet.serial_number,
                    inventory_number = data.tablet.inventory_number,
                    delivery_date = data.tablet.delivery_date,
                    deployment_date = data.tablet.deployment_date,
                    bos_date = data.tablet.bos_date,
                    supplier_name = data.tablet.supplier_name,
                    device_cost = data.tablet.device_cost,
                    status_id = data.tablet.status_id,
                    parish_id = data.tablet.parish_id,
                    ltype_id = data.tablet.ltype_id,
                    division_id = data.tablet.division_id,
                    location_id = data.tablet.location_id,
                    branch_id = data.tablet.branch_id,
                    added_by = current_user.firstname + " " + current_user.lastname,
            )

            db.add(device_section)
            db.flush()

            tablet_section = Tablets(
                
                hard_disk_capacity = data.tablet.hard_disk_capacity,
                memory_capacity = data.tablet.memory_capacity,
                warranty_start_date = data.tablet.warranty_start_date,
                warranty_end_date = data.tablet.warranty_end_date,
                return_date = data.tablet.return_date,
                device_size = data.tablet.device_size,
                operating_system = data.tablet.operating_system,
                imei_number = data.tablet.imei_number,
                version = data.tablet.version,

                devices_id = device_section.devices_id,
            )

            db.add(tablet_section)

            if data.bag:
                bag_section = Bags(
                    bag_type_id = data.bag.bag_type_id,
                    bag_brand = data.bag.bag_brand,
                    bag_model = data.bag.bag_model,
                    bag_ministry_number = data.bag.bag_ministry_number,
                    bag_fabric_type_id = data.bag.bag_fabric_type_id,
                    bag_delivery_date = data.bag.bag_delivery_date,
                    bag_assignment_date = data.bag.bag_assignment_date,
                    bag_status_id = data.bag.bag_status_id,
                    bag_bos_date = data.bag.bag_bos_date,

                    devices_id = device_section.devices_id,
                )

                db.add(bag_section)
            
            if data.adapter:
                adapter_section = Adapters(
                    adapter_serial_number = data.adapter.adapter_serial_number,
                    adapter_brand = data.adapter.adapter_brand,
                    adapter_model = data.adapter.adapter_model,
                    adapter_ministry_number = data.adapter.adapter_ministry_number,
                    adapter_delivery_date = data.adapter.adapter_delivery_date,
                    adapter_assignment_date = data.adapter.adapter_assignment_date,
                    adapter_status_id = data.adapter.adapter_status_id,
                    adapter_bos_date = data.adapter.adapter_bos_date,

                    devices_id = device_section.devices_id,
                )

                db.add(adapter_section)

            comment_section = Comments(
                devices_id = device_section.devices_id,
                comment_value = data.tablet.comment,
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
                    parish_id = mouse_keyboard.parish_id,
                    ltype_id = mouse_keyboard.ltype_id,
                    division_id = mouse_keyboard.division_id,
                    location_id = mouse_keyboard.location_id,
                    branch_id = mouse_keyboard.branch_id,
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
                    parish_id = scanner.parish_id,
                    ltype_id = scanner.ltype_id,
                    division_id = scanner.division_id,
                    location_id = scanner.location_id,
                    branch_id = scanner.branch_id,
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
                    parish_id = surge_protector.parish_id,
                    ltype_id = surge_protector.ltype_id,
                    division_id = surge_protector.division_id,
                    location_id = surge_protector.location_id,
                    branch_id = surge_protector.branch_id,
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
                    parish_id = ups.parish_id,
                    ltype_id = ups.ltype_id,
                    division_id = ups.division_id,
                    location_id = ups.location_id,
                    branch_id = ups.branch_id,
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
                    parish_id = speaker.parish_id,
                    ltype_id = speaker.ltype_id,
                    division_id = speaker.division_id,
                    location_id = speaker.location_id,
                    branch_id = speaker.branch_id,
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

@app.post('/add-webcam/')
def add_webcam_view(webcam: DeviceRequest, current_user: user_dependency, db: Session=Depends(get_db)):
    try:

        serialExists = db.query(Devices).filter(Devices.serial_number == webcam.serial_number).first()
        inventoryExists = db.query(Devices).filter(Devices.inventory_number == webcam.inventory_number).first()


        if serialExists:
            return "Serial Found"
        elif inventoryExists:
            return "Inventory Found"  
        else:
            device_section = Devices(
                    category = webcam.category,
                    brand = webcam.brand,
                    model = webcam.model,
                    serial_number = webcam.serial_number,
                    inventory_number = webcam.inventory_number,
                    delivery_date = webcam.delivery_date,
                    deployment_date = webcam.deployment_date,
                    bos_date = webcam.bos_date,
                    supplier_name = webcam.supplier_name,
                    device_cost = webcam.device_cost,
                    status_id = webcam.status_id,
                    parish_id = webcam.parish_id,
                    ltype_id = webcam.ltype_id,
                    division_id = webcam.division_id,
                    location_id = webcam.location_id,
                    branch_id = webcam.branch_id,
                    added_by = current_user.firstname + " " + current_user.lastname,
            )

            db.add(device_section)
            db.flush()

            comment_section = Comments(
                devices_id = device_section.devices_id,
                comment_value = webcam.comment,
            )

            db.add(comment_section)

            db.commit()
            return {"message": "Webcam Has Been Added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post('/add-other-equipment/')
def add_other_equipment_view(other_equipment: OtherEquipmentRequest, current_user: user_dependency, db: Session=Depends(get_db)):
    try:

        serialExists = db.query(Devices).filter(Devices.serial_number == other_equipment.serial_number).first()
        inventoryExists = db.query(Devices).filter(Devices.inventory_number == other_equipment.inventory_number).first()


        if serialExists:
            return "Serial Found"
        elif inventoryExists:
            return "Inventory Found"  
        else:
            device_section = Devices(
                    category = other_equipment.category,
                    brand = other_equipment.brand,
                    model = other_equipment.model,
                    serial_number = other_equipment.serial_number,
                    inventory_number = other_equipment.inventory_number,
                    delivery_date = other_equipment.delivery_date,
                    deployment_date = other_equipment.deployment_date,
                    bos_date = other_equipment.bos_date,
                    supplier_name = other_equipment.supplier_name,
                    device_cost = other_equipment.device_cost,
                    status_id = other_equipment.status_id,
                    parish_id = other_equipment.parish_id,
                    ltype_id = other_equipment.ltype_id,
                    division_id = other_equipment.division_id,
                    location_id = other_equipment.location_id,
                    branch_id = other_equipment.branch_id,
                    added_by = current_user.firstname + " " + current_user.lastname,
            )

            db.add(device_section)
            db.flush()

            other_equipment_section = OtherEquipments(
                equipment_type = other_equipment.equipment_type,
                
                devices_id = device_section.devices_id,
            )

            db.add(other_equipment_section)

            comment_section = Comments(
                devices_id = device_section.devices_id,
                comment_value = other_equipment.comment,
            )

            db.add(comment_section)

            db.commit()
            db.refresh(other_equipment_section)
            return {"message": "Other Equipment Has Been Added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post('/add-printer/')
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
            bos_date = printer.bos_date,
            supplier_name = printer.supplier_name,
            device_cost = printer.device_cost,
            status_id = printer.status_id,
            parish_id = printer.parish_id,
            ltype_id = printer.ltype_id,
            division_id = printer.division_id,
            location_id = printer.location_id,
            branch_id = printer.branch_id,
            added_by = current_user.firstname + " " + current_user.lastname,
        )

        db.add(device_section)
        db.flush()

        printer_section = Printers(
            return_date = printer.return_date,
            ip_address = printer.ip_address,
            feature_id = printer.feature_id,
            connection_type_id = printer.connection_type_id,
            devices_id = device_section.devices_id,
        )

        db.add(printer_section)

        comment_section = Comments(
                devices_id = device_section.devices_id,
                comment_value = printer.comment,
            )

        db.add(comment_section)

        db.commit()
        db.refresh(printer_section)
        return {"message": "Printer Has Been Added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post('/add-projector/')
def add_projector_view(projector: DeviceRequest, current_user: user_dependency, db: Session=Depends(get_db)):
    try:

        serialExists = db.query(Devices).filter(Devices.serial_number == projector.serial_number).first()
        inventoryExists = db.query(Devices).filter(Devices.inventory_number == projector.inventory_number).first()


        if serialExists:
            return "Serial Found"
        elif inventoryExists:
            return "Inventory Found"  
        else:
            device_section = Devices(
                    category = projector.category,
                    brand = projector.brand,
                    model = projector.model,
                    serial_number = projector.serial_number,
                    inventory_number = projector.inventory_number,
                    delivery_date = projector.delivery_date,
                    deployment_date = projector.deployment_date,
                    bos_date = projector.bos_date,
                    supplier_name = projector.supplier_name,
                    device_cost = projector.device_cost,
                    status_id = projector.status_id,
                    parish_id = projector.parish_id,
                    ltype_id = projector.ltype_id,
                    division_id = projector.division_id,
                    location_id = projector.location_id,
                    branch_id = projector.branch_id,
                    added_by = current_user.firstname + " " + current_user.lastname,
            )

            db.add(device_section)
            db.flush()

            comment_section = Comments(
                devices_id = device_section.devices_id,
                comment_value = projector.comment,
            )

            db.add(comment_section)

            db.commit()
            return {"message": "Projector Has Been Added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post('/add-crav-equipment/')
def add_crav_equipment_view(crav_equipment: CRAVEquipmentRequest, current_user: user_dependency, db: Session=Depends(get_db)):
    try:
        serialExists = db.query(Devices).filter(Devices.serial_number == crav_equipment.serial_number).first()
        inventoryExists = db.query(Devices).filter(Devices.inventory_number == crav_equipment.inventory_number).first()


        if serialExists:
            return "Serial Found"
        elif inventoryExists:
            return "Inventory Found"  
        else:
            device_section = Devices(
            category = crav_equipment.category,
            brand = crav_equipment.brand,
            model = crav_equipment.model,
            serial_number = crav_equipment.serial_number,
            inventory_number = crav_equipment.inventory_number,
            delivery_date = crav_equipment.delivery_date,
            deployment_date = crav_equipment.deployment_date,
            bos_date = crav_equipment.bos_date,
            supplier_name = crav_equipment.supplier_name,
            device_cost = crav_equipment.device_cost,
            status_id = crav_equipment.status_id,
            parish_id = crav_equipment.parish_id,
            ltype_id = crav_equipment.ltype_id,
            division_id = crav_equipment.division_id,
            location_id = crav_equipment.location_id,
            branch_id = crav_equipment.branch_id,
            added_by = current_user.firstname + " " + current_user.lastname,
            )

            db.add(device_section)
            db.flush()

            crav_section = CRAVEquipments(
                name = crav_equipment.name,
                ip_address = crav_equipment.ip_address,
                mac_address = crav_equipment.mac_address,
                meeting_room_id = crav_equipment.meeting_room_id,
                crav_equipment_type_id = crav_equipment.crav_equipment_type_id,
                devices_id = device_section.devices_id,
            )

            db.add(crav_section)

            comment_section = Comments(
                devices_id = device_section.devices_id,
                comment_value = crav_equipment.comment,
            )

            db.add(comment_section)


            db.commit()
            db.refresh(crav_section)
            return {"message": "CRAV Has Been Added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post('/add-network-switch/')
def add_network_switch_view(network_switch: NetworkSwitchRequest, current_user: user_dependency, db: Session=Depends(get_db)):
    try:
        serialExists = db.query(Devices).filter(Devices.serial_number == network_switch.serial_number).first()
        inventoryExists = db.query(Devices).filter(Devices.inventory_number == network_switch.inventory_number).first()


        if serialExists:
            return "Serial Found"
        elif inventoryExists:
            return "Inventory Found"  
        else:
            device_section = Devices(
                category = network_switch.category,
                brand = network_switch.brand,
                model = network_switch.model,
                serial_number = network_switch.serial_number,
                inventory_number = network_switch.inventory_number,
                delivery_date = network_switch.delivery_date,
                deployment_date = network_switch.deployment_date,
                bos_date = network_switch.bos_date,
                supplier_name = network_switch.supplier_name,
                device_cost = network_switch.device_cost,
                status_id = network_switch.status_id,
                parish_id = network_switch.parish_id,
                ltype_id = network_switch.ltype_id,
                division_id = network_switch.division_id,
                location_id = network_switch.location_id,
                branch_id = network_switch.branch_id,
                added_by = current_user.firstname + " " + current_user.lastname,
            )

            db.add(device_section)
            db.flush()

            network_switch_section = NetworkSwitches(
                warranty_start_date = network_switch.warranty_start_date,
                warranty_end_date = network_switch.warranty_end_date,
                return_date = network_switch.return_date,
                mac_address = network_switch.mac_address,
                number_of_ports = network_switch.number_of_ports,
                device_size = network_switch.device_size,
                firmware_type = network_switch.firmware_type,
                firmware_version = network_switch.firmware_version,
                device_name = network_switch.device_name,
                manufactured_date = network_switch.manufactured_date,
                physical_location = network_switch.physical_location,
                devices_id = device_section.devices_id,
            )

            db.add(network_switch_section)

            comment_section = Comments(
                devices_id = device_section.devices_id,
                comment_value = network_switch.comment,
            )

            db.add(comment_section)


            db.commit()
            db.refresh(network_switch_section)
            return {"message": "Network Switch Has Been Added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
 
@app.post('/add-monitor/')
def add_monitor_view(monitor: MonitorRequest, current_user: user_dependency, db: Session=Depends(get_db)):
    try:
        serialExists = db.query(Devices).filter(Devices.serial_number == monitor.serial_number).first()
        inventoryExists = db.query(Devices).filter(Devices.inventory_number == monitor.inventory_number).first()


        if serialExists:
            return "Serial Found"
        elif inventoryExists:
            return "Inventory Found"  
        else:
            device_section = Devices(
                category = monitor.category,
                brand = monitor.brand,
                model = monitor.model,
                serial_number = monitor.serial_number,
                inventory_number = monitor.inventory_number,
                delivery_date = monitor.delivery_date,
                deployment_date = monitor.deployment_date,
                bos_date = monitor.bos_date,
                supplier_name = monitor.supplier_name,
                device_cost = monitor.device_cost,
                status_id = monitor.status_id,
                parish_id = monitor.parish_id,
                ltype_id = monitor.ltype_id,
                division_id = monitor.division_id,
                location_id = monitor.location_id,
                branch_id = monitor.branch_id,
                added_by = current_user.firstname + " " + current_user.lastname,
            )

            db.add(device_section)
            db.flush()

            monitor_section = Monitors(
                warranty_start_date = monitor.warranty_start_date,
                warranty_end_date = monitor.warranty_end_date,
                return_date = monitor.return_date,
                manufactured_date = monitor.manufactured_date,
                monitor_size = monitor.monitor_size,
                monitor_type_id = monitor.monitor_type_id,
                monitor_function_id = monitor.monitor_function_id,

                devices_id = device_section.devices_id,
            )

            db.add(monitor_section)

            comment_section = Comments(
                devices_id = device_section.devices_id,
                comment_value = monitor.comment,
            )

            db.add(comment_section)


            db.commit()
            db.refresh(monitor_section)
            return {"message": "Monitor Switch Has Been Added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e)) 

@app.post("/add-client/", status_code=status.HTTP_201_CREATED)
async def add_client_view(client_model: CreateClientRequest, current_user: user_dependency, db: Session=Depends(get_db)):
    nameExists = db.query(Clients).filter(Clients.firstname == client_model.firstname, Clients.lastname == client_model.lastname).first()
    emailExists = db.query(Clients).filter(Clients.email == client_model.email).first()

    if nameExists or emailExists:
        return "User Found"
    else:
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
    
@app.post('/add-raid-type/')
def add_raid_type_view(raid_type: RaidTypeCreate, current_user: user_dependency, db: Session=Depends(get_db)):
    try:
        new_raid_type = RaidTypes(
            raid_type_description = raid_type.raid_type,
        )

        db.add(new_raid_type)
        db.commit()
        db.refresh(new_raid_type)
        return {"message": "Raid Type Has Been Added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
 
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
    
@app.post('/add-form-factor/')
def add_form_factor_view(form_factor: FormFactorCreate, current_user: user_dependency, db: Session=Depends(get_db)):
    try:
        new_form_factor = FormFactors(
            form_factor_description = form_factor.form_factor,
        )

        db.add(new_form_factor)
        db.commit()
        db.refresh(new_form_factor)
        return {"message": "Form Factor Has Been Added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post('/add-meeting-room/')
def add_meeting_room_view(meeting_room: MeetingRoomCreate, current_user: user_dependency, db: Session=Depends(get_db)):
    try:
        new_meeting_room = MeetingRooms(
            meeting_room_description = meeting_room.meeting_room,
        )

        db.add(new_meeting_room)
        db.commit()
        db.refresh(new_meeting_room)
        return {"message": "Meeting Room Has Been Added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
   
@app.post('/add-monitor-type/')
def add_monitor_type_view(monitor_type: MonitorTypeCreate, current_user: user_dependency, db: Session=Depends(get_db)):
    try:
        new_monitor_type = MonitorTypes(
            monitor_type_description = monitor_type.monitor_type,
        )

        db.add(new_monitor_type)
        db.commit()
        db.refresh(new_monitor_type)
        return {"message": "Monitor Type Has Been Added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post('/add-monitor-function/')
def add_monitor_function_view(monitor_function: MonitorFunctionCreate, current_user: user_dependency, db: Session=Depends(get_db)):
    try:
        new_monitor_function = MonitorFunctions(
            monitor_function_description = monitor_function.monitor_function,
        )

        db.add(new_monitor_function)
        db.commit()
        db.refresh(new_monitor_function)
        return {"message": "Monitor Function Has Been Added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post('/add-bag-type/')
def add_bag_type_view(bag_type: BagTypeCreate, current_user: user_dependency, db: Session=Depends(get_db)):
    try:
        new_bag_type = BagTypes(
            bag_type_description = bag_type.bag_type,
        )

        db.add(new_bag_type)
        db.commit()
        db.refresh(new_bag_type)
        return {"message": "Bag Type Has Been Added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post('/add-bag-fabric-type/')
def add_bag_fabric_type_view(bag_fabric_type: BagFabricTypeCreate, current_user: user_dependency, db: Session=Depends(get_db)):
    try:
        new_bag_fabric_type = BagFabricTypes(
            bag_fabric_type_description = bag_fabric_type.bag_fabric_type,
        )

        db.add(new_bag_fabric_type)
        db.commit()
        db.refresh(new_bag_fabric_type)
        return {"message": "Fabric Type Has Been Added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

######################### SECTION FOR GETTING INFORMATION #######################################
@app.get('/get-items/')
def get_items_view(
    current_user: user_dependency,
    device_type: Optional[str] = None,
    serial_number: Optional[str] = None,
    client: Optional[str] = None,
    status: Optional[str] = None,
    division: Optional[str] = None,
    db: Session=Depends(get_db)
    ):

    query = (
        db.query(
            Devices, 
            SystemStatus.status_description, 
            Divisions.division_name,
            Locations.location_name,
            Parishes.parish_name,
            LocationTypes.ltype_name,
            Branches.branch_name,
            Clients.firstname,
            Clients.lastname,
        )
        .outerjoin(SystemStatus, Devices.status_id == SystemStatus.status_id)
        .outerjoin(Divisions, Devices.division_id == Divisions.division_id)
        .outerjoin(Locations, Devices.location_id == Locations.location_id)
        .outerjoin(Parishes, Devices.parish_id == Parishes.parish_id)
        .outerjoin(LocationTypes, Devices.ltype_id == LocationTypes.ltype_id)
        .outerjoin(Branches, Devices.branch_id == Branches.branch_id)
        .outerjoin(Clients, Devices.client_id == Clients.client_id)
    )

    if device_type:
        query = query.filter(Devices.category.ilike(f"%{device_type}%"))

    if status:
        query = query.filter(SystemStatus.status_description.ilike(f"%{status}%"))

    if division:
        query = query.filter(Divisions.division_name.ilike(f"%{division}%"))

    if serial_number:
        query = query.filter(Devices.serial_number.ilike(f"%{serial_number}%"))
        
    # if filter == "Delivery Date":
    #     parsed_date = datetime.strptime(input, "%Y-%m-%d").date()
    #     query = query.filter(Devices.delivery_date == parsed_date)

    # if filter == "Deployment Date":
    #     parsed_date = datetime.strptime(input, "%Y-%m-%d").date()
    #     query = query.filter(Devices.deployment_date == parsed_date)

    if client:
        query = query.filter(
            or_(
                Clients.firstname.ilike(f"%{client}%"),
                Clients.lastname.ilike(f"%{client}%"),
            )
        )


    rows = query.all()
    result_list = []

    for device, status_description, division_name, location_name, parish_name, ltype_name, branch_name, firstname, lastname in rows:
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
            "status_description": status_description,
            "division_name": division_name,
            "location_name": location_name,
            "parish_name": parish_name,
            "ltype_name": ltype_name,
            "branch_name": branch_name,
            "client_id": device.client_id,
            "client_name": client_name, 
        }
        result_list.append(item)


    return result_list


@app.get('/get-unassigned-items/')
def get__unassigned_items_view(
    current_user: user_dependency, 
    device_type: Optional[str] = None,
    serial_number: Optional[str] = None,
    status: Optional[str] = None,
    division: Optional[str] = None,
    db: Session=Depends(get_db)):

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

    if device_type:
        query = query.filter(Devices.category.ilike(f"%{device_type}%"))

    if status:
        query = query.filter(SystemStatus.status_description.ilike(f"%{status}%"))

    if division:
        query = query.filter(Divisions.division_name.ilike(f"%{division}%"))

    if serial_number:
        query = query.filter(Devices.serial_number.ilike(f"%{serial_number}%"))


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
def get_items_view(
    current_user: user_dependency, 
    device_type: Optional[str] = None,
    serial_number: Optional[str] = None,
    client: Optional[str] = None,
    status: Optional[str] = None,
    division: Optional[str] = None,
    db: Session=Depends(get_db)):

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

    if device_type:
        query = query.filter(Devices.category.ilike(f"%{device_type}%"))

    if status:
        query = query.filter(SystemStatus.status_description.ilike(f"%{status}%"))

    if division:
        query = query.filter(Divisions.division_name.ilike(f"%{division}%"))

    if serial_number:
        query = query.filter(Devices.serial_number.ilike(f"%{serial_number}%"))
        
    # if filter == "Delivery Date":
    #     parsed_date = datetime.strptime(input, "%Y-%m-%d").date()
    #     query = query.filter(Devices.delivery_date == parsed_date)

    # if filter == "Deployment Date":
    #     parsed_date = datetime.strptime(input, "%Y-%m-%d").date()
    #     query = query.filter(Devices.deployment_date == parsed_date)

    if client:
        query = query.filter(
            or_(
                Clients.firstname.ilike(f"%{client}%"),
                Clients.lastname.ilike(f"%{client}%"),
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
                Clients,
                Locations,
                CPUTypes,
                Laptops
            )
            .outerjoin(SystemStatus, Devices.status_id == SystemStatus.status_id)
            .outerjoin(Divisions, Devices.division_id == Divisions.division_id)
            .outerjoin(Clients, Devices.client_id == Clients.client_id)
            .outerjoin(Locations, Devices.location_id == Locations.location_id)
            .outerjoin(Laptops, Devices.devices_id == Laptops.devices_id)
            .outerjoin(CPUTypes, Laptops.cpu_type_id == CPUTypes.cpu_type_id)
            .filter(Devices.serial_number == serial_number)
            .first()
        )

    elif category == "Desktop":

        result = (
            db.query(
                Devices,
                SystemStatus.status_description,
                Divisions.division_name,
                Clients,
                Locations,
                CPUTypes,
                FormFactors,
                Desktops
            )
            .outerjoin(SystemStatus, Devices.status_id == SystemStatus.status_id)
            .outerjoin(Divisions, Devices.division_id == Divisions.division_id)
            .outerjoin(Clients, Devices.client_id == Clients.client_id)
            .outerjoin(Locations, Devices.location_id == Locations.location_id)
            .outerjoin(Desktops, Devices.devices_id == Desktops.devices_id)
            .outerjoin(CPUTypes, Desktops.cpu_type_id == CPUTypes.cpu_type_id)
            .outerjoin(FormFactors, Desktops.form_factor_id == FormFactors.form_factor_id)
            .filter(Devices.serial_number == serial_number)
            .first()
        )

    elif category == "Server":

        result = (
            db.query(
                Devices,
                SystemStatus.status_description,
                Divisions.division_name,
                Clients,
                Locations,
                CPUTypes,
                FormFactors,
                RaidTypes,
                Servers
            )
            .outerjoin(SystemStatus, Devices.status_id == SystemStatus.status_id)
            .outerjoin(Divisions, Devices.division_id == Divisions.division_id)
            .outerjoin(Clients, Devices.client_id == Clients.client_id)
            .outerjoin(Locations, Devices.location_id == Locations.location_id)
            .outerjoin(Servers, Devices.devices_id == Servers.devices_id)
            .outerjoin(CPUTypes, Servers.cpu_type_id == CPUTypes.cpu_type_id)
            .outerjoin(FormFactors, Servers.form_factor_id == FormFactors.form_factor_id)
            .outerjoin(RaidTypes, Servers.raid_type_id == RaidTypes.raid_type_id)
            .filter(Devices.serial_number == serial_number)
            .first()
        )

    elif category == "Tablet":
        result = (
            db.query(
                Devices,
                SystemStatus.status_description,
                Divisions.division_name,
                Clients,
                Locations,
                Tablets,
                Bags,
                Adapters,
                BagTypes,
                BagFabricTypes,
            )
            .outerjoin(SystemStatus, Devices.status_id == SystemStatus.status_id)
            .outerjoin(Divisions, Devices.division_id == Divisions.division_id)
            .outerjoin(Clients, Devices.client_id == Clients.client_id)
            .outerjoin(Locations, Devices.location_id == Locations.location_id)
            .outerjoin(Tablets, Devices.devices_id == Tablets.devices_id)
            .outerjoin(Bags, Devices.devices_id == Bags.devices_id)
            .outerjoin(Adapters, Devices.devices_id == Adapters.devices_id)
            .outerjoin(BagTypes, Bags.bag_type_id == BagTypes.bag_type_id)
            .outerjoin(BagFabricTypes, Bags.bag_fabric_type_id == BagFabricTypes.bag_fabric_type_id)
            .filter(Devices.serial_number == serial_number)
            .first()
        )


    elif (category == "Mouse") or (category == "Keyboard"):
        result = (
            db.query(
                Devices,
                SystemStatus.status_description,
                Divisions.division_name,
                Clients,
                Locations,
                ConnectionTypes,
                MouseKeyboards
            )
            .outerjoin(SystemStatus, Devices.status_id == SystemStatus.status_id)
            .outerjoin(Divisions, Devices.division_id == Divisions.division_id)
            .outerjoin(Clients, Devices.client_id == Clients.client_id)
            .outerjoin(Locations, Devices.location_id == Locations.location_id)
            .outerjoin(MouseKeyboards, Devices.devices_id == MouseKeyboards.devices_id)
            .outerjoin(ConnectionTypes, MouseKeyboards.connection_type_id == ConnectionTypes.ctype_id)
            .filter(Devices.serial_number == serial_number)
            .first()
        )

    elif (category == "Scanner"):
        result = (
            db.query(
                Devices,
                SystemStatus.status_description,
                Divisions.division_name,
                Clients,
                Locations,
                ConnectionTypes,
                Scanners
            )
            .outerjoin(SystemStatus, Devices.status_id == SystemStatus.status_id)
            .outerjoin(Divisions, Devices.division_id == Divisions.division_id)
            .outerjoin(Clients, Devices.client_id == Clients.client_id)
            .outerjoin(Locations, Devices.location_id == Locations.location_id)
            .outerjoin(Scanners, Devices.devices_id == Scanners.devices_id)
            .outerjoin(ConnectionTypes, Scanners.connection_type_id == ConnectionTypes.ctype_id)
            .filter(Devices.serial_number == serial_number)
            .first()
        )

    elif (category == "Surge Protector"):
        result = (
            db.query(
                Devices,
                SystemStatus.status_description,
                Divisions.division_name,
                Clients,
                Locations,
                SurgeProtectors
            )
            .outerjoin(SystemStatus, Devices.status_id == SystemStatus.status_id)
            .outerjoin(Divisions, Devices.division_id == Divisions.division_id)
            .outerjoin(Clients, Devices.client_id == Clients.client_id)
            .outerjoin(Locations, Devices.location_id == Locations.location_id)
            .outerjoin(SurgeProtectors, Devices.devices_id == SurgeProtectors.devices_id)
            .filter(Devices.serial_number == serial_number)
            .first()
        )

    elif (category == "UPS"):
        result = (
            db.query(
                Devices,
                SystemStatus.status_description,
                Divisions.division_name,
                Clients,
                Locations,
                UPS
            )
            .outerjoin(SystemStatus, Devices.status_id == SystemStatus.status_id)
            .outerjoin(Divisions, Devices.division_id == Divisions.division_id)
            .outerjoin(Clients, Devices.client_id == Clients.client_id)
            .outerjoin(Locations, Devices.location_id == Locations.location_id)
            .outerjoin(UPS, Devices.devices_id == UPS.devices_id)
            .filter(Devices.serial_number == serial_number)
            .first()
        )

    elif (category == "Speaker"):
        result = (
            db.query(
                Devices,
                SystemStatus.status_description,
                Divisions.division_name,
                Clients,
                Locations,
                SpeakerTypes,
                Speakers
            )
            .outerjoin(SystemStatus, Devices.status_id == SystemStatus.status_id)
            .outerjoin(Divisions, Devices.division_id == Divisions.division_id)
            .outerjoin(Clients, Devices.client_id == Clients.client_id)
            .outerjoin(Locations, Devices.location_id == Locations.location_id)
            .outerjoin(Speakers, Devices.devices_id == Speakers.devices_id)
            .outerjoin(SpeakerTypes, Speakers.speaker_type_id == SpeakerTypes.speaker_type_id)
            .filter(Devices.serial_number == serial_number)
            .first()
        )

    elif (category == "Webcam"):
        result = (
            db.query(
                Devices,
                SystemStatus.status_description,
                Divisions.division_name,
                Clients,
                Locations,
            )
            .outerjoin(SystemStatus, Devices.status_id == SystemStatus.status_id)
            .outerjoin(Divisions, Devices.division_id == Divisions.division_id)
            .outerjoin(Clients, Devices.client_id == Clients.client_id)
            .outerjoin(Locations, Devices.location_id == Locations.location_id)
            .filter(Devices.serial_number == serial_number)
            .first()
        )

    elif (category == "Other Equipment"):
        result = (
            db.query(
                Devices,
                SystemStatus.status_description,
                Divisions.division_name,
                Clients,
                Locations,
                OtherEquipments
            )
            .outerjoin(SystemStatus, Devices.status_id == SystemStatus.status_id)
            .outerjoin(Divisions, Devices.division_id == Divisions.division_id)
            .outerjoin(Clients, Devices.client_id == Clients.client_id)
            .outerjoin(Locations, Devices.location_id == Locations.location_id)
            .outerjoin(OtherEquipments, Devices.devices_id == OtherEquipments.devices_id)
            .filter(Devices.serial_number == serial_number)
            .first()
        )
        
    elif category == "Printer":
        result = (
            db.query(
                Devices,
                SystemStatus.status_description,
                Divisions.division_name,
                Clients,
                Locations,
                ConnectionTypes,
                PrinterFeatures,
                Printers
            )
            .outerjoin(SystemStatus, Devices.status_id == SystemStatus.status_id)
            .outerjoin(Divisions, Devices.division_id == Divisions.division_id)
            .outerjoin(Clients, Devices.client_id == Clients.client_id)
            .outerjoin(Locations, Devices.location_id == Locations.location_id)
            .outerjoin(Printers, Devices.devices_id == Printers.devices_id)
            .outerjoin(ConnectionTypes, Printers.connection_type_id == ConnectionTypes.ctype_id)
            .outerjoin(PrinterFeatures, Printers.feature_id == PrinterFeatures.feature_id)
            .filter(Devices.serial_number == serial_number)
            .first()
        )

    elif (category == "Projector"):
        result = (
            db.query(
                Devices,
                SystemStatus.status_description,
                Divisions.division_name,
                Clients,
                Locations,
            )
            .outerjoin(SystemStatus, Devices.status_id == SystemStatus.status_id)
            .outerjoin(Divisions, Devices.division_id == Divisions.division_id)
            .outerjoin(Clients, Devices.client_id == Clients.client_id)
            .outerjoin(Locations, Devices.location_id == Locations.location_id)
            .filter(Devices.serial_number == serial_number)
            .first()
        )
        
    elif category == "CRAV":
        result = (
            db.query(
                Devices,
                SystemStatus.status_description,
                Divisions.division_name,
                Clients,
                Locations,
                MeetingRooms,
                CRAVEquipmentTypes,
                CRAVEquipments
            )
            .outerjoin(SystemStatus, Devices.status_id == SystemStatus.status_id)
            .outerjoin(Divisions, Devices.division_id == Divisions.division_id)
            .outerjoin(Clients, Devices.client_id == Clients.client_id)
            .outerjoin(Locations, Devices.location_id == Locations.location_id)
            .outerjoin(CRAVEquipments, Devices.devices_id == CRAVEquipments.devices_id)
            .outerjoin(MeetingRooms, CRAVEquipments.meeting_room_id == MeetingRooms.meeting_room_id)
            .outerjoin(CRAVEquipmentTypes, CRAVEquipments.crav_equipment_type_id == CRAVEquipmentTypes.crav_equipment_type_id)
            .filter(Devices.serial_number == serial_number)
            .first()
        )
    
    elif category == "Network Switch":
        result = (
            db.query(
                Devices,
                SystemStatus.status_description,
                Divisions.division_name,
                Clients,
                Locations,
                NetworkSwitches
            )
            .outerjoin(SystemStatus, Devices.status_id == SystemStatus.status_id)
            .outerjoin(Divisions, Devices.division_id == Divisions.division_id)
            .outerjoin(Clients, Devices.client_id == Clients.client_id)
            .outerjoin(Locations, Devices.location_id == Locations.location_id)
            .outerjoin(NetworkSwitches, Devices.devices_id == NetworkSwitches.devices_id)
            .filter(Devices.serial_number == serial_number)
            .first()
        )

    elif category == "Monitor":
        result = (
            db.query(
                Devices,
                SystemStatus.status_description,
                Divisions.division_name,
                Clients,
                Locations,
                MonitorTypes,
                MonitorFunctions,
                Monitors
            )
            .outerjoin(SystemStatus, Devices.status_id == SystemStatus.status_id)
            .outerjoin(Divisions, Devices.division_id == Divisions.division_id)
            .outerjoin(Clients, Devices.client_id == Clients.client_id)
            .outerjoin(Locations, Devices.location_id == Locations.location_id)
            .outerjoin(Monitors, Devices.devices_id == Monitors.devices_id)
            .outerjoin(MonitorTypes, Monitors.monitor_type_id == MonitorTypes.monitor_type_id)
            .outerjoin(MonitorFunctions, Monitors.monitor_function_id == MonitorFunctions.monitor_function_id)
            .filter(Devices.serial_number == serial_number)
            .first()
        )
        
    else:
        result = (
            db.query(
                Devices,
                SystemStatus.status_description,
                Divisions.division_name,
                Clients,
                Locations
            )
            .outerjoin(SystemStatus, Devices.status_id == SystemStatus.status_id)
            .outerjoin(Divisions, Devices.division_id == Divisions.division_id)
            .outerjoin(Clients, Devices.client_id == Clients.client_id)
            .outerjoin(Locations, Devices.location_id == Locations.location_id)
            .filter(Devices.serial_number == serial_number)
            .first()
        )

    if result:
        if (category == "Laptop"):
            device, status_description, division_name, client, location, cpu_type, laptop = result

        elif (category == "Desktop"):
            device, status_description, division_name, client, location, cpu_type, form_factor, desktop = result

        elif (category == "Server"):
            device, status_description, division_name, client, location, cpu_type, form_factor, raid_type, server = result

        elif category == "Tablet":
            device, status_description, division_name, client, location, tablet, bag, adapter, bag_type, bag_fabric_type = result

        elif (category == "Mouse") or (category == "Keyboard"):
            device, status_description, division_name, client, location, connection_type, mouse_keyboard = result

        elif (category == "Scanner"):
            device, status_description, division_name, client, location, connection_type, scanner = result
        
        elif (category == "Surge Protector"):
            device, status_description, division_name, client, location, surge_protector = result

        elif (category == "UPS"):
            device, status_description, division_name, client, location, ups = result

        elif (category == "Speaker"):
            device, status_description, division_name, client, location, speaker_type, speaker = result

        elif (category == "Other Equipment"):
            device, status_description, division_name, client, location, other_equipment = result

        elif category == "Printer":
            device, status_description, division_name, client, location, connection_type, printer_feature, printer = result

        elif category == "CRAV":
            device, status_description, division_name, client, location, meeting_room, equipment_type, crav = result

        elif category == "Network Switch":
            device, status_description, division_name, client, location, network_switch = result

        elif category == "Monitor":
            device, status_description, division_name, client, location, monitor_types, monitor_functions, monitor = result

        else:
            device, status_description, division_name, client, location = result

        device_item = {
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
            "status_description": status_description if status_description else None,
            "division_name": division_name if division_name else None,
            "client_name": client.firstname + " " + client.lastname if client else None,
            "added_by": device.added_by,
            "last_updated_by": device.last_updated_by,
            "repaired_date": device.repaired_date,
            "bos_date": device.bos_date,
            "bos_by": device.bos_by,
            "deployed_by": device.deployed_by,
            "assigned_on": device.assigned_on,
            "unassigned_on": device.unassigned_on,
            "supplier_name": device.supplier_name,
            "device_cost": device.device_cost,
        }

        if (category == "Laptop"):
            device_item.update({
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
                "manufactured_date": laptop.manufactured_date,
                "memory_type": laptop.memory_type,
                "cpu_type": cpu_type.cpu_type_description if cpu_type else None,

            })

        elif (category == "Desktop"):
            device_item.update({
                "hard_disk_capacity": desktop.hard_disk_capacity,
                "memory_capacity": desktop.memory_capacity,
                "processor_speed": desktop.processor_speed,
                "processor_type": desktop.processor_type,
                "computer_name": desktop.computer_name,
                "mac_address": desktop.mac_address,
                "operating_system": desktop.operating_system,
                "microsoft_office_version": desktop.microsoft_office_version,
                "antivirus": desktop.antivirus,
                "pdf_reader": desktop.pdf_reader,
                "warranty_start_date": desktop.warranty_start_date,
                "warranty_end_date": desktop.warranty_end_date,
                "return_date": desktop.return_date,
                "manufactured_date": desktop.manufactured_date,
                "memory_type": desktop.memory_type,
                "cpu_type": cpu_type.cpu_type_description if cpu_type else None,
                "form_factor": form_factor.form_factor_description if form_factor else None
            })

        elif (category == "Server"):
            device_item.update({
                "hard_disk_capacity": server.hard_disk_capacity,
                "memory_capacity": server.memory_capacity,
                "processor_speed": server.processor_speed,
                "processor_type": server.processor_type,
                "computer_name": server.computer_name,
                "mac_address": server.mac_address,
                "operating_system": server.operating_system,
                "microsoft_office_version": server.microsoft_office_version,
                "antivirus": server.antivirus,
                "pdf_reader": server.pdf_reader,
                "warranty_start_date": server.warranty_start_date,
                "warranty_end_date": server.warranty_end_date,
                "return_date": server.return_date,
                "manufactured_date": server.manufactured_date,
                "memory_type": server.memory_type,
                "cpu_type": cpu_type.cpu_type_description if cpu_type else None,
                "form_factor": form_factor.form_factor_description if form_factor else None,
                "raid_type": raid_type.raid_type_description if raid_type else None
            })

        elif (category == "Tablet"):
            device_item.update({
                "hard_disk_capacity": tablet.hard_disk_capacity,
                "memory_capacity": tablet.memory_capacity,
                "operating_system": tablet.operating_system,
                "warranty_start_date": tablet.warranty_start_date,
                "warranty_end_date": tablet.warranty_end_date,
                "return_date": tablet.return_date,
                "imei_number": tablet.imei_number,
                "version": tablet.version,
                "device_size": tablet.device_size,

                "bag_id": bag.bag_id if bag else None,
                "bag_brand": bag.bag_brand if bag else None,
                "bag_model": bag.bag_model if bag else None,
                "bag_ministry_number": bag.bag_ministry_number if bag else None,
                "bag_delivery_date": bag.bag_delivery_date if bag else None,
                "bag_assignment_date": bag.bag_assignment_date if bag else None,
                "bag_bos_date": bag.bag_bos_date if bag else None,
                "bag_type": bag_type.bag_type_description if bag_type else None,
                "bag_fabric_type": bag_fabric_type.bag_fabric_type_description if bag_fabric_type else None,

                "adapter_id": adapter.adapter_id if adapter else None,
                "adapter_serial_number": adapter.adapter_serial_number if adapter else None,
                "adapter_brand": adapter.adapter_brand if adapter else None,
                "adapter_model": adapter.adapter_model if adapter else None,
                "adapter_ministry_number": adapter.adapter_ministry_number if adapter else None,
                "adapter_delivery_date": adapter.adapter_delivery_date if adapter else None,
                "adapter_assignment_date": adapter.adapter_assignment_date if adapter else None,
                "adapter_bos_date": adapter.adapter_bos_date if adapter else None,
            })

        elif (category == "Mouse") or (category == "Keyboard") or (category == "Scanner"):
            device_item.update({
                "connection_type": connection_type.ctype_description
            })

        elif (category == "Surge Protector"):
            device_item.update({
                "number_of_outlets": surge_protector.number_of_outlets
            })

        elif (category == "UPS"):
            device_item.update({
                "number_of_outlets": ups.number_of_outlets,
                "return_date": ups.return_date
            })

        elif (category == "Speaker"):
            device_item.update({
                "return_date": speaker.return_date,
                "number_of_speakers": speaker.number_of_speakers,
                "speaker_type": speaker_type.speaker_type_description
            })

        elif (category == "Other Equipment"):
            device_item.update({
                "equipment_type": other_equipment.equipment_type,
            })

        elif (category == "Printer"):
            device_item.update({
                "ip_address": printer.ip_address,
                "feature": printer_feature.feature_description,
                "connection_type": connection_type.ctype_description,
                "return_date": printer.return_date
            })

        elif (category == "CRAV"):
            device_item.update({
                "name": crav.name,
                "ip_address": crav.ip_address,
                "mac_address": crav.mac_address,
                "meeting_room": meeting_room.meeting_room_description,
                "equipment_type": equipment_type.crav_equipment_type_description,
            })

        elif (category == "Network Switch"):
            device_item.update({
                "warranty_start_date": network_switch.warranty_start_date,
                "warranty_end_date": network_switch.warranty_end_date,
                "return_date": network_switch.return_date,
                "mac_address": network_switch.mac_address,
                "device_size": network_switch.device_size,
                "firmware_type": network_switch.firmware_type,
                "firmware_version": network_switch.firmware_version,
                "device_name": network_switch.device_name,
                "manufactured_date": network_switch.manufactured_date,
                "physical_location": network_switch.physical_location
            })

        elif (category == "Monitor"):
            device_item.update({
                "warranty_start_date": monitor.warranty_start_date,
                "warranty_end_date": monitor.warranty_end_date,
                "return_date": monitor.return_date,
                
                "manufactured_date": monitor.manufactured_date,
                "monitor_size": monitor.monitor_size,
                "monitor_type": monitor_types.monitor_type_description,
                "monitor_function": monitor_functions.monitor_function_description
            })
        
        return device_item
    
    else:
        return {"message": "Category not supported"}

@app.get('/get-clients/')
def get_client_view(current_user: user_dependency, name: Optional[str] = None, db: Session=Depends(get_db)):

    if name:
        search = f"%{name.strip()}%"
        query = db.query(Clients).filter((Clients.firstname + " " + Clients.lastname).ilike(search)).all()
        return query
    else:
        return db.query(Clients).all()

@app.get('/get-client/')
def get_client_view(current_user: user_dependency, firstname: str, lastname: str, db: Session=Depends(get_db)):

    isClient = db.query(Clients).filter(Clients.firstname == firstname, Clients.lastname == lastname).all()

    if isClient:
        return True
    else:
        return False

@app.get('/get-roles/')
def get_roles_view(current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(Roles).all()

@app.get('/get-users/')
def get_client_view(current_user: user_dependency, name: Optional[str] = None, db: Session=Depends(get_db)):

    if name:
        search = f"%{name.strip()}%"
        query = db.query(Users).filter((Users.firstname + " " + Users.lastname).ilike(search)).all()
        return query
    else:
        return db.query(Users).all()
    
@app.get('/get-statuses/', status_code=status.HTTP_200_OK)
def get_statuses_view(current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(SystemStatus).all()


@app.get('/get-status/')
def get_status_view(status: str, current_user: user_dependency, db: Session=Depends(get_db)):
    isStatus = db.query(SystemStatus).filter(SystemStatus.status_description == status).all()

    if isStatus:
        return True
    else:
        return False

@app.get('/get-cpu-types/')
def get_cpu_types_view(current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(CPUTypes).all()

@app.get('/get-cpu-type/')
def get_cpu_type_view(cpu_type: str, current_user: user_dependency, db: Session=Depends(get_db)):
    isCpuType = db.query(CPUTypes).filter(CPUTypes.cpu_type_description == cpu_type).all()

    if isCpuType:
        return True
    else:
        return False

@app.get('/get-connection-types/')
def get_connection_types_view(current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(ConnectionTypes).all()

@app.get('/get-connection-type/')
def get_connection_type_view(connection_type: str, current_user: user_dependency, db: Session=Depends(get_db)):
    isConnectionType = db.query(ConnectionTypes).filter(ConnectionTypes.ctype_description == connection_type).all()

    if isConnectionType:
        return True
    else:
        return False

@app.get('/get-printer-features/')
def get_printer_features_view(current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(PrinterFeatures).all()

@app.get('/get-printer-feature/')
def get_printer_feature_view(printer_feature: str, current_user: user_dependency, db: Session=Depends(get_db)):
    isPrinterFeature = db.query(PrinterFeatures).filter(PrinterFeatures.feature_description == printer_feature).all()

    if isPrinterFeature:
        return True
    else:
        return False
    
@app.get('/get-form-factors/')
def get_form_factors_view(current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(FormFactors).all()

@app.get('/get-form-factor/')
def get_form_factor_view(form_factor: str, current_user: user_dependency, db: Session=Depends(get_db)):
    isFormFactor = db.query(FormFactors).filter(FormFactors.form_factor_description == form_factor).all()

    if isFormFactor:
        return True
    else:
        return False

@app.get('/get-raid-types/')
def get_raid_types_view(current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(RaidTypes).all()

@app.get('/get-raid-type/')
def get_raid_type_view(raid_type: str, current_user: user_dependency, db: Session=Depends(get_db)):
    isRaidType = db.query(RaidTypes).filter(RaidTypes.raid_type_description == raid_type).all()

    if isRaidType:
        return True
    else:
        return False

@app.get('/get-speaker-types/')
def get_speaker_types_view(current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(SpeakerTypes).all()

@app.get('/get-meeting-rooms/')
def get_meeting_rooms_view(current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(MeetingRooms).all()

@app.get('/get-meeting-room/')
def get_meeting_room_view(meeting_room: str, current_user: user_dependency, db: Session=Depends(get_db)):
    isMeetingRoom = db.query(MeetingRooms).filter(MeetingRooms.meeting_room_description == meeting_room).all()

    if isMeetingRoom:
        return True
    else:
        return False

@app.get('/get-crav-equipment-types/')
def get_crav_equipment_types_view(current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(CRAVEquipmentTypes).all()

@app.get('/get-monitor-types/')
def get_monitor_types_view(current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(MonitorTypes).all()

@app.get('/get-monitor-type/')
def get_monitor_type_view(monitor_type: str, current_user: user_dependency, db: Session=Depends(get_db)):
    isMonitorType = db.query(MonitorTypes).filter(MonitorTypes.monitor_type_description == monitor_type).all()

    if isMonitorType:
        return True
    else:
        return False

@app.get('/get-monitor-functions/')
def get_monitor_functions_view(current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(MonitorFunctions).all()

@app.get('/get-monitor-function/')
def get_monitor_function_view(monitor_function: str, current_user: user_dependency, db: Session=Depends(get_db)):
    isMonitorFunction = db.query(MonitorFunctions).filter(MonitorFunctions.monitor_function_description == monitor_function).all()

    if isMonitorFunction:
        return True
    else:
        return False
    
@app.get('/get-bag-types/')
def get_bag_types_view(current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(BagTypes).all()

@app.get('/get-bag-type/')
def get_bag_type_view(bag_type: str, current_user: user_dependency, db: Session=Depends(get_db)):
    isBagType = db.query(BagTypes).filter(BagTypes.bag_type_description == bag_type).all()

    if isBagType:
        return True
    else:
        return False

@app.get('/get-bag-fabric-types/')
def get_bag_fabric_types_view(current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(BagFabricTypes).all()

@app.get('/get-bag-fabric-type/')
def get_bag_fabric_type_view(bag_fabric_type: str, current_user: user_dependency, db: Session=Depends(get_db)):
    isBagFabricType = db.query(BagFabricTypes).filter(BagFabricTypes.bag_fabric_type_description == bag_fabric_type).all()

    if isBagFabricType:
        return True
    else:
        return False

@app.get('/get-divisions/')
def get_divisions_view(current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(Divisions).all()

@app.get('/get-branches/')
def get_divisions_view(current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(Branches).all()

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

@app.get('/get-division-branches/')
def get_parish_locations_view(current_user: user_dependency, db: Session=Depends(get_db), division_id: Optional[int] = None):

    if division_id:
        branches = (
            db.query(Branches)
            .join(Divisions, Divisions.division_id == Branches.division_id)
            .filter(Divisions.division_id == division_id)
            .all()
        )
    else:
        branches = (
            db.query(Branches).all()
        )

    return branches

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

@app.get('/get-comments/')
def get_comments_view(current_user: user_dependency, devices_id: int, db: Session=Depends(get_db)):
    return db.query(Comments).filter(Comments.devices_id == devices_id).order_by(desc(Comments.comment_id)).all()

@app.get('/get-location-names/')
def get_location_names_view(current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(Locations).all()

@app.get("/get-all-locations/")
def get_all_locations(db: Session = Depends(get_db)):

    try:
        data = (
            db.query(
                Locations.location_name,
                Devices.category,
                func.count(Devices.devices_id).label("count")
            )
            .join(DivisionLocation, DivisionLocation.location_id == Locations.location_id)
            .join(Divisions, Divisions.division_id == DivisionLocation.division_id)
            .join(Devices, Devices.division_id == Divisions.division_id)
            .group_by(Locations.location_name, Devices.category)
            .all()
        )

        result_map = {}

        for location_name, category, count in data:
            if location_name not in result_map:
                result_map[location_name] = []

            result_map[location_name].append({
                "category": category,
                "count": count
            })

        return [
            {
                "location_name": loc,
                "category_counts": counts
            }
            for loc, counts in result_map.items()
        ]

    except Exception as e:
        print(f"Error fetching location data: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving location data.")

@app.get('/get-parish-names/')
def get_parish_names_view(current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(Parishes).all()

@app.get('/get-items-delivery-date/')
def get_items_delivery_date_view(delivery_date: date, current_user: user_dependency, db: Session=Depends(get_db)):
    return db.query(Devices).filter(Devices.delivery_date > delivery_date).all()



######################### SECTION FOR DELETING INFORMATION #######################################
@app.delete('/delete-item/')
def delete_item_view(current_user: user_dependency, serial_number: str, db: Session=Depends(get_db)):
    deleted = db.query(Devices).filter(Devices.serial_number == serial_number).first()

    if not deleted:
        raise HTTPException(status_code=404, detail="Device not found")
    
    db.delete(deleted)
    db.commit()
    
    return {"message": "Device has been deleted"}

@app.delete('/delete-client/')
def delete_client_view(email: str, current_user: user_dependency, db: Session=Depends(get_db)):

    deleted = db.query(Clients).filter(Clients.email == email).first()

    if deleted:
        db.delete(deleted)
        db.commit()
        return {"message": "Client has been deleted"}
    else:
        return "Client Not Found"

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

@app.delete('/delete-cpu-type/')
def delete_status_view(cpu_type: str, current_user: user_dependency, db: Session=Depends(get_db)):
    deleted = db.query(CPUTypes).filter(CPUTypes.cpu_type_description == cpu_type).delete()
    db.commit()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="CPU Type not found")
    
    return {"message": "Cpu Type has been deleted"}

@app.delete('/delete-raid-type/')
def delete_raid_view(raid_type: str, current_user: user_dependency, db: Session=Depends(get_db)):
    deleted = db.query(RaidTypes).filter(RaidTypes.raid_type_description == raid_type).delete()
    db.commit()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Raid Type not found")
    
    return {"message": "Raid Type has been deleted"}

@app.delete('/delete-connection-type/')
def delete_connection_type_view(current_user: user_dependency, ctype: str, db: Session=Depends(get_db)):
    deleted = db.query(ConnectionTypes).filter(ConnectionTypes.ctype_description == ctype).delete()
    db.commit()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Connection Type not found")
    
    return {"message": "Connection Type has been deleted"}

@app.delete('/delete-printer-feature/')
def delete_printer_feature_view(current_user: user_dependency, printer_feature: str, db: Session=Depends(get_db)):
    deleted = db.query(PrinterFeatures).filter(PrinterFeatures.feature_description == printer_feature).delete()
    db.commit()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Printer Feature not found")
    
    return {"message": "Printer Feature has been deleted"}

@app.delete('/delete-form-factor/')
def delete_form_factor_view(form_factor: str, current_user: user_dependency, db: Session=Depends(get_db)):      
    deleted = db.query(FormFactors).filter(FormFactors.form_factor_description == form_factor).delete()
    db.commit()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Form Factor not found")
    
    return {"message": "Form Factor has been deleted"}

@app.delete('/delete-meeting-room/')
def delete_meeting_room_view(meeting_room: str, current_user: user_dependency, db: Session=Depends(get_db)):      
    deleted = db.query(MeetingRooms).filter(MeetingRooms.meeting_room_description == meeting_room).delete()
    db.commit()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Meeting Room not found")
    
    return {"message": "Meeting Room has been deleted"}

@app.delete('/delete-monitor-type/')
def delete_monitor_type_view(monitor_type: str, current_user: user_dependency, db: Session=Depends(get_db)):      
    deleted = db.query(MonitorTypes).filter(MonitorTypes.monitor_type_description == monitor_type).delete()
    db.commit()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Monitor Type not found")
    
    return {"message": "Monitor Type has been deleted"}

@app.delete('/delete-monitor-function/')
def delete_monitor_function_view(monitor_function: str, current_user: user_dependency, db: Session=Depends(get_db)):      
    deleted = db.query(MonitorFunctions).filter(MonitorFunctions.monitor_function_description == monitor_function).delete()
    db.commit()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Monitor Function not found")
    
@app.delete('/delete-bag-type/')
def delete_bag_type_view(bag_type: str, current_user: user_dependency, db: Session=Depends(get_db)):      
    deleted = db.query(BagTypes).filter(BagTypes.bag_type_description == bag_type).delete()
    db.commit()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Bag Type not found")
    
    return {"message": "Bag Type has been deleted"}

@app.delete('/delete-bag-fabric-type/')
def delete_bag_fabric_type_view(bag_fabric_type: str, current_user: user_dependency, db: Session=Depends(get_db)):      
    deleted = db.query(BagFabricTypes).filter(BagFabricTypes.bag_fabric_type_description == bag_fabric_type).delete()
    db.commit()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Fabric Type not found")
    
    return {"message": "Fabric Type has been deleted"}

@app.delete('/delete-comment/')
def delete_comments_view(current_user: user_dependency, id: int, db: Session=Depends(get_db)):
    deleted = db.query(Comments).filter(Comments.comment_id == id).delete()
    db.commit()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return {"message": "comment has been deleted"}




######################### SECTION FOR OTHER INFORMATION #######################################
@app.put('/assign-device/')
def assign_device_view(current_user: user_dependency, device_sn: str, client_id: int, db: Session=Depends(get_db)):
    device = db.query(Devices).filter(Devices.serial_number == device_sn).first()
    client = db.query(Clients).filter(Clients.client_id == client_id).first()

    if client:
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
    else:
        return {"message": "Client Not Found", "item_id": device.devices_id, "client": client_id}


@app.post('/unassign-item/')
def delete_item_view(current_user: user_dependency, serial_number: str, db: Session=Depends(get_db)):
    device = db.query(Devices).filter(Devices.serial_number == serial_number).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    device.client_id = None
    db.commit()

    return {"message": "Device has been unassigned from the client"}


@app.get("/filter-deployment-date/")
def filter_deployment_date(
    year: Optional[int] = None,
    month: Optional[int] = None,
    quarter: Optional[int] = None,
    current_user: user_dependency = None,
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
            Devices.deployment_date,
            Divisions.division_name,
            SystemStatus.status_description,
        )
        .join(Divisions, Devices.division_id == Divisions.division_id)
        .join(SystemStatus, Devices.status_id == SystemStatus.status_id)
    )

    if year is not None:
        query = query.filter(
            extract("year", Devices.deployment_date) == year
        )

    if month is not None:
        query = query.filter(
            extract("month", Devices.deployment_date) == month
        )

    if quarter is not None:
        query = query.filter(
            extract("quarter", Devices.delivery_date) == quarter
        )

    # Execute the query
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
            Parishes.parish_name,
        )
        .join(SystemStatus, Devices.status_id == SystemStatus.status_id, isouter=True)
        .join(Divisions, Devices.division_id == Divisions.division_id, isouter=True)
        .join(DivisionLocation, DivisionLocation.division_id == Divisions.division_id, isouter=True)
        .join(Locations, Locations.location_id == DivisionLocation.location_id, isouter=True)
        .join(Parishes, Locations.parish_id == Parishes.parish_id, isouter=True)
    )

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
            "parish_name": r.parish_name,
        }
        for r in results
    ]

@app.get("/filter-delivery-date/")
def filter_delivery_date(
    year: Optional[int] = None,
    month: Optional[int] = None,
    quarter: Optional[int] = None,
    current_user: user_dependency = None,
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
            Divisions.division_name,
            SystemStatus.status_description,
        )
        .join(Divisions, Devices.division_id == Divisions.division_id)
        .join(SystemStatus, Devices.status_id == SystemStatus.status_id)
    )

    if year is not None:
        query = query.filter(
            extract("year", Devices.delivery_date) == year
        )

    if month is not None:
        query = query.filter(
            extract("month", Devices.delivery_date) == month
        )

    if quarter is not None:
        query = query.filter(
            extract("quarter", Devices.delivery_date) == quarter
        )

    # Execute the query
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
    
@app.post("/update-device/")
async def update_device(new_device: UpdatePackage, current_user: user_dependency, db: Session=Depends(get_db)):
    device = db.query(Devices).filter(Devices.serial_number == new_device.serial_number).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    update_data = new_device.dict(exclude_unset=True)

    for field, value in update_data.items():
        if hasattr(device, field) and value is not None:
            setattr(device, field, value)
    


    device2 = None

    if device.category == "Laptop":
        device2 = db.query(Laptops).filter(Laptops.devices_id == device.devices_id).first()

    elif device.category == "Desktop":
        device2 = db.query(Desktops).filter(Desktops.devices_id == device.devices_id).first()

    elif device.category == "Server":
        device2 = db.query(Servers).filter(Servers.devices_id == device.devices_id).first()

    elif device.category == "Tablet":
        device2 = db.query(Tablets).filter(Tablets.devices_id == device.devices_id).first()

    elif device.category == "Mouse" or device.category == "Keyboard":
        device2 = db.query(MouseKeyboards).filter(MouseKeyboards.devices_id == device.devices_id).first()

    elif device.category == "Scanner":
        device2 = db.query(Scanners).filter(Scanners.devices_id == device.devices_id).first()

    elif device.category == "Surge Protector":
        device2 = db.query(SurgeProtectors).filter(SurgeProtectors.devices_id == device.devices_id).first()

    elif device.category == "UPS":
        device2 = db.query(UPS).filter(UPS.devices_id == device.devices_id).first()

    elif device.category == "Speaker":
        device2 = db.query(Speakers).filter(Speakers.devices_id == device.devices_id).first()

    elif device.category == "Other Equipment":
        device2 = db.query(OtherEquipments).filter(OtherEquipments.devices_id == device.devices_id).first()

    elif device.category == "Printer":
        device2 = db.query(Printers).filter(Printers.devices_id == device.devices_id).first()

    elif device.category == "CRAV":
        device2 = db.query(CRAVEquipments).filter(CRAVEquipments.devices_id == device.devices_id).first()

    elif device.category == "Network Switch":
        device2 = db.query(NetworkSwitches).filter(NetworkSwitches.devices_id == device.devices_id).first()

    elif device.category == "Monitor":
        device2 = db.query(Monitors).filter(Monitors.devices_id == device.devices_id).first()

    if device2:
        for field, value in update_data.items():
            if hasattr(device2, field) and value is not None:
                setattr(device2, field, value)

    db.commit()
    db.refresh(device)
    if device2:
        db.refresh(device2)
        return device, device2
    
    else:
        return device
    

        
