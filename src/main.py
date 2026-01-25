import sys
import os

# Add project root to sys.path to allow imports from src
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir)) # VidOrg/src/main.py -> VidOrg
sys.path.append(project_root)

# Also add the directory containing main.py's parent (VidOrg) to path just in case
sys.path.append(os.path.dirname(current_dir))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from src.ui.window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("src/assets/icon.png"))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
