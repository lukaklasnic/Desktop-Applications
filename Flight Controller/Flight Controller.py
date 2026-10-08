import sys
import math
import os
import serial
import serial.tools.list_ports
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPixmap
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, 
                             QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QLabel, QGridLayout, QSizePolicy)

class SerialReaderThread(QThread):
    data_received = pyqtSignal(float, float, float, float, float, float, float)

    def __init__(self, port, baud=9600):
        super().__init__()
        self.port = port
        self.baud = baud
        self.running = True

    def run(self):
        try:
            ser = serial.Serial(self.port, self.baud, timeout=1)
            print(f"Uspelo povezivanje na {self.port}")
            while self.running:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    print(f"Primljeno: {line}")
                    parts = line.split(',')
                    if len(parts) >= 7:
                        ax = float(parts[0])
                        ay = float(parts[1])
                        az = float(parts[2])
                        gx = float(parts[3])
                        gy = float(parts[4])
                        gz = float(parts[5])
                        temp = float(parts[6])
                        
                        self.data_received.emit(ax, ay, az, gx, gy, gz, temp)
        except Exception as e:
            print(f"UART Greška: {e}")

    def stop(self):
        self.running = False
        self.wait()

class ArtificialHorizonWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.roll = 0.0   
        self.pitch = 0.0  
        self.setMinimumSize(220, 220)
        self.setMaximumSize(500, 500)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def set_values(self, ax, ay, az, gx=0.0, gy=0.0, gz=0.0, temp=0.0):
        self.roll = math.degrees(math.atan2(ay, az))
        self.pitch = math.degrees(math.atan2(-ax, math.sqrt(ay**2 + az**2)))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        center_x = width / 2
        center_y = height / 2
        radius = min(width, height) / 2 - 8

        painter.setBrush(QBrush(QColor(20, 20, 20, 230)))
        painter.setPen(QPen(QColor(100, 100, 100), 3))
        painter.drawEllipse(int(center_x - radius), int(center_y - radius), int(radius * 2), int(radius * 2))

        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(self.roll)
        
        pitch_offset = self.pitch * 2.5 
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(30, 144, 255)))
        painter.drawRect(int(-radius * 2), int(-radius * 2 + pitch_offset), int(radius * 4), int(radius * 2))
        painter.setBrush(QBrush(QColor(139, 69, 19)))
        painter.drawRect(int(-radius * 2), int(pitch_offset), int(radius * 4), int(radius * 2))

        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawLine(int(-radius * 2), int(pitch_offset), int(radius * 2), int(pitch_offset))
        painter.restore()

        painter.setPen(QPen(QColor(255, 255, 0), 2))
        painter.drawLine(int(center_x - 20), int(center_y), int(center_x - 6), int(center_y))
        painter.drawLine(int(center_x - 6), int(center_y), int(center_x - 6), int(center_y + 4))
        painter.drawLine(int(center_x + 6), int(center_y), int(center_x + 20), int(center_y))
        painter.drawLine(int(center_x + 6), int(center_y), int(center_x + 6), int(center_y + 4))
        painter.drawPoint(int(center_x), int(center_y))

        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.setFont(QFont("Arial", 8))
        painter.drawText(10, 18, f"R:{self.roll:.1f}°")
        painter.drawText(10, 30, f"P:{self.pitch:.1f}°")

class MapWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.base_width = 220
        self.base_height = 220
        self.setFixedSize(self.base_width, self.base_height)
        self.expanded = False

    def mousePressEvent(self, event):
        x = event.pos().x()
        y = event.pos().y()
        w = self.width()
        h = self.height()

        if x >= w - 35 and y >= h - 35:
            self.expanded = not self.expanded
            current_pos = self.pos()
            
            if self.expanded:
                new_w = self.base_width * 2
                new_h = self.base_height * 2
                self.setFixedSize(new_w, new_h)
                self.setGeometry(current_pos.x(), current_pos.y() - self.base_height, new_w, new_h)
                self.raise_()
            else:
                self.setFixedSize(self.base_width, self.base_height)
                self.setGeometry(current_pos.x(), current_pos.y() + self.base_height, self.base_width, self.base_height)
            
            self.update()
        else:
            super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        painter.setBrush(QBrush(QColor(35, 45, 55)))
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.drawRect(0, 0, width, height)

        painter.setPen(QPen(QColor(60, 75, 90), 1, Qt.PenStyle.DashLine))
        step = 30
        for x in range(0, width, step):
            painter.drawLine(x, 0, x, height)
        for y in range(0, height, step):
            painter.drawLine(0, y, width, y)

        painter.setPen(QPen(QColor(0, 255, 150), 2))
        painter.setBrush(QBrush(QColor(0, 255, 150, 100)))
        painter.drawEllipse(int(width / 2) - 6, int(height / 2) - 6, 12, 12)

        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        painter.drawText(12, 22, "MAPA / GPS")

        btn_x = width - 28
        btn_y = height - 28
        painter.setBrush(QBrush(QColor(70, 130, 180)))
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawRect(btn_x, btn_y, 22, 22)
        
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        if not self.expanded:
            painter.drawLine(btn_x + 6, btn_y + 16, btn_x + 16, btn_y + 6)
            painter.drawLine(btn_x + 11, btn_y + 6, btn_x + 16, btn_y + 6)
            painter.drawLine(btn_x + 16, btn_y + 6, btn_x + 16, btn_y + 11)
        else:
            painter.drawLine(btn_x + 6, btn_y + 6, btn_x + 16, btn_y + 16)
            painter.drawLine(btn_x + 11, btn_y + 16, btn_x + 16, btn_y + 16)
            painter.drawLine(btn_x + 16, btn_y + 11, btn_x + 16, btn_y + 16)

