from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QLabel,
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

class VolumePopup(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Container to give a background and border
        self.container = QWidget()
        self.container.setObjectName("VolumeContainer")
        self.container.setStyleSheet("""
            #VolumeContainer {
                background-color: rgba(45, 45, 45, 230);
                border: 1px solid #555;
                border-radius: 8px;
            }
        """)
        container_layout = QVBoxLayout(self.container)
        
        self.slider = ClickableSlider(Qt.Orientation.Vertical)
        self.slider.setRange(0, 100)
        self.slider.setFixedHeight(150)
        container_layout.addWidget(self.slider)
        
        layout.addWidget(self.container)
        self.setFixedSize(40, 180)

class VolumeButton(QPushButton):
    volumeChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(30, 30)
        self.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaVolume))
        self.setToolTip("Volume")
        
        self.popup = VolumePopup(self)
        self.popup.slider.valueChanged.connect(self.on_volume_changed)
        self.clicked.connect(self.toggle_popup)

    def on_volume_changed(self, value):
        # Update icon based on volume level
        if value == 0:
            self.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaVolumeMuted))
        else:
            self.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaVolume))
        self.volumeChanged.emit(value)

    def toggle_popup(self):
        if self.popup.isVisible():
            self.popup.hide()
        else:
            # Position the popup above the button
            btn_pos = self.mapToGlobal(self.rect().bottomLeft())
            popup_height = self.popup.height()
            # Try to center it horizontally relative to the button
            x = btn_pos.x() + (self.width() - self.popup.width()) // 2
            y = btn_pos.y() - self.height() - popup_height - 5
            self.popup.move(x, y)
            self.popup.show()

    def setVolume(self, value):
        self.popup.slider.setValue(value)

from PyQt6.QtWidgets import QDialog, QProgressBar
from PyQt6.QtCore import QThread, pyqtSignal
import shutil

class WaitDialog(QDialog):
    def __init__(self, message="Moving file...", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Please Wait")
        self.setModal(True)
        self.setFixedSize(300, 100)
        
        # Remove close button
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
        
        layout = QVBoxLayout(self)
        
        # Message label
        self.label = QLabel(message)
        layout.addWidget(self.label)
        
        # Progress bar (indeterminate)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminate mode
        layout.addWidget(self.progress)

class FileMoveWorker(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, src, dst):
        super().__init__()
        self.src = src
        self.dst = dst
    
    def run(self):
        try:
            shutil.move(self.src, self.dst)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
