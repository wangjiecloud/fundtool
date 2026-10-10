import sqlite3
import sys, os
from pyecharts.commons.utils import JsCode
from PyQt5 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton,
    QHBoxLayout, QTabWidget, QInputDialog, QMessageBox, QComboBox
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from PyQt5.QtWebEngineWidgets import QWebEngineView
from pyecharts.charts import Line
from pyecharts import options as opts
import jinja2

# 修改数据库初始化函数，增加基金表
def init_database():
    conn = None
    try:
        conn = sqlite3.connect('fund.db')
        c = conn.cursor()
        
        # Check if is_deleted column exists
        c.execute("PRAGMA table_info(fund_transactions)")
        columns = [column[1] for column in c.fetchall()]
        
        # Add is_deleted column if it doesn't exist
        if 'is_deleted' not in columns:
            c.execute('''ALTER TABLE fund_transactions 
                        ADD COLUMN is_deleted INTEGER DEFAULT 0''')
            conn.commit()
            
        # Create tables if they don't exist
        c.execute('''CREATE TABLE IF NOT EXISTS funds
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    code TEXT UNIQUE)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS fund_transactions
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fund_id INTEGER,
                    time TEXT,
                    buy_price REAL,
                    buy_quantity INTEGER,
                    total_buy REAL,
                    sell_price REAL,
                    sell_quantity INTEGER,
                    total_sell REAL,
                    high REAL,
                    low REAL,
                    open REAL,
                    close REAL,
                    change_percent TEXT,
                    is_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (fund_id) REFERENCES funds (id))''')
        
        # Insert sample data if no data exists
        c.execute("SELECT COUNT(*) FROM funds")
        if c.fetchone()[0] == 0:
            c.execute("INSERT INTO funds (name, code) VALUES (?, ?)", 
                     ("示例基金", "000001"))
            fund_id = c.lastrowid
            
            sample_data = (fund_id, '2025-04-07', 1.307, 2000, 9159, 0, 0, 0, 
                          1.35, 1.27, 1.35, 1.3053, '-4.62%', 0)
            c.execute('''INSERT INTO fund_transactions 
                        (fund_id, time, buy_price, buy_quantity, total_buy,
                        sell_price, sell_quantity, total_sell,
                        high, low, open, close, change_percent, is_deleted)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', sample_data)
        
        conn.commit()
        
    except Exception as e:
        print(f"Database initialization error: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

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
        self.load_funds()

    def load_funds(self):
        conn = sqlite3.connect('fund.db')
        c = conn.cursor()
        c.execute("SELECT id, name, code FROM funds")
        funds = c.fetchall()
        conn.close()

        for fund in funds:
            self.add_fund_tab(fund[0], fund[1], fund[2])

    def add_fund(self):
        name, ok = QInputDialog.getText(self, '新增基金', '请输入基金名称:')
        if ok and name:
            # Check if trying to add sample fund
            if self.is_sample_fund(name=name):
                QMessageBox.warning(self, '警告', '不能添加"示例基金"，此名称已被保留！')
                return
                
            code, ok = QInputDialog.getText(self, '新增基金', '请输入基金代码:')
            if ok and code:
                try:
                    # Check if trying to use sample fund code
                    if self.is_sample_fund(code=code):
                        QMessageBox.warning(self, '警告', '不能使用示例基金代码！')
                        return
                    
                    conn = sqlite3.connect('fund.db')
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

    def add_fund_tab(self, fund_id, name, code):
        # 创建基金页面
        fund_page = QWidget()
        layout = QVBoxLayout(fund_page)
        
        # 搜索面板
        search_panel = self.create_search_panel(fund_id)
        layout.addWidget(search_panel)
        
        # 表格 - Store table reference in a dictionary using fund_id as key
        if not hasattr(self, 'fund_tables'):
            self.fund_tables = {}
        
        table = self.create_table()
        self.fund_tables[fund_id] = table
        layout.addWidget(table)
        
        # 添加到tab
        self.tab_widget.addTab(fund_page, f"{name}({code})")
        
        # 更新表格数据
        self.update_table(table, fund_id)

    def close_tab(self, index):
        tab_text = self.tab_widget.tabText(index)
        # if "示例基金" in tab_text:
        #     QMessageBox.warning(self, '警告', '示例基金不能被删除！')
        #     return
            
        reply = QMessageBox.question(self, '确认', 
                                   '确定要删除此基金及其所有交易记录吗？此操作不可恢复！',
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect('fund.db')
                c = conn.cursor()
                
                # Get fund_id from tab text
                fund_code = tab_text.split('(')[1].split(')')[0]
                c.execute("SELECT id FROM funds WHERE code=?", (fund_code,))
                fund_id = c.fetchone()[0]
                
                # Delete fund and its transactions
                c.execute("DELETE FROM fund_transactions WHERE fund_id=?", (fund_id,))
                c.execute("DELETE FROM funds WHERE id=?", (fund_id,))
                
                conn.commit()
                conn.close()
                
                # Remove tab
                self.tab_widget.removeTab(index)
                
            except Exception as e:
                QMessageBox.critical(self, '错误', f'删除基金失败：{str(e)}')

    def create_table(self):
        table = QTableWidget()
        table.setStyleSheet('''
            QTableWidget { border: 1px solid #ccc; font-size: 12px; }
            QTableWidget::header { background: #f0f0f0; }
            QTableWidget::item { padding: 8px; border-bottom: 1px solid #eee; }
        ''')
        
        # 启用编辑功能
        table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)
        
        # 连接编辑完成信号
        table.itemChanged.connect(lambda item: self.on_cell_changed(item, table))
        
        # 添加右键菜单
        table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(lambda pos, t=table: self.show_context_menu(pos, t))
        
        return table

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
        add_btn.clicked.connect(lambda: self.add_new_record(fund_id))
        layout.addWidget(add_btn)
        
        return panel

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
            
            conn = sqlite3.connect('fund.db')
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
                conn = sqlite3.connect('fund.db')
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
            conn = sqlite3.connect('fund.db')
            c = conn.cursor()
            query = '''SELECT time, buy_price, buy_quantity, total_buy, 
                              sell_price, sell_quantity, total_sell, 
                              high, low, open, close, change_percent 
                       FROM fund_transactions
                       WHERE fund_id = ? AND is_deleted = 0'''
            
            params = [fund_id]
            if filter_text:
                query += " AND time LIKE ?"
                params.append(f'%{filter_text}%')
            
            query += " ORDER BY time DESC"  # 按时间倒序排列
            
            c.execute(query, params)
            rows = c.fetchall()

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
            conn.close()
        finally:
            # 移除标志
            delattr(self, '_updating_table')

    def apply_filters(self, fund_id):
        filter_text = self.time_filter.text()
        if fund_id in self.fund_tables:
            self.update_table(self.fund_tables[fund_id], fund_id, filter_text)

    def show_echart_window(self):
        if not hasattr(self, 'echart_window') or not self.echart_window:
            self.echart_window = EChartWindow(self)
        self.echart_window.show()

    def is_sample_fund(self, name=None, code=None):
        """Check if the given name or code belongs to the sample fund"""
        if name and name.strip() == "示例基金":
            return True
        if code and code.strip() == "000001":
            return True
        return False

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
                self.update_table(table, self.get_fund_id(fund_code))
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

    def get_fund_id(self, fund_code):
        conn = sqlite3.connect('fund.db')
        c = conn.cursor()
        c.execute("SELECT id FROM funds WHERE code=?", (fund_code,))
        fund_id = c.fetchone()[0]
        conn.close()
        return fund_id

class EChartWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('ECharts 图表页面')
        self.setGeometry(200, 200, 1000, 600)
        
        # 创建布局
        layout = QVBoxLayout()
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
        # 创建基金选择下拉框
        self.fund_combo = QComboBox()
        self.load_funds()
        layout.addWidget(self.fund_combo)
        
        # 创建图表视图
        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)
        
        # 连接信号
        self.fund_combo.currentIndexChanged.connect(self.update_chart)
        
        # 初始化图表
        self.update_chart()

    def load_funds(self):
        conn = sqlite3.connect('fund.db')
        c = conn.cursor()
        c.execute("SELECT id, name, code FROM funds")
        funds = c.fetchall()
        conn.close()
        
        for fund in funds:
            self.fund_combo.addItem(f"{fund[1]}({fund[2]})", fund[0])

    def update_chart(self):
        try:
            fund_id = self.fund_combo.currentData()
            if fund_id is None:
                return

            conn = sqlite3.connect('fund.db')
            c = conn.cursor()
            query = '''SELECT time, open, close, low, high 
                      FROM fund_transactions 
                      WHERE fund_id = ? AND is_deleted = 0
                      ORDER BY time'''
            c.execute(query, (fund_id,))
            data = c.fetchall()
            conn.close()

            if not data:
                return

            # 处理K线图数据
            times = [row[0] for row in data]
            k_data = [[row[1], row[2], row[3], row[4]] for row in data]  # [open, close, low, high]

            # 创建K线图
            from pyecharts.charts import Kline
            from pyecharts.globals import JsCode
            kline = (
                Kline()
                .add_xaxis(times)
                .add_yaxis(
                    "K线图",
                    k_data,
                    itemstyle_opts=opts.ItemStyleOpts(
                        color="#ef232a",  # 上涨颜色
                        color0="#14b143",  # 下跌颜色
                        border_color="#ef232a",  # 上涨边框颜色
                        border_color0="#14b143",  # 下跌边框颜色
                    ),
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(
                        title="基金K线图",
                        subtitle="基于开盘价/收盘价/最高价/最低价"
                    ),
                    xaxis_opts=opts.AxisOpts(
                        type_="category",
                        is_scale=True,
                        boundary_gap=True,
                        axislabel_opts=opts.LabelOpts(rotate=45)
                    ),
                    yaxis_opts=opts.AxisOpts(
                        is_scale=True,
                        splitline_opts=opts.SplitLineOpts(is_show=True)
                    ),
                    datazoom_opts=[
                        opts.DataZoomOpts(type_="inside"),
                        opts.DataZoomOpts(type_="slider")
                    ],
                    tooltip_opts=opts.TooltipOpts(
                        trigger="axis",
                        axis_pointer_type="cross",
                        formatter=JsCode("""
                            function(params) {
                                var date = params[0].name;
                                var data = params[0].data;
                                return [
                                    '时间: ' + date + '<br/>',
                                    '开盘价: ' + data[0] + '<br/>',
                                    '收盘价: ' + data[1] + '<br/>',
                                    '最低价: ' + data[2] + '<br/>',
                                    '最高价: ' + data[3] + '<br/>'
                                ].join('');
                            }
                        """)
                    ),
                    toolbox_opts=opts.ToolboxOpts(
                        is_show=True,
                        feature={
                            "saveAsImage": {},
                            "dataZoom": {},
                            "dataView": {},
                            "restore": {},
                        }
                    ),
                    visualmap_opts=opts.VisualMapOpts(
                        is_show=False,
                        dimension=2,
                        series_index=0,
                        is_piecewise=True,
                    ),
                )
            )

            # 生成HTML内容
            current_dir = os.path.dirname(os.path.abspath(__file__))
            echarts_path = os.path.join(current_dir, 'static', 'echarts.min.js')
            echarts_url = QtCore.QUrl.fromLocalFile(echarts_path).toString()

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <script src="{echarts_url}"></script>
                <style>
                    #main {{
                        width: 100%;
                        height: 100vh;
                        margin: 0;
                        padding: 0;
                    }}
                </style>
            </head>
            <body>
                <div id="main"></div>
                <script>
                    var chart = echarts.init(document.getElementById('main'));
                    var option = {kline.dump_options()};
                    chart.setOption(option);
                    
                    // 添加鼠标事件监听
                    chart.on('mouseover', function(params) {{
                        console.log('mouseover:', params);
                    }});
                    
                    window.addEventListener('resize', function() {{
                        chart.resize();
                    }});
                </script>
            </body>
            </html>
            """

            # 启用本地文件访问
            self.web_view.page().settings().setAttribute(
                QtWebEngineWidgets.QWebEngineSettings.LocalContentCanAccessFileUrls,
                True
            )

            # 设置HTML内容
            base_url = QtCore.QUrl.fromLocalFile(os.path.join(current_dir, 'static/'))
            self.web_view.setHtml(html_content, base_url)

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                '错误',
                f'更新图表时发生错误：{str(e)}'
            )

if __name__ == '__main__':
    app = QApplication(sys.argv)
    visualizer = FundVisualizer()
    visualizer.show()
    sys.exit(app.exec_())