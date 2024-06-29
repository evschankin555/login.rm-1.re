import face_recognition
import os
import pickle

# Путь к папке с известными лицами
KNOWN_FACES_DIR = "people"

# Загрузка и кодирование изображений сотрудников
known_encodings = []
known_names = []
known_dict = {}

for person_name in os.listdir(KNOWN_FACES_DIR):
    person_dir = os.path.join(KNOWN_FACES_DIR, person_name)
    if os.path.isdir(person_dir):
        for filename in os.listdir(person_dir):
            if filename.endswith(".jpg") or filename.endswith(".png") or filename.endswith(".JPG") or filename.endswith(".jpeg"):
                img_path = os.path.join(person_dir, filename)
                image = face_recognition.load_image_file(img_path)
                encodings = face_recognition.face_encodings(image)
                if encodings:                                     
                    #if not known_dict.get(person_name):
                    #    known_dict[person_name] = []

                    encoding = encodings[0]
                    known_encodings.append(encoding)
                    known_names.append(person_name)

                    #known_dict[person_name].append(encoding)

known_dict['known_names'] = known_names
known_dict['known_encodings'] = known_encodings

with open('dataset_faces.dat', 'wb') as f:
    pickle.dump(known_dict, f)
