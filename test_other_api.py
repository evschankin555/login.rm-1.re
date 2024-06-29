import requests
from requests.auth import HTTPBasicAuth

# Замените логин и пароль на свои данные
username = 'robot_json'
password = 'robotjson2023_'

# URL для запроса
url = 'https://rmone.corp.rarus-cloud.ru/rm1-personal/hs/rm1org/unit?auth_guid=A0F47AEE-014F-4D8E-9697-291595790FF7'

# Выполнение GET запроса с использованием базовой аутентификации
response = requests.get(url, auth=HTTPBasicAuth(username, password))

# Проверка статуса ответа
if response.status_code == 200:
    # Преобразование ответа в JSON (если это JSON)
    data = response.json()
    print(data)
else:
    print(f"Error: {response.status_code}")
    print(response.text)
