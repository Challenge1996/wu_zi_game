#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
悔棋请求对话框
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class UndoRequestDialog(QDialog):
    """悔棋请求对话框 - 显示对手的悔棋请求，让用户选择同意或拒绝"""
    
    def __init__(self, undo_request, parent=None):
        super().__init__(parent)
        self.undo_request = undo_request
        self.result_accept = None
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("悔棋请求")
        self.setMinimumSize(400, 250)
        self.setModal(True)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QPushButton {
                border: none;
                padding: 10px 25px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
                min-width: 100px;
            }
            QPushButton:hover {
                opacity: 0.8;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        title_label = QLabel("🤔 悔棋请求")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        requester_name = self.undo_request.get('requester_name', '对手')
        desc_label = QLabel(f"<b>{requester_name}</b> 向您请求悔棋")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        hint_label = QLabel("请选择是否同意悔棋：")
        hint_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint_label)
        
        btn_layout = QHBoxLayout()
        
        self.accept_btn = QPushButton("✓ 同意悔棋")
        self.accept_btn.setMinimumSize(120, 50)
        self.accept_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
            }
            QPushButton:hover {
                background-color: #388e3c;
            }
        """)
        self.accept_btn.clicked.connect(self.on_accept)
        
        self.decline_btn = QPushButton("✗ 拒绝悔棋")
        self.decline_btn.setMinimumSize(120, 50)
        self.decline_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        self.decline_btn.clicked.connect(self.on_decline)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.accept_btn)
        btn_layout.addSpacing(20)
        btn_layout.addWidget(self.decline_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
    def on_accept(self):
        """同意悔棋"""
        self.result_accept = True
        self.accept()
        
    def on_decline(self):
        """拒绝悔棋"""
        self.result_accept = False
        self.accept()
        
    def get_result(self):
        """获取结果"""
        return self.result_accept
