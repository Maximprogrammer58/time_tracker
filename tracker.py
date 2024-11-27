import datetime
import os
import time
import threading

import ctypes
import psutil
import pygetwindow as gw

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


class WindowTracker:
    def __init__(self):
        self.visited_apps = {}
        self.running = False
        self.current_app = None
        self.app_start_time = None

    def clean_string(self, s):
        return ''.join(c for c in s if c.isprintable())

    def track_active_windows(self):
        self.running = True
        while self.running:
            active_window = gw.getActiveWindow()
            current_time = datetime.datetime.now()

            if active_window:
                app_title = self.clean_string(active_window.title)

                if app_title != self.current_app:
                    # Если приложение изменилось, сохраняем время для предыдущего приложения
                    if self.current_app:
                        elapsed_time = (current_time - self.app_start_time).total_seconds()
                        if self.current_app in self.visited_apps:
                            self.visited_apps[self.current_app] += elapsed_time
                        else:
                            self.visited_apps[self.current_app] = elapsed_time

                    self.current_app = app_title
                    self.app_start_time = current_time

            time.sleep(1)

    def start_tracking(self):
        tracking_thread = threading.Thread(target=self.track_active_windows)
        tracking_thread.start()

    def stop_tracking(self):
        self.running = False
        if self.current_app and self.app_start_time:
            elapsed_time = (datetime.datetime.now() - self.app_start_time).total_seconds()
            if self.current_app in self.visited_apps:
                self.visited_apps[self.current_app] += elapsed_time
            else:
                self.visited_apps[self.current_app] = elapsed_time
        return self.visited_apps