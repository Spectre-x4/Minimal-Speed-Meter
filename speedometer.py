import sys
import psutil
from PyQt5.QtWidgets import (
    QApplication, QLabel, QWidget, QVBoxLayout, QMenu,
    QSystemTrayIcon, QAction, QStyle
)
from PyQt5.QtCore import Qt, QTimer, QPoint, QSettings
from PyQt5.QtGui import QFont, QCursor, QIcon


class SpeedWidget(QWidget):
    def __init__(self):
        super().__init__()

        # ✅ Frameless, Transparent, Always on Top, No taskbar entry
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)

        # Font
        font = QFont("Segoe UI", 10)
        font.setStyleStrategy(QFont.PreferAntialias)

        # Labels
        self.download_label = QLabel("↓ 0 KB/s")
        self.upload_label = QLabel("↑ 0 KB/s")
        self.upload_label.hide()

        self.download_label.setFont(font)
        self.upload_label.setFont(font)
        self.download_label.setStyleSheet("color: white;")
        self.upload_label.setStyleSheet("color: lightgray;")

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)
        layout.addWidget(self.upload_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.download_label, alignment=Qt.AlignCenter)

        self.setLayout(layout)
        self.setStyleSheet("background-color: rgba(30,30,30,180); border-radius: 8px;")

        self.prev_bytes_sent = psutil.net_io_counters().bytes_sent
        self.prev_bytes_recv = psutil.net_io_counters().bytes_recv

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_speed)
        self.timer.start(1000)

        self.setFixedSize(130, 50)
        self.drag_pos = None

        self.settings = QSettings("SpeedMeter", "App")
        self.load_position()

        # 🔔 System Tray
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(QApplication.style().standardIcon(QStyle.SP_ComputerIcon)))

        tray_menu = QMenu()
        self.pause_action = QAction("Pause")
        self.reset_action = QAction("Reset Counters")
        quit_action = QAction("Exit")

        tray_menu.addAction(self.pause_action)
        tray_menu.addAction(self.reset_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)

        self.pause_action.triggered.connect(self.toggle_pause)
        self.reset_action.triggered.connect(self.reset_counters)
        quit_action.triggered.connect(QApplication.quit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        self.is_paused = False

    def update_speed(self):
        if self.is_paused:
            return

        current = psutil.net_io_counters()
        down = current.bytes_recv - self.prev_bytes_recv
        up = current.bytes_sent - self.prev_bytes_sent
        self.prev_bytes_recv = current.bytes_recv
        self.prev_bytes_sent = current.bytes_sent

        self.download_label.setText(f"↓ {self.format_speed(down)}")
        self.upload_label.setText(f"↑ {self.format_speed(up)}")

    def format_speed(self, bytes_per_sec):
        kb = bytes_per_sec / 1024
        if kb > 1000:
            return f"{kb / 1024:.1f} MB/s"
        return f"{kb:.0f} KB/s"

    def enterEvent(self, event):
        self.upload_label.show()

    def leaveEvent(self, event):
        self.upload_label.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
        elif event.button() == Qt.RightButton:
            self.show_context_menu(event.globalPos())

    def mouseMoveEvent(self, event):
        if self.drag_pos and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_pos)

    def mouseReleaseEvent(self, event):
        self.drag_pos = None
        self.save_position()

    def show_context_menu(self, pos):
        menu = QMenu()
        pause_action = menu.addAction("Pause" if not self.is_paused else "Resume")
        reset_action = menu.addAction("Reset Counters")
        quit_action = menu.addAction("Exit")
        action = menu.exec_(pos)

        if action == pause_action:
            self.toggle_pause()
        elif action == reset_action:
            self.reset_counters()
        elif action == quit_action:
            QApplication.quit()

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        self.pause_action.setText("Resume" if self.is_paused else "Pause")

    def reset_counters(self):
        current = psutil.net_io_counters()
        self.prev_bytes_sent = current.bytes_sent
        self.prev_bytes_recv = current.bytes_recv

    def save_position(self):
        self.settings.setValue("pos", self.pos())

    def load_position(self):
        if self.settings.contains("pos"):
            self.move(self.settings.value("pos", type=QPoint))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # ⚠️ Important to keep tray running
    widget = SpeedWidget()
    widget.show()
    sys.exit(app.exec_())
