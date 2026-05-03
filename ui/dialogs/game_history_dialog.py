#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
历史对局记录列表对话框
"""

from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor


class GameHistoryDialog(QDialog):
    """历史对局记录列表对话框"""
    
    def __init__(self, records, parent=None):
        super().__init__(parent)
        self.records = records or []
        self.selected_record = None
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("历史对局记录")
        self.setMinimumSize(700, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QListWidget {
                border: 2px solid #cccccc;
                border-radius: 5px;
                background-color: white;
            }
            QListWidget::item {
                padding: 15px;
                border-bottom: 1px solid #eeeeee;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
            }
            QPushButton {
                background-color: #4a90d9;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        title_label = QLabel(f"历史对局记录 (共 {len(self.records)} 条)")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title_label)
        
        if not self.records:
            empty_label = QLabel("暂无历史对局记录")
            empty_label.setFont(QFont("Arial", 12))
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #999999; padding: 50px;")
            layout.addWidget(empty_label)
            
            close_btn = QPushButton("关闭")
            close_btn.clicked.connect(self.reject)
            
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            btn_layout.addWidget(close_btn)
            layout.addLayout(btn_layout)
            return
        
        self.record_list = QListWidget()
        self.record_list.itemClicked.connect(self.on_record_selected)
        self.record_list.itemDoubleClicked.connect(self.on_record_double_clicked)
        
        for record in self.records:
            self._add_record_item(record)
        
        layout.addWidget(self.record_list, 1)
        
        btn_layout = QHBoxLayout()
        
        self.replay_btn = QPushButton("复盘对局")
        self.replay_btn.clicked.connect(self.replay_record)
        self.replay_btn.setEnabled(False)
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.replay_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)
    
    def _add_record_item(self, record):
        """添加记录项到列表"""
        opponent_name = record.get('opponent_name', '未知对手')
        my_color = record.get('my_color', 1)
        is_winner = record.get('is_winner', False)
        total_moves = record.get('total_moves', 0)
        resign_reason = record.get('resign_reason')
        finished_at = record.get('finished_at')
        
        color_name = "黑棋" if my_color == 1 else "白棋"
        result_text = "胜利" if is_winner else "失败"
        result_color = QColor('#4caf50') if is_winner else QColor('#f44336')
        
        time_text = ""
        if finished_at:
            try:
                dt = datetime.fromtimestamp(finished_at)
                time_text = dt.strftime('%m-%d %H:%M')
            except:
                pass
        
        end_reason = ""
        if resign_reason:
            reason_names = {
                'user': '认输',
                'timeout': '超时',
                'offline': '离线'
            }
            end_reason = f"({reason_names.get(resign_reason, resign_reason)})"
        
        item_text = (
            f"对手: {opponent_name} | "
            f"执子: {color_name} | "
            f"结果: {result_text} {end_reason}| "
            f"步数: {total_moves}"
        )
        if time_text:
            item_text += f" | 时间: {time_text}"
        
        item = QListWidgetItem(item_text)
        item.setData(Qt.UserRole, record)
        item.setForeground(result_color)
        
        self.record_list.addItem(item)
    
    def on_record_selected(self, item):
        """记录被选中"""
        self.replay_btn.setEnabled(True)
    
    def on_record_double_clicked(self, item):
        """记录被双击"""
        self.selected_record = item.data(Qt.UserRole)
        self.accept()
    
    def replay_record(self):
        """复盘对局"""
        current_item = self.record_list.currentItem()
        if current_item:
            self.selected_record = current_item.data(Qt.UserRole)
            self.accept()
    
    def get_selected_record(self):
        """获取选中的记录"""
        return self.selected_record
