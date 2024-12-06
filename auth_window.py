import logging
import requests

from modules.json_helper import save_user_data, read_json
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout,
    QLabel, QLineEdit, QMessageBox
)


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class AuthWindow(QWidget):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Авторизация')
        self.setGeometry(100, 100, 250, 120)

        layout = QVBoxLayout()

        self.username_label = QLabel('Логин:', self)
        self.username_input = QLineEdit(self)
        self.password_label = QLabel('Пароль:', self)
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.Password)

        self.login_button = QPushButton('Войти', self)
        self.login_button.clicked.connect(self.check_credentials)

        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def check_credentials(self):
        username = self.username_input.text()
        password = self.password_input.text()

        settings = read_json("settings.json")

        try:
            response = requests.post(settings['url_server_login'], json={
                'email': username,
                'password': password
            })

            if response.status_code == 200:
                data = response.json()
                first_name = data.get('first_name')
                last_name = data.get('last_name')
                boss_token = data.get('boss_token')
                email = username

                save_user_data(settings["path_data_file"], first_name, last_name, email, boss_token)

                logging.info(f"The user {first_name} {last_name} with {email} has logged into the application")

                self.on_login_success()
                self.close()
            else:
                QMessageBox.warning(self, 'Ошибка', 'Неверный логин или пароль.')
        except Exception as e:
            logging.info(f"Error connecting to server: {str(e)}")