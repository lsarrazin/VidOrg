from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QSplitter, QTreeView, QListView, QLabel, QFrame,
                             QFileDialog, QPushButton, QMessageBox, QComboBox,
                             QSlider, QStyle, QSizePolicy, QStyle)
from PyQt6.QtCore import Qt, QDir, QUrl, QSettings
from PyQt6.QtGui import QAction, QFileSystemModel, QStandardItemModel, QStandardItem
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
import shutil
import shutil
import os
from src.ui.preferences import PreferencesDialog
from src.ui.widgets import CustomVideoWidget, ClickableSlider

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Sorter")
        self.resize(1200, 800)
        self.settings = QSettings("MyCompany", "VideoSorter")
        self.setup_ui()
        self.setup_menu()
        self.load_preferences()

    def setup_menu(self):
        menu_bar = self.menuBar()
        
        # --- File Menu ---
        file_menu = menu_bar.addMenu("&File")
        
        # Preferences
        action_prefs = QAction("&Preferences...", self)
        action_prefs.triggered.connect(self.show_preferences)
        file_menu.addAction(action_prefs)
        
        file_menu.addSeparator()
        
        # Quit
        action_quit = QAction("&Quit", self)
        action_quit.setShortcut("Ctrl+Q")
        action_quit.triggered.connect(self.close)
        file_menu.addAction(action_quit)
        
        # --- Help Menu ---
        help_menu = menu_bar.addMenu("&Help")
        
        # About
        action_about = QAction("&About", self)
        action_about.triggered.connect(self.show_about)
        help_menu.addAction(action_about)

    def setup_ui(self):
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main Layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Splitter for resizable panels
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)
        
        # --- Left Panel: Source ---
        self.source_panel = QFrame()
        self.source_panel.setFrameShape(QFrame.Shape.StyledPanel)
        source_layout = QVBoxLayout(self.source_panel)
        source_layout.addWidget(QLabel("Source Folder"))
        
        # Source Selector (ComboBox)
        self.source_combo = QComboBox()
        self.source_combo.currentIndexChanged.connect(self.on_source_combo_changed)
        source_layout.addWidget(self.source_combo)
        
        # File System Model
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(QDir.homePath())
        self.file_model.setNameFilters(["*.mp4", "*.mkv", "*.avi", "*.mov"])
        self.file_model.setNameFilterDisables(False)
        
        self.source_tree = QTreeView()
        self.source_tree.setModel(self.file_model)
        self.source_tree.setRootIndex(self.file_model.index(QDir.homePath()))
        
        # Hide internal columns (Size, Type, Date..) - keep Name
        for i in range(1, 4):
            self.source_tree.setColumnHidden(i, True)
            
        self.source_tree.clicked.connect(self.on_file_selected)
        source_layout.addWidget(self.source_tree)
        
        self.source_tree.clicked.connect(self.on_file_selected)
        source_layout.addWidget(self.source_tree)
        
        # Button to change Root (Manual override)
        self.btn_change_source = QPushButton("Browse...")
        self.btn_change_source.clicked.connect(self.browse_source_folder)
        source_layout.addWidget(self.btn_change_source)
        
        # --- Center Panel: Player ---
        self.player_panel = QFrame()
        self.player_panel.setFrameShape(QFrame.Shape.StyledPanel)
        player_layout = QVBoxLayout(self.player_panel)
        player_layout.addWidget(QLabel("Video Player"))
        
        self.video_widget = CustomVideoWidget()
        self.video_widget.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        self.video_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.video_widget.doubleClicked.connect(self.toggle_fullscreen)
        player_layout.addWidget(self.video_widget)
        
        # --- Seeker Layout ---
        seeker_layout = QHBoxLayout()
        player_layout.addLayout(seeker_layout)
        
        self.label_elapsed = QLabel("00:00")
        seeker_layout.addWidget(self.label_elapsed)
        
        self.slider_position = ClickableSlider(Qt.Orientation.Horizontal)
        self.slider_position.setRange(0, 0)
        self.slider_position.sliderMoved.connect(self.seek_video)
        seeker_layout.addWidget(self.slider_position)
        
        self.label_duration = QLabel("00:00")
        seeker_layout.addWidget(self.label_duration)
        
        # --- Controls Layout ---
        controls_layout = QHBoxLayout()
        player_layout.addLayout(controls_layout)
        
        # Previous
        self.btn_prev = QPushButton()
        self.btn_prev.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSkipBackward))
        self.btn_prev.setToolTip("Previous Video")
        self.btn_prev.clicked.connect(self.play_previous_video)
        controls_layout.addWidget(self.btn_prev)
        
        # Backward 1 min
        self.btn_back_1m = QPushButton("-1m")
        self.btn_back_1m.clicked.connect(lambda: self.seek_relative(-60000))
        controls_layout.addWidget(self.btn_back_1m)
        
        # Play/Pause
        self.btn_play = QPushButton()
        self.btn_play.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.btn_play.setToolTip("Play/Pause")
        self.btn_play.clicked.connect(self.toggle_playback)
        controls_layout.addWidget(self.btn_play)
        
        # Stop
        self.btn_stop = QPushButton()
        self.btn_stop.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop))
        self.btn_stop.setToolTip("Stop")
        self.btn_stop.clicked.connect(self.stop_video)
        controls_layout.addWidget(self.btn_stop)
        
        # Forward 1 min
        self.btn_fwd_1m = QPushButton("+1m")
        self.btn_fwd_1m.clicked.connect(lambda: self.seek_relative(60000))
        controls_layout.addWidget(self.btn_fwd_1m)
        
        # Next
        self.btn_next = QPushButton()
        self.btn_next.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSkipForward))
        self.btn_next.setToolTip("Next Video")
        self.btn_next.clicked.connect(self.play_next_video)
        controls_layout.addWidget(self.btn_next)
        
        # Separator (Spacer)
        controls_layout.addStretch()
        
        # Volume
        controls_layout.addWidget(QLabel("Vol:"))
        self.volume_slider = ClickableSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.valueChanged.connect(self.set_volume)
        controls_layout.addWidget(self.volume_slider)
        
        # Media Player
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)
        
        # Signals for seeker
        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.update_duration)
        
        # --- Right Panel: Destination ---
        self.dest_panel = QFrame()
        self.dest_panel.setFrameShape(QFrame.Shape.StyledPanel)
        dest_layout = QVBoxLayout(self.dest_panel)
        dest_layout.addWidget(QLabel("Destinations"))
        
        # Destination Root Selector
        self.dest_combo = QComboBox()
        self.dest_combo.currentIndexChanged.connect(self.on_dest_combo_changed)
        dest_layout.addWidget(self.dest_combo)
        
        # Destination File System Model (Dirs Only)
        self.dest_file_model = QFileSystemModel()
        self.dest_file_model.setFilter(QDir.Filter.AllDirs | QDir.Filter.NoDotAndDotDot)
        
        self.dest_tree = QTreeView()
        self.dest_tree.setModel(self.dest_file_model)
        for i in range(1, 4):
            self.dest_tree.setColumnHidden(i, True)
        dest_layout.addWidget(self.dest_tree)
        
        # Add Dest Button
        self.btn_add_dest = QPushButton("Add Folder")
        self.btn_add_dest.clicked.connect(self.add_destination)
        dest_layout.addWidget(self.btn_add_dest)
        
        # Move Button
        self.btn_move = QPushButton("Move Video")
        self.btn_move.clicked.connect(self.move_current_video)
        dest_layout.addWidget(self.btn_move)
        
        # Add panels to splitter
        self.splitter.addWidget(self.source_panel)
        self.splitter.addWidget(self.player_panel)
        self.splitter.addWidget(self.dest_panel)
        
        # Set initial sizes (20%, 60%, 20%)
        self.splitter.setSizes([240, 720, 240])
        
    # --- Playback Logic ---

    def format_time(self, ms):
        seconds = (ms // 1000) % 60
        minutes = (ms // (1000 * 60)) % 60
        hours = (ms // (1000 * 60 * 60))
        if hours > 0:
            return f"{hours:02}:{minutes:02}:{seconds:02}"
        return f"{minutes:02}:{seconds:02}"

    def update_position(self, ms):
        self.slider_position.blockSignals(True)
        self.slider_position.setValue(ms)
        self.slider_position.blockSignals(False)
        self.label_elapsed.setText(self.format_time(ms))

    def update_duration(self, ms):
        self.slider_position.setRange(0, ms)
        self.label_duration.setText(self.format_time(ms))

    def seek_video(self, ms):
        self.player.setPosition(ms)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.source_panel.show()
            self.dest_panel.show()
            self.menuBar().show()
        else:
            self.showFullScreen()
            self.source_panel.hide()
            self.dest_panel.hide()
            self.menuBar().hide()

    def browse_source_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Source Directory", QDir.homePath())
        if folder:
            self.source_combo.addItem(folder)
            self.source_combo.setCurrentText(folder)
            # This triggers on_source_combo_changed

    def on_source_combo_changed(self):
        folder = self.source_combo.currentText()
        if folder and os.path.isdir(folder):
            self.source_tree.setRootIndex(self.file_model.index(folder))

    def on_file_selected(self, index):
        file_path = self.file_model.filePath(index)
        if self.file_model.isDir(index):
            return
            
        print(f"Selected: {file_path}")
        self.player.setSource(QUrl.fromLocalFile(file_path))
        self.player.play()

    def add_destination(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if folder:
            self.dest_combo.addItem(folder)
            self.dest_combo.setCurrentText(folder)
            
    def on_dest_combo_changed(self):
        folder = self.dest_combo.currentText()
        if folder and os.path.exists(folder):
            self.dest_file_model.setRootPath(folder)
            self.dest_tree.setRootIndex(self.dest_file_model.index(folder))

    def move_current_video(self):
        # 1. Get current video
        source_idx = self.source_tree.currentIndex()
        if not source_idx.isValid():
            return
            
        file_path = self.file_model.filePath(source_idx)
        if not file_path or not os.path.exists(file_path):
            return
        
        # 2. Get destination
        # Check if we selected a sub-folder in Tree
        dest_idx = self.dest_tree.currentIndex()
        if dest_idx.isValid():
            dest_folder = self.dest_file_model.filePath(dest_idx)
        else:
            # Fallback to current root in combo
            dest_folder = self.dest_combo.currentText()
            
        if not dest_folder or not os.path.exists(dest_folder):
            QMessageBox.warning(self, "No Destination", "Please select a valid destination folder.")
            return
        
        # 3. Move file
        file_name = os.path.basename(file_path)
        target_path = os.path.join(dest_folder, file_name)
        
        # Save current position to restore selection (which effectively selects 'next' as items shift up)
        current_row = source_idx.row()
        parent_idx = source_idx.parent()
        
        try:
            self.player.stop() # Release file lock if any
            self.player.setSource(QUrl())
            
            shutil.move(file_path, target_path)
            print(f"Moved directory: {file_path} -> {target_path}")
            
            # 4. Auto-advance to "next" file
            # Since the current file is gone, the file that was below it is now at 'current_row'.
            # We need to wait slightly for the filesystem watcher to update the model?
            # QFileSystemModel is async. Let's try re-selecting after a short delay or just accept it might deselect.
            # A robust way is complicated with QFileSystemModel. 
            # For now, let's just clear selection so user knows to pick next, 
            # or better users often click manually.
            pass
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to move file:\n{e}")

    def show_preferences(self):
        dlg = PreferencesDialog(self)
        if dlg.exec():
            self.load_preferences()

    def load_preferences(self):
        # 1. Sources
        sources = self.settings.value("source_folders", [], type=list)
        if not isinstance(sources, list): sources = []
        
        # Save current selection to restore it if possible
        current_source = self.source_combo.currentText()
        
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        self.source_combo.addItems(sources)
        self.source_combo.blockSignals(False)
        
        # Restore selection or select first
        index = self.source_combo.findText(current_source)
        if index >= 0:
            self.source_combo.setCurrentIndex(index)
        elif self.source_combo.count() > 0:
            self.source_combo.setCurrentIndex(0)
            self.on_source_combo_changed()
            
        # 2. Destinations
        dests = self.settings.value("dest_folders", [], type=list)
        if not isinstance(dests, list): dests = []
        
        current_dest = self.dest_combo.currentText()
        
        self.dest_combo.blockSignals(True)
        self.dest_combo.clear()
        self.dest_combo.addItems(dests)
        self.dest_combo.blockSignals(False)
        
        index = self.dest_combo.findText(current_dest)
        if index >= 0:
            self.dest_combo.setCurrentIndex(index)
        elif self.dest_combo.count() > 0:
            self.dest_combo.setCurrentIndex(0)
            self.on_dest_combo_changed()


    def show_about(self):
        QMessageBox.about(self, "About Video Sorter", 
                          "<h3>Video Sorter</h3>"
                          "<p>Version 1.0</p>"
                          "<p>A simple tool to sort your video collection.</p>"
                          "<p>Built with Python & PyQt6.</p>")

    # --- Playback Controls ---
    
    def toggle_playback(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.btn_play.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        else:
            self.player.play()
            self.btn_play.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))

    def stop_video(self):
        self.player.stop()
        self.btn_play.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))

    def seek_relative(self, delta_ms):
        pos = self.player.position()
        self.player.setPosition(pos + delta_ms)

    def set_volume(self, value):
        self.audio_output.setVolume(value / 100.0)

    def resolve_next_index(self, step=1):
        """Helper to find the next/prev index based on current selection."""
        current_idx = self.source_tree.currentIndex()
        if not current_idx.isValid():
            return None
        
        # We need to traverse the model in the visible order.
        # QTreeView doesn't easily give "visual index + 1".
        # Simplest approach for QFileSystemModel in standard view:
        # Use QTreeView.indexBelow() / indexAbove()
        
        if step > 0:
            next_idx = self.source_tree.indexBelow(current_idx)
        else:
            next_idx = self.source_tree.indexAbove(current_idx)
            
        if next_idx.isValid() and not self.file_model.isDir(next_idx):
            return next_idx
        elif next_idx.isValid():
             # If directory, skip it? Or just select it?
             # If we hit a dir, try one more step?
             # For simplicity, let's just accept it and let handling logic filter
             pass
        
        return next_idx

    def play_previous_video(self):
        idx = self.resolve_next_index(step=-1)
        if idx and idx.isValid():
             self.source_tree.setCurrentIndex(idx)
             self.on_file_selected(idx)

    def play_next_video(self):
        idx = self.resolve_next_index(step=1)
        if idx and idx.isValid():
             self.source_tree.setCurrentIndex(idx)
             self.on_file_selected(idx)
