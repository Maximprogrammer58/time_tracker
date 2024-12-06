import json
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def read_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        logging.error(f"File {file_path} not found")
        return None
    except Exception as e:
        logging.error(f"Error reading json file: {e}")
        return None


def save_user_data(file_path, first_name, last_name, email, boss_token):
    user_data = {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'boss_token': boss_token
    }
    try:
        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(user_data, json_file, ensure_ascii=False, indent=4)
    except FileNotFoundError:
        logging.error(f"File {file_path} not found")
    except Exception as e:
        logging.error(f"Error writting json file: {e}")