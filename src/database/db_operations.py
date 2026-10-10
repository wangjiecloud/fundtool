import sqlite3
from PyQt5 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets
from src.utils.constants import DB_PATH, SAMPLE_FUND, DB_FIELDS
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton,
    QHBoxLayout, QTabWidget, QInputDialog, QMessageBox, QComboBox
)
class DBOperations:
    @staticmethod
    def get_fund_transactions(fund_id, filter_text=None):
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            query = """SELECT time, buy_price, buy_quantity, total_buy,
                      sell_price, sell_quantity, total_sell,
                      high, low, open, close, change_percent
                      FROM fund_transactions 
                      WHERE fund_id = ? AND is_deleted = 0"""
            params = [fund_id]
            
            if filter_text:
                query += " AND time LIKE ?"
                params.append(f'%{filter_text}%')
                
            query += " ORDER BY time DESC"
            c.execute(query, params)
            return c.fetchall()

    @staticmethod
    def create_table():
        from PyQt5.QtWidgets import QTableWidget
        table = QTableWidget()
        table.setStyleSheet('''
            QTableWidget { border: 1px solid #ccc; font-size: 12px; }
            QTableWidget::header { background: #f0f0f0; }
            QTableWidget::item { padding: 8px; border-bottom: 1px solid #eee; }
        ''')
        return table

    @staticmethod
    def get_all_funds():
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT id, name, code FROM funds")
            return c.fetchall()

    @staticmethod
    def delete_fund(fund_id):
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM fund_transactions WHERE fund_id=?", (fund_id,))
            c.execute("DELETE FROM funds WHERE id=?", (fund_id,))
            conn.commit()
  

    def add_new_record(self, fund_id):
        self.add_dialog = QtWidgets.QDialog()
        self.add_dialog.setWindowTitle('新增交易记录')
        layout = QVBoxLayout()
        
        # Create input fields
        fields = []
        field_names = ['时间', '买入价', '买入数量', '总买入价', 
                    '卖出价', '卖出数量', '总卖出价', 
                    '最高价', '最低价', '开盘价', '收盘价', '涨跌情况']
        
        for name in field_names:
            label = QLabel(name)
            edit = QLineEdit()
            if name == '时间':
                edit.setPlaceholderText('格式: YYYY-MM-DD')
            layout.addWidget(label)
            layout.addWidget(edit)
            fields.append(edit)
        
        # Add buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("保存")
        save_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        save_btn.clicked.connect(lambda: self.save_new_record(fields, fund_id))
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.add_dialog.close)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.add_dialog.setLayout(layout)
        self.add_dialog.exec_()

    def save_new_record(self, fields, fund_id):
        try:
            values = [field.text() for field in fields]
            
            # Convert empty strings to None
            values = [val if val != '' else None for val in values]
            
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('''INSERT INTO fund_transactions 
                        (fund_id, time, buy_price, buy_quantity, total_buy,
                        sell_price, sell_quantity, total_sell,
                        high, low, open, close, change_percent)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (fund_id, *values))
            conn.commit()
            conn.close()
            
            self.add_dialog.close()
            
            # Use the correct table reference from fund_tables dictionary
            if fund_id in self.fund_tables:
                self.update_table(self.fund_tables[fund_id], fund_id)
            
            QtWidgets.QMessageBox.information(
                self, '成功', 
                '新记录添加成功！'
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, '错误',
                f'添加记录时发生错误：{str(e)}'
            )

    def clear_all_data(self, fund_id):
        reply = QtWidgets.QMessageBox.question(
            self, '确认', 
            '确定要清空所有交易数据吗？此操作可在数据库中恢复！',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            try:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                
                # 软删除：将记录标记为已删除而不是真正删除
                c.execute("""UPDATE fund_transactions 
                            SET is_deleted = 1 
                            WHERE fund_id = ?""", (fund_id,))
                
                conn.commit()
                
                # 更新表格显示
                if fund_id in self.fund_tables:
                    self.update_table(self.fund_tables[fund_id], fund_id)
                
                QtWidgets.QMessageBox.information(
                    self, '成功', 
                    '数据已隐藏！可以通过数据库恢复。'
                )
                
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self, '错误', 
                    f'操作失败：{str(e)}'
                )
            finally:
                if conn:
                    conn.close()

    def update_table(self, table, fund_id, filter_text=''):
        # 设置标志防止触发itemChanged信号
        self._updating_table = True
        try:
            rows = self.get_fund_transactions(fund_id, filter_text)

            table.setRowCount(len(rows))
            table.setColumnCount(12)
            headers = ['时间', '买入价', '买入数量', '总买入价', 
                       '卖出价', '卖出数量', '总卖出价', 
                       '最高价', '最低价', '开盘价', '收盘价', '涨跌情况']
            table.setHorizontalHeaderLabels(headers)

            for row_idx, row in enumerate(rows):
                for col_idx in range(12):
                    item = QTableWidgetItem(str(row[col_idx]) if row[col_idx] is not None else '')
                    table.setItem(row_idx, col_idx, item)

            table.resizeColumnsToContents()
        finally:
            # 移除标志
            delattr(self, '_updating_table')
    
    def get_fund_id(self, fund_code):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id FROM funds WHERE code=?", (fund_code,))
        fund_id = c.fetchone()[0]
        conn.close()
        return fund_id