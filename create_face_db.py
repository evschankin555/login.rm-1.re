
import face_recognition
import os
import pickle
import json
from datetime import datetime, timedelta

# Путь к папке с известными лицами
KNOWN_FACES_DIR = "images"

# Загрузка и кодирование изображений сотрудников
def update_face_base():
    known_encodings = []
    known_code = []
    known_dict = {}
    start_update = datetime.now()

    with open('fase_base_status_new.json', 'r', encoding='utf-8') as file:
        fase_base_status = json.load(file)

    last_run_update = datetime.strptime(fase_base_status.get('last_run_update'), '%Y-%m-%d %H:%M:%S.%f')

    if (fase_base_status.get('last_update') == "в процессе") and (datetime.now() - last_run_update < timedelta(minutes=15)):
        return 'обновление в процессе'

    face_base = {
        "last_update": "в процессе",
        "update_processing": True,
        "last_run_update": fase_base_status.get('last_update'),
        "start_update": str(datetime.now())
    }
    with open('fase_base_status_new.json', 'w', encoding='utf-8') as file:
        json.dump(face_base, file, ensure_ascii=False, indent=4)

    try:
        #person_name
        #person_dir = os.path.join(KNOWN_FACES_DIR, person_name)
        for filename in os.listdir(KNOWN_FACES_DIR):
            if filename.endswith(".jpg") or filename.endswith(".png") or filename.endswith(".JPG") or filename.endswith(".jpeg"):
                img_path = os.path.join(KNOWN_FACES_DIR, filename)
                image = face_recognition.load_image_file(img_path)
                encodings = face_recognition.face_encodings(image)
                #print(filename, encodings)
                if encodings:                                     
                    #if not known_dict.get(person_name):
                    #    known_dict[person_name] = []
                    person_id = filename.split('_')[0]

                    encoding = encodings[0]
                    known_encodings.append(encoding)
                    known_code.append(person_id)
                    

                    #known_dict[person_name].append(encoding)

        known_dict['known_code'] = known_code
        known_dict['known_encodings'] = known_encodings
        #print(known_dict)

        with open('dataset_faces.dat', 'wb') as f:
            pickle.dump(known_dict, f)

    except Exception as e:
        print(f'ERROR!! {e}')

    face_base = {
        "last_update": str(datetime.now()),
        "update_processing": False,
        "last_run_update":  str(datetime.now()),
        "update_time": str(datetime.now() - start_update)
    }
    with open('fase_base_status_new.json', 'w', encoding='utf-8') as file:
        json.dump(face_base, file, ensure_ascii=False, indent=4)

    return 'обновление завершено'


if __name__ == "__main__": 
    print(update_face_base())