import datetime
import time
import threading
import pygetwindow as gw

from modules.AppTracker import AppTracker


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
        self.visited_apps = {}
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
        return {app: AppTracker.format_time(summ) for app, summ in self.visited_apps.items()}