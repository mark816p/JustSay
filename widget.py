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
        self.height_val = 60
        self.resize(self.width_val, self.height_val)
        
        # Position at the bottom center of the primary screen
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width_val) // 2
        y = screen.height() - self.height_val - 120
        self.move(x, y)
        
        self.is_recording = False
        
        self.undo_btn = QPushButton("Add Custom Word?", self)
        self.undo_btn.setGeometry(50, 15, 200, 30)
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
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw pill background
        painter.setBrush(QColor(30, 30, 30, 225))
        painter.setPen(Qt.PenStyle.NoPen)
        rect = QRectF(0, 0, self.width_val, self.height_val)
        painter.drawRoundedRect(rect, self.height_val/2, self.height_val/2)
        
        if self.is_recording:
            # Draw waveform (monochromatic grey)
            painter.setPen(QPen(QColor(150, 150, 150), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            
            center_y = self.height_val / 2
            num_bars = 10
            bar_spacing = 15
            start_x = (self.width_val - (num_bars * bar_spacing)) / 2 + (bar_spacing/2)
            
            for i in range(num_bars):
                h = random.randint(10, 40)
                painter.drawLine(int(start_x + i * bar_spacing), int(center_y - h/2),
                                 int(start_x + i * bar_spacing), int(center_y + h/2))
        elif not self.undo_btn.isVisible():
            # Draw idle indicator
            painter.setBrush(QColor(100, 100, 100))
            painter.drawEllipse(int(self.width_val/2 - 6), int(self.height_val/2 - 6), 12, 12)

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
    
    def check_queue():
        while not command_queue.empty():
            cmd = command_queue.get()
            if cmd == "START":
                widget.is_recording = True
                widget.undo_btn.hide()
                widget.show()
            elif cmd == "STOP":
                widget.is_recording = False
            elif cmd == "PASTED":
                widget.show_undo_btn()
            elif cmd == "SHOW":
                widget.show()
            elif cmd == "HIDE":
                widget.hide()
            elif cmd == "QUIT":
                app.quit()
    
    timer = QTimer()
    timer.timeout.connect(check_queue)
    timer.start(100)
    
    widget.show()
    sys.exit(app.exec())
