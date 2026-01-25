from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QPushButton, QFileDialog, QAbstractItemView, QStyle)
from PyQt6.QtCore import Qt

class PathListWidget(QWidget):
    def __init__(self, title="Paths"):
        super().__init__()
        self.layout = QVBoxLayout(self)
        
        # List
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list_widget.setAlternatingRowColors(True)
        self.layout.addWidget(self.list_widget)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_add = QPushButton("Add Folder")
        self.btn_add.clicked.connect(self.add_folder)
        btn_layout.addWidget(self.btn_add)
        
        self.btn_remove = QPushButton("Remove")
        self.btn_remove.clicked.connect(self.remove_selection)
        btn_layout.addWidget(self.btn_remove)
        
        self.btn_up = QPushButton("Up")
        self.btn_up.clicked.connect(self.move_up)
        btn_layout.addWidget(self.btn_up)
        
        self.btn_down = QPushButton("Down")
        self.btn_down.clicked.connect(self.move_down)
        btn_layout.addWidget(self.btn_down)
        
        self.layout.addLayout(btn_layout)

    def set_paths(self, paths):
        self.list_widget.clear()
        self.list_widget.addItems(paths)

    def get_paths(self):
        return [self.list_widget.item(i).text() for i in range(self.list_widget.count())]

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Directory")
        if folder:
            # Avoid duplicates
            if not self.list_widget.findItems(folder, Qt.MatchFlag.MatchExactly):
                self.list_widget.addItem(folder)

    def remove_selection(self):
        for item in self.list_widget.selectedItems():
            self.list_widget.takeItem(self.list_widget.row(item))

    def move_up(self):
        curr = self.list_widget.currentRow()
        if curr > 0:
            item = self.list_widget.takeItem(curr)
            self.list_widget.insertItem(curr - 1, item)
            self.list_widget.setCurrentRow(curr - 1)

    def move_down(self):
        curr = self.list_widget.currentRow()
        if curr < self.list_widget.count() - 1:
            item = self.list_widget.takeItem(curr)
            self.list_widget.insertItem(curr + 1, item)
            self.list_widget.setCurrentRow(curr + 1)

from PyQt6.QtWidgets import QSlider, QStyleOptionSlider
from PyQt6.QtCore import Qt, pyqtSignal

class ClickableSlider(QSlider):
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Calculate the value based on the click position
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)
            sr = self.style().subControlRect(QStyle.ComplexControl.CC_Slider, opt, QStyle.SubControl.SC_SliderGroove, self)
            
            if self.orientation() == Qt.Orientation.Horizontal:
                slider_length = sr.width()
                slider_pos = event.position().x() - sr.x()
            else:
                slider_length = sr.height()
                slider_pos = event.position().y() - sr.y()
                # For vertical sliders, the value is inverted (bottom is min)
                slider_pos = slider_length - slider_pos

            if slider_length > 0:
                new_value = self.minimum() + int((self.maximum() - self.minimum()) * slider_pos / slider_length)
                self.setValue(new_value)
                # Emit sliderMoved to trigger video seek immediately
                self.sliderMoved.emit(new_value)
            
            event.accept()
        super().mousePressEvent(event)

from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import pyqtSignal

class CustomVideoWidget(QVideoWidget):
    doubleClicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit()
        event.accept()
