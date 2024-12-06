import datetime
import json
import threading

import matplotlib.pyplot as plt
import requests

from tracker import AppTracker, WindowTracker
from database import execute_query
from json_helper import read_json
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem, QMessageBox,
    QTabWidget, QDialog, QListWidget, QProgressBar, QListWidgetItem, QDateEdit
)


class MeasurementApp(QWidget):
    def __init__(self):
        super().__init__()
        self.tracker = None
        self.window_tracker = None
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
        self.data_table.setColumnCount(5)
        self.data_table.setHorizontalHeaderLabels(["Время начала", "Время конца", "Общее время", "Действия", "Журнал"])
        self.data_table.setRowCount(0)

        self.load_data()

        layout.addWidget(self.data_table)
        self.data_tab.setLayout(layout)

    def load_data(self):
        self.data_table.setRowCount(0)

        rows = execute_query('SELECT start_time, end_time, total_time, results, visited_apps FROM app_usage')

        for row in rows:
            start_time, end_time, total_time, results, visited_apps = row
            row_position = self.data_table.rowCount()
            self.data_table.insertRow(row_position)
            self.data_table.setItem(row_position, 0, QTableWidgetItem(start_time))
            self.data_table.setItem(row_position, 1, QTableWidgetItem(end_time))
            self.data_table.setItem(row_position, 2, QTableWidgetItem(total_time))

            details_button_1 = QPushButton("Подробнее")
            details_button_1.clicked.connect(lambda checked, r=results, t=total_time: self.show_details(r, t))
            self.data_table.setCellWidget(row_position, 3, details_button_1)

            journal_button = QPushButton("Журнал")
            journal_button.clicked.connect(lambda checked, v=visited_apps: self.show_journal(v))
            self.data_table.setCellWidget(row_position, 4, journal_button)

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

        rows = execute_query('''
                SELECT start_time, end_time, total_time FROM app_usage 
                WHERE start_time >= ? AND end_time <= ?
            ''', (start_date + " 00:00:00", end_date + " 23:59:59"))

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

        if total_time_data:
            plt.figure(figsize=(10, 6))
            plt.bar(labels, total_time_data, color='skyblue')
            plt.xlabel('Промежутки времени')
            plt.ylabel('Общее время (секунды)')
            plt.title('Столбчатая диаграмма общего времени по промежуткам')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.show()

        self.generate_popularity_chart(start_date, end_date)

    def generate_popularity_chart(self, start_date, end_date):
        rows = execute_query('''
                       SELECT results FROM app_usage 
                       WHERE start_time >= ? AND end_time <= ?
                   ''', (start_date + " 00:00:00", end_date + " 23:59:59"))

        app_usage = {}

        for row in rows:
            results = json.loads(row[0])
            for app, time in results.items():
                if app not in app_usage:
                    app_usage[app] = 0
                app_usage[app] += self.time_to_seconds(time)

        apps = list(app_usage.keys())
        usage_times = list(app_usage.values())

        plt.figure(figsize=(10, 6))
        plt.bar(apps, usage_times, color='lightgreen')
        plt.xlabel('Приложения')
        plt.ylabel('Общее время использования (сек)')
        plt.title('Наиболее популярные приложения по времени использования')
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

    def show_journal(self, visited_apps):
        journal_dialog = QDialog(self)
        journal_dialog.setWindowTitle("Журнал посещенных приложений")
        journal_dialog.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()
        journal_table = QTableWidget(journal_dialog)
        journal_table.setColumnCount(2)
        journal_table.setHorizontalHeaderLabels(["Приложение", "Время использования"])
        journal_table.setRowCount(0)

        visited_apps_dict = json.loads(visited_apps)

        for app, time in visited_apps_dict.items():
            row_position = journal_table.rowCount()
            journal_table.insertRow(row_position)
            journal_table.setItem(row_position, 0, QTableWidgetItem(app))
            journal_table.setItem(row_position, 1, QTableWidgetItem(AppTracker.format_time(time)))

        layout.addWidget(journal_table)
        journal_dialog.setLayout(layout)
        journal_dialog.exec_()

    def startMeasurement(self):
        if self.tracker is None or not self.tracker.running:
            self.tracker = AppTracker()
            self.window_tracker = WindowTracker()
            self.startButton.setVisible(False)
            self.endButton.setVisible(True)

            self.tracker_thread = threading.Thread(target=self.tracker.start_tracking)
            self.tracker_thread.start()

            self.window_tracker.start_tracking()
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

            visited_apps = self.window_tracker.stop_tracking()

            self.save_to_database(results, visited_apps)
            self.send_data_to_server(results, visited_apps)
            self.load_data()

            self.startButton.setVisible(True)
            self.endButton.setVisible(False)
            self.tracker_thread.join()
            self.tracker = None
            self.window_tracker = None

    def save_to_database(self, results, visited_apps):
        end_time = datetime.datetime.now()
        total_time = self.tracker.format_time(self.tracker.total_time_seconds)

        execute_query('''
            INSERT INTO app_usage (start_time, end_time, total_time, results, visited_apps)
            VALUES (?, ?, ?, ?, ?)
        ''', (self.tracker.start_time.strftime("%d.%m.%y %H:%M:%S"), end_time.strftime("%d.%m.%y %H:%M:%S"), total_time,
            json.dumps(results), json.dumps(visited_apps)), fetch=False)

    def send_data_to_server(self, results, visited_apps):
        settings = read_json("settings.json")
        api_data = read_json(settings["path_data_file"])

        end_time = datetime.datetime.now()
        data = {
            "first_name": api_data["first_name"],
            "last_name": api_data["last_name"],
            "email": api_data["email"],
            "start_time": self.tracker.start_time.strftime("%d.%m.%y %H:%M:%S"),
            "end_time": end_time.strftime("%d.%m.%y %H:%M:%S"),
            "total_time": self.tracker.format_time(self.tracker.total_time_seconds),
            "results": results,
            "visited_apps": visited_apps,
            "boss_token": api_data["boss_token"]
        }

        try:
            response = requests.post(settings["url_server_data"], json=data)
            if response.status_code == 200:
                print("Данные успешно отправлены на сервер.")
            else:
                print("Ошибка при отправке данных:", response.text)
        except Exception as e:
            print("Ошибка подключения к серверу:", str(e))