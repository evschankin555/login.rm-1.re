import face_recognition
import os
from datetime import datetime
import numpy as np

# Путь к папке с известными лицами
KNOWN_FACES_DIR = "people"

# Порог для определения совпадения (чем ниже значение, тем строже проверка)
MATCH_THRESHOLD = 0.6

# Загрузка и кодирование изображений сотрудников
known_encodings = []
known_names = []

for person_name in os.listdir(KNOWN_FACES_DIR):
    person_dir = os.path.join(KNOWN_FACES_DIR, person_name)
    if os.path.isdir(person_dir):
        for filename in os.listdir(person_dir):
            if filename.endswith(".jpg") or filename.endswith(".png") or filename.endswith(".JPG") or filename.endswith(".jpeg"):
                img_path = os.path.join(person_dir, filename)
                image = face_recognition.load_image_file(img_path)
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    encoding = encodings[0]
                    known_encodings.append(encoding)
                    known_names.append(person_name)

# Функция для регистрации совпадений
def register_match(unknown_image_name, name, similarity):
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    with open("matches_log.csv", "a") as log:
        log.write(f"{unknown_image_name},{name},{similarity:.2f},{current_time}\n")
    print(f"Совпадение найдено: {unknown_image_name} - {name} ({similarity:.2f}%) в {current_time}")

# Преобразование расстояния в процент совпадения
def distance_to_similarity(distance):
    return (1.0 - distance) * 100

# Функция для распознавания лица на неизвестном изображении
def recognize_face(unknown_image_path):
    unknown_image = face_recognition.load_image_file(unknown_image_path)
    unknown_encodings = face_recognition.face_encodings(unknown_image)

    if unknown_encodings:  # Проверка, что найдены лица на неизвестном изображении
        for unknown_encoding in unknown_encodings:
            distances = face_recognition.face_distance(known_encodings, unknown_encoding)
            if len(distances) > 0:
                best_match_index = np.argmin(distances)
                best_match_distance = distances[best_match_index]
                similarity = distance_to_similarity(best_match_distance)
                name = "Unknown"

                if best_match_distance <= MATCH_THRESHOLD:
                    name = known_names[best_match_index]
                    register_match(unknown_image_path, name, similarity)
                else:
                    print(f"Неизвестное лицо: {unknown_image_path} - Процент совпадения: {similarity:.2f}%")
            else:
                print(f"Неизвестное лицо: {unknown_image_path} - Не найдены известные лица для сравнения")
    else:
        print(f"Неизвестное лицо: {unknown_image_path} - Не найдены лица на изображении")

# Пример использования функции
unknown_image_path = "unknown_faces/find_2.jpeg"  # Замените на путь к вашему изображению
recognize_face(unknown_image_path)
