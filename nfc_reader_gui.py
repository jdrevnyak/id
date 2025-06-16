import sys
import serial
import serial.tools.list_ports
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QComboBox, QPushButton, 
                            QMessageBox, QTableWidget, QTableWidgetItem,
                            QHeaderView, QTabWidget, QLineEdit, QDialog,
                            QFormLayout, QFileDialog, QFrame, QGroupBox,
                            QGridLayout, QSizePolicy)
from PyQt5.QtCore import QTimer, Qt, QTime
from PyQt5.QtGui import QFont, QColor, QPainter, QPen
from student_db import StudentDatabase

class AddStudentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Student")
        self.setModal(True)
        
        layout = QFormLayout(self)
        
        self.student_id = QLineEdit()
        self.student_name = QLineEdit()
        
        layout.addRow("Student ID:", self.student_id)
        layout.addRow("Student Name:", self.student_name)
        
        buttons = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
        buttons.addWidget(self.ok_button)
        buttons.addWidget(self.cancel_button)
        layout.addRow(buttons)

class ImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Students")
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # File selection
        file_layout = QHBoxLayout()
        self.file_path = QLineEdit()
        self.file_path.setReadOnly(True)
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_file)
        file_layout.addWidget(QLabel("File:"))
        file_layout.addWidget(self.file_path)
        file_layout.addWidget(self.browse_button)
        layout.addLayout(file_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.import_button = QPushButton("Import")
        self.cancel_button = QPushButton("Cancel")
        
        self.import_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.import_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
    
    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "",
            "CSV Files (*.csv);;JSON Files (*.json)"
        )
        if file_path:
            self.file_path.setText(file_path)

class StatusIndicator(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 50)  # Size of the square
        self.setFrameShape(QFrame.Box)
        self.setFrameShadow(QFrame.Raised)
        self.setLineWidth(2)
        self.set_status(False)  # Start with green (no active breaks)
    
    def set_status(self, has_active_breaks):
        """Set the color based on bathroom break status"""
        if has_active_breaks:
            self.setStyleSheet("background-color: #ff4444;")  # Red
        else:
            self.setStyleSheet("background-color: #44ff44;")  # Green

# Add custom AnalogClock widget
class AnalogClock(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 220)
        timer = QTimer(self)
        timer.timeout.connect(self.update)
        timer.start(1000)

    def paintEvent(self, event):
        side = min(self.width(), self.height())
        time = QTime.currentTime()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(side / 200.0, side / 200.0)

        # Draw clock face
        painter.setPen(QPen(QColor("#2bb3a3"), 8))
        painter.drawEllipse(-90, -90, 180, 180)

        # Draw hour ticks
        painter.setPen(QPen(Qt.black, 4))
        for i in range(12):
            painter.save()
            painter.rotate(i * 30)
            painter.drawLine(0, -80, 0, -90)
            painter.restore()

        # Draw minute ticks
        painter.setPen(QPen(Qt.black, 1))
        for i in range(60):
            if i % 5 != 0:
                painter.save()
                painter.rotate(i * 6)
                painter.drawLine(0, -85, 0, -90)
                painter.restore()

        # Draw hour hand
        painter.setPen(QPen(Qt.black, 8, Qt.SolidLine, Qt.RoundCap))
        hour_angle = 30 * ((time.hour() % 12) + time.minute() / 60.0)
        painter.save()
        painter.rotate(hour_angle)
        painter.drawLine(0, 0, 0, -45)
        painter.restore()

        # Draw minute hand
        painter.setPen(QPen(Qt.black, 4, Qt.SolidLine, Qt.RoundCap))
        minute_angle = 6 * (time.minute() + time.second() / 60.0)
        painter.save()
        painter.rotate(minute_angle)
        painter.drawLine(0, 0, 0, -70)
        painter.restore()

        # Draw second hand (red)
        painter.setPen(QPen(Qt.red, 2, Qt.SolidLine, Qt.RoundCap))
        second_angle = 6 * time.second()
        painter.save()
        painter.rotate(second_angle)
        painter.drawLine(0, 10, 0, -75)
        painter.restore()

        # Draw center dot
        painter.setBrush(Qt.black)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(-6, -6, 12, 12)

class KeypadOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: rgba(0,0,0,0.5);")
        self.setWindowFlags(Qt.Widget | Qt.FramelessWindowHint)
        self.setVisible(False)
        self.setGeometry(parent.rect())
        self.parent = parent

        # Main layout for keypad
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        container = QWidget()
        container.setStyleSheet("background: white; border-radius: 24px;")
        container.setFixedSize(340, 440)
        vbox = QVBoxLayout(container)
        vbox.setAlignment(Qt.AlignCenter)
        vbox.setContentsMargins(24, 24, 24, 24)
        self.input = QLineEdit()
        self.input.setAlignment(Qt.AlignCenter)
        self.input.setFont(QFont('Arial', 28, QFont.Bold))
        self.input.setReadOnly(True)
        self.input.setStyleSheet(
            "QLineEdit { background: #fff; color: #23405a; border: 2px solid #23405a; border-radius: 10px; padding: 8px; }"
        )
        vbox.addWidget(self.input)
        grid = QGridLayout()
        buttons = [
            ('1', 0, 0), ('2', 0, 1), ('3', 0, 2),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2),
            ('Clear', 3, 0), ('0', 3, 1), ('OK', 3, 2)
        ]
        for text, row, col in buttons:
            btn = QPushButton(text)
            btn.setFont(QFont('Arial', 22, QFont.Bold))
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            if text.isdigit():
                btn.setStyleSheet(
                    "QPushButton { background: #f5f7fa; color: #23405a; border-radius: 16px; border: 2px solid #23405a; }"
                    "QPushButton:hover { background: #e0e7ef; }"
                    "QPushButton:pressed { background: #cfd8e3; }"
                )
            elif text == 'Clear':
                btn.setStyleSheet(
                    "QPushButton { background: #e0e0e0; color: #23405a; border-radius: 16px; border: 2px solid #b0b0b0; }"
                    "QPushButton:hover { background: #cccccc; }"
                    "QPushButton:pressed { background: #bbbbbb; }"
                )
            elif text == 'OK':
                btn.setStyleSheet(
                    "QPushButton { background: #2bb3a3; color: white; border-radius: 16px; border: 2px solid #249e90; }"
                    "QPushButton:hover { background: #249e90; }"
                    "QPushButton:pressed { background: #1e857a; }"
                )
            grid.addWidget(btn, row, col)
            if text.isdigit():
                btn.clicked.connect(lambda _, t=text: self.input.setText(self.input.text() + t))
            elif text == 'Clear':
                btn.clicked.connect(lambda: self.input.setText(''))
            elif text == 'OK':
                btn.clicked.connect(self.ok_pressed)
        vbox.addLayout(grid)
        # Cancel button below keypad
        cancel_btn = QPushButton('Cancel')
        cancel_btn.setFont(QFont('Arial', 18))
        cancel_btn.setStyleSheet('QPushButton { background: #eee; color: #23405a; border-radius: 12px; padding: 8px 0; border: 2px solid #b0b0b0; } QPushButton:hover { background: #e0e0e0; } QPushButton:pressed { background: #cccccc; }')
        cancel_btn.clicked.connect(self.hide)
        vbox.addWidget(cancel_btn)
        layout.addWidget(container)

    def ok_pressed(self):
        student_id = self.input.text()
        self.hide()
        if student_id:
            self.parent.handle_manual_id_entry(student_id)

    def show_overlay(self):
        self.input.setText("")
        self.setGeometry(self.parent.rect())
        self.setVisible(True)
        self.raise_()

    def hideEvent(self, event):
        self.setVisible(False)

class SettingsOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: rgba(0,0,0,0.5);")
        self.setWindowFlags(Qt.Widget | Qt.FramelessWindowHint)
        self.setVisible(False)
        self.setGeometry(parent.rect())
        self.parent = parent
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        container = QWidget()
        container.setStyleSheet("background: white; border-radius: 24px;")
        container.setFixedSize(400, 300)
        vbox = QVBoxLayout(container)
        vbox.setAlignment(Qt.AlignCenter)
        vbox.addStretch()
        # Add New Student button
        add_btn = QPushButton('Add New Student')
        add_btn.setFont(QFont('Arial', 18, QFont.Bold))
        add_btn.setStyleSheet('QPushButton { background: #2bb3a3; color: white; border-radius: 16px; padding: 12px 0; } QPushButton:hover { background: #249e90; } QPushButton:pressed { background: #1e857a; }')
        add_btn.clicked.connect(self.show_add_student_dialog)
        vbox.addWidget(add_btn)
        vbox.addStretch()
        layout.addWidget(container)

    def show_add_student_dialog(self):
        dialog = AddStudentDialog(self)
        dialog.setWindowModality(Qt.ApplicationModal)
        dialog.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        # Add NFC UID field
        if not hasattr(dialog, 'nfc_uid'):
            dialog.nfc_uid = QLineEdit()
            dialog.layout().insertRow(0, "NFC UID:", dialog.nfc_uid)
        if dialog.exec_():
            nfc_uid = dialog.nfc_uid.text().strip()
            student_id = dialog.student_id.text().strip()
            name = dialog.student_name.text().strip()
            # All fields are now optional
            success = self.parent.db.add_student(nfc_uid, student_id, name)
            if success:
                QMessageBox.information(self, "Success", "Student added successfully!")
            else:
                QMessageBox.warning(self, "Error", "Student with this NFC UID or Student ID already exists.")

    def show_overlay(self):
        self.setGeometry(self.parent.rect())
        self.setVisible(True)
        self.raise_()

    def mousePressEvent(self, event):
        # Dismiss if click outside the white box
        for child in self.children():
            if isinstance(child, QWidget) and child.geometry().contains(event.pos()):
                return
        self.hide()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()

class BathroomOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: rgba(0,0,0,0.7);")
        self.setWindowFlags(Qt.Widget | Qt.FramelessWindowHint)
        self.setVisible(False)
        self.setGeometry(parent.rect())
        self.parent = parent
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        container = QWidget()
        container.setStyleSheet("background: white; border-radius: 24px;")
        container.setFixedSize(400, 520)
        vbox = QVBoxLayout(container)
        vbox.setAlignment(Qt.AlignCenter)
        vbox.setContentsMargins(24, 24, 24, 24)
        # Prompt
        prompt = QLabel("Scan ID or enter ID number")
        prompt.setAlignment(Qt.AlignCenter)
        prompt.setFont(QFont('Arial', 24, QFont.Bold))
        prompt.setStyleSheet("color: #23405a; margin-bottom: 16px;")
        vbox.addWidget(prompt)
        # Message label for errors/info
        self.message_label = QLabel("")
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setFont(QFont('Arial', 16, QFont.Bold))
        self.message_label.setStyleSheet("color: #b71c1c; margin-bottom: 8px;")
        self.message_label.hide()
        vbox.addWidget(self.message_label)
        # Keypad
        self.input = QLineEdit()
        self.input.setAlignment(Qt.AlignCenter)
        self.input.setFont(QFont('Arial', 28, QFont.Bold))
        self.input.setReadOnly(True)
        self.input.setStyleSheet(
            "QLineEdit { background: #fff; color: #23405a; border: 2px solid #23405a; border-radius: 10px; padding: 8px; }"
        )
        vbox.addWidget(self.input)
        grid = QGridLayout()
        buttons = [
            ('1', 0, 0), ('2', 0, 1), ('3', 0, 2),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2),
            ('Clear', 3, 0), ('0', 3, 1), ('OK', 3, 2)
        ]
        for text, row, col in buttons:
            btn = QPushButton(text)
            btn.setFont(QFont('Arial', 22, QFont.Bold))
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            if text.isdigit():
                btn.setStyleSheet(
                    "QPushButton { background: #f5f7fa; color: #23405a; border-radius: 16px; border: 2px solid #23405a; }"
                    "QPushButton:hover { background: #e0e7ef; }"
                    "QPushButton:pressed { background: #cfd8e3; }"
                )
            elif text == 'Clear':
                btn.setStyleSheet(
                    "QPushButton { background: #e0e0e0; color: #23405a; border-radius: 16px; border: 2px solid #b0b0b0; }"
                    "QPushButton:hover { background: #cccccc; }"
                    "QPushButton:pressed { background: #bbbbbb; }"
                )
            elif text == 'OK':
                btn.setStyleSheet(
                    "QPushButton { background: #2bb3a3; color: white; border-radius: 16px; border: 2px solid #249e90; }"
                    "QPushButton:hover { background: #249e90; }"
                    "QPushButton:pressed { background: #1e857a; }"
                )
            grid.addWidget(btn, row, col)
            if text.isdigit():
                btn.clicked.connect(lambda _, t=text: self.input.setText(self.input.text() + t))
            elif text == 'Clear':
                btn.clicked.connect(lambda: self.input.setText(''))
            elif text == 'OK':
                btn.clicked.connect(self.ok_pressed)
        vbox.addLayout(grid)
        # Cancel button
        cancel_btn = QPushButton('Cancel')
        cancel_btn.setFont(QFont('Arial', 18))
        cancel_btn.setStyleSheet('QPushButton { background: #eee; color: #23405a; border-radius: 12px; padding: 8px 0; border: 2px solid #b0b0b0; } QPushButton:hover { background: #e0e0e0; } QPushButton:pressed { background: #cccccc; }')
        cancel_btn.clicked.connect(self.hide)
        vbox.addWidget(cancel_btn)
        layout.addWidget(container)
        self._message_timer = QTimer(self)
        self._message_timer.setSingleShot(True)
        self._message_timer.timeout.connect(self.clear_message)

    def show_overlay(self):
        self.input.setText("")
        self.setGeometry(self.parent.rect())
        self.setVisible(True)
        self.raise_()
        self.clear_message()

    def show_message(self, message, duration=4000):
        self.message_label.setText(message)
        self.message_label.show()
        self._message_timer.start(duration)

    def clear_message(self):
        self.message_label.hide()
        self.message_label.setText("")

    def ok_pressed(self):
        student_id = self.input.text()
        if student_id:
            self.parent.process_bathroom_entry(student_id=student_id)
            self.hide()

    def process_card(self, nfc_uid):
        self.parent.process_bathroom_entry(nfc_uid=nfc_uid)
        self.hide()

class NFCReaderGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Student Attendance System")
        self.setGeometry(100, 100, 800, 500)
        
        # Initialize database
        self.db = StudentDatabase()
        
        # Serial connection variables
        self.serial_port = None
        self.serial_connection = None
        self.connection_error_count = 0
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with date and time
        self.header = QLabel()
        self.header.setAlignment(Qt.AlignCenter)
        self.header.setFont(QFont('Arial', 32, QFont.Bold))
        self.header.setStyleSheet("color: #fff; background-color: #23405a; padding: 24px 0 24px 0; border-top-left-radius: 24px; border-top-right-radius: 24px;")
        main_layout.addWidget(self.header)
        
        # Center layout for clock and buttons
        center_layout = QHBoxLayout()
        center_layout.setContentsMargins(40, 40, 40, 40)
        center_layout.setSpacing(60)
        
        # Left: Analog clock (remove digital time label)
        clock_layout = QVBoxLayout()
        clock_layout.setAlignment(Qt.AlignCenter)
        self.analog_clock = AnalogClock()
        clock_layout.addWidget(self.analog_clock)
        center_layout.addLayout(clock_layout)
        
        # Right: Buttons
        button_layout = QVBoxLayout()
        button_layout.setAlignment(Qt.AlignVCenter)
        self.break_start_button = QPushButton("Bathroom")
        self.nurse_button = QPushButton("Nurse")
        for btn in [self.break_start_button, self.nurse_button]:
            btn.setMinimumSize(340, 80)
            btn.setFont(QFont('Arial', 32, QFont.Bold))
            btn.setCursor(Qt.PointingHandCursor)
        self.break_start_button.setStyleSheet('''
            QPushButton {
                background-color: #2bb3a3;
                color: white;
                border-radius: 24px;
                border: none;
                margin-bottom: 32px;
            }
            QPushButton:hover {
                background-color: #249e90;
            }
            QPushButton:pressed {
                background-color: #1e857a;
            }
        ''')
        self.nurse_button.setStyleSheet('''
            QPushButton {
                background-color: #23405a;
                color: white;
                border-radius: 24px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1a2e3d;
            }
            QPushButton:pressed {
                background-color: #162534;
            }
        ''')
        button_layout.addWidget(self.break_start_button)
        button_layout.addWidget(self.nurse_button)
        center_layout.addLayout(button_layout)
        
        main_layout.addLayout(center_layout)
        
        # Prompt at the bottom
        self.prompt = QLabel("Tap your ID or enter ID number")
        self.prompt.setAlignment(Qt.AlignCenter)
        self.prompt.setFont(QFont('Arial', 24))
        self.prompt.setStyleSheet("color: #23405a; background: #f5f7fa; padding: 24px 0 24px 0; border-bottom-left-radius: 24px; border-bottom-right-radius: 24px;")
        main_layout.addWidget(self.prompt)
        
        # Timer for updating header date and time
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_header_datetime)
        self.time_timer.start(1000)
        self.update_header_datetime()
        
        # Current student ID
        self.current_student_id = None
        
        # Auto-checkout on startup
        self.db.auto_checkout_students()
        # Periodic auto-checkout every minute
        self.auto_checkout_timer = QTimer(self)
        self.auto_checkout_timer.timeout.connect(self.db.auto_checkout_students)
        self.auto_checkout_timer.start(60 * 1000)  # every 60 seconds
        
        self.keypad_overlay = KeypadOverlay(self)
        self.analog_clock.mousePressEvent = self.show_keypad_overlay
        self.settings_overlay = SettingsOverlay(self)
        self.header.installEventFilter(self)
        self._header_press_time = None
        self._header_timer = QTimer(self)
        self._header_timer.setSingleShot(True)
        self._header_timer.timeout.connect(self._show_settings_overlay)
        self.bathroom_mode = False
        self.break_start_button.clicked.connect(self.show_bathroom_overlay)
        self.bathroom_overlay = BathroomOverlay(self)
    
    def refresh_ports(self):
        """Refresh the list of available serial ports"""
        self.port_combo.clear()
        ports = [port.device for port in serial.tools.list_ports.comports() 
                if not port.device.endswith('debugconsole')]
        if not ports:
            self.status_label.setText("Status: No serial ports found")
        self.port_combo.addItems(ports)
    
    def validate_port(self, port):
        """Check if the port is valid and accessible"""
        try:
            test_connection = serial.Serial(port)
            test_connection.close()
            return True
        except:
            return False
    
    def toggle_connection(self):
        """Connect to or disconnect from the selected serial port"""
        if self.serial_connection is None:
            try:
                port = self.port_combo.currentText()
                if not port:
                    QMessageBox.warning(self, "Connection Error", "No port selected")
                    return
                
                if not self.validate_port(port):
                    QMessageBox.warning(self, "Connection Error", 
                                      f"Port {port} is not accessible. Please check if the device is connected.")
                    return
                
                self.serial_connection = serial.Serial(port, 115200, timeout=1)
                self.status_label.setText(f"Status: Connected to {port}")
                self.connect_button.setText("Disconnect")
                self.timer.start(100)  # Read every 100ms
                self.connection_error_count = 0
            except Exception as e:
                QMessageBox.critical(self, "Connection Error", str(e))
        else:
            self.disconnect()
    
    def disconnect(self):
        """Safely disconnect from the serial port"""
        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
        except:
            pass
        finally:
            self.serial_connection = None
            self.status_label.setText("Status: Disconnected")
            self.connect_button.setText("Connect")
            self.timer.stop()
            self.button_widget.hide()
    
    def parse_uid(self, data):
        """Extract UID from the serial data"""
        if "UID Value:" in data:
            uid_part = data.split("UID Value:")[1].strip()
            uid = uid_part.replace("0x", "").replace(" ", "")
            return uid
        return None
    
    def show_add_student_dialog(self):
        """Show dialog to add a new student"""
        if not self.current_student_id:
            self.prompt.setText("Please scan a student card first")
            return
            
        dialog = AddStudentDialog(self)
        if dialog.exec_():
            name = dialog.student_name.text()
            if name:
                if self.db.add_student(self.current_student_id, name):
                    self.prompt.setText("Student added successfully")
                else:
                    self.prompt.setText("Student ID already exists")
    
    def handle_break_start(self):
        """Handle start of bathroom break"""
        if not self.current_student_id:
            self.prompt.setText("Please scan a student card first")
            return
            
        self.bathroom_mode = True
        self.prompt.setText("Tap or enter ID number")
        self.break_start_button.setEnabled(False)
        self.nurse_button.setEnabled(False)
        success, message = self.db.start_bathroom_break(self.current_student_id)
        if success:
            # Update the bathroom status indicator immediately
            self.bathroom_status.set_status(True)
            # Update the tables to show the new break
            self.update_tables()
            # Show success message
            self.prompt.setText("Break started successfully")
        else:
            # Show error message
            self.prompt.setText(message)
    
    def handle_nurse_start(self):
        """Handle start of nurse visit"""
        if not self.current_student_id:
            self.prompt.setText("Please scan a student card first")
            return
            
        success, message = self.db.start_nurse_visit(self.current_student_id)
        if success:
            # Update the tables to show the new nurse visit
            self.update_tables()
            # Show success message
            self.prompt.setText("Nurse visit started successfully")
        else:
            # Show error message
            self.prompt.setText(message)
    
    def update_tables(self):
        """Update attendance and breaks tables"""
        # Update attendance table
        attendance_data = self.db.get_today_attendance()
        print(f"Updating attendance table with {len(attendance_data)} records")
        
        self.attendance_table.setRowCount(len(attendance_data))
        for i, (student_id, name, check_in, _) in enumerate(attendance_data):
            print(f"Processing student {name} (ID: {student_id})")
            
            # Name column
            name_item = QTableWidgetItem(name or "Unknown")
            name_item.setTextAlignment(Qt.AlignCenter)
            self.attendance_table.setItem(i, 0, name_item)
            
            # Check-in column
            if check_in:
                check_in_str = check_in.strftime("%H:%M:%S")
                print(f"  Check-in time: {check_in_str}")
            else:
                check_in_str = "Not checked in"
                print(f"  No check-in time")
            check_in_item = QTableWidgetItem(check_in_str)
            check_in_item.setTextAlignment(Qt.AlignCenter)
            self.attendance_table.setItem(i, 1, check_in_item)
        
        # Update breaks table
        breaks_data = self.db.get_today_breaks()
        self.breaks_table.setRowCount(len(breaks_data))
        for i, (name, start, end, duration) in enumerate(breaks_data):
            # Name column
            name_item = QTableWidgetItem(name)
            name_item.setTextAlignment(Qt.AlignCenter)
            self.breaks_table.setItem(i, 0, name_item)
            
            # Break start column
            start_str = start.strftime("%H:%M:%S") if start else ""
            start_item = QTableWidgetItem(start_str)
            start_item.setTextAlignment(Qt.AlignCenter)
            self.breaks_table.setItem(i, 1, start_item)
            
            # Break end column
            end_str = end.strftime("%H:%M:%S") if end else "In progress"
            end_item = QTableWidgetItem(end_str)
            end_item.setTextAlignment(Qt.AlignCenter)
            self.breaks_table.setItem(i, 2, end_item)
            
            # Duration column
            duration_str = f"{duration} min" if duration else ""
            duration_item = QTableWidgetItem(duration_str)
            duration_item.setTextAlignment(Qt.AlignCenter)
            self.breaks_table.setItem(i, 3, duration_item)
        
        # Update bathroom status indicator
        has_active_breaks = any(break_end is None for _, _, break_end, _ in breaks_data)
        self.bathroom_status.set_status(has_active_breaks)
        
        # Update nurse visits table
        nurse_data = self.db.get_today_nurse_visits()
        self.nurse_table.setRowCount(len(nurse_data))
        for i, (name, start, end, duration) in enumerate(nurse_data):
            # Name column
            name_item = QTableWidgetItem(name)
            name_item.setTextAlignment(Qt.AlignCenter)
            self.nurse_table.setItem(i, 0, name_item)
            
            # Visit start column
            start_str = start.strftime("%H:%M:%S") if start else ""
            start_item = QTableWidgetItem(start_str)
            start_item.setTextAlignment(Qt.AlignCenter)
            self.nurse_table.setItem(i, 1, start_item)
            
            # Visit end column
            end_str = end.strftime("%H:%M:%S") if end else "In progress"
            end_item = QTableWidgetItem(end_str)
            end_item.setTextAlignment(Qt.AlignCenter)
            self.nurse_table.setItem(i, 2, end_item)
            
            # Duration column
            duration_str = f"{duration} min" if duration else ""
            duration_item = QTableWidgetItem(duration_str)
            duration_item.setTextAlignment(Qt.AlignCenter)
            self.nurse_table.setItem(i, 3, duration_item)
        
        # Force the table to update
        self.attendance_table.viewport().update()
    
    def show_import_dialog(self):
        """Show dialog to import students from file"""
        dialog = ImportDialog(self)
        if dialog.exec_():
            file_path = dialog.file_path.text()
            if not file_path:
                return
                
            try:
                if file_path.endswith('.csv'):
                    results = self.db.import_from_csv(file_path)
                elif file_path.endswith('.json'):
                    results = self.db.import_from_json(file_path)
                else:
                    QMessageBox.warning(self, "Error", "Unsupported file format")
                    return
                
                # Show results
                message = f"Import completed:\n"
                message += f"Successfully imported: {results['success']}\n"
                message += f"Failed to import: {results['failed']}\n"
                
                if results['errors']:
                    message += "\nErrors:\n"
                    for error in results['errors'][:5]:  # Show first 5 errors
                        message += f"- {error}\n"
                    if len(results['errors']) > 5:
                        message += f"... and {len(results['errors']) - 5} more errors"
                
                QMessageBox.information(self, "Import Results", message)
                
            except Exception as e:
                QMessageBox.critical(self, "Import Error", str(e))

    def update_header_datetime(self):
        now = datetime.now()
        date_str = now.strftime('%A, %B %d, %Y')
        time_str = now.strftime('%I:%M %p').lstrip('0')
        self.header.setText(f"{date_str}   {time_str}")

    def show_keypad_overlay(self, event):
        self.keypad_overlay.show_overlay()

    def handle_manual_id_entry(self, student_id):
        # Always resolve student_id to nfc_uid and use whichever is available
        result = self.db.get_student_by_student_id(student_id)
        if result:
            nfc_uid, student_name = result
            print(f"[DEBUG] Manual entry resolved student_id {student_id} to nfc_uid {nfc_uid}")
            identifier = nfc_uid if nfc_uid else student_id
            # Check in using whichever identifier is available
            success, message = self.db.check_in(nfc_uid=nfc_uid if nfc_uid else None, student_id=student_id if not nfc_uid else None)
            if success:
                QMessageBox.information(self, "Info", f"Student: {student_name}\n(ID: {student_id}) checked in.")
            else:
                QMessageBox.warning(self, "Error", message)
        else:
            QMessageBox.warning(self, "Error", f"No student found with ID: {student_id}")

    def eventFilter(self, obj, event):
        if obj == self.header:
            if event.type() == event.MouseButtonPress:
                self._header_press_time = datetime.now()
                self._header_timer.start(5000)
            elif event.type() == event.MouseButtonRelease:
                self._header_timer.stop()
            elif event.type() == event.Leave:
                self._header_timer.stop()
        return super().eventFilter(obj, event)

    def _show_settings_overlay(self):
        self.settings_overlay.show_overlay()

    def show_bathroom_overlay(self):
        self.bathroom_overlay.show_overlay()

    def process_bathroom_entry(self, student_id=None, nfc_uid=None):
        # Unified logic: use nfc_uid if available, else use student_id
        if nfc_uid:
            result = self.db.get_student_by_uid(nfc_uid)
            if not result:
                self.prompt.setText("No student found with that card.")
                return
            student_id_db, _ = result
            identifier = nfc_uid if nfc_uid else student_id_db
        elif student_id:
            result = self.db.get_student_by_student_id(student_id)
            if not result:
                self.prompt.setText("No student found with that ID.")
                return
            nfc_uid_db, _ = result
            identifier = nfc_uid_db if nfc_uid_db else student_id
        else:
            self.prompt.setText("No student information provided.")
            return

        print(f"[DEBUG] Bathroom entry using identifier: {identifier}")
        is_on_break = self.db.is_on_break(identifier)
        if is_on_break:
            success, message = self.db.end_bathroom_break(identifier)
            if success:
                self.prompt.setText("Bathroom break ended!")
                QTimer.singleShot(3000, self.bathroom_overlay.hide)
                QTimer.singleShot(3000, lambda: self.prompt.setText("Tap your ID or enter ID number"))
            else:
                self.prompt.setText(message)
        else:
            if not self.db.is_checked_in(identifier):
                self.prompt.setText("Student is not checked in")
                return
            success, message = self.db.start_bathroom_break(identifier)
            if success:
                self.prompt.setText("Bathroom break started!")
                QTimer.singleShot(3000, self.bathroom_overlay.hide)
                QTimer.singleShot(3000, lambda: self.prompt.setText("Tap your ID or enter ID number"))
            else:
                self.prompt.setText(message)

    def read_serial(self):
        if not self.serial_connection:
            return
        try:
            if self.serial_connection.is_open and self.serial_connection.in_waiting:
                data = self.serial_connection.readline().decode('utf-8').strip()
                if data:
                    uid = self.parse_uid(data)
                    if uid:
                        if self.bathroom_overlay.isVisible():
                            self.bathroom_overlay.process_card(uid)
                            return
                        # ... existing logic for normal card scan ...
                        self.current_student_id = uid
                        result = self.db.get_student_by_uid(uid)
                        if result:
                            student_id, student_name = result
                            success, message = self.db.check_in(nfc_uid=uid)
                            if success:
                                QMessageBox.information(self, "Check In", f"Student: {student_name}\n(ID: {student_id}) checked in.")
                            else:
                                QMessageBox.warning(self, "Error", message)
                        else:
                            QMessageBox.warning(self, "Error", f"Unknown Student (UID: {uid})")
        except Exception as e:
            QMessageBox.critical(self, "Serial Error", str(e))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = NFCReaderGUI()
    window.show()
    sys.exit(app.exec_()) 