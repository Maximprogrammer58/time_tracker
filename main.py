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
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem, QLineEdit, QMessageBox,
    QTabWidget, QHBoxLayout, QDialog, QTextEdit, QListWidget, QProgressBar, QListWidgetItem, QDateEdit
)
from PyQt5.QtCore import Qt, QTimer

USER_DATABASE = {
    '': '',
}


def initialize_database():
    conn = sqlite3.connect('app_tracker.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT,
            end_time TEXT,
            total_time TEXT,
            results TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print("База данных и таблица инициализированы.")


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

        if USER_DATABASE.get(username) == password:
            self.on_login_success()
            self.close()
        else:
            QMessageBox.warning(self, 'Ошибка', 'Неверный логин или пароль.')


class AppTracker:
    def __init__(self):
        self.app_summaries = {}
        self.running = False
        self.start_time = datetime.datetime.now()
        self.total_time_seconds = 0  # Инициализация общего времени
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
                        self.total_time_seconds += 1  # Увеличение общего времени
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
        return self.print_summary()


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
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: #ffffff;")

        self.tabs = QTabWidget(self)
        self.measurement_tab = QWidget()
        self.data_tab = QWidget()
        self.analytics_tab = QWidget()

        self.tabs.addTab(self.measurement_tab, "Замер")
        self.tabs.addTab(self.data_tab, "Данные")
        self.tabs.addTab(self.analytics_tab, "Аналитика")

        self.init_measurement_tab()
        self.init_data_tab()
        self.init_analytics_tab()

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def init_measurement_tab(self):
        layout = QVBoxLayout()

        self.endButton = QPushButton('Закончить', self)
        self.startButton = QPushButton('Начать замер')

        self.startButton.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 10px;
                font-size: 16px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)

        self.endButton.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                padding: 10px;
                font-size: 16px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)

        self.endButton.setVisible(False)

        self.startButton.clicked.connect(self.startMeasurement)
        self.endButton.clicked.connect(self.endMeasurement)

        self.table = QTableWidget(self)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Приложение", "Время"])
        self.table.setRowCount(0)

        layout.addWidget(self.endButton)
        layout.addWidget(self.startButton)
        layout.addWidget(self.table)
        layout.setAlignment(Qt.AlignTop)
        self.measurement_tab.setLayout(layout)

    def init_data_tab(self):
        layout = QVBoxLayout()

        self.data_table = QTableWidget(self)
        self.data_table.setColumnCount(4)
        self.data_table.setHorizontalHeaderLabels(["Время начала", "Время конца", "Общее время", "Действия"])
        self.data_table.setRowCount(0)

        self.load_data()

        layout.addWidget(self.data_table)
        self.data_tab.setLayout(layout)

    def load_data(self):
        self.data_table.setRowCount(0)
        conn = sqlite3.connect('app_tracker.db')
        cursor = conn.cursor()

        cursor.execute('SELECT start_time, end_time, total_time, results FROM app_usage')
        rows = cursor.fetchall()

        for row in rows:
            start_time, end_time, total_time, results = row
            row_position = self.data_table.rowCount()
            self.data_table.insertRow(row_position)
            self.data_table.setItem(row_position, 0, QTableWidgetItem(start_time))
            self.data_table.setItem(row_position, 1, QTableWidgetItem(end_time))
            self.data_table.setItem(row_position, 2, QTableWidgetItem(total_time))

            details_button = QPushButton("Подробнее")
            details_button.clicked.connect(lambda checked, r=results, t=total_time: self.show_details(r, t))
            self.data_table.setCellWidget(row_position, 3, details_button)

        conn.close()

    def init_analytics_tab(self):
        layout = QVBoxLayout()

        self.start_date_label = QLabel('Дата начала:', self)
        self.start_date_input = QDateEdit(self)
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDisplayFormat("dd-MM-yyyy")
        self.start_date_input.setStyleSheet("font-size: 16px; padding: 5px;")

        self.end_date_label = QLabel('Дата конца:', self)
        self.end_date_input = QDateEdit(self)
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setDisplayFormat("dd-MM-yyyy")
        self.end_date_input.setStyleSheet("font-size: 16px; padding: 5px;")

        self.search_button = QPushButton('Поиск', self)
        self.search_button.clicked.connect(self.search_data)
        self.search_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 10px;
                font-size: 16px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)

        self.analytics_table = QTableWidget(self)
        self.analytics_table.setColumnCount(2)
        self.analytics_table.setHorizontalHeaderLabels(["Время замера", "Продолжительность"])
        self.analytics_table.setRowCount(0)

        layout.addWidget(self.start_date_label)
        layout.addWidget(self.start_date_input)
        layout.addWidget(self.end_date_label)
        layout.addWidget(self.end_date_input)
        layout.addWidget(self.search_button)
        layout.addWidget(self.analytics_table)

        self.analytics_tab.setLayout(layout)

    def search_data(self):
        start_date = self.start_date_input.date().toString("dd.MM.yy")
        end_date = self.end_date_input.date().toString("dd.MM.yy")

        if not start_date or not end_date:
            QMessageBox.warning(self, 'Ошибка', 'Введите обе даты.')
            return

        self.analytics_table.setRowCount(0)
        conn = sqlite3.connect('app_tracker.db')
        cursor = conn.cursor()

        cursor.execute('''
                SELECT start_time, end_time, total_time FROM app_usage 
                WHERE start_time >= ? AND end_time <= ?
            ''', (start_date + " 00:00:00", end_date + " 23:59:59"))

        rows = cursor.fetchall()

        total_time_data = []
        labels = []

        for row in rows:
            start_time, end_time, total_time = row
            row_position = self.analytics_table.rowCount()
            self.analytics_table.insertRow(row_position)
            self.analytics_table.setItem(row_position, 0, QTableWidgetItem(start_time + " - " + end_time))
            self.analytics_table.setItem(row_position, 1, QTableWidgetItem(str(total_time)))

            labels.append(start_time + " - " + end_time)
            total_time_data.append(self.time_to_seconds(total_time))

        conn.close()

        if total_time_data:
            plt.figure(figsize=(10, 6))
            plt.bar(labels, total_time_data, color='skyblue')
            plt.xlabel('Промежутки времени')
            plt.ylabel('Общее время (секунды)')
            plt.title('Столбчатая диаграмма общего времени по промежуткам')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.show()


    def time_to_seconds(self, time_str):
        hours, minutes, seconds = 0, 0, 0
        if 'ч' in time_str:
            hours = int(time_str.split('ч')[0].strip())
            time_str = time_str.split('ч')[1]
        if 'мин' in time_str:
            minutes = int(time_str.split('мин')[0].strip())
            time_str = time_str.split('мин')[1]
        if 'сек' in time_str:
            seconds = int(time_str.split('сек')[0].strip())
        return hours * 3600 + minutes * 60 + seconds

    def show_details(self, results, total_time):
        details_dialog = QDialog(self)
        details_dialog.setWindowTitle("Детали использования")
        details_dialog.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()
        details_list = QListWidget()

        parsed_results = json.loads(results)
        total_time_seconds = self.time_to_seconds(total_time)

        for app, time in parsed_results.items():
            app_time_seconds = self.time_to_seconds(time)

            item = QListWidgetItem(f"{app}: {time}")
            details_list.addItem(item)

            progress_bar = QProgressBar()
            if total_time_seconds > 0:
                percentage = (app_time_seconds / total_time_seconds) * 100
                progress_bar.setValue(int(percentage))
            else:
                progress_bar.setValue(0)
            details_list.addItem(QListWidgetItem())
            details_list.setItemWidget(details_list.item(details_list.count() - 1), progress_bar)

        layout.addWidget(details_list)
        details_dialog.setLayout(layout)
        details_dialog.exec_()

    def startMeasurement(self):
        if self.tracker is None or not self.tracker.running:
            self.tracker = AppTracker()
            self.startButton.setVisible(False)
            self.endButton.setVisible(True)

            self.tracker_thread = threading.Thread(target=self.tracker.start_tracking)
            self.tracker_thread.start()

            self.timer.start(10000)
            self.data_timer.start(10000)

    def update_table(self):
        if self.tracker and self.tracker.running:
            summaries = self.tracker.print_summary()
            self.table.setRowCount(0)
            for app, time in summaries.items():
                row_position = self.table.rowCount()
                self.table.insertRow(row_position)
                self.table.setItem(row_position, 0, QTableWidgetItem(app))
                self.table.setItem(row_position, 1, QTableWidgetItem(time))

    def endMeasurement(self):
        if self.tracker:
            self.timer.stop()
            self.data_timer.stop()
            results = self.tracker.stop_tracking()

            # Записываем данные в базу данных
            self.save_to_database(results)

            self.load_data()

            self.startButton.setVisible(True)
            self.endButton.setVisible(False)
            self.tracker_thread.join()
            self.tracker = None

    def save_to_database(self, results):
        conn = sqlite3.connect('app_tracker.db')
        cursor = conn.cursor()

        end_time = datetime.datetime.now()
        total_time = self.tracker.format_time(self.tracker.total_time_seconds)  # Получаем общее время из tracker

        cursor.execute('''
            INSERT INTO app_usage (start_time, end_time, total_time, results)
            VALUES (?, ?, ?, ?)
        ''', (self.tracker.start_time.strftime("%d.%m.%y %H:%M:%S"), end_time.strftime("%d.%m.%y %H:%M:%S"), total_time,
              json.dumps(results)))

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
    initialize_database()
    main_app = MainApp()
    main_app.run()
