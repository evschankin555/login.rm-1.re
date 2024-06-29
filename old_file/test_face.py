import face_recognition
import os
from datetime import datetime

# Путь к папке с известными фотографиями
KNOWN_FACES_DIR = "known_faces"

# Путь к папке с неизвестными фотографиями
UNKNOWN_FACES_DIR = "unknown_faces"

# Порог для определения совпадения (чем ниже значение, тем строже проверка)
MATCH_THRESHOLD = 0.6

# Загрузка и кодирование изображений сотрудников
known_encodings = []
known_names = []

for filename in os.listdir(KNOWN_FACES_DIR):
    if filename.endswith(".jpg") or filename.endswith(".png") or filename.endswith(".JPG") or filename.endswith(".jpeg"):
        img_path = os.path.join(KNOWN_FACES_DIR, filename)
        image = face_recognition.load_image_file(img_path)
        encodings = face_recognition.face_encodings(image)
        if encodings:
            known_encodings.append(encodings[0])
            known_names.append(os.path.splitext(filename)[0])
        else:
            print(f"Предупреждение: Лицо не найдено на изображении {filename}.")

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

# Поиск совпадений среди неизвестных фотографий
for filename in os.listdir(UNKNOWN_FACES_DIR):
    if filename.endswith(".jpg") or filename.endswith(".png") or filename.endswith(".JPG") or filename.endswith(".jpeg"):
        img_path = os.path.join(UNKNOWN_FACES_DIR, filename)
        unknown_image = face_recognition.load_image_file(img_path)
        unknown_encodings = face_recognition.face_encodings(unknown_image)

        if not unknown_encodings:
            print(f"Предупреждение: Лицо не найдено на изображении {filename}.")
            continue

        for unknown_encoding in unknown_encodings:
            distances = face_recognition.face_distance(known_encodings, unknown_encoding)
            
            if len(distances) == 0:
                print(f"Предупреждение: Нет известных кодировок для сравнения с {filename}.")
                continue

            best_match_index = distances.argmin()
            best_match_distance = distances[best_match_index]
            similarity = distance_to_similarity(best_match_distance)
            name = "Unknown"

            if best_match_distance <= MATCH_THRESHOLD:
                name = known_names[best_match_index]
                register_match(filename, name, similarity)
            else:
                print(f"Неизвестное лицо: {filename} - Процент совпадения: {similarity:.2f}%")

print("Обработка завершена.")
