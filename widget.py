import sys
import random
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QPainterPath

class WisprWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.width_val = 200
        self.height_val = 60
        self.resize(self.width_val, self.height_val)
        
        # Position at the bottom center of the primary screen
        # Usually taskbar is 40-50px. Let's place it 80px from bottom.
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width_val) // 2
        y = screen.height() - self.height_val - 120
        self.move(x, y)
        
        self.is_recording = False
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50) # 20 fps
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw pill background
        painter.setBrush(QColor(30, 30, 30, 220))
        painter.setPen(Qt.PenStyle.NoPen)
        rect = QRectF(0, 0, self.width_val, self.height_val)
        painter.drawRoundedRect(rect, self.height_val/2, self.height_val/2)
        
        if self.is_recording:
            # Draw waveform
            painter.setPen(QPen(QColor(187, 134, 252), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            
            center_y = self.height_val / 2
            num_bars = 10
            bar_spacing = 15
            start_x = (self.width_val - (num_bars * bar_spacing)) / 2 + (bar_spacing/2)
            
            for i in range(num_bars):
                # Random height for waveform effect
                h = random.randint(10, 40)
                painter.drawLine(int(start_x + i * bar_spacing), int(center_y - h/2),
                                 int(start_x + i * bar_spacing), int(center_y + h/2))
        else:
            # Draw idle indicator
            painter.setBrush(QColor(100, 100, 100))
            painter.drawEllipse(int(self.width_val/2 - 6), int(self.height_val/2 - 6), 12, 12)

def run_widget_app(command_queue):
    app = QApplication(sys.argv)
    widget = WisprWidget()
    
    def check_queue():
        while not command_queue.empty():
            cmd = command_queue.get()
            if cmd == "START":
                widget.is_recording = True
                widget.show()
            elif cmd == "STOP":
                widget.is_recording = False
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
