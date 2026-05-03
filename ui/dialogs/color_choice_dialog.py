#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
颜色选择对话框
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QPushButton
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class ColorChoiceDialog(QDialog):
    """颜色选择对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_color = None
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("选择执子颜色")
        self.setMinimumSize(350, 280)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #4caf50;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                padding: 10px 25px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #388e3c;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        title_label = QLabel("🎉 恭喜！您猜对了！")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #4caf50;")
        layout.addWidget(title_label)
        
        desc_label = QLabel("请选择您想要执的棋子颜色")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        color_group = QGroupBox("选择颜色")
        color_layout = QHBoxLayout(color_group)
        
        self.black_btn = QPushButton("⚫ 执黑棋 (先手)")
        self.black_btn.setMinimumSize(120, 80)
        self.black_btn.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: white;
                border: 3px solid #111111;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #555555;
                border-color: #333333;
            }
        """)
        self.black_btn.clicked.connect(lambda: self.select_color(1))
        
        self.white_btn = QPushButton("⚪ 执白棋 (后手)")
        self.white_btn.setMinimumSize(120, 80)
        self.white_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #333333;
                border: 3px solid #cccccc;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                border-color: #999999;
            }
        """)
        self.white_btn.clicked.connect(lambda: self.select_color(2))
        
        color_layout.addWidget(self.black_btn)
        color_layout.addWidget(self.white_btn)
        
        layout.addWidget(color_group)
        
    def select_color(self, color):
        """选择颜色"""
        self.selected_color = color
        self.accept()
        
    def get_color(self):
        """获取选择的颜色"""
        return self.selected_color
