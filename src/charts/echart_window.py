import os,sqlite3
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QComboBox
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5 import QtCore, QtWidgets, QtWebEngineWidgets
from pyecharts.charts import Kline
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode
from src.utils.constants import STATIC_PATH, CHART_COLORS
from src.database.db_operations import DBOperations

class EChartWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('K线图')
        self.init_ui()

    def init_ui(self):
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
        fund_id = self.fund_combo.currentData()
        if fund_id is None:
            return
            
        try:
            rows = DBOperations.get_fund_transactions(fund_id)
            if not rows:
                return

            # 处理数据
            times = [row[0] for row in rows]
            k_data = [[row[9], row[10], row[8], row[7]] for row in rows]  # [open, close, low, high]

            # 创建K线图
            kline = (
                Kline()
                .add_xaxis(times)
                .add_yaxis(
                    "K线图",
                    k_data,
                    itemstyle_opts=opts.ItemStyleOpts(
                        color=CHART_COLORS['up'],
                        color0=CHART_COLORS['down'],
                        border_color=CHART_COLORS['up_border'],
                        border_color0=CHART_COLORS['down_border'],
                    ),
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(title="基金K线图"),
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
                )
            )

            # 生成HTML内容
            echarts_path = os.path.join(STATIC_PATH, 'echarts.min.js')
            echarts_url = QtCore.QUrl.fromLocalFile(echarts_path).toString()

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <script src="{echarts_url}"></script>
                <style>
                    #main {{ width: 100%; height: 100vh; margin: 0; padding: 0; }}
                </style>
            </head>
            <body>
                <div id="main"></div>
                <script>
                    var chart = echarts.init(document.getElementById('main'));
                    var option = {kline.dump_options()};
                    chart.setOption(option);
                    window.addEventListener('resize', function() {{
                        chart.resize();
                    }});
                </script>
            </body>
            </html>
            """

            self.web_view.setHtml(html_content)

        except Exception as e:
            print(f"Chart update error: {str(e)}")