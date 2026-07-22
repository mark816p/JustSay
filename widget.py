import sys
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QInputDialog, QMessageBox
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QPainter, QColor
import database


class JustSayWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.width_val = 140
        self.height_val = 60
        self.resize(self.width_val, self.height_val)

        # Position at the bottom center of the primary screen
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width_val) // 2
        y = screen.height() - self.height_val - 60
        self.move(x, y)

        self.show_ui = True

        self.is_recording = False

        self.undo_btn = QPushButton("Add Word?", self)
        self.undo_btn.setGeometry(20, 15, 100, 30)
        self.undo_btn.setStyleSheet("""
            QPushButton {
                background-color: #4b5563;
                color: white;
                border-radius: 10px;
                font-weight: bold;
                font-family: Arial, sans-serif;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #6b7280;
            }
        """)
        self.undo_btn.clicked.connect(self.add_word_action)
        self.undo_btn.hide()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)  # 20 fps

    def paintEvent(self, event):
        if not self.show_ui:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.is_recording:
            # Animate width based on volume
            target_w = 40 + \
                min((getattr(self, 'current_volume', 0) / 2000.0) * 80, 80)
            if not hasattr(self, 'animated_w'):
                self.animated_w = 40
            self.animated_w += (target_w - self.animated_w) * 0.2

            pill_w = max(40, self.animated_w)
            pill_h = 40
            start_x = (self.width_val - pill_w) / 2
            start_y = (self.height_val - pill_h) / 2

            # Glowing blue orb style for active recording
            if not hasattr(self, 'pulse_alpha'):
                self.pulse_alpha = 150
                self.pulse_dir = 8

            self.pulse_alpha += self.pulse_dir
            if self.pulse_alpha >= 255:
                self.pulse_alpha = 255
                self.pulse_dir = -8
            elif self.pulse_alpha <= 120:
                self.pulse_alpha = 120
                self.pulse_dir = 8

            # Draw outer glow
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(59, 130, 246, int(
                self.pulse_alpha * 0.4)))  # Blue glow
            painter.drawRoundedRect(QRectF(
                start_x - 6, start_y - 6, pill_w + 12, pill_h + 12), (pill_h + 12) / 2, (pill_h + 12) / 2)

            # Draw inner pill
            painter.setBrush(
                QColor(37, 99, 235, self.pulse_alpha))  # Solid blue
            painter.drawRoundedRect(
                QRectF(start_x, start_y, pill_w, pill_h), pill_h / 2, pill_h / 2)

            # Draw listening icon/dots
            painter.setBrush(QColor(255, 255, 255, 255))
            painter.drawEllipse(
                QRectF(self.width_val/2 - 4, self.height_val/2 - 4, 8, 8))
        else:
            # Idle state: very subtle translucent small pill
            pill_w = 20
            pill_h = 6
            start_x = (self.width_val - pill_w) / 2
            start_y = self.height_val - pill_h - 4

            if hasattr(self, 'pulse_alpha'):
                del self.pulse_alpha
            if hasattr(self, 'animated_w'):
                del self.animated_w

            painter.setPen(Qt.PenStyle.NoPen)
            # Light translucent pill for dark themes
            painter.setBrush(QColor(255, 255, 255, 40))
            painter.drawRoundedRect(
                QRectF(start_x, start_y, pill_w, pill_h), pill_h / 2, pill_h / 2)

    def add_word_action(self):
        self.undo_btn.hide()

        # Prompt user to input the correct word to teach the transcriber
        text, ok = QInputDialog.getText(
            self, 'Vocabulary', 'Add word/phrase to local dictionary:')
        if ok and text.strip():
            database.add_to_dictionary(text.strip())
            # Show a brief notification
            msg = QMessageBox(self)
            msg.setWindowTitle("Dictionary")
            msg.setText(f"Added '{text.strip()}' to dictionary!")
            msg.setStyleSheet("background-color: #222; color: white;")
            QTimer.singleShot(1500, msg.close)
            msg.show()

    def show_undo_btn(self):
        self.undo_btn.show()
        # Hide it after exactly 2 seconds
        QTimer.singleShot(2000, self.undo_btn.hide)


def run_widget_app(command_queue):
    app = QApplication(sys.argv)
    widget = JustSayWidget()
    widget.current_volume = 0

    db_check_counter = 0

    def check_queue():
        nonlocal db_check_counter
        while not command_queue.empty():
            cmd = command_queue.get()
            if cmd == "START":
                widget.is_recording = True
                widget.current_volume = 0
                widget.undo_btn.hide()
            elif cmd == "STOP":
                widget.is_recording = False
                widget.current_volume = 0
            elif cmd.startswith("VOL:"):
                try:
                    vol = float(cmd.split(":")[1])
                    widget.current_volume = vol
                except:
                    pass
            elif cmd == "PASTED":
                if widget.show_ui:
                    widget.show_undo_btn()
            elif cmd == "SHOW":
                widget.show()
            elif cmd == "HIDE":
                widget.hide()
            elif cmd == "QUIT":
                app.quit()

        db_check_counter += 1
        if db_check_counter >= 10:
            db_check_counter = 0
            settings = database.get_user_settings("localuser@localhost")
            if settings:
                widget.show_ui = settings.get("show_ui", True)
                if not widget.show_ui and widget.isVisible():
                    widget.hide()
                elif widget.show_ui and not widget.isVisible():
                    widget.show()

    timer = QTimer()
    timer.timeout.connect(check_queue)
    timer.start(100)

    # Check settings initially
    settings = database.get_user_settings("localuser@localhost")
    if settings and not settings.get("show_ui", True):
        widget.hide()
    else:
        widget.show()
    sys.exit(app.exec())
