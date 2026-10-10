from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton
)
from PyQt5.QtCore import pyqtSignal
from src.utils.constants import STYLES
from src.database.db_operations import DBOperations
from charts.echart_window import EChartWindow

class SearchPanel(QWidget):
    
    def create_search_panel(self, fund_id):
        panel = QWidget()
        layout = QHBoxLayout(panel)
        
        self.time_filter = QLineEdit()
        self.time_filter.setPlaceholderText('按时间搜索 (如: 2025-04-07)')
        layout.addWidget(QLabel('时间过滤:'))
        layout.addWidget(self.time_filter)
        
        search_btn = QPushButton('执行搜索')
        search_btn.clicked.connect(lambda: self.apply_filters(fund_id))
        layout.addWidget(search_btn)
        
        # Replace clear button with show chart button
        chart_btn = QPushButton('查看图表')
        chart_btn.setStyleSheet("background-color: #1976D2; color: white;")
        chart_btn.clicked.connect(self.show_echart_window)
        layout.addWidget(chart_btn)
        
        # Add new record button
        add_btn = QPushButton('新增记录')
        add_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        add_btn.clicked.connect(lambda: DBOperations.add_new_record(fund_id))
        layout.addWidget(add_btn)
        
        return panel
    
    def apply_filters(self, fund_id):
        filter_text = self.time_filter.text()
        if fund_id in self.fund_tables:
            self.update_table(self.fund_tables[fund_id], fund_id, filter_text)
    
    def show_echart_window(self):
        if not hasattr(self, 'echart_window') or not self.echart_window:
            self.echart_window = EChartWindow(self)
        self.echart_window.show()