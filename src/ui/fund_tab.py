import sqlite3
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton,
    QHBoxLayout, QTabWidget, QInputDialog, QMessageBox, QComboBox
)
from src.utils.constants import TABLE_HEADERS, STYLES, SAMPLE_FUND
from src.charts.echart_window import EChartWindow
from src.database.db_operations import DBOperations
from src.ui.components import create_table
from .search_panel import SearchPanel
from src.utils.constants import DB_PATH, SAMPLE_FUND, DB_FIELDS


class FundTab(QWidget):
    def __init__(self, fund_id, parent=None):
        super().__init__(parent)
        self.fund_id = fund_id
        self.init_ui()
    
    def load_funds(self):
        funds = DBOperations.get_all_funds()
        for fund in funds:
            self.add_fund_tab(fund[0], fund[1], fund[2])
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Add search panel
        search_panel = SearchPanel(self.fund_id)
        layout.addWidget(search_panel)
        
        # Add table
        self.table = create_table()
        layout.addWidget(self.table)
        
        # Update table data
        self.update_table()
    
    def add_fund(self):
        name, ok = QInputDialog.getText(self, '新增基金', '请输入基金名称:')
        if ok and name:
            code, ok = QInputDialog.getText(self, '新增基金', '请输入基金代码:')
            if ok and code:
                try:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    
                    # Check if name or code already exists
                    c.execute("SELECT name FROM funds WHERE name=? OR code=?", (name, code))
                    if c.fetchone():
                        QMessageBox.warning(self, '警告', '基金名称或代码已存在！')
                        conn.close()
                        return
                        
                    c.execute("INSERT INTO funds (name, code) VALUES (?, ?)", (name, code))
                    fund_id = c.lastrowid
                    conn.commit()
                    conn.close()
                    
                    self.add_fund_tab(fund_id, name, code)
                except Exception as e:
                    QMessageBox.critical(self, '错误', f'添加基金失败：{str(e)}')

    def update_table(self, filter_text=None):
        rows = DBOperations.get_fund_transactions(self.fund_id, filter_text)
        self.table.setRowCount(len(rows))
        # ... rest of the table update code ...

