from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTabWidget, QDialogButtonBox)
from PyQt6.QtCore import QSettings
from src.ui.widgets import PathListWidget

class PreferencesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.resize(600, 400)
        
        self.settings = QSettings("MyCompany", "VideoSorter")
        
        main_layout = QVBoxLayout(self)
        
        # Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Source Tab
        self.source_list = PathListWidget()
        self.tabs.addTab(self.source_list, "Source Folders")
        
        # Destination Tab
        self.dest_list = PathListWidget()
        self.tabs.addTab(self.dest_list, "Destination Folders")
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)
        
        self.load_settings()

    def load_settings(self):
        sources = self.settings.value("source_folders", [], type=list)
        dests = self.settings.value("dest_folders", [], type=list)
        # Type verification because QSettings sometimes returns generic QVariant
        if not isinstance(sources, list): sources = []
        if not isinstance(dests, list): dests = []
        
        self.source_list.set_paths(sources)
        self.dest_list.set_paths(dests)

    def accept(self):
        # Save on OK
        self.settings.setValue("source_folders", self.source_list.get_paths())
        self.settings.setValue("dest_folders", self.dest_list.get_paths())
        super().accept()
