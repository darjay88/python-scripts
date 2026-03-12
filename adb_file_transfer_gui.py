#!/usr/bin/env python3
"""
ADB File Transfer GUI - A graphical interface for ADB file/directory transfers to Android devices
Arch Linux optimized - ENHANCED COLORFUL VERSION
"""

import sys
import os
import subprocess
import threading
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog, QComboBox,
    QTextEdit, QMessageBox, QProgressBar, QGroupBox, QFormLayout,
    QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QThread
from PyQt5.QtGui import QFont, QIcon, QColor, QLinearGradient, QPalette
from PyQt5.QtGui import QTextCursor


class TransferWorker(QObject):
    """Worker thread for handling ADB transfers"""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    output = pyqtSignal(str)
    
    def __init__(self, path, device_id):
        super().__init__()
        self.path = path
        self.device_id = device_id
    
    def run(self):
        """Execute the ADB transfer"""
        try:
            if os.path.isfile(self.path):
                self._send_file(self.path)
            elif os.path.isdir(self.path):
                self._send_directory(self.path)
            else:
                self.error.emit("Invalid path: neither file nor directory")
                return
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
    
    def _send_file(self, file_path):
        """Send a single file via ADB"""
        filename = os.path.basename(file_path)
        dest_path = f"/storage/self/primary/Arch-Files/{{filename}}"
        command = ["adb", "push", file_path, dest_path]
        
        if self.device_id != "default":
            command.insert(1, "-s")
            command.insert(2, self.device_id)
        
        self.output.emit(f"Sending {{filename}} to device {{self.device_id}}...\n")
        
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            self.output.emit(result.stdout)
            self.output.emit(f"✓ Successfully sent {{filename}}\n")
        except subprocess.CalledProcessError as e:
            self.error.emit(f"Error sending {{filename}}: {{e.stderr}}")
    
    def _send_directory(self, dir_path):
        """Send all files in a directory recursively via ADB"""
        file_count = 0
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                self._send_file(file_path)
                file_count += 1
        
        self.output.emit(f"\n✓ Transfer complete! {{file_count}} files sent.\n")


