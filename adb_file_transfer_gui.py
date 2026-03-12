#!/usr/bin/env python3
"""
ADB File Transfer GUI - A graphical interface for ADB file/directory transfers to Android devices
Arch Linux optimized
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
from PyQt5.QtGui import QFont, QIcon, QColor
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
        dest_path = f"/storage/self/primary/Arch-Files/{filename}"
        command = ["adb", "push", file_path, dest_path]
        
        if self.device_id != "default":
            command.insert(1, "-s")
            command.insert(2, self.device_id)
        
        self.output.emit(f"Sending {filename} to device {self.device_id}...\n")
        
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            self.output.emit(result.stdout)
            self.output.emit(f"✓ Successfully sent {filename}\n")
        except subprocess.CalledProcessError as e:
            self.error.emit(f"Error sending {filename}: {e.stderr}")
    
    def _send_directory(self, dir_path):
        """Send all files in a directory recursively via ADB"""
        file_count = 0
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                self._send_file(file_path)
                file_count += 1
        
        self.output.emit(f"\n✓ Transfer complete! {file_count} files sent.\n")


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
        self.setGeometry(100, 100, 900, 700)
        
        # Apply stylesheet for better appearance
        self.apply_stylesheet()
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("ADB File Transfer")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)
        
        # Device Selection Group
        device_group = QGroupBox("Device Selection")
        device_layout = QFormLayout()
        
        self.device_combo = QComboBox()
        self.device_combo.addItem("Auto-detect")
        device_layout.addRow("Device:", self.device_combo)
        
        refresh_btn = QPushButton("Refresh Devices")
        refresh_btn.clicked.connect(self.refresh_devices)
        device_layout.addRow("", refresh_btn)
        
        device_group.setLayout(device_layout)
        main_layout.addWidget(device_group)
        
        # File/Directory Selection Group
        file_group = QGroupBox("File/Directory Selection")
        file_layout = QFormLayout()
        
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Select a file or directory...")
        file_layout.addRow("Path:", self.path_input)
        
        file_browse_layout = QHBoxLayout()
        file_btn = QPushButton("Browse File")
        file_btn.clicked.connect(self.browse_file)
        dir_btn = QPushButton("Browse Directory")
        dir_btn.clicked.connect(self.browse_directory)
        file_browse_layout.addWidget(file_btn)
        file_browse_layout.addWidget(dir_btn)
        file_layout.addRow("", file_browse_layout)
        
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # Transfer Group
        transfer_group = QGroupBox("Transfer")
        transfer_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        transfer_layout.addWidget(self.progress_bar)
        
        transfer_btn = QPushButton("Start Transfer")
        transfer_btn.clicked.connect(self.start_transfer)
        transfer_btn.setStyleSheet("QPushButton { padding: 10px; font-size: 12px; font-weight: bold; }")
        transfer_layout.addWidget(transfer_btn)
        
        transfer_group.setLayout(transfer_layout)
        main_layout.addWidget(transfer_group)
        
        # Output/Logs Group
        output_group = QGroupBox("Transfer Log")
        output_layout = QVBoxLayout()
        
        self.output_text = QTextEdit()
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
        """Apply custom stylesheet for Arch Linux aesthetic"""
        stylesheet = """
        QMainWindow {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        QGroupBox {
            border: 1px solid #3a3a3a;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
            font-weight: bold;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 3px 0 3px;
        }
        QPushButton {
            background-color: #0184bc;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #016a8f;
        }
        QPushButton:pressed {
            background-color: #014d68;
        }
        QLineEdit, QTextEdit, QComboBox {
            background-color: #2a2a2a;
            color: #ffffff;
            border: 1px solid #3a3a3a;
            border-radius: 4px;
            padding: 5px;
        }
        QLabel {
            color: #ffffff;
        }
        QProgressBar {
            border: 1px solid #3a3a3a;
            border-radius: 4px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #0184bc;
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
                self.statusBar().showMessage(f"Found {len(devices)} device(s)")
            else:
                self.statusBar().showMessage("No devices found")
                self.log_output("⚠ No ADB devices detected. Make sure ADB is installed and a device is connected.")
        
        except FileNotFoundError:
            self.log_output("✗ Error: ADB not found. Please install android-tools.")
            self.statusBar().showMessage("ADB not found")
        except Exception as e:
            self.log_output(f"✗ Error refreshing devices: {str(e)}")
            self.statusBar().showMessage("Error refreshing devices")
    
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
        self.log_output(f"Starting transfer...\n")
        self.statusBar().showMessage("Transferring...")
        
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
        self.statusBar().showMessage("Transfer failed")
        self.log_output(f"\n✗ Error: {error_message}\n")
        QMessageBox.critical(self, "Transfer Error", error_message)
    
    def transfer_complete(self):
        """Handle transfer completion"""
        self.statusBar().showMessage("Transfer complete!")
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