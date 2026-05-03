#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
玩家列表对话框
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor


class PlayerListDialog(QDialog):
    """玩家列表对话框"""
    
    def __init__(self, players, my_player_id, parent=None):
        super().__init__(parent)
        self.players = players
        self.my_player_id = my_player_id
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("在线玩家列表")
        self.setMinimumSize(500, 400)
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
                padding: 10px;
                border-bottom: 1px solid #eeeeee;
            }
            QPushButton {
                background-color: #607d8b;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #455a64;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        title_label = QLabel(f"在线玩家 (共 {len(self.players)} 人)")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title_label)
        
        self.player_list = QListWidget()
        
        status_colors = {
            'idle': '#4caf50',
            'waiting': '#ff9800',
            'challenging': '#9c27b0',
            'in_game': '#f44336'
        }
        
        status_names = {
            'idle': '空闲',
            'waiting': '等待中',
            'challenging': '挑战中',
            'in_game': '游戏中'
        }
        
        for player in self.players:
            is_self = player.get('id') == self.my_player_id
            name = player.get('name', '未知') + (' (我)' if is_self else '')
            status = player.get('status', 'unknown')
            status_name = status_names.get(status, status)
            status_color = status_colors.get(status, '#999999')
            
            item_text = f"{name} - [{status_name}]"
            item = QListWidgetItem(item_text)
            item.setForeground(QColor(status_color))
            self.player_list.addItem(item)
        
        layout.addWidget(self.player_list)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #607d8b;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #455a64;
            }
        """)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
