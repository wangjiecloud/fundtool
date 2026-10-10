from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox
)
from src.utils.constants import TABLE_HEADERS, STYLES, SAMPLE_FUND
from src.database.db_operations import add_fund, add_transaction

class AddFundDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('新增基金')
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 基金名称输入
        self.name_edit = QLineEdit()
        layout.addWidget(QLabel('基金名称:'))
        layout.addWidget(self.name_edit)
        
        # 基金代码输入
        self.code_edit = QLineEdit()
        layout.addWidget(QLabel('基金代码:'))
        layout.addWidget(self.code_edit)
        
        # 按钮
        btn_layout = QHBoxLayout()
        save_btn = QPushButton('保存')
        save_btn.setStyleSheet(STYLES['success_button'])
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton('取消')
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def save(self):
        try:
            name = self.name_edit.text().strip()
            code = self.code_edit.text().strip()
            
            if not name or not code:
                raise ValueError("基金名称和代码不能为空")
                
            if name == SAMPLE_FUND['name'] or code == SAMPLE_FUND['code']:
                raise ValueError("不能使用示例基金的名称或代码")
            
            self.fund_id = add_fund(name, code)
            self.fund_name = name
            self.fund_code = code
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, '错误', str(e))

class AddRecordDialog(QDialog):
    def __init__(self, fund_id, parent=None):
        super().__init__(parent)
        self.fund_id = fund_id
        self.setWindowTitle('新增交易记录')
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 创建输入字段
        self.fields = []
        for header in TABLE_HEADERS:
            label = QLabel(header)
            edit = QLineEdit()
            if header == '时间':
                edit.setPlaceholderText('格式: YYYY-MM-DD')
            layout.addWidget(label)
            layout.addWidget(edit)
            self.fields.append(edit)
        
        # 按钮
        btn_layout = QHBoxLayout()
        save_btn = QPushButton('保存')
        save_btn.setStyleSheet(STYLES['success_button'])
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton('取消')
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def save(self):
        try:
            values = [field.text() for field in self.fields]
            
            # 验证时间格式
            if not values[0]:
                raise ValueError("时间不能为空")
            
            # 转换数值
            for i in range(1, len(values)):
                if values[i]:
                    try:
                        values[i] = float(values[i])
                    except ValueError:
                        raise ValueError(f"{TABLE_HEADERS[i]}必须是数字")
            
            add_transaction(self.fund_id, values)
            
            # 更新父窗口的表格
            if hasattr(self.parent().parent(), 'update_table'):
                self.parent().parent().update_table()
                
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, '错误', str(e))