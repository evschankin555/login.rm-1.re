import face_recognition
import os
from datetime import datetime
import numpy as np
import pickle

# Путь к папке с известными лицами
KNOWN_FACES_DIR = "people"

# Порог для определения совпадения (чем ниже значение, тем строже проверка)
MATCH_THRESHOLD = 0.6

# Загрузка и кодирование изображений сотрудников
known_encodings = []
known_names = []
time_list = []

time_list.append(datetime.now())

# Load face encodings
with open('dataset_faces.dat', 'rb') as f:
	all_face_encodings = pickle.load(f)

known_encodings = all_face_encodings.get('known_encodings')
known_names = all_face_encodings.get('known_names')

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

time_list.append(datetime.now())

# Пример использования функции
unknown_image_path = "unknown_faces/find_2.jpeg"  # Замените на путь к вашему изображению
recognize_face(unknown_image_path)

time_list.append(datetime.now())

unknown_image_path = "unknown_faces/find.jpeg"  # Замените на путь к вашему изображению
recognize_face(unknown_image_path)

time_list.append(datetime.now())

unknown_image_path = "unknown_faces/find_3.jpeg"  # Замените на путь к вашему изображению
recognize_face(unknown_image_path)

time_list.append(datetime.now())

unknown_image_path = "unknown_faces/find_4.jpeg"  # Замените на путь к вашему изображению
recognize_face(unknown_image_path)

for time_id, time in enumerate(time_list):
    if time_id + 1 < len(time_list):
        time_new = time_list[time_id + 1]
    else: 
        time_new = datetime.now()
    print('Время работы (time_id): ' + str(time_new - time))