class ADBFileTransferGUI(QMainWindow):
    """Main GUI window for ADB File Transfer"""
    
    def __init__(self):
        super().__init__()
        self.transfer_thread = None
        self.worker = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("ADB File Transfer - Arch Linux")
        self.setGeometry(100, 100, 1000, 750)
        
        # Apply stylesheet for better appearance
        self.apply_stylesheet()
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title with gradient background
        title_frame = QFrame()
        title_frame.setObjectName("titleFrame")
        title_layout = QVBoxLayout(title_frame)
        title_layout.setContentsMargins(15, 15, 15, 15)
        
        title = QLabel("🚀 ADB File Transfer")
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setObjectName("title")
        title_layout.addWidget(title)
        
        main_layout.addWidget(title_frame)
        
        # Device Selection Group
        device_group = QGroupBox("📱 Device Selection")
        device_group.setObjectName("deviceGroup")
        device_layout = QFormLayout()
        
        self.device_combo = QComboBox()
        self.device_combo.setObjectName("deviceCombo")
        self.device_combo.addItem("Auto-detect")
        device_layout.addRow("Device:", self.device_combo)
        
        refresh_btn = QPushButton("🔄 Refresh Devices")
        refresh_btn.setObjectName("refreshBtn")
        refresh_btn.clicked.connect(self.refresh_devices)
        device_layout.addRow("", refresh_btn)
        
        device_group.setLayout(device_layout)
        main_layout.addWidget(device_group)
        
        # File/Directory Selection Group
        file_group = QGroupBox("📁 File/Directory Selection")
        file_group.setObjectName("fileGroup")
        file_layout = QFormLayout()
        
        self.path_input = QLineEdit()
        self.path_input.setObjectName("pathInput")
        self.path_input.setPlaceholderText("Select a file or directory...")
        file_layout.addRow("Path:", self.path_input)
        
        file_browse_layout = QHBoxLayout()
        file_btn = QPushButton("📄 Browse File")
        file_btn.setObjectName("fileBrowseBtn")
        file_btn.clicked.connect(self.browse_file)
        dir_btn = QPushButton("📂 Browse Directory")
        dir_btn.setObjectName("dirBrowseBtn")
        dir_btn.clicked.connect(self.browse_directory)
        file_browse_layout.addWidget(file_btn)
        file_browse_layout.addWidget(dir_btn)
        file_layout.addRow("", file_browse_layout)
        
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # Transfer Group
        transfer_group = QGroupBox("⚡ Transfer")
        transfer_group.setObjectName("transferGroup")
        transfer_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #FF6B6B;
                border-radius: 8px;
                background-color: #1a1a1a;
                height: 25px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF6B6B, stop:0.5 #FFD93D, stop:1 #6BCB77);
            }
        """)
        transfer_layout.addWidget(self.progress_bar)
        
        transfer_btn = QPushButton("🚀 START TRANSFER")
        transfer_btn.setObjectName("transferBtn")
        transfer_btn.clicked.connect(self.start_transfer)
        transfer_layout.addWidget(transfer_btn)
        
        transfer_group.setLayout(transfer_layout)
        main_layout.addWidget(transfer_group)
        
        # Output/Logs Group
        output_group = QGroupBox("📋 Transfer Log")
        output_group.setObjectName("outputGroup")
        output_layout = QVBoxLayout()
        
        self.output_text = QTextEdit()
        self.output_text.setObjectName("outputText")
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Monospace", 9))
        output_layout.addWidget(self.output_text)
        
        output_group.setLayout(output_layout)
        main_layout.addWidget(output_group)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Refresh devices on startup
        self.refresh_devices()
    
    def apply_stylesheet(self):
        """Apply custom stylesheet for vibrant, flashy appearance"""
        stylesheet = """
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #0F0E17, stop:0.5 #1a0f2e, stop:1 #16213e);
            color: #ffffff;
        }
        
        #titleFrame {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #FF006E, stop:0.5 #FFB703, stop:1 #FB5607);
            border-radius: 10px;
            border: 2px solid #FFD60A;
        }
        
        #title {
            color: #ffffff;
            font-weight: bold;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        }
        
        QGroupBox {
            border: 2px solid #6A4C93;
            border-radius: 8px;
            margin-top: 15px;
            padding-top: 15px;
            font-weight: bold;
            font-size: 12px;
            color: #FFD60A;
        }
        
        #deviceGroup {
            border: 2px solid #1D7874;
        }
        
        #fileGroup {
            border: 2px solid #6A4C93;
        }
        
        #transferGroup {
            border: 2px solid #FF006E;
        }
        
        #outputGroup {
            border: 2px solid #FFB703;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #FF006E, stop:0.5 #FF4B4B, stop:1 #FF006E);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        #refreshBtn {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #1D7874, stop:0.5 #118B8B, stop:1 #1D7874);
        }
        
        #fileBrowseBtn {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #6A4C93, stop:0.5 #8E7CC3, stop:1 #6A4C93);
        }
        
        #dirBrowseBtn {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #FFB703, stop:0.5 #FFD60A, stop:1 #FFB703);
            color: #000000;
        }
        
        #transferBtn {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #FF006E, stop:0.5 #FB5607, stop:1 #FFBE0B);
            color: white;
            padding: 15px 30px;
            font-size: 13px;
            font-weight: bold;
            border: 2px solid #FFD60A;
            border-radius: 8px;
        }
        
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #FF4B4B, stop:0.5 #FFB703, stop:1 #FF4B4B);
            border: 2px solid #FFFFFF;
            box-shadow: 0 0 15px rgba(255, 0, 110, 0.8);
        }
        
        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:1, x2:1, y2:0,
                stop:0 #FF006E, stop:0.5 #FB5607, stop:1 #FFBE0B);
            transform: scale(0.98);
        }
        
        #refreshBtn:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #00D084, stop:0.5 #23D997, stop:1 #00D084);
            box-shadow: 0 0 15px rgba(29, 120, 116, 0.8);
        }
        
        #fileBrowseBtn:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #C77DFF, stop:0.5 #E0AAFF, stop:1 #C77DFF);
            box-shadow: 0 0 15px rgba(106, 76, 147, 0.8);
        }
        
        #dirBrowseBtn:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #FFD60A, stop:0.5 #FFC300, stop:1 #FFD60A);
            box-shadow: 0 0 15px rgba(255, 183, 3, 0.8);
        }
        
        QLineEdit, QTextEdit, QComboBox {
            background-color: #1a1a1a;
            color: #00D084;
            border: 2px solid #00D084;
            border-radius: 6px;
            padding: 8px;
            font-weight: bold;
        }
        
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
            background-color: #0F0E17;
            border: 2px solid #FFD60A;
            color: #FFD60A;
            box-shadow: 0 0 10px rgba(255, 214, 10, 0.5);
        }
        
        QLineEdit::placeholder {
            color: #666666;
        }
        
        QLabel {
            color: #E0AAFF;
            font-weight: bold;
        }
        
        QProgressBar {
            border: 2px solid #FF6B6B;
            border-radius: 8px;
            background-color: #1a1a1a;
            height: 25px;
            text-align: center;
            color: #FFD60A;
            font-weight: bold;
        }
        
        QProgressBar::chunk {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #FF6B6B, stop:0.5 #FFD93D, stop:1 #6BCB77);
            border-radius: 6px;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        
        QComboBox::down-arrow {
            image: none;
            background-color: #00D084;
            border-radius: 3px;
        }
        
        QStatusBar {
            background-color: #0F0E17;
            color: #FFD60A;
            border-top: 2px solid #00D084;
            font-weight: bold;
        }
        """
        self.setStyleSheet(stylesheet)
    
    def refresh_devices(self):
        """Refresh the list of connected ADB devices"""
        self.statusBar().showMessage("Refreshing devices...")
        try:
            result = subprocess.run(
                ["adb", "devices", "-l"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            devices = []
            for line in result.stdout.split('\n')[1:]:
                if line.strip() and 'device' in line and 'offline' not in line:
                    device_id = line.split()[0]
                    devices.append(device_id)
            
            self.device_combo.clear()
            self.device_combo.addItem("Auto-detect")
            
            if devices:
                self.device_combo.addItems(devices)
                self.statusBar().showMessage(f"✓ Found {{len(devices)}} device(s)")
            else:
                self.statusBar().showMessage("⚠ No devices found")
                self.log_output("⚠ No ADB devices detected. Make sure ADB is installed and a device is connected.")
        
        except FileNotFoundError:
            self.log_output("✗ Error: ADB not found. Please install android-tools.")
            self.statusBar().showMessage("✗ ADB not found")
        except Exception as e:
            self.log_output(f"✗ Error refreshing devices: {{str(e)}}")
            self.statusBar().showMessage("✗ Error refreshing devices")
    
    def browse_file(self):
        """Open file browser dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File to Transfer",
            str(Path.home())
        )
        if file_path:
            self.path_input.setText(file_path)
    
    def browse_directory(self):
        """Open directory browser dialog"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Directory to Transfer",
            str(Path.home())
        )
        if dir_path:
            self.path_input.setText(dir_path)
    
    def start_transfer(self):
        """Start the file transfer"""
        path = self.path_input.text()
        
        if not path:
            QMessageBox.warning(self, "Input Error", "Please select a file or directory.")
            return
        
        if not os.path.exists(path):
            QMessageBox.warning(self, "Path Error", "The selected path does not exist.")
            return
        
        device_id = self.device_combo.currentText()
        if device_id == "Auto-detect":
            device_id = "default"
        
        self.output_text.clear()
        self.log_output(f"🚀 Starting transfer...\n")
        self.statusBar().showMessage("⚡ Transferring...")
        
        # Create and start worker thread
        self.worker = TransferWorker(path, device_id)
        self.transfer_thread = QThread()
        self.worker.moveToThread(self.transfer_thread)
        
        self.worker.output.connect(self.log_output)
        self.worker.error.connect(self.handle_error)
        self.worker.finished.connect(self.transfer_complete)
        self.transfer_thread.started.connect(self.worker.run)
        
        self.transfer_thread.start()
    
    def log_output(self, message):
        """Append message to output text"""
        self.output_text.moveCursor(QTextCursor.End)
        self.output_text.insertPlainText(message)
        self.output_text.moveCursor(QTextCursor.End)
    
    def handle_error(self, error_message):
        """Handle transfer errors"""
        self.statusBar().showMessage("✗ Transfer failed")
        self.log_output(f"\n✗ Error: {{error_message}}\n")
        QMessageBox.critical(self, "Transfer Error", error_message)
    
    def transfer_complete(self):
        """Handle transfer completion"""
        self.statusBar().showMessage("✓ Transfer complete!")
        if self.transfer_thread:
            self.transfer_thread.quit()
            self.transfer_thread.wait()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    window = ADBFileTransferGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()