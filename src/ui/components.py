from PyQt5.QtWidgets import QTableWidget
from src.utils.constants import STYLES

def create_table():
    table = QTableWidget()
    table.setStyleSheet(STYLES['table'])
    return table