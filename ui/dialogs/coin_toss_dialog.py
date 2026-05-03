#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抛硬币对话框
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QPushButton, QRadioButton, QButtonGroup, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class CoinTossDialog(QDialog):
    """抛硬币对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_choice = None
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("抛硬币猜先")
        self.setMinimumSize(350, 250)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ff9800;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                padding: 10px 25px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
            QRadioButton {
                font-size: 14px;
                padding: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        title_label = QLabel("🪙 猜硬币决定先手")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        desc_label = QLabel("请选择硬币的一面，猜对者可选择执子颜色")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        choice_group = QGroupBox("选择硬币")
        choice_layout = QVBoxLayout(choice_group)
        
        self.button_group = QButtonGroup(self)
        
        self.head_radio = QRadioButton("正面 (☀️)")
        self.head_radio.setFont(QFont("Arial", 14))
        
        self.tail_radio = QRadioButton("反面 (🌙)")
        self.tail_radio.setFont(QFont("Arial", 14))
        
        self.button_group.addButton(self.head_radio, 0)
        self.button_group.addButton(self.tail_radio, 1)
        
        choice_layout.addWidget(self.head_radio)
        choice_layout.addWidget(self.tail_radio)
        
        layout.addWidget(choice_group)
        
        confirm_btn = QPushButton("确认选择")
        confirm_btn.clicked.connect(self.on_confirm)
        layout.addWidget(confirm_btn, alignment=Qt.AlignCenter)
        
    def on_confirm(self):
        """确认选择"""
        checked_id = self.button_group.checkedId()
        if checked_id == -1:
            QMessageBox.warning(self, "提示", "请先选择硬币的一面！")
            return
        
        self.selected_choice = checked_id
        self.accept()
        
    def get_choice(self):
        """获取选择结果"""
        return self.selected_choice
