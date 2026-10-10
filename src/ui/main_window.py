from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton, 
    QTableWidget, QTabWidget, QMessageBox
)
import sqlite3
from PyQt5 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets

from src.utils.constants import STYLES, SAMPLE_FUND
from src.database.init_db import init_database
from src.database.db_operations import DBOperations
from src.ui.fund_tab import FundTab


class FundVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        init_database()
        self.setWindowTitle('基金交易数据可视化平台')
        self.setGeometry(100, 100, 1200, 900)
        self.init_ui()
        self.echart_window = None

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 创建tab控件
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        main_layout.addWidget(self.tab_widget)

        # 添加"新增基金"按钮
        add_fund_btn = QPushButton('新增基金')
        add_fund_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        add_fund_btn.clicked.connect(self.add_fund)
        main_layout.addWidget(add_fund_btn)

        # 加载现有基金
        FundTab.load_funds()

    def show_context_menu(self, pos, table):
        menu = QtWidgets.QMenu()
        delete_action = menu.addAction("删除记录")
        
        # 获取点击的行
        row = table.rowAt(pos.y())
        if row >= 0:
            action = menu.exec_(table.mapToGlobal(pos))
            if action == delete_action:
                self.delete_record(table, row)

    def delete_record(self, table, row):
        try:
            # 获取时间作为标识
            time = table.item(row, 0).text()
            
            # 获取当前基金ID
            current_tab_text = self.tab_widget.tabText(self.tab_widget.currentIndex())
            fund_code = current_tab_text.split('(')[1].split(')')[0]
            
            reply = QMessageBox.question(
                self, '确认删除', 
                f'确定要删除 {time} 的记录吗？此操作将标记记录为已删除。',
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                conn = sqlite3.connect('fund.db')
                c = conn.cursor()
                
                # 获取fund_id
                c.execute("SELECT id FROM funds WHERE code=?", (fund_code,))
                fund_id = c.fetchone()[0]
                
                # 软删除记录
                c.execute("""UPDATE fund_transactions 
                            SET is_deleted = 1 
                            WHERE fund_id = ? AND time = ?""", 
                         (fund_id, time))
                
                conn.commit()
                conn.close()
                
                # 更新表格显示
                if fund_id in self.fund_tables:
                    self.update_table(self.fund_tables[fund_id], fund_id)
                
                QMessageBox.information(self, '成功', '记录已删除！')
                
        except Exception as e:
            QMessageBox.critical(self, '错误', f'删除记录失败：{str(e)}')

    def on_cell_changed(self, item, table):
        try:
            # 防止在更新表格时触发
            if hasattr(self, '_updating_table'):
                return
                
            row = item.row()
            col = item.column()
            new_value = item.text()
            
            # 获取时间和基金ID
            time = table.item(row, 0).text()
            current_tab_text = self.tab_widget.tabText(self.tab_widget.currentIndex())
            fund_code = current_tab_text.split('(')[1].split(')')[0]
            
            # 检查是否是示例基金
            if "示例基金" in current_tab_text:
                QMessageBox.warning(self, '警告', '示例基金数据不能修改！')
                self.update_table(table, DBOperations.get_fund_id(fund_code))
                return
            
            # 获取对应的数据库字段名
            headers = ['time', 'buy_price', 'buy_quantity', 'total_buy', 
                      'sell_price', 'sell_quantity', 'total_sell', 
                      'high', 'low', 'open', 'close', 'change_percent']
            field_name = headers[col]
            
            # 数据验证
            if col > 0 and col < 11:  # 数值字段
                try:
                    if new_value:
                        float(new_value)
                except ValueError:
                    QMessageBox.warning(self, '警告', '请输入有效的数字！')
                    self.update_table(table, self.get_fund_id(fund_code))
                    return
            
            # 更新数据库
            conn = sqlite3.connect('fund.db')
            c = conn.cursor()
            
            # 获取fund_id
            c.execute("SELECT id FROM funds WHERE code=?", (fund_code,))
            fund_id = c.fetchone()[0]
            
            # 更新记录
            c.execute(f"""UPDATE fund_transactions 
                         SET {field_name} = ? 
                         WHERE fund_id = ? AND time = ?""", 
                     (new_value if new_value else None, fund_id, time))
            
            conn.commit()
            conn.close()
            
            # 如果图表窗口打开，更新图表
            if hasattr(self, 'echart_window') and self.echart_window:
                self.echart_window.update_chart()
                
        except Exception as e:
            QMessageBox.critical(self, '错误', f'更新数据失败：{str(e)}')

