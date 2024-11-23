import sys

from auth_window import AuthWindow
from database import initialize_database
from measurement_app import MeasurementApp
from PyQt5.QtWidgets import QApplication


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
