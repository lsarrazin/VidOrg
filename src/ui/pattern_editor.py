"""Pattern editor dialog with live preview and regex help."""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QLineEdit, QTextEdit, QDialogButtonBox, 
                              QGroupBox, QSplitter, QWidget, QScrollArea)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from src.core.pattern_manager import PatternManager
import re


class PatternEditorDialog(QDialog):
    """Dialog for creating/editing a rename pattern with live preview."""
    
    REGEX_HELP = """<h3>Common Regex Patterns</h3>

<b>Basic Matching:</b>
<table>
<tr><td><code>.</code></td><td>Any single character</td></tr>
<tr><td><code>*</code></td><td>0 or more of previous</td></tr>
<tr><td><code>+</code></td><td>1 or more of previous</td></tr>
<tr><td><code>?</code></td><td>0 or 1 of previous</td></tr>
<tr><td><code>^</code></td><td>Start of string</td></tr>
<tr><td><code>$</code></td><td>End of string</td></tr>
</table>

<b>Character Classes:</b>
<table>
<tr><td><code>\\d</code></td><td>Any digit (0-9)</td></tr>
<tr><td><code>\\w</code></td><td>Word character (a-z, A-Z, 0-9, _)</td></tr>
<tr><td><code>\\s</code></td><td>Whitespace</td></tr>
<tr><td><code>[abc]</code></td><td>Any of a, b, or c</td></tr>
<tr><td><code>[^abc]</code></td><td>Not a, b, or c</td></tr>
</table>

<b>Groups:</b>
<table>
<tr><td><code>(pattern)</code></td><td>Capture group (\\1, \\2, ...)</td></tr>
<tr><td><code>(?P&lt;name&gt;pattern)</code></td><td>Named group {name}</td></tr>
<tr><td><code>(?:pattern)</code></td><td>Non-capturing group</td></tr>
</table>

<b>Examples:</b>
<table>
<tr><td><code>^\\[.*?\\]\\s*(.*)$</code></td><td>Match [tag] prefix</td></tr>
<tr><td><code>^(?P&lt;name&gt;.+?)\\s*\\(\\d{4}\\)$</code></td><td>Match "Name (2024)"</td></tr>
<tr><td><code>^\\d+[-_](.*)$</code></td><td>Match number prefix</td></tr>
</table>

<b>Renaming:</b>
<ul>
<li>Use <code>\\1</code>, <code>\\2</code> for numbered groups</li>
<li>Use <code>{name}</code> for named groups</li>
</ul>
"""
    
    def __init__(self, pattern=None, parent=None):
        """Initialize the pattern editor.
        
        Args:
            pattern: Optional Pattern object to edit
            parent: Parent widget
        """
        super().__init__(parent)
        self.pattern = pattern
        self.setWindowTitle("Edit Pattern" if pattern else "New Pattern")
        self.setMinimumSize(900, 600)
        
        self.setup_ui()
        
        # Load existing pattern if editing
        if pattern:
            self.load_pattern(pattern)
        else:
            # Set default example
            self.sample_input.setText("[TAG] Example Video Name.mp4")
        
        # Initial update
        self.update_preview()
    
    def setup_ui(self):
        """Setup the user interface."""
        layout = QHBoxLayout(self)
        
        # Main splitter: Editor on left, Help on right
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # --- Left Panel: Editor ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Description
        desc_group = QGroupBox("Description")
        desc_layout = QVBoxLayout()
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("e.g., Remove bracketed tags")
        desc_layout.addWidget(self.description_input)
        desc_group.setLayout(desc_layout)
        left_layout.addWidget(desc_group)
        
        # Sample Filename
        sample_group = QGroupBox("Test Filename")
        sample_layout = QVBoxLayout()
        sample_label = QLabel("Enter a sample filename to test your pattern:")
        sample_layout.addWidget(sample_label)
        self.sample_input = QLineEdit()
        self.sample_input.setPlaceholderText("e.g., [TAG] My Video.mp4")
        self.sample_input.textChanged.connect(self.update_preview)
        sample_layout.addWidget(self.sample_input)
        sample_group.setLayout(sample_layout)
        left_layout.addWidget(sample_group)
        
        # Matching Pattern
        match_group = QGroupBox("Matching Pattern (Regex)")
        match_layout = QVBoxLayout()
        match_label = QLabel("Enter the regex pattern to match filenames:")
        match_layout.addWidget(match_label)
        
        self.matching_input = QTextEdit()
        self.matching_input.setMaximumHeight(80)
        self.matching_input.setPlaceholderText("e.g., ^\\[.*?\\]\\s*(.*)$")
        self.matching_input.textChanged.connect(self.update_preview)
        match_layout.addWidget(self.matching_input)
        
        # Match indicator
        self.match_indicator = QLabel()
        self.match_indicator.setWordWrap(True)
        match_layout.addWidget(self.match_indicator)
        
        match_group.setLayout(match_layout)
        left_layout.addWidget(match_group)
        
        # Renaming Pattern
        rename_group = QGroupBox("Renaming Pattern")
        rename_layout = QVBoxLayout()
        rename_label = QLabel("Enter the replacement pattern (use \\1, \\2 or {name} for groups):")
        rename_layout.addWidget(rename_label)
        
        self.renaming_input = QTextEdit()
        self.renaming_input.setMaximumHeight(80)
        self.renaming_input.setPlaceholderText("e.g., \\1 or {name}")
        self.renaming_input.textChanged.connect(self.update_preview)
        rename_layout.addWidget(self.renaming_input)
        
        rename_group.setLayout(rename_layout)
        left_layout.addWidget(rename_group)
        
        # Preview
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()
        self.preview_label = QLabel()
        self.preview_label.setWordWrap(True)
        self.preview_label.setStyleSheet("padding: 10px; background-color: #707070; border-radius: 4px;")
        preview_layout.addWidget(self.preview_label)
        preview_group.setLayout(preview_layout)
        left_layout.addWidget(preview_group)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept_pattern)
        buttons.rejected.connect(self.reject)
        left_layout.addWidget(buttons)
        
        splitter.addWidget(left_widget)
        
        # --- Right Panel: Help ---
        help_scroll = QScrollArea()
        help_scroll.setWidgetResizable(True)
        help_scroll.setMinimumWidth(300)
        
        help_widget = QWidget()
        help_layout = QVBoxLayout(help_widget)
        
        help_label = QLabel(self.REGEX_HELP)
        help_label.setWordWrap(True)
        help_label.setTextFormat(Qt.TextFormat.RichText)
        help_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Set monospace font for code examples
        font = QFont("Courier New", 9)
        help_label.setFont(font)
        
        help_layout.addWidget(help_label)
        help_layout.addStretch()
        
        help_scroll.setWidget(help_widget)
        splitter.addWidget(help_scroll)
        
        # Set splitter sizes (70% editor, 30% help)
        splitter.setSizes([630, 270])
    
    def load_pattern(self, pattern):
        """Load a pattern into the editor."""
        self.description_input.setText(pattern.description)
        self.matching_input.setPlainText(pattern.matching_pattern)
        self.renaming_input.setPlainText(pattern.renaming_pattern)
    
    def update_preview(self):
        """Update the match indicator and preview based on current inputs."""
        sample = self.sample_input.text()
        matching = self.matching_input.toPlainText()
        renaming = self.renaming_input.toPlainText()
        
        if not sample or not matching:
            self.match_indicator.setText("")
            self.preview_label.setText("<i>Enter a sample filename and matching pattern to see preview</i>")
            self.match_indicator.setStyleSheet("")
            return
        
        # Validate and test pattern
        is_valid, error_msg, preview = PatternManager.validate_pattern(
            matching, renaming, sample
        )
        
        if not is_valid:
            # Error in pattern
            self.match_indicator.setText(f"❌ Error: {error_msg}")
            self.match_indicator.setStyleSheet("color: red; font-weight: bold; padding: 5px;")
            self.preview_label.setText("")
        elif preview == "No match":
            # Pattern is valid but doesn't match
            self.match_indicator.setText("⚠️ Pattern does not match the sample filename")
            self.match_indicator.setStyleSheet("color: orange; font-weight: bold; padding: 5px;")
            self.preview_label.setText("")
        else:
            # Success
            self.match_indicator.setText("✓ Pattern matches!")
            self.match_indicator.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
            
            # Show preview with before/after
            preview_html = f"""
            <table style="width: 100%;">
            <tr>
                <td style="font-weight: bold; width: 80px;">Original:</td>
                <td>{sample}</td>
            </tr>
            <tr>
                <td style="font-weight: bold;">Renamed:</td>
                <td style="color: #0066cc; font-weight: bold;">{preview}</td>
            </tr>
            </table>
            """
            self.preview_label.setText(preview_html)
    
    def accept_pattern(self):
        """Validate and accept the pattern."""
        description = self.description_input.text().strip()
        matching = self.matching_input.toPlainText().strip()
        renaming = self.renaming_input.toPlainText().strip()
        
        if not description:
            self.match_indicator.setText("❌ Please enter a description")
            self.match_indicator.setStyleSheet("color: red; font-weight: bold; padding: 5px;")
            return
        
        if not matching:
            self.match_indicator.setText("❌ Please enter a matching pattern")
            self.match_indicator.setStyleSheet("color: red; font-weight: bold; padding: 5px;")
            return
        
        # Validate pattern syntax
        is_valid, error_msg, _ = PatternManager.validate_pattern(matching, renaming)
        if not is_valid:
            self.match_indicator.setText(f"❌ {error_msg}")
            self.match_indicator.setStyleSheet("color: red; font-weight: bold; padding: 5px;")
            return
        
        self.accept()
    
    def get_pattern_data(self):
        """Get the pattern data from the dialog."""
        return {
            'description': self.description_input.text().strip(),
            'matching_pattern': self.matching_input.toPlainText().strip(),
            'renaming_pattern': self.renaming_input.toPlainText().strip(),
            'enabled': True
        }