class HUDWidget(QWidget):
    def __init__(self, bg_image_path="background.jpg"):
        super().__init__()
        self.roll = 0.0    
        self.pitch = 0.0    
        self.altitude = 0.0 
        self.speed = 0.0    
        self.temp = 0.0
        self.heading = 0.0 
        
        self.v_h = 0.0
        self.v_v = 0.0

        self.resize(1200, 768)
        self.setMinimumSize(700, 490)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.bg_image = QPixmap(bg_image_path)
        if self.bg_image.isNull():
            self.bg_image = QPixmap(1200, 768)
            self.bg_image.fill(QColor(15, 25, 40))

    def set_values(self, ax, ay, az, gx, gy, gz, temp):
        dt = 0.05 
        self.roll = math.degrees(math.atan2(ay, az))
        self.pitch = math.degrees(math.atan2(-ax, math.sqrt(ay**2 + az**2)))
        self.temp = temp

        self.heading = (self.heading + gz * dt) % 360.0

        az_ms2 = (az - 1.0) * 9.81
        ah_ms2 = math.sqrt(max(0.0, ax**2 + ay**2)) * 9.81
        
        self.v_h = 0.95 * self.v_h + ah_ms2 * dt
        self.speed = abs(self.v_h * 3.6) 

        self.v_v = 0.95 * self.v_v + az_ms2 * dt
        self.altitude += self.v_v * dt

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        center_x = width / 2
        center_y = height / 2

        scaled_bg = self.bg_image.scaled(width, height, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
        painter.drawPixmap(0, 0, scaled_bg)

        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(self.roll)
        
        pitch_offset = self.pitch * 3.5  
        hud_pen = QPen(QColor(0, 255, 0), 2)
        painter.setPen(hud_pen)
        
        painter.drawLine(int(-150), int(pitch_offset), int(150), int(pitch_offset))
        painter.drawLine(int(-150), int(pitch_offset), int(-150), int(pitch_offset - 15))
        painter.drawLine(int(150), int(pitch_offset), int(150), int(pitch_offset - 15))
        
        painter.restore() 

        painter.setPen(hud_pen)
        font = QFont("Consolas", 11, QFont.Weight.Bold)
        painter.setFont(font)

        # Nišan u centru
        painter.drawLine(int(center_x - 50), int(center_y), int(center_x - 18), int(center_y))
        painter.drawLine(int(center_x - 18), int(center_y), int(center_x - 18), int(center_y + 12))
        painter.drawLine(int(center_x + 18), int(center_y), int(center_x + 50), int(center_y))
        painter.drawLine(int(center_x + 18), int(center_y), int(center_x + 18), int(center_y + 12))
        painter.drawPoint(int(center_x), int(center_y))

        tape_left = 115
        tape_right = width - 100
        tape_center_x = (tape_left + tape_right) / 2
        tape_y = 25

        painter.drawLine(tape_left, tape_y, tape_right, tape_y)
        painter.drawLine(int(tape_center_x), tape_y - 6, int(tape_center_x), tape_y + 6)

        font_small = QFont("Consolas", 9, QFont.Weight.Bold)
        painter.setFont(font_small)
        painter.drawText(int(tape_center_x) - 20, tape_y + 20, f"{self.heading:.0f}°")

        directions = [("N", 0), ("E", 90), ("S", 180), ("W", 270), 
                      ("NE", 45), ("SE", 135), ("SW", 225), ("NW", 315)]
        pixels_per_degree = 2.0  

        for label, deg in directions:
            diff = deg - self.heading
            while diff < -180: diff += 360
            while diff > 180: diff -= 360
            pos_x = tape_center_x + (diff * pixels_per_degree)
            if tape_left <= pos_x <= tape_right:
                painter.drawLine(int(pos_x), tape_y, int(pos_x), tape_y + 4)
                painter.drawText(int(pos_x) - 10, tape_y - 4, label)

        painter.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        painter.drawRect(20, int(center_y - 45), 110, 42)
        painter.drawText(25, int(center_y - 19), f"SPD:{self.speed:.1f}")
        painter.drawText(25, int(center_y - 7),  f"km/h")

        painter.drawRect(width - 130, int(center_y - 45), 110, 42)
        painter.drawText(width - 125, int(center_y - 19), f"ALT:{self.altitude:.1f}")
        painter.drawText(width - 125, int(center_y - 7),  f"m")

        painter.setFont(QFont("Consolas", 10))
        painter.drawText(20, 25, f"Roll:  {self.roll:.1f}°")
        painter.drawText(20, 45, f"Pitch: {self.pitch:.1f}°")
        painter.drawText(20, 65, f"Temp:  {self.temp:.1f} °C")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flight Controller")
        self.resize(1100, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        controls_layout = QHBoxLayout()
        self.port_combo = QComboBox()
        self.refresh_ports()
        
        self.connect_btn = QPushButton("Poveži se")
        self.connect_btn.clicked.connect(self.toggle_connection)

        controls_layout.addWidget(QLabel("UART Port:"))
        controls_layout.addWidget(self.port_combo)
        controls_layout.addWidget(self.connect_btn)
        main_layout.addLayout(controls_layout)

        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(15, 15, 15, 15)

        self.hud_widget = HUDWidget()
        grid_layout.addWidget(self.hud_widget, 1, 1, alignment=Qt.AlignmentFlag.AlignCenter)

        self.horizon_widget = ArtificialHorizonWidget()
        grid_layout.addWidget(self.horizon_widget, 2, 2, alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)

        grid_layout.setRowStretch(0, 1) 
        grid_layout.setRowStretch(1, 5) 
        grid_layout.setRowStretch(2, 1) 

        grid_layout.setColumnStretch(0, 1) 
        grid_layout.setColumnStretch(1, 5) 
        grid_layout.setColumnStretch(2, 1) 

        main_layout.addLayout(grid_layout)

        self.map_widget = MapWidget(central_widget)
        self.update_map_initial_position()

        self.serial_thread = None

    def update_map_initial_position(self):
        margin = 15
        x = margin
        y = self.centralWidget().height() - self.map_widget.height() - margin
        if not self.map_widget.expanded:
            self.map_widget.move(x, y)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self.map_widget.expanded:
            self.update_map_initial_position()

    def refresh_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(port.device)

    def toggle_connection(self):
        if self.connect_btn.text() == "Poveži se":
            port = self.port_combo.currentText()
            if not port:
                return
            
            self.serial_thread = SerialReaderThread(port, baud=9600)
            self.serial_thread.data_received.connect(self.horizon_widget.set_values)
            self.serial_thread.data_received.connect(self.hud_widget.set_values)
            self.serial_thread.start()

            self.connect_btn.setText("Prekini vezu")
            self.port_combo.setEnabled(False)
        else:
            if self.serial_thread:
                self.serial_thread.stop()
            self.connect_btn.setText("Poveži se")
            self.port_combo.setEnabled(True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())