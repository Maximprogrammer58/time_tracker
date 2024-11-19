import sys
import psutil
import ctypes
from ctypes import wintypes
import time
import datetime
import os
import json
import sqlite3
import threading
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem, QLineEdit, QMessageBox,
    QTabWidget, QHBoxLayout, QDialog, QTextEdit, QListWidget
)
from PyQt5.QtCore import Qt, QTimer

USER_DATABASE = {
    'admin': 'password123',  # Логин: admin, Пароль: password123
}

class AuthWindow(QWidget):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Авторизация')
        self.setGeometry(100, 100, 250, 120)  # Уменьшение размера окна

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

        if USER_DATABASE.get(username) == password:
            self.on_login_success()  # Вход успешен
            self.close()
        else:
            QMessageBox.warning(self, 'Ошибка', 'Неверный логин или пароль.')

class AppTracker:
    def __init__(self):
        self.app_summaries = {}
        self.running = False
        self.start_time = datetime.datetime.now()
        self.user = os.getlogin()
        print(self.data_time(), "Старт, пользователь:", self.user)

    def data_time(self):
        now = datetime.datetime.now()
        return now.strftime("%d.%m.%y %H:%M:%S")

    def format_time(self, total_seconds):
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours)} ч {int(minutes)} мин {int(seconds)} сек"

    def print_summary(self):
        print(self.data_time(), "Цикл остановлен")
        return {app: self.format_time(summ) for app, summ in self.app_summaries.items()}

    def track_apps(self):
        try:
            while self.running:
                pid = wintypes.DWORD()
                active = ctypes.windll.user32.GetForegroundWindow()
                active_window = ctypes.windll.user32.GetWindowThreadProcessId(active, ctypes.byref(pid))
                pid = pid.value

                for item in psutil.process_iter():
                    if pid == item.pid:
                        name_aw = item.name()
                        if name_aw not in self.app_summaries:
                            self.app_summaries[name_aw] = 0
                        self.app_summaries[name_aw] += 1
                        break

                time.sleep(1)

        except Exception as e:
            print(f"Ошибка: {e}")
            self.print_summary()

    def start_tracking(self):
        self.running = True
        self.track_apps()

    def stop_tracking(self):
        self.running = False
        return self.print_summary()  # Возвращаем результаты

