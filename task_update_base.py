import schedule
import time
import os
from datetime import datetime, timedelta

from create_face_db import update_face_base
import api_data
from models import Base, engine, SessionLocal, User, Devises, LogConfirm
from fast_api import get_user_images


def delete_old_devises(db=None):
    close_db = False
    if db == None:
        db = SessionLocal()
        close_db = True

    try:
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        db.query(Devises).filter(Devises.modify_at < thirty_days_ago).delete(synchronize_session=False)
        db.commit()
    finally:
        if close_db:
            db.close()


def delete_old_logs(db=None):
    close_db = False
    if db == None:
        db = SessionLocal()
        close_db = True

    try:
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        db.query(LogConfirm).filter(LogConfirm.created_at < thirty_days_ago).delete(synchronize_session=False)
        db.commit()
    finally:
        if close_db:
            db.close()


def run_update():
    # проверяем, что все юзеры в нашей базе есть в базе 1С
    user_list_api = api_data.get_users()
    if user_list_api == []:
        print('Не получили данных по АПИ')
        return 
    
    user_list_api_code = [user.get('empl_code') for user in user_list_api]

    db = SessionLocal()
    try:
        user_list_base = db.query(User).all()
        user_list_base = [user.__dict__ for user in user_list_base]
        #print(user_list_base)

        # если их нет, то удаляем фото, а потом из таблицы
        for user_base in user_list_base:
            if not user_base.get('code') in user_list_api_code:
                image_list = get_user_images(user_base.get('code'))
                
                #print(image_list)
                for image in image_list:
                    file_path = f'./images/{image}'
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    
                user = db.query(User).filter(User.code == user_base.get('code')).first()
                if user:
                    db.delete(user)
                    db.commit()
    except Exception as e:
        print('ERROR -> ', e)
    finally:
        db.close()
    
    # так же проверяем и админов и удаляем, если не нашли
    # (пока не реализованно, нужно протянуть код сотрудника в таблицу админов)
    db = SessionLocal()
    try:
        delete_old_devises()
        delete_old_logs()
    except Exception as e:
        print('ERROR -> ', e)
    finally:
        db.close()

    print('обновление базы лиц', update_face_base())

    print('конец обновления')


def run_cycle_update():
    try:
        run_update()
    except Exception as e:
        print('ERROR -> ', e)


def start_scheduler():
    run_cycle_update()
    
    schedule.every(15).minutes.do(run_cycle_update)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    start_scheduler()