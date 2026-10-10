import os

# Project paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(ROOT_DIR, 'fund.db')
STATIC_PATH = os.path.join(ROOT_DIR, 'static')

# Table headers
TABLE_HEADERS = [
    '时间', '买入价', '买入数量', '总买入价', 
    '卖出价', '卖出数量', '总卖出价', 
    '最高价', '最低价', '开盘价', '收盘价', '涨跌情况'
]

# Database fields
DB_FIELDS = [
    'time', 'buy_price', 'buy_quantity', 'total_buy',
    'sell_price', 'sell_quantity', 'total_sell',
    'high', 'low', 'open', 'close', 'change_percent'
]

# Sample fund constants
SAMPLE_FUND = {
    'name': '示例基金',
    'code': '000001',
    'sample_data': (
        '2025-04-07', 1.307, 2000, 9159, 0, 0, 0, 
        1.35, 1.27, 1.35, 1.3053, '-4.62%', 0
    )
}

# Styles
STYLES = {
    'table': '''
        QTableWidget { border: 1px solid #ccc; font-size: 12px; }
        QTableWidget::header { background: #f0f0f0; }
        QTableWidget::item { padding: 8px; border-bottom: 1px solid #eee; }
    ''',
    'primary_button': 'background-color: #1976D2; color: white;',
    'success_button': 'background-color: #4CAF50; color: white;'
}

# Chart colors
CHART_COLORS = {
    'up': "#ef232a",
    'down': "#14b143",
    'up_border': "#ef232a",
    'down_border': "#14b143"
}