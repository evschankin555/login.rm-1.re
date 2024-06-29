import requests
from requests.auth import HTTPBasicAuth
import json


API_settings = None

def get_API_settings():
    global API_settings
    with open('api_data.json', 'r', encoding='utf-8') as file:
        API_settings = json.load(file)

get_API_settings()


def get_departments():
    departments_settings = API_settings.get('departments')

    response = requests.get(departments_settings.get('API'), auth=HTTPBasicAuth(departments_settings.get('login'), departments_settings.get('password')))

    if response.status_code == 200:
        departments_list = response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        departments_list = []

    print(departments_list)
    
    return departments_list


def get_users():
    users_settings = API_settings.get('users')

    response = requests.get(users_settings.get('API'), auth=HTTPBasicAuth(users_settings.get('login'), users_settings.get('password')))

    if response.status_code == 200:
        users_list = response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        users_list = []

    print(users_list)

    return users_list