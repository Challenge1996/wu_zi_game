#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
挑战对话框
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QListWidget, QListWidgetItem, QDialogButtonBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class ChallengeDialog(QDialog):
    """挑战对话框"""
    
    def __init__(self, players, parent=None):
        super().__init__(parent)
        self.players = players
        self.selected_player = None
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("发起挑战")
        self.setMinimumSize(400, 300)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #4a90d9;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QPushButton {
                background-color: #4a90d9;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:pressed {
                background-color: #2d6899;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QListWidget {
                border: 2px solid #cccccc;
                border-radius: 5px;
                background-color: white;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eeeeee;
            }
            QListWidget::item:selected {
                background-color: #4a90d9;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e8f4fc;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        title_label = QLabel("选择要挑战的玩家")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        player_group = QGroupBox("在线玩家")
        player_layout = QVBoxLayout(player_group)
        
        self.player_list = QListWidget()
        self.player_list.itemClicked.connect(self.on_player_selected)
        
        for player in self.players:
            status_text = {
                'idle': '空闲',
                'waiting': '等待中',
                'challenging': '挑战中',
                'in_game': '游戏中'
            }.get(player.get('status'), player.get('status'))
            
            can_challenge = player.get('status') == 'idle'
            item_text = f"{player.get('name', '未知')} - {status_text}"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, player)
            
            if not can_challenge:
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            
            self.player_list.addItem(item)
        
        player_layout.addWidget(self.player_list)
        layout.addWidget(player_group)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        self.ok_button = button_box.button(QDialogButtonBox.Ok)
        self.ok_button.setText("发起挑战")
        self.ok_button.setEnabled(False)
        
        layout.addWidget(button_box)
        
    def on_player_selected(self, item):
        """玩家被选中"""
        self.selected_player = item.data(Qt.UserRole)
        self.ok_button.setEnabled(True)
        
    def get_selected_player(self):
        """获取选中的玩家"""
        return self.selected_player
