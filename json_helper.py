import json


def get_values_from_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        return list(data.values())


def save_user_data(first_name, last_name, email, boss_token):
    user_data = {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'boss_token': boss_token
    }
    with open('user_data.json', 'w', encoding='utf-8') as json_file:
        json.dump(user_data, json_file, ensure_ascii=False, indent=4)