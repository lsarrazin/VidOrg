"""Pattern management widget for preferences dialog."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QTableWidget, QTableWidgetItem, QHeaderView,
                              QMessageBox, QCheckBox)
from PyQt6.QtCore import Qt
from src.core.pattern_manager import Pattern, PatternManager
from src.ui.pattern_editor import PatternEditorDialog


class PatternWidget(QWidget):
    """Widget for managing rename patterns in preferences."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pattern_manager = PatternManager()
        self.setup_ui()
        self.load_patterns()
    
    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        
        # Table for patterns
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Order", "Enabled", "Description", "Matching Pattern", "Renaming Pattern"
        ])
        
        # Configure table
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.itemDoubleClicked.connect(self.edit_pattern)
        self.table.itemChanged.connect(self.on_item_changed)
        
        layout.addWidget(self.table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.btn_add = QPushButton("Add Pattern")
        self.btn_add.clicked.connect(self.add_pattern)
        button_layout.addWidget(self.btn_add)
        
        self.btn_edit = QPushButton("Edit Pattern")
        self.btn_edit.clicked.connect(self.edit_pattern)
        button_layout.addWidget(self.btn_edit)
        
        self.btn_delete = QPushButton("Delete Pattern")
        self.btn_delete.clicked.connect(self.delete_pattern)
        button_layout.addWidget(self.btn_delete)
        
        button_layout.addStretch()
        
        self.btn_move_up = QPushButton("↑ Move Up")
        self.btn_move_up.clicked.connect(self.move_up)
        button_layout.addWidget(self.btn_move_up)
        
        self.btn_move_down = QPushButton("↓ Move Down")
        self.btn_move_down.clicked.connect(self.move_down)
        button_layout.addWidget(self.btn_move_down)
        
        layout.addLayout(button_layout)
    
    def load_patterns(self):
        """Load patterns from manager into table."""
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        
        for i, pattern in enumerate(self.pattern_manager.patterns):
            self.add_pattern_row(i, pattern)
        
        self.table.blockSignals(False)
    
    def add_pattern_row(self, row: int, pattern: Pattern):
        """Add a pattern to the table."""
        self.table.insertRow(row)
        
        # Order (1-indexed for display)
        order_item = QTableWidgetItem(str(row + 1))
        order_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        order_item.setFlags(order_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 0, order_item)
        
        # Enabled checkbox
        checkbox_widget = QWidget()
        checkbox_layout = QHBoxLayout(checkbox_widget)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        checkbox = QCheckBox()
        checkbox.setChecked(pattern.enabled)
        checkbox.stateChanged.connect(lambda state, r=row: self.on_enabled_changed(r, state))
        checkbox_layout.addWidget(checkbox)
        
        self.table.setCellWidget(row, 1, checkbox_widget)
        
        # Description
        desc_item = QTableWidgetItem(pattern.description)
        desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 2, desc_item)
        
        # Matching Pattern
        match_item = QTableWidgetItem(pattern.matching_pattern)
        match_item.setFlags(match_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        match_item.setFont(self.table.font())
        self.table.setItem(row, 3, match_item)
        
        # Renaming Pattern
        rename_item = QTableWidgetItem(pattern.renaming_pattern)
        rename_item.setFlags(rename_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        rename_item.setFont(self.table.font())
        self.table.setItem(row, 4, rename_item)
    
    def on_enabled_changed(self, row: int, state: int):
        """Handle enabled checkbox state change."""
        if 0 <= row < len(self.pattern_manager.patterns):
            self.pattern_manager.patterns[row].enabled = (state == Qt.CheckState.Checked.value)
    
    def on_item_changed(self, item):
        """Handle item changes in the table."""
        # Currently all items are read-only, so this shouldn't be called
        pass
    
    def add_pattern(self):
        """Add a new pattern."""
        dialog = PatternEditorDialog(parent=self)
        if dialog.exec():
            pattern_data = dialog.get_pattern_data()
            pattern = Pattern.from_dict(pattern_data)
            
            self.pattern_manager.add_pattern(pattern)
            self.load_patterns()
    
    def edit_pattern(self):
        """Edit the selected pattern."""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "No Selection", "Please select a pattern to edit.")
            return
        
        if current_row >= len(self.pattern_manager.patterns):
            return
        
        pattern = self.pattern_manager.patterns[current_row]
        dialog = PatternEditorDialog(pattern=pattern, parent=self)
        
        if dialog.exec():
            pattern_data = dialog.get_pattern_data()
            # Update the pattern
            pattern.description = pattern_data['description']
            pattern.matching_pattern = pattern_data['matching_pattern']
            pattern.renaming_pattern = pattern_data['renaming_pattern']
            
            self.load_patterns()
    
    def delete_pattern(self):
        """Delete the selected pattern."""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "No Selection", "Please select a pattern to delete.")
            return
        
        pattern = self.pattern_manager.patterns[current_row]
        reply = QMessageBox.question(
            self, 
            "Confirm Delete",
            f"Are you sure you want to delete the pattern '{pattern.description}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.pattern_manager.remove_pattern(current_row)
            self.load_patterns()
    
    def move_up(self):
        """Move the selected pattern up (higher priority)."""
        current_row = self.table.currentRow()
        if current_row <= 0:
            return
        
        self.pattern_manager.move_pattern_up(current_row)
        self.load_patterns()
        self.table.selectRow(current_row - 1)
    
    def move_down(self):
        """Move the selected pattern down (lower priority)."""
        current_row = self.table.currentRow()
        if current_row < 0 or current_row >= len(self.pattern_manager.patterns) - 1:
            return
        
        self.pattern_manager.move_pattern_down(current_row)
        self.load_patterns()
        self.table.selectRow(current_row + 1)
    
    def save_patterns(self):
        """Save patterns to settings."""
        self.pattern_manager.save_patterns()
    
    def get_patterns(self):
        """Get the current list of patterns."""
        return self.pattern_manager.patterns
