from fastapi import FastAPI, File, Form, UploadFile, Depends, Request, HTTPException, Header, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from sqlalchemy.future import select
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional

import shutil
import os
import aiofiles
from datetime import datetime, date
import json
import functools
import requests
from requests.auth import HTTPBasicAuth
import curlify
import uuid

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from base64 import urlsafe_b64encode, urlsafe_b64decode

from models import Base, engine, SessionLocal, User, Admin, Devises, DepartmentSettings, LogConfirm
from face_find import recognize_face, compare_faces
from create_face_db import update_face_base
import api_data

app = FastAPI()

# Настройка CORS
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    # Добавьте здесь любые другие источники, которые должны быть разрешены
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

secret_key = "fdsdwr452rq*%#$efg4423++=="


API_settings = None

def get_API_settings():
    global API_settings
    with open('api_data.json', 'r', encoding='utf-8') as file:
        API_settings = json.load(file)

get_API_settings()


# Подключение статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключение папки с изображениями как статические файлы
app.mount("/images", StaticFiles(directory="images"), name="images")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/users/")
async def read_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@app.post("/users/")
async def create_user(name: str, email: str, db: Session = Depends(get_db)):
    user = User(name=name, email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
    
# =================== РАСПОЗНАНИЕ =================== <<<
@app.post("/uploadphoto/")
async def upload_photo(photo: UploadFile = File(...), db: Session = Depends(get_db)):
    upload_folder = 'uploads'
    os.makedirs(upload_folder, exist_ok=True)
    file_location = os.path.join(upload_folder, photo.filename)

    with open(file_location, 'wb') as buffer:
        shutil.copyfileobj(photo.file, buffer)

    recognize_face_info = recognize_face(file_location)

    user = db.query(User).filter(User.code == recognize_face_info.get('code')).first()

    return {"success": True, "name": recognize_face_info, "info": recognize_face_info, "user": user}


@app.post("/confirm")
async def confirm(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    came_or_went = data.get("came_or_went")
    user_code = data.get("user_code")
    #department_guid = data.get("department_guid")
    current_time_user:str = data.get("current_time_user")
    device_id = data.get("device_id")
    
    print(came_or_went, user_code)
    devise:Devises = get_device(device_id, db)
    if not devise:
        return JSONResponse(content={"success": False, "error": 'Неверный device_id'})
    
    if devise.department in ['', None]:
        return JSONResponse(content={"success": False, "error": 'Выберите Департамент!'})

    user = db.query(User).filter(User.code == user_code).first()

    confirm_user_settings = API_settings.get('confirm_user')

    headers = {
        'Content-Type': 'application/json'
    }
    bio_inout = 1 if came_or_went == 'came' else 2
    json_data = json.dumps({
        "auth_guid": "491824AC-51BE-4803-8DE9-3F74E91E4D0C",
        "bio_empl_guid": user.guide,
        "bio_unit_guid": devise.department,
        "bio_inout": bio_inout,
        "bio_workdate": current_time_user.replace(' ', 'T')
    })
    print('data_to_send -> ', json_data)

    response = requests.post(confirm_user_settings.get('API'), auth=HTTPBasicAuth(confirm_user_settings.get('login'), confirm_user_settings.get('password')), headers=headers, data=json_data)
    # Проверка статуса ответа
    curl_command = curlify.to_curl(response.request)
    print(curl_command)

    # лог прихода и ухода
    log_confirm = LogConfirm(
        guide = user.guide,
        user_name = user.name,
        devise_guid = device_id,
        department_id = devise.department,
        inout = 'пришёл' if came_or_went == 'came' else 'ушёл', 
        response = str(response.status_code) + ' ' + response.text,
        json_data = str(json_data)
    )
    db.add(log_confirm)
    db.commit()
    
    if response.status_code in [200, 201]:
        # Преобразование ответа в JSON (если это JSON)
       return JSONResponse(content={"success": True})
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return JSONResponse(content={"success": False})


@app.get("/", response_class=HTMLResponse)
async def read_index():
    async with aiofiles.open("static/main.html", mode="r") as f:
        content = await f.read()
    return HTMLResponse(content=content)


@app.post("/get_device_id/")
async def get_device_id(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    device_id = data.get('device_id')
    print('device_id ', device_id)

    devise:Devises = get_device(device_id, db)

    if devise:
        if devise:
            devise.modify_at = datetime.utcnow()
            db.commit()

    else:
        new_devise = Devises(
            admin_id=0,                  # Уникальный admin_id
            department=''        # Название отдела
        )
        db.add(new_devise)
        db.commit()
        print('new_devise', new_devise)
        print(new_devise.id)

        devise = new_devise

    devise_dict = {
        "id": str(devise.id),
        "department": devise.department

    }
    print('devise_dict', devise_dict)

    return JSONResponse(content={"success": True, "device": devise_dict})


def get_device(device_id:str, db: Session = Depends(get_db)) -> Devises:
    try:
        devise_uuid = uuid.UUID(device_id)
    except Exception as e:
        print(f"Ошибка преобразования UUID: {e}")
        return None

    devise = db.query(Devises).filter(Devises.id == devise_uuid).first()

    return devise

# =================== РАСПОЗНАНИЕ =================== >>>

# =================== АДМИН =================== <<<
@app.get("/admin", response_class=HTMLResponse)
async def admin_get():
    async with aiofiles.open("static/admin.html", mode="r") as f:
        content = await f.read()
    return HTMLResponse(content=content)


def is_admin_hash(admin_role: str='admin'):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Получаем аргумент request из args или kwargs
            request = kwargs.get('request') if 'request' in kwargs else args[0] if args else None
            data = await request.json()

            if not data or not data.get('hash'):
                raise HTTPException(status_code=400, detail="Неверный ключ")

            try:
                hash = data.get('hash')
                hash_text = decrypt(hash)
                hash_list = hash_text.split(' ')
                
                if hash_list[1] != str(datetime.now().date()):
                    print('date ', hash_list[1])
                    raise HTTPException(status_code=400, detail="Неверный ключ")
                
                db = SessionLocal()
                try:      
                    admin_find = db.query(Admin).filter(Admin.id == hash_list[0]).first()
                    if (admin_role != admin_find.role) and (admin_find.role != 'super'):
                        raise HTTPException(status_code=400, detail="Неверный ключ")
                finally:
                    db.close()
                if not admin_find:
                    print('admin_find ', admin_find, admin_role)
                    raise HTTPException(status_code=400, detail="Неверный ключ")
            except Exception as e:
                print('ERROE -> ', e)
                raise HTTPException(status_code=400, detail="Неверный ключ")

            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


@app.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    login = data.get('username')
    password = data.get('password')
    device_id = data.get('device_id')

    admin_find = db.query(Admin).filter(and_(Admin.login == login, or_(Admin.role == 'admin', Admin.role == None))).first()
    if not admin_find or decrypt(admin_find.password) != password:
        raise HTTPException(status_code=400, detail="Неверный логин или пароль!")
    
    return_add_admin = add_admin_id_to_device(device_id, admin_find.id, db=db)
    if not return_add_admin['success']:
        return JSONResponse(content=return_add_admin)

    encrypt_text = f'{admin_find.id} {datetime.now().date()}'
    return JSONResponse(content={"success": True, "hash": encrypt(encrypt_text)})


@app.post("/get_users")
@is_admin_hash()
async def get_users_post(request: Request):
    data = await request.json()
    user_id = data.get('user_id')

    users_list = get_users(user_id)
    if users_list == []:
       raise HTTPException(status_code=400, detail="Пользователь не найден!")
        
    return JSONResponse(content={"success": True, "users": users_list})



def get_users(user_id) -> list:
    users_list = api_data.get_users()
    if users_list == []:
        return []
    
    print(user_id)
    if user_id != None:
        for user in users_list:
            if user.get('empl_code') == user_id:
                user_images = get_user_images(user.get('empl_code'))
                user_images = [{'url':'images/' + user_image, 'id': user_image.split('_')[-1].split('.')[0]} for user_image in user_images]
                user['images'] = user_images
                users_list = [user]
                return users_list
        return []
    
    return users_list


@app.post("/get_departments")
@is_admin_hash()
async def get_departments_post(request: Request):
    departments_list = get_departments()
    if departments_list == []:
       raise HTTPException(status_code=400, detail="Дипартаментов нету!")
        
    return JSONResponse(content={"success": True, "departments": departments_list})
 

def get_departments() -> list:
    departments_list = api_data.get_departments()
    if departments_list == []:
        return []

    departments_list = [department for department in departments_list if department.get('unit_isDeleted') == False]

    return departments_list


@app.post("/base_status")

async def base_status(request: Request):

    return JSONResponse(content={"success": True, "base_status": get_fase_base_status()})


@app.post("/update_base")
@is_admin_hash()
async def update_base(request: Request, background_tasks: BackgroundTasks):

    fase_base_status = get_fase_base_status()
    if fase_base_status.get('update_processing') == True:
        return JSONResponse(content={"success": True})
    
    background_tasks.add_task(update_face_base)

    return JSONResponse(content={"success": True})


@app.post("/save_photo/")
async def save_photo(photo: UploadFile = File(...), hash: str = Form(...), device_id: str = Form(...), user_id: str = Form(...), db: Session = Depends(get_db)):
    upload_folder = 'images'

    try:
        hash_text = decrypt(hash)
        hash_list = hash_text.split(' ')
        if hash_list[1] != str(datetime.now().date()):
            raise HTTPException(status_code=400, detail="Неверный ключ")
    except:
        raise HTTPException(status_code=400, detail="Неверный ключ")

    devise = get_device(device_id, db)
    if not devise:
        print("Неверный device_id")
        raise HTTPException(status_code=400, detail="Неверный device_id")
    
    images_list = get_user_images(user_id)

    department_settings:DepartmentSettings = get_department_settings(devise.department, db)
    admin = db.query(Admin).filter(Admin.id == devise.admin_id).first()
    max_photo_count = department_settings.max_photo_count
    if len(images_list) >= max_photo_count and (admin.role != 'super'):
        #return JSONResponse(content={"success": False, "error": f'На данной точке максимальное число фотографий {max_photo_count}'})
        print(f"На данной точке максимальное число фотографий {max_photo_count}")
        return JSONResponse(content={"success": False, "error": f"На данной точке максимальное число фотографий {max_photo_count}"})

    max_img_index = 0
    for image in images_list:
        img_index = int(image.split('_')[-1].split('.')[0])
        if img_index > max_img_index:
            max_img_index = img_index

    photo_name = f'{user_id}_{max_img_index + 1}.' + str(photo.filename).split('.')[-1]

    file_location = os.path.join(upload_folder, photo_name)

    with open(file_location, 'wb') as buffer:
        shutil.copyfileobj(photo.file, buffer)

    # проверяем, что фото одного и того же человека
    if len(images_list) > 1:
        images_list_path = [upload_folder + '/' + image for image in images_list]
        is_same_person = compare_faces(file_location, images_list_path)
        print(is_same_person)
        if not is_same_person:
            if os.path.exists(file_location):
                os.remove(file_location)  # Удаляем файл
            return JSONResponse(content={"success": False, "error": "Загруженное фото не совпадает с фото загруженными ранее!"})

    print(user_id)
    user = db.query(User).filter(User.code == user_id).first()
    if not user:
        user_data = get_users(user_id)[0]
        new_user = User(
            code = user_id,
            name = user_data.get('empl_name'),
            guide = user_data.get('empl_guid'),
        )

        # Добавление объекта в сессию
        db.add(new_user)
        db.commit()

    return JSONResponse(content={"success": True})


@app.post("/update_device/")
@is_admin_hash()
async def update_device_post(request: Request, db: Session = Depends(get_db)):
    data = await request.json()

    device_id = data.get('device_id')
    department_guid = data.get('department_guid') 
    hash = data.get('hash')


    return update_device(device_id, department_guid, hash, db)


def update_device(device_id, department_guid, hash, db):
    devise_get:Devises = get_device(device_id, db)
    if not devise_get:
        return JSONResponse(content={"success": False, "error": 'Неверный device_id'})

    hash_text = decrypt(hash)
    admin_id = hash_text.split(' ')[0]
    admin_find = db.query(Admin).filter(Admin.id == admin_id).first()
    admin_role = admin_find.role

    if department_guid:
        department_settings:DepartmentSettings = get_department_settings(department_guid, db)
        max_count_device = department_settings.max_divice_count
        if department_guid != '': 
            if admin_role not in ['super']:
                devises = db.query(Devises).filter(Devises.department == department_guid).all()
                valid_devises = []  
                for devise in devises:
                    admin = db.query(Admin).filter(and_(Admin.id == devise.admin_id, Admin.role == 'admin')).first()
                    if admin:
                        valid_devises.append(devise)
                print(valid_devises)
                if len(valid_devises) >= max_count_device:
                    return JSONResponse(content={"success": False, "error": f'К подразделению уже привязаны {len(valid_devises)} устройства. Максимальное число {max_count_device}.'})

    devise_get.department = department_guid

    devise_get.modify_at = datetime.utcnow()
    db.commit()

    return JSONResponse(content={"success": True})


def get_fase_base_status() -> dict:
    with open('fase_base_status_new.json', 'r', encoding='utf-8') as file:
        fase_base_status = json.load(file)
    return fase_base_status

def get_user_images(user_id: str) -> list:
    images_list = []
    for filename in os.listdir('images'):
        if filename.startswith(f'{user_id}_'):
            images_list.append(filename)
    
    return images_list

def derive_key(hash_key: str, salt: bytes) -> bytes:
    return PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    ).derive(hash_key.encode())

def encrypt(text: str, hash_key: str=None) -> str:
    if not hash_key:
        hash_key = secret_key

    salt, iv = os.urandom(16), os.urandom(12)
    key = derive_key(hash_key, salt)
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend()).encryptor()
    ciphertext = cipher.update(text.encode()) + cipher.finalize()
    return urlsafe_b64encode(salt + iv + cipher.tag + ciphertext).decode('utf-8')

def decrypt(encrypted_text: str, hash_key: str=None) -> str:
    if not hash_key:
        hash_key = secret_key

    data = urlsafe_b64decode(encrypted_text)
    salt, iv, tag, ciphertext = data[:16], data[16:28], data[28:44], data[44:]
    key = derive_key(hash_key, salt)
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend()).decryptor()
    return (cipher.update(ciphertext) + cipher.finalize()).decode('utf-8')


