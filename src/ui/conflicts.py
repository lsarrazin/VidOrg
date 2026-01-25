import os
import datetime
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QGroupBox, QGridLayout)
from PyQt6.QtCore import Qt

class ConflictDialog(QDialog):
    RENAME = 1
    OVERWRITE = 2
    CANCEL = 0

    def __init__(self, source_path, dest_dir, parent=None):
        super().__init__(parent)
        self.setWindowTitle("File Conflict")
        self.source_path = source_path
        self.dest_dir = dest_dir
        self.filename = os.path.basename(source_path)
        self.result_code = self.CANCEL
        self.final_filename = self.filename
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel(f"<b>A file named '{self.filename}' already exists in the destination.</b>"))
        
        grid = QGridLayout()
        layout.addLayout(grid)
        
        # Source File Info (The one being moved)
        src_group = QGroupBox("New version (source)")
        src_lay = QVBoxLayout(src_group)
        src_lay.addWidget(QLabel(self.format_file_info(self.source_path)))
        grid.addWidget(src_group, 0, 0)
        
        # Dest File Info (The one already there)
        dest_path = os.path.join(self.dest_dir, self.filename)
        dst_group = QGroupBox("Existing version (destination)")
        dst_lay = QVBoxLayout(dst_group)
        dst_lay.addWidget(QLabel(self.format_file_info(dest_path)))
        grid.addWidget(dst_group, 0, 1)
        
        # Rename Input
        layout.addWidget(QLabel("New name:"))
        self.name_edit = QLineEdit()
        suggested = self.suggest_name()
        self.name_edit.setText(suggested)
        layout.addWidget(self.name_edit)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_rename = QPushButton("Rename")
        self.btn_rename.setDefault(True)
        self.btn_rename.clicked.connect(self.on_rename)
        btn_layout.addWidget(self.btn_rename)
        
        self.btn_overwrite = QPushButton("Overwrite")
        self.btn_overwrite.setStyleSheet("color: red;")
        self.btn_overwrite.clicked.connect(self.on_overwrite)
        btn_layout.addWidget(self.btn_overwrite)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(btn_layout)

    def format_file_info(self, path):
        try:
            stat = os.stat(path)
            size = self.format_size(stat.st_size)
            date = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            return f"Size: {size}\nDate: {date}"
        except Exception:
            return "Unable to read file info"

    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"

    def suggest_name(self):
        base, ext = os.path.splitext(self.filename)
        n = 1
        while True:
            candidate = f"{base} #{n}{ext}"
            if not os.path.exists(os.path.join(self.dest_dir, candidate)):
                return candidate
            n += 1

    def on_rename(self):
        self.result_code = self.RENAME
        self.final_filename = self.name_edit.text()
        self.accept()

    def on_overwrite(self):
        self.result_code = self.OVERWRITE
        self.final_filename = self.filename
        self.accept()
