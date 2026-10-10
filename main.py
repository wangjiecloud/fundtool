import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from PyQt5.QtWidgets import QApplication
from src.ui.main_window import FundVisualizer

if __name__ == '__main__':
    app = QApplication(sys.argv)
    visualizer = FundVisualizer()
    visualizer.show()
    sys.exit(app.exec_())