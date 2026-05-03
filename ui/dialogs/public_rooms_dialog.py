#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公开对局列表对话框 - 用于显示和选择公开房间进行观战
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor


class PublicRoomsDialog(QDialog):
    """公开对局列表对话框"""
    
    def __init__(self, rooms, parent=None):
        super().__init__(parent)
        self.rooms = rooms
        self.selected_room = None
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("观战大厅 - 公开对局列表")
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
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QLabel {
                font-size: 13px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #e8f4fc;
                border: 2px solid #4a90d9;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        
        title_label = QLabel("🎮 观战大厅")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setStyleSheet("color: #4a90d9;")
        header_layout.addWidget(title_label)
        
        info_label = QLabel(f"当前共有 {len(self.rooms)} 个公开对局。选择一个对局后点击\"进入观战\"按钮。")
        info_label.setStyleSheet("color: #666666;")
        header_layout.addWidget(info_label)
        
        layout.addWidget(header_frame)
        
        self.room_list = QListWidget()
        self.room_list.itemClicked.connect(self.on_room_selected)
        self.room_list.itemDoubleClicked.connect(self.on_room_double_clicked)
        
        status_names = {
            'waiting': '等待中',
            'coin_toss': '猜先中',
            'playing': '游戏中',
            'finished': '已结束'
        }
        
        for room in self.rooms:
            room_id = room.get('id', '')
            name = room.get('name', '未知对局')
            player1_name = room.get('player1_name', '玩家1')
            player2_name = room.get('player2_name', '玩家2')
            status = room.get('status', 'unknown')
            status_name = status_names.get(status, status)
            spectator_count = room.get('spectator_count', 0)
            is_hot_game = room.get('is_hot_game', False)
            
            hot_icon = "🔥 " if is_hot_game else ""
            spectator_text = f"👥 {spectator_count}人观战"
            
            if is_hot_game:
                spectator_text += " (热门)"
            
            item_text = f"{hot_icon}{name}\n"
            item_text += f"   状态: {status_name} | {spectator_text}\n"
            item_text += f"   对阵: {player1_name} vs {player2_name}"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, room)
            
            if is_hot_game:
                item.setForeground(QColor('#ff6b35'))
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            
            if status == 'playing':
                item.setBackground(QColor('#f0fff0'))
            elif status == 'finished':
                item.setForeground(QColor('#999999'))
            
            self.room_list.addItem(item)
        
        layout.addWidget(self.room_list, 1)
        
        btn_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 刷新列表")
        self.refresh_btn.clicked.connect(self.refresh_rooms)
        
        self.watch_btn = QPushButton("👁️ 进入观战")
        self.watch_btn.clicked.connect(self.join_spectate)
        self.watch_btn.setEnabled(False)
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.watch_btn)
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)
        
    def on_room_selected(self, item):
        """房间被选中"""
        room = item.data(Qt.UserRole)
        status = room.get('status')
        
        can_watch = status == 'playing'
        self.watch_btn.setEnabled(can_watch)
        
        if not can_watch and status != 'playing':
            self.watch_btn.setToolTip("只能观战正在进行中的对局")
        else:
            self.watch_btn.setToolTip("")
            
    def on_room_double_clicked(self, item):
        """房间被双击"""
        room = item.data(Qt.UserRole)
        status = room.get('status')
        
        if status == 'playing':
            self.selected_room = room
            self.accept()
            
    def refresh_rooms(self):
        """刷新房间列表"""
        self.selected_room = None
        self.reject()
        
    def join_spectate(self):
        """进入观战"""
        current_item = self.room_list.currentItem()
        if current_item:
            room = current_item.data(Qt.UserRole)
            self.selected_room = room
            self.accept()
            
    def get_selected_room(self):
        """获取选中的房间"""
        return self.selected_room
