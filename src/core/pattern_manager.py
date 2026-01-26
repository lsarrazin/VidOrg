"""Pattern manager for user-defined rename patterns."""
import re
import json
from typing import List, Optional, Tuple
from PyQt6.QtCore import QSettings


class Pattern:
    """Represents a single rename pattern."""
    
    def __init__(self, description: str, matching_pattern: str, 
                 renaming_pattern: str, enabled: bool = True):
        self.description = description
        self.matching_pattern = matching_pattern
        self.renaming_pattern = renaming_pattern
        self.enabled = enabled
    
    def to_dict(self) -> dict:
        """Convert pattern to dictionary for serialization."""
        return {
            'description': self.description,
            'matching_pattern': self.matching_pattern,
            'renaming_pattern': self.renaming_pattern,
            'enabled': self.enabled
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'Pattern':
        """Create pattern from dictionary."""
        return Pattern(
            description=data.get('description', ''),
            matching_pattern=data.get('matching_pattern', ''),
            renaming_pattern=data.get('renaming_pattern', ''),
            enabled=data.get('enabled', True)
        )
    
    def matches(self, filename: str) -> bool:
        """Check if pattern matches the given filename."""
        if not self.enabled:
            return False
        try:
            return re.search(self.matching_pattern, filename) is not None
        except re.error:
            return False
    
    def apply(self, filename: str) -> Optional[str]:
        """Apply the renaming pattern to the filename.
        
        Returns the new filename if successful, None otherwise.
        """
        if not self.enabled:
            return None
        
        try:
            match = re.search(self.matching_pattern, filename)
            if not match:
                return None
            
            # Use named groups if available, otherwise use numbered groups
            if match.groupdict():
                # Named groups: use format with named placeholders
                return self.renaming_pattern.format(**match.groupdict())
            else:
                # Numbered groups: use regex substitution
                return re.sub(self.matching_pattern, self.renaming_pattern, filename)
        except (re.error, KeyError, IndexError):
            return None


class PatternManager:
    """Manages user-defined rename patterns."""
    
    SETTINGS_KEY = "rename_patterns"
    
    def __init__(self):
        self.settings = QSettings("org.fr.laurent", "VidOrg")
        self.patterns: List[Pattern] = []
        self.load_patterns()
    
    def load_patterns(self):
        """Load patterns from QSettings."""
        patterns_json = self.settings.value(self.SETTINGS_KEY, "[]")
        
        # Handle both string and list types from QSettings
        if isinstance(patterns_json, str):
            try:
                patterns_data = json.loads(patterns_json)
            except json.JSONDecodeError:
                patterns_data = []
        elif isinstance(patterns_json, list):
            patterns_data = patterns_json
        else:
            patterns_data = []
        
        self.patterns = [Pattern.from_dict(p) for p in patterns_data]
    
    def save_patterns(self):
        """Save patterns to QSettings."""
        patterns_data = [p.to_dict() for p in self.patterns]
        patterns_json = json.dumps(patterns_data)
        self.settings.setValue(self.SETTINGS_KEY, patterns_json)
    
    def add_pattern(self, pattern: Pattern, index: Optional[int] = None):
        """Add a pattern at the specified index (or at the end)."""
        if index is None:
            self.patterns.append(pattern)
        else:
            self.patterns.insert(index, pattern)
    
    def remove_pattern(self, index: int):
        """Remove pattern at the specified index."""
        if 0 <= index < len(self.patterns):
            del self.patterns[index]
    
    def move_pattern_up(self, index: int):
        """Move pattern up in the list (higher priority)."""
        if 0 < index < len(self.patterns):
            self.patterns[index], self.patterns[index - 1] = \
                self.patterns[index - 1], self.patterns[index]
    
    def move_pattern_down(self, index: int):
        """Move pattern down in the list (lower priority)."""
        if 0 <= index < len(self.patterns) - 1:
            self.patterns[index], self.patterns[index + 1] = \
                self.patterns[index + 1], self.patterns[index]
    
    def find_matching_patterns(self, filename: str) -> List[Tuple[int, Pattern]]:
        """Find all patterns that match the filename.
        
        Returns list of (index, pattern) tuples in order of priority.
        """
        matching = []
        for i, pattern in enumerate(self.patterns):
            if pattern.matches(filename):
                matching.append((i, pattern))
        return matching
    
    def apply_first_matching(self, filename: str) -> Optional[Tuple[Pattern, str]]:
        """Apply the first matching pattern to the filename.
        
        Returns (pattern, new_filename) if successful, None otherwise.
        """
        for pattern in self.patterns:
            if pattern.enabled:
                new_name = pattern.apply(filename)
                if new_name is not None:
                    return (pattern, new_name)
        return None
    
    @staticmethod
    def validate_pattern(matching_pattern: str, renaming_pattern: str, 
                        test_filename: str = "") -> Tuple[bool, str, str]:
        """Validate a pattern and optionally test it.
        
        Returns (is_valid, error_message, preview_result).
        """
        # Validate matching pattern
        try:
            re.compile(matching_pattern)
        except re.error as e:
            return (False, f"Invalid matching pattern: {e}", "")
        
        # Test if provided
        if test_filename:
            try:
                match = re.search(matching_pattern, test_filename)
                if not match:
                    return (True, "", "No match")
                
                # Try to apply renaming pattern
                if match.groupdict():
                    try:
                        result = renaming_pattern.format(**match.groupdict())
                        return (True, "", result)
                    except KeyError as e:
                        return (False, f"Invalid group reference: {e}", "")
                else:
                    try:
                        result = re.sub(matching_pattern, renaming_pattern, test_filename)
                        return (True, "", result)
                    except re.error as e:
                        return (False, f"Invalid renaming pattern: {e}", "")
            except Exception as e:
                return (False, f"Error testing pattern: {e}", "")
        
        return (True, "", "")