def add_admin_id_to_device(device_id:str, admin_id:str, db: Session = Depends(get_db)):
    print(device_id)

    devise:Devises = get_device(device_id, db)
    if not devise:
        return {"success": False, "error": 'Неверный device_id'}

    devise.admin_id = admin_id

    devise.modify_at = datetime.utcnow()
    db.commit()

    return {"success": True}


def get_department_settings(department_id, db: Session = Depends(get_db)) -> DepartmentSettings:
    department_settings = db.query(DepartmentSettings).filter_by(department_id=department_id).first()

    if department_settings is None:
        # Если запись не найдена, создаём новую с дефолтными значениями
        department_settings = DepartmentSettings(
            department_id=department_id,
            max_photo_count=3,  
            max_divice_count=2   
        )
        db.add(department_settings)
        db.commit()  # Сохраняем изменения в базе данных

    return department_settings
# =================== АДМИН =================== >>>

# =================== СУПЕР АДМИН =================== <<<
@app.get("/superadmin", response_class=HTMLResponse)
async def superadmin_get():
    async with aiofiles.open("static/superadmin.html", mode="r") as f:
        content = await f.read()
    return HTMLResponse(content=content)


@app.post("/superlogin")
async def superlogin(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    login = data.get('username')
    password = data.get('password')
    device_id = data.get('device_id')
    print(data)

    super_admin = db.query(Admin).filter(and_(Admin.login == login, Admin.role == 'super')).first()
    if not super_admin or decrypt(super_admin.password) != password:
        raise HTTPException(status_code=400, detail="Неверный логин или пароль!")
    
    return_add_admin = add_admin_id_to_device(device_id, super_admin.id, db=db)
    if not return_add_admin['success']:
        return JSONResponse(content=return_add_admin)

    encrypt_text = f'{super_admin.id} {datetime.now().date()}'
    return JSONResponse(content={"success": True, "hash": encrypt(encrypt_text)})


@app.post("/get_users_sa")
@is_admin_hash('super')
async def get_users_sa(request: Request):
    data = await request.json()
    user_id = data.get('user_id')

    users_list = get_users(user_id)
    if users_list == []:
       raise HTTPException(status_code=400, detail="Пользователь не найден!")
        
    return JSONResponse(content={"success": True, "users": users_list})


@app.post("/get_admins")
@is_admin_hash('super')
async def get_admins(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    id_filter = data.get('id_filter')
    name_filter = data.get('name_filter')
    filter_list = []

    if id_filter:
        filter_list.append(Admin.id == id_filter)
    
    filter_list.append(or_(Admin.role == 'admin', Admin.role == None))

    if name_filter:
        filter_list.append(or_(Admin.name.like(f'%{name_filter}%'), Admin.login.like(f'%{name_filter}%')))

    admins = db.query(Admin)

    if len(filter_list) == 1:
        admins = admins.filter(*filter_list)
    elif len(filter_list) >= 2:
        admins = admins.filter(and_(*filter_list))

    admins_obj = admins.all()
    admins_list = [
        {
            "id": admin.id,
            "name": admin.name,
            "login": admin.login
        }
    for admin in admins_obj]

    return JSONResponse(content={"success": True, "admins": admins_list})


@app.post("/add_admin")
@is_admin_hash('super')
async def add_admin(request: Request, db: Session = Depends(get_db)):
    data = await request.json()

    admin_find = db.query(Admin).filter(Admin.id == data.get('code')).first()
    if admin_find:
        return JSONResponse(content={"success": False, "error": f"Админу уже существует с логином {admin_find.login}"})

    admin_find = db.query(Admin).filter(Admin.login == data.get('login')).first()
    if admin_find:
        return JSONResponse(content={"success": False, "error": "Логин занят!"})

    print(data)
    new_admin = Admin(
        id = data.get('code'),
        name = data.get('name'),
        login = data.get('login'),
        password = encrypt(data.get('password'))
    )

    # Добавление объекта в сессию
    db.add(new_admin)
    db.commit()

    return JSONResponse(content={"success": True})


@app.delete("/delete_admin/{admin_id}", response_model=dict)
async def delete_admin(admin_id, authorization: str = Header(...), db: Session = Depends(get_db)):
    # authorization содержит значение заголовка Authorization
    hash = authorization.split(" ")[1]  # Извлечение токена из заголовка (Bearer <token>)
    try:
        hash_text = decrypt(hash)
        hash_list = hash_text.split(' ')
        if hash_list[1] != str(datetime.now().date()):
            raise HTTPException(status_code=400, detail="Неверный ключ")
    except:
        raise HTTPException(status_code=400, detail="Неверный ключ")

    admin_to_delete = db.query(Admin).filter(Admin.id == admin_id).first()

    if admin_to_delete:
        db.delete(admin_to_delete)
        db.commit()

    if admin_to_delete:
        return {"success": True}
    else:
        raise HTTPException(status_code=400, detail="Ошибка удаления админа")
    

@app.post("/delete_photo")
@is_admin_hash()
async def delete_photo(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    photo_url = data.get('photo_url')
    photo_url = '/'.join(photo_url.split('/')[-2:])
    user_id = data.get('user_id')

    if os.path.exists(photo_url):
        os.remove(photo_url)

    user = db.query(User).filter(User.code == user_id).first()
    if user:
        if len(get_user_images(user_id)) == 0:
            db.delete(user)
            db.commit()

    return JSONResponse(content={"success": True})


@app.delete("/delete_device/{device_id}", response_model=dict)
async def delete_device(device_id, authorization: str = Header(...), db: Session = Depends(get_db)):
    # authorization содержит значение заголовка Authorization
    hash = authorization.split(" ")[1]  # Извлечение токена из заголовка (Bearer <token>)
    try:
        hash_text = decrypt(hash)
        hash_list = hash_text.split(' ')
        if hash_list[1] != str(datetime.now().date()):
            raise HTTPException(status_code=400, detail="Неверный ключ")
    except:
        raise HTTPException(status_code=400, detail="Неверный ключ")

    devise:Devises = get_device(device_id, db)
    if not devise:
        raise HTTPException(status_code=400, detail="Неверный device_id")

    if devise:
        db.delete(devise)
        db.commit()

    if devise:
        return {"success": True}
    else:
        raise HTTPException(status_code=400, detail="Ошибка удаления девайса")


@app.post("/get_department_data")
@is_admin_hash('super')
async def get_department_data(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    department_id = data.get('department')
    
    department_settings:DepartmentSettings = get_department_settings(department_id, db)
    department_data_json = get_department_data_json(department_settings, db)

    return JSONResponse(content={"success": True, "department_data": department_data_json})


def get_department_data_json(department_settings:DepartmentSettings, db: Session = Depends(get_db)) -> dict:
    print(department_settings.department_id)
    devises = db.query(Devises).filter(Devises.department == department_settings.department_id).all()
    devises_list = []  
    for devise in devises:

        admin_data = None
        if devise.admin_id:
            admin_data = db.query(Admin).filter(Admin.id == devise.admin_id).first()
            if admin_data:
                admin_data = {
                    "id": admin_data.id,
                    "name": admin_data.name,
                    "login": admin_data.login,
                    "created_at": str(admin_data.created_at)
                }
            
        devises_list.append({
            "id": str(devise.id),
            "admin": admin_data, #devise.admin_id,
            "department": devise.department,
            "modify_at": str(devise.modify_at)
        })

    department_json = {
        "settings": {
            "department": department_settings.department_id,
            "max_photo_count": department_settings.max_photo_count,
            "max_divice_count": department_settings.max_divice_count
        },
        "devises": devises_list 
    }

    return department_json


@app.post("/update_department_settings/")
@is_admin_hash('super')
async def update_device_post(request: Request, db: Session = Depends(get_db)):
    data = await request.json()

    device_id = data.get('device_id')
    department = data.get('department')
    max_photo_count = data.get('max_photo_count') 
    max_divice_count = data.get('max_divice_count')

    devise:Devises = get_device(device_id, db)
    if not devise:
        return JSONResponse(content={"success": False, "error": 'Неправильный device_id'})

    if not department:
        department = devise.department
    
    department_settings = get_department_settings(department, db)
    
    if max_photo_count is not None:
        try:
            department_settings.max_photo_count = int(max_photo_count)
        except ValueError:
            pass

    if max_divice_count is not None:
        try:
            department_settings.max_divice_count = int(max_divice_count)
        except ValueError:
            pass
    
    db.commit()

    department_data_json = get_department_data_json(department_settings, db)

    return JSONResponse(content={"success": True, "department_data": department_data_json})

@app.post("/logs/", response_model=List[dict])
@is_admin_hash('super')
async def read_logs(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    date_param = data.get("date")

    # Преобразование даты
    if date_param:
        try:
            filter_date = datetime.strptime(date_param, "%Y-%m-%d").date()
            start_date = datetime.combine(filter_date, datetime.min.time())
            end_date = datetime.combine(filter_date, datetime.max.time())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    else:
        today = date.today()
        start_date = datetime.combine(today, datetime.min.time())
        end_date = datetime.combine(today, datetime.max.time())

    # Запрос к базе данных с использованием синхронного метода
    query = db.query(LogConfirm).filter(LogConfirm.created_at >= start_date, LogConfirm.created_at <= end_date)
    logs = query.all()  # Получаем все записи

    # Возвращаем данные в виде списка словарей
    return_dict = [
        {
            "id": log.id,
            "guide": log.guide,
            "user_name": log.user_name,
            "devise_guid": log.devise_guid,
            "department_id": log.department_id,
            "inout": log.inout,
            "response": log.response,
            "json_data": log.json_data,
            "created_at": str(log.created_at),
        } for log in logs
    ]
    print(return_dict)

    return return_dict
# =================== СУПЕР АДМИН =================== >>>

# =================== ТЕСТ =================== <<<
@app.get("/testpem", response_class=HTMLResponse)
async def testpem_get():
    async with aiofiles.open("static/test.html", mode="r") as f:
        content = await f.read()
    return HTMLResponse(content=content)
# =================== ТЕСТ =================== >>>

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
