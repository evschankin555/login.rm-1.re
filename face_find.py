import face_recognition
from datetime import datetime, timezone, timedelta
import numpy as np
import pickle

# Путь к папке с известными лицами
KNOWN_FACES_DIR = "people"

# Порог для определения совпадения (чем ниже значение, тем строже проверка)
MATCH_THRESHOLD = 0.6

all_face_encodings = None
known_encodings = None
known_code = None 
# Load face encodings
def ubdate_all_face_encoding():
    global all_face_encodings
    global known_encodings
    global known_code

    with open('dataset_faces.dat', 'rb') as f:
        all_face_encodings = pickle.load(f)

    known_encodings = all_face_encodings.get('known_encodings')
    known_code = all_face_encodings.get('known_code') 

ubdate_all_face_encoding()


def send_find_user():
    pass

# Функция для регистрации совпадений
def register_match(unknown_image_name, code, similarity) -> str:
    msk_timezone = timezone(timedelta(hours=3))
    now = datetime.now(msk_timezone)
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    with open("matches_log.csv", "a") as log:
        log.write(f"{unknown_image_name},{code},{similarity:.2f},{current_time}\n")
    print(f"Совпадение найдено: {unknown_image_name} - {code} ({similarity:.2f}%) в {current_time}")

    send_find_user()

    return {"ststus": "known", "percent": f"{similarity:.2f}%", "code": code, "current_time": current_time, "unknown_image_name": unknown_image_name}
    return f"Совпадение найдено: {unknown_image_name} - {code} ({similarity:.2f}%) в {current_time}"

# Преобразование расстояния в процент совпадения
def distance_to_similarity(distance):
    return (1.0 - distance) * 100

# Функция для распознавания лица на неизвестном изображении
def recognize_face(unknown_image_path):
    ubdate_all_face_encoding()
        
    unknown_image = face_recognition.load_image_file(unknown_image_path)
    unknown_encodings = face_recognition.face_encodings(unknown_image)

    if unknown_encodings:  # Проверка, что найдены лица на неизвестном изображении
        for unknown_encoding in unknown_encodings:
            distances = face_recognition.face_distance(known_encodings, unknown_encoding)
            if len(distances) > 0:
                best_match_index = np.argmin(distances)
                best_match_distance = distances[best_match_index]
                similarity = distance_to_similarity(best_match_distance)
                print(similarity, best_match_distance)
                code = "Unknown"

                if best_match_distance <= MATCH_THRESHOLD:
                    code = known_code[best_match_index]
                    return register_match(unknown_image_path, code, similarity)
                else:
                    print(f"Неизвестное лицо: {unknown_image_path} - Процент совпадения: {similarity:.2f}%")
                    return {"ststus": "unknown", "percent": f"{similarity:.2f}%", "code": code}
            else:
                print(f"Неизвестное лицо: {unknown_image_path} - Не найдены известные лица для сравнения")
    else:
        print(f"Неизвестное лицо: {unknown_image_path} - Не найдены лица на изображении")

    return {"ststus": "unknown"}


def compare_faces(test_image_path, known_images_paths):
    # Загрузить проверяемое фото и закодировать лицо на нем
    test_image = face_recognition.load_image_file(test_image_path)
    test_encoding = face_recognition.face_encodings(test_image)
    
    # Проверить, что на проверяемом фото есть хотя бы одно лицо
    if len(test_encoding) == 0:
        return False
    
    # Берем первую (и единственную) кодировку лица
    test_encoding = test_encoding[0]

    # Перебираем все известные фото и сравниваем с проверяемым лицом
    for known_image_path in known_images_paths:
        known_image = face_recognition.load_image_file(known_image_path)
        known_encodings = face_recognition.face_encodings(known_image)
        
        # Проверим все лица на каждом из известных фото
        for known_encoding in known_encodings:
            # Сравниваем лица
            results = face_recognition.compare_faces([known_encoding], test_encoding)
            if results[0]:
                print('results', results)
                return True  # Найдено совпадение
    return False  # Совпадений нет