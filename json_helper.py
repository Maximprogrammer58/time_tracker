import json


def read_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


def save_user_data(file_path, first_name, last_name, email, boss_token):
    user_data = {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'boss_token': boss_token
    }
    with open(file_path, 'w', encoding='utf-8') as json_file:
        json.dump(user_data, json_file, ensure_ascii=False, indent=4)