import datetime
import os
import time

import ctypes
import psutil

from ctypes import wintypes


class AppTracker:
    def __init__(self):
        self.app_summaries = {}
        self.running = False
        self.start_time = datetime.datetime.now()
        self.total_time_seconds = 0
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
                        self.total_time_seconds += 1
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