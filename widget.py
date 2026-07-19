import sys
import random
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QInputDialog, QMessageBox
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen
import keyboard
import threading
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
        
        self.width_val = 300
        self.height_val = 40
        self.resize(self.width_val, self.height_val)
        
        # Position at the bottom center of the primary screen
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width_val) // 2
        y = screen.height() - self.height_val - 20
        self.move(x, y)
        
        self.show_ui = True
        
        self.is_recording = False
        
        self.undo_btn = QPushButton("Add Custom Word?", self)
        self.undo_btn.setGeometry(50, 0, 200, 30)
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
        self.timer.start(50) # 20 fps
        
    def paintEvent(self, event):
        if not self.show_ui:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        line_w = 150
        start_x = (self.width_val - line_w) / 2
        
        if self.is_recording:
            # Animate height based on volume
            target_h = 3 + min((getattr(self, 'current_volume', 0) / 2000.0) * 12, 12)
            if not hasattr(self, 'animated_h'): self.animated_h = 3
            self.animated_h += (target_h - self.animated_h) * 0.4
            
            line_h = max(3, self.animated_h)
            start_y = self.height_val - line_h
            
            # Subtle red line that pulses smoothly when recording
            if not hasattr(self, 'pulse_alpha'):
                self.pulse_alpha = 100
                self.pulse_dir = 5
            
            self.pulse_alpha += self.pulse_dir
            if self.pulse_alpha >= 250:
                self.pulse_alpha = 250
                self.pulse_dir = -5
            elif self.pulse_alpha <= 50:
                self.pulse_alpha = 50
                self.pulse_dir = 5
                
            painter.setBrush(QColor(255, 50, 50, self.pulse_alpha))
        else:
            # Subtle black line when idle
            line_h = 3
            start_y = self.height_val - line_h
            if hasattr(self, 'pulse_alpha'):
                del self.pulse_alpha
            if hasattr(self, 'animated_h'):
                del self.animated_h
            painter.setBrush(QColor(0, 0, 0, 200))
            
        painter.setPen(Qt.PenStyle.NoPen)
        rect = QRectF(start_x, start_y, line_w, line_h)
        painter.drawRoundedRect(rect, 1.5, 1.5)

    def add_word_action(self):
        self.undo_btn.hide()
        
        # Prompt user to input the correct word to teach the transcriber
        text, ok = QInputDialog.getText(self, 'Vocabulary', 'Add word/phrase to local dictionary:')
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
                if widget.show_ui: widget.show_undo_btn()
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