class MeasurementApp(QWidget):
    def __init__(self):
        super().__init__()
        self.tracker = None
        self.initUI()
        self.timer = QTimer()
        self.data_timer = QTimer()
        self.timer.timeout.connect(self.update_table)
        self.data_timer.timeout.connect(self.load_data)

    def initUI(self):
        self.setWindowTitle('Замер времени')
        self.setGeometry(100, 100, 500, 300)  # Уменьшение размера окна
        self.setStyleSheet("background-color: #ffffff;")

        # Создаем вкладки
        self.tabs = QTabWidget(self)
        self.measurement_tab = QWidget()
        self.data_tab = QWidget()

        self.tabs.addTab(self.measurement_tab, "Замер")
        self.tabs.addTab(self.data_tab, "Данные")

        self.init_measurement_tab()
        self.init_data_tab()

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def init_measurement_tab(self):
        layout = QVBoxLayout()

        self.endButton = QPushButton('Закончить', self)
        self.startButton = QPushButton('Начать замер')

        self.startButton.setStyleSheet("""
            QPushButton {
                background-color: #28a745; /* Зеленый */
                color: white;
                padding: 10px;
                font-size: 16px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838; /* Темно-зеленый */
            }
        """)

        self.endButton.setStyleSheet("""
            QPushButton {
                background-color: #dc3545; /* Красный */
                color: white;
                padding: 10px;
                font-size: 16px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c82333; /* Темно-красный */
            }
        """)

        self.endButton.setVisible(False)  # Скрываем кнопку "Закончить" изначально

        # Подключаем кнопки к методам
        self.startButton.clicked.connect(self.startMeasurement)
        self.endButton.clicked.connect(self.endMeasurement)

        # Создаем таблицу
        self.table = QTableWidget(self)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Приложение", "Время"])
        self.table.setRowCount(0)

        layout.addWidget(self.endButton)
        layout.addWidget(self.startButton)
        layout.addWidget(self.table)
        layout.setAlignment(Qt.AlignTop)  # Центрируем кнопки сверху
        self.measurement_tab.setLayout(layout)

    def init_data_tab(self):
        layout = QVBoxLayout()

        self.data_table = QTableWidget(self)
        self.data_table.setColumnCount(3)
        self.data_table.setHorizontalHeaderLabels(["Время начала", "Время конца", "Действия"])
        self.data_table.setRowCount(0)

        self.load_data()

        layout.addWidget(self.data_table)
        self.data_tab.setLayout(layout)

    def load_data(self):
        self.data_table.setRowCount(0)  # Очищаем таблицу перед загрузкой
        conn = sqlite3.connect('app_tracker.db')
        cursor = conn.cursor()

        cursor.execute('SELECT start_time, end_time, results FROM app_usage')
        rows = cursor.fetchall()

        for row in rows:
            start_time, end_time, results = row
            row_position = self.data_table.rowCount()
            self.data_table.insertRow(row_position)
            self.data_table.setItem(row_position, 0, QTableWidgetItem(start_time))
            self.data_table.setItem(row_position, 1, QTableWidgetItem(end_time))

            details_button = QPushButton("Подробнее")
            details_button.clicked.connect(lambda checked, r=results: self.show_details(r))
            self.data_table.setCellWidget(row_position, 2, details_button)

        conn.close()

    def show_details(self, results):
        details_dialog = QDialog(self)
        details_dialog.setWindowTitle("Детали использования")
        details_dialog.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()
        details_list = QListWidget()

        parsed_results = json.loads(results)
        for app, time in parsed_results.items():
            details_list.addItem(f"{app}: {time}")

        layout.addWidget(details_list)
        details_dialog.setLayout(layout)
        details_dialog.exec_()

    def startMeasurement(self):
        if self.tracker is None or not self.tracker.running:
            self.tracker = AppTracker()  # Создаем новый экземпляр AppTracker
            self.startButton.setVisible(False)  # Скрываем кнопку "Начать замер"
            self.endButton.setVisible(True)  # Показываем кнопку "Закончить"

            # Запускаем отслеживание в отдельном потоке
            self.tracker_thread = threading.Thread(target=self.tracker.start_tracking)
            self.tracker_thread.start()

            # Запускаем таймер для обновления таблицы
            self.timer.start(60000)  # Каждые 1 минуту
            self.data_timer.start(60000)  # Каждые 1 минуту для обновления данных

    def update_table(self):
        if self.tracker and self.tracker.running:
            summaries = self.tracker.print_summary()
            self.table.setRowCount(0)  # Очищаем таблицу
            for app, time in summaries.items():
                row_position = self.table.rowCount()
                self.table.insertRow(row_position)
                self.table.setItem(row_position, 0, QTableWidgetItem(app))
                self.table.setItem(row_position, 1, QTableWidgetItem(time))

    def endMeasurement(self):
        if self.tracker:
            self.timer.stop()  # Останавливаем таймер
            self.data_timer.stop()  # Останавливаем таймер для данных
            results = self.tracker.stop_tracking()  # Останавливаем отслеживание

            # Записываем данные в базу данных
            self.save_to_database(results)

            self.load_data()  # Обновляем данные в таблице

            self.startButton.setVisible(True)  # Показываем кнопку "Начать замер"
            self.endButton.setVisible(False)  # Скрываем кнопку "Закончить"
            self.tracker_thread.join()  # Ждем завершения потока
            self.tracker = None  # Сбрасываем трекер

    def save_to_database(self, results):
        conn = sqlite3.connect('app_tracker.db')
        cursor = conn.cursor()

        # Создаем таблицу, если она не существует
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TEXT,
                end_time TEXT,
                results TEXT
            )
        ''')

        end_time = datetime.datetime.now().strftime("%d.%m.%y %H:%M:%S")
        # Формируем словарь с результатами
        formatted_results = {app: time for app, time in results.items()}

        cursor.execute('''
            INSERT INTO app_usage (start_time, end_time, results)
            VALUES (?, ?, ?)
        ''', (self.tracker.start_time.strftime("%d.%m.%y %H:%M:%S"), end_time, json.dumps(formatted_results)))

        conn.commit()
        conn.close()
        print("Данные сохранены в базу данных.")

class MainApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.auth_window = AuthWindow(self.open_measurement_app)
        self.auth_window.show()

    def open_measurement_app(self):
        self.auth_window.close()
        self.measurement_app = MeasurementApp()
        self.measurement_app.show()

    def run(self):
        sys.exit(self.app.exec_())

if __name__ == '__main__':
    main_app = MainApp()
    main_app.run()
