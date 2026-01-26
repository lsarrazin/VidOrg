from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QGroupBox, QCheckBox,
                             QMessageBox, QScrollArea, QWidget, QComboBox)
from PyQt6.QtCore import Qt
import os
import re
from src.core.pattern_manager import PatternManager


class RenameDialog(QDialog):
    """Assisted file renaming dialog with pattern detection and removal."""
    
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.directory = os.path.dirname(file_path)
        self.original_name = os.path.basename(file_path)
        self.name_without_ext, self.extension = os.path.splitext(self.original_name)
        
        self.detected_prefixes = []
        self.detected_suffixes = []
        self.prefix_checkboxes = []
        self.suffix_checkboxes = []
        
        # User-defined patterns
        self.pattern_manager = PatternManager()
        self.matching_patterns = []
        self.selected_pattern_index = -1
        
        self.new_filename = self.original_name
        
        self.setWindowTitle("Assisted Rename")
        self.setMinimumWidth(600)
        self.setup_ui()
        self.detect_user_patterns()
        self.detect_patterns()
        self.update_preview()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Original filename display
        orig_group = QGroupBox("Original Filename")
        orig_layout = QVBoxLayout()
        self.label_original = QLabel(self.original_name)
        self.label_original.setWordWrap(True)
        self.label_original.setStyleSheet("font-weight: bold; padding: 5px;")
        orig_layout.addWidget(self.label_original)
        orig_group.setLayout(orig_layout)
        layout.addWidget(orig_group)
        
        # User-defined patterns section
        self.user_patterns_group = QGroupBox("User-Defined Patterns")
        user_patterns_layout = QVBoxLayout()
        
        user_patterns_label = QLabel("Select a pattern to apply:")
        user_patterns_layout.addWidget(user_patterns_label)
        
        self.pattern_combo = QComboBox()
        self.pattern_combo.currentIndexChanged.connect(self.on_pattern_selected)
        user_patterns_layout.addWidget(self.pattern_combo)
        
        self.pattern_preview = QLabel()
        self.pattern_preview.setWordWrap(True)
        self.pattern_preview.setStyleSheet("font-style: italic; color: #666; padding: 5px;")
        user_patterns_layout.addWidget(self.pattern_preview)
        
        self.user_patterns_group.setLayout(user_patterns_layout)
        layout.addWidget(self.user_patterns_group)
        
        # Detected patterns section
        patterns_group = QGroupBox("Detected Patterns")
        patterns_layout = QVBoxLayout()
        
        # Prefixes
        self.prefix_label = QLabel("Prefixes:")
        self.prefix_label.setStyleSheet("font-weight: bold;")
        patterns_layout.addWidget(self.prefix_label)
        
        # Scrollable area for prefix checkboxes
        self.prefix_scroll = QScrollArea()
        self.prefix_scroll.setWidgetResizable(True)
        self.prefix_scroll.setMaximumHeight(150)
        self.prefix_widget = QWidget()
        self.prefix_layout = QVBoxLayout(self.prefix_widget)
        self.prefix_layout.setContentsMargins(10, 5, 10, 5)
        self.prefix_scroll.setWidget(self.prefix_widget)
        patterns_layout.addWidget(self.prefix_scroll)
        
        # Suffixes
        self.suffix_label = QLabel("Suffixes:")
        self.suffix_label.setStyleSheet("font-weight: bold;")
        patterns_layout.addWidget(self.suffix_label)
        
        # Scrollable area for suffix checkboxes
        self.suffix_scroll = QScrollArea()
        self.suffix_scroll.setWidgetResizable(True)
        self.suffix_scroll.setMaximumHeight(150)
        self.suffix_widget = QWidget()
        self.suffix_layout = QVBoxLayout(self.suffix_widget)
        self.suffix_layout.setContentsMargins(10, 5, 10, 5)
        self.suffix_scroll.setWidget(self.suffix_widget)
        patterns_layout.addWidget(self.suffix_scroll)
        
        patterns_group.setLayout(patterns_layout)
        layout.addWidget(patterns_group)
        
        # Manual edit section
        manual_group = QGroupBox("Manual Edit")
        manual_layout = QVBoxLayout()
        
        manual_label = QLabel("Edit filename directly (without extension):")
        manual_layout.addWidget(manual_label)
        
        self.edit_filename = QLineEdit()
        self.edit_filename.setText(self.name_without_ext)
        self.edit_filename.textChanged.connect(self.on_manual_edit)
        manual_layout.addWidget(self.edit_filename)
        
        manual_group.setLayout(manual_layout)
        layout.addWidget(manual_group)
        
        # Preview section
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()
        self.label_preview = QLabel()
        self.label_preview.setWordWrap(True)
        self.label_preview.setStyleSheet("font-weight: bold; color: #0066cc; padding: 5px;")
        preview_layout.addWidget(self.label_preview)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_cancel)
        
        self.btn_rename = QPushButton("Rename")
        self.btn_rename.clicked.connect(self.accept_rename)
        self.btn_rename.setDefault(True)
        button_layout.addWidget(self.btn_rename)
        
        layout.addLayout(button_layout)
        
    def detect_patterns(self):
        """Detect common prefixes and suffixes in the filename."""
        name = self.name_without_ext
        
        # Detect prefixes
        prefix_patterns = [
            # Bracketed patterns at start
            (r'^(\[[^\]]+\])', 'Bracketed tag'),
            (r'^(\([^\)]+\))', 'Parenthesized tag'),
            (r'^(\{[^\}]+\})', 'Braced tag'),
            # Date patterns
            (r'^(\d{4}-\d{2}-\d{2})', 'Date (YYYY-MM-DD)'),
            (r'^(\d{8})', 'Date (YYYYMMDD)'),
            (r'^(\d{4}\.\d{2}\.\d{2})', 'Date (YYYY.MM.DD)'),
            # Common prefixes
            (r'^(copy\s+of\s+)', 'Copy prefix'),
            (r'^(new\s+)', 'New prefix'),
            (r'^(\d+\s*[-_]\s*)', 'Number prefix'),
            # Separators after text
            (r'^([^_\-\.]+[-_\.]+)', 'Text with separator'),
        ]
        
        for pattern, description in prefix_patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                prefix_text = match.group(1)
                # Avoid duplicates
                if prefix_text not in [p[0] for p in self.detected_prefixes]:
                    self.detected_prefixes.append((prefix_text, description))
        
        # Detect suffixes
        suffix_patterns = [
            # Bracketed patterns at end
            (r'(\[[^\]]+\])$', 'Bracketed tag'),
            (r'(\([^\)]+\))$', 'Parenthesized tag'),
            (r'(\{[^\}]+\})$', 'Braced tag'),
            # Common suffixes
            (r'([-_\s]+copy)$', 'Copy suffix'),
            (r'([-_\s]+new)$', 'New suffix'),
            (r'([-_\s]+\d+)$', 'Number suffix'),
            (r'([-_\s]+final)$', 'Final suffix'),
            (r'([-_\s]+old)$', 'Old suffix'),
            (r'([-_\s]+backup)$', 'Backup suffix'),
            # Separators before text
            (r'([-_\.]+[^_\-\.]+)$', 'Separator with text'),
        ]
        
        for pattern, description in suffix_patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                suffix_text = match.group(1)
                # Avoid duplicates
                if suffix_text not in [s[0] for s in self.detected_suffixes]:
                    self.detected_suffixes.append((suffix_text, description))
        
        # Create checkboxes for detected patterns
        if self.detected_prefixes:
            for prefix_text, description in self.detected_prefixes:
                cb = QCheckBox(f'Remove "{prefix_text}" ({description})')
                cb.stateChanged.connect(self.update_preview)
                self.prefix_checkboxes.append((cb, prefix_text))
                self.prefix_layout.addWidget(cb)
        else:
            no_prefix_label = QLabel("No common prefixes detected")
            no_prefix_label.setStyleSheet("font-style: italic; color: #666;")
            self.prefix_layout.addWidget(no_prefix_label)
            
        if self.detected_suffixes:
            for suffix_text, description in self.detected_suffixes:
                cb = QCheckBox(f'Remove "{suffix_text}" ({description})')
                cb.stateChanged.connect(self.update_preview)
                self.suffix_checkboxes.append((cb, suffix_text))
                self.suffix_layout.addWidget(cb)
        else:
            no_suffix_label = QLabel("No common suffixes detected")
            no_suffix_label.setStyleSheet("font-style: italic; color: #666;")
            self.suffix_layout.addWidget(no_suffix_label)
    
    def detect_user_patterns(self):
        """Detect and populate user-defined patterns that match the filename."""
        self.matching_patterns = self.pattern_manager.find_matching_patterns(self.name_without_ext)
        
        # Populate combo box
        self.pattern_combo.blockSignals(True)
        self.pattern_combo.clear()
        self.pattern_combo.addItem("-- No pattern --", -1)
        
        if self.matching_patterns:
            for idx, (pattern_idx, pattern) in enumerate(self.matching_patterns):
                self.pattern_combo.addItem(pattern.description, pattern_idx)
            
            # Auto-select first matching pattern
            self.pattern_combo.setCurrentIndex(1)  # Index 1 is first pattern (0 is "No pattern")
            self.selected_pattern_index = 0
            self.user_patterns_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        else:
            self.pattern_combo.addItem("(No matching patterns found)", -1)
            self.pattern_combo.setEnabled(False)
            self.user_patterns_group.setStyleSheet("")
        
        self.pattern_combo.blockSignals(False)
    
    def on_pattern_selected(self, combo_index):
        """Handle pattern selection from combo box."""
        if combo_index <= 0:
            # "No pattern" selected
            self.selected_pattern_index = -1
            self.pattern_preview.setText("")
            self.update_preview()
            return
        
        # Get the actual pattern index from combo data
        pattern_idx = self.pattern_combo.currentData()
        if pattern_idx is None or pattern_idx < 0:
            self.selected_pattern_index = -1
            self.pattern_preview.setText("")
            self.update_preview()
            return
        
        # Find the pattern in our matching list
        for idx, (p_idx, pattern) in enumerate(self.matching_patterns):
            if p_idx == pattern_idx:
                self.selected_pattern_index = idx
                
                # Show preview of what this pattern will do
                result = pattern.apply(self.name_without_ext)
                if result:
                    self.pattern_preview.setText(f"Preview: {result}")
                else:
                    self.pattern_preview.setText("")
                
                # Apply the pattern
                self.update_preview()
                break
    
    def update_preview(self):
        """Update the preview based on selected patterns."""
        # Start with original name (without extension)
        new_name = self.name_without_ext
        
        # First, apply user-defined pattern if selected
        if self.selected_pattern_index >= 0 and self.selected_pattern_index < len(self.matching_patterns):
            _, pattern = self.matching_patterns[self.selected_pattern_index]
            result = pattern.apply(new_name)
            if result:
                new_name = result
                # When user pattern is applied, skip the automatic prefix/suffix detection
                # User can still manually edit after
                self.edit_filename.blockSignals(True)
                self.edit_filename.setText(new_name)
                self.edit_filename.blockSignals(False)
                
                self.new_filename = new_name + self.extension
                self.label_preview.setText(self.new_filename)
                return
        
        # Otherwise, use the old prefix/suffix detection logic
        # Remove selected prefixes (in order of appearance)
        for cb, prefix_text in self.prefix_checkboxes:
            if cb.isChecked():
                new_name = new_name.replace(prefix_text, '', 1)
        
        # Remove selected suffixes (in reverse order to handle overlaps)
        for cb, suffix_text in reversed(self.suffix_checkboxes):
            if cb.isChecked():
                # Remove from the end
                if new_name.endswith(suffix_text):
                    new_name = new_name[:-len(suffix_text)]
        
        # Clean up multiple separators and trim
        new_name = re.sub(r'[-_\\.]+', '_', new_name)  # Normalize separators
        new_name = new_name.strip('_-. ')  # Trim separators from edges
        
        # Ensure we have a valid name
        if not new_name:
            new_name = "renamed"
        
        # Update the manual edit field (without triggering the signal)
        self.edit_filename.blockSignals(True)
        self.edit_filename.setText(new_name)
        self.edit_filename.blockSignals(False)
        
        # Update preview with extension
        self.new_filename = new_name + self.extension
        self.label_preview.setText(self.new_filename)
        
    def on_manual_edit(self, text):
        """Handle manual editing of the filename."""
        # Update preview with the manually edited name
        new_name = text.strip()
        if not new_name:
            new_name = "renamed"
        
        self.new_filename = new_name + self.extension
        self.label_preview.setText(self.new_filename)
    
    def accept_rename(self):
        """Validate and accept the rename."""
        # Get the final name from the edit field
        new_name = self.edit_filename.text().strip()
        
        # Validation
        if not new_name:
            QMessageBox.warning(self, "Invalid Name", "Filename cannot be empty.")
            return
        
        # Check for invalid characters
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        if any(char in new_name for char in invalid_chars):
            QMessageBox.warning(self, "Invalid Name", 
                              f"Filename contains invalid characters: {', '.join(invalid_chars)}")
            return
        
        # Add extension back
        self.new_filename = new_name + self.extension
        
        # Check if name changed
        if self.new_filename == self.original_name:
            QMessageBox.information(self, "No Change", "The filename hasn't changed.")
            return
        
        # Check if file already exists
        new_path = os.path.join(self.directory, self.new_filename)
        if os.path.exists(new_path):
            reply = QMessageBox.question(self, "File Exists", 
                                        f"A file named '{self.new_filename}' already exists. Overwrite?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        self.accept()
    
    def get_new_filename(self):
        """Return the new filename."""
        return self.new_filename
