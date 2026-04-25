#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
挑战列表对话框
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor


class ChallengeListDialog(QDialog):
    """挑战列表对话框"""
    
    def __init__(self, challenges, parent=None):
        super().__init__(parent)
        self.challenges = challenges
        self.result_action = None
        self.result_challenge_id = None
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("我的挑战列表")
        self.setMinimumSize(600, 400)
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
                padding: 12px;
                border-bottom: 1px solid #eeeeee;
            }
            QPushButton {
                background-color: #4a90d9;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        title_label = QLabel(f"挑战列表 (共 {len(self.challenges)} 条)")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title_label)
        
        self.challenge_list = QListWidget()
        self.challenge_list.itemClicked.connect(self.on_challenge_selected)
        
        status_names = {
            'pending': '待处理',
            'accepted': '已接受',
            'declined': '已拒绝',
            'expired': '已过期'
        }
        
        for challenge in self.challenges:
            is_my = challenge.get('is_my_challenge', False)
            challenge_type = "我发起的" if is_my else "收到的"
            opponent = challenge.get('challenged_name') if is_my else challenge.get('challenger_name')
            status = challenge.get('status', 'unknown')
            status_name = status_names.get(status, status)
            
            can_accept = status == 'pending' and not is_my
            
            item_text = f"[{challenge_type}] 对方: {opponent} - 状态: {status_name}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, challenge)
            
            if can_accept:
                item.setForeground(QColor('#4caf50'))
            
            self.challenge_list.addItem(item)
        
        layout.addWidget(self.challenge_list)
        
        btn_layout = QHBoxLayout()
        
        self.accept_btn = QPushButton("接受挑战")
        self.accept_btn.clicked.connect(self.accept_challenge)
        self.accept_btn.setEnabled(False)
        
        self.decline_btn = QPushButton("拒绝挑战")
        self.decline_btn.clicked.connect(self.decline_challenge)
        self.decline_btn.setEnabled(False)
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.accept_btn)
        btn_layout.addWidget(self.decline_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)
        
    def on_challenge_selected(self, item):
        """挑战被选中"""
        challenge = item.data(Qt.UserRole)
        status = challenge.get('status')
        is_my = challenge.get('is_my_challenge')
        
        can_operate = status == 'pending' and not is_my
        self.accept_btn.setEnabled(can_operate)
        self.decline_btn.setEnabled(can_operate)
        
    def accept_challenge(self):
        """接受挑战"""
        current_item = self.challenge_list.currentItem()
        if current_item:
            challenge = current_item.data(Qt.UserRole)
            self.result_action = 'accept'
            self.result_challenge_id = challenge.get('id')
            self.accept()
            
    def decline_challenge(self):
        """拒绝挑战"""
        current_item = self.challenge_list.currentItem()
        if current_item:
            challenge = current_item.data(Qt.UserRole)
            self.result_action = 'decline'
            self.result_challenge_id = challenge.get('id')
            self.accept()
            
    def get_result(self):
        """获取结果"""
        return self.result_action, self.result_challenge_id
