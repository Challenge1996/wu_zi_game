#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
五子棋游戏GUI客户端 - 桌面端界面
基于PyQt5实现，包含完整的游戏UI界面
"""

import sys
import requests
import json
import time
import threading
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QLabel, QFrame, QGroupBox, QDialog,
    QListWidget, QListWidgetItem, QMessageBox, QInputDialog, QLineEdit,
    QSpinBox, QFormLayout, QStatusBar, QScrollArea, QSplitter,
    QDialogButtonBox, QRadioButton, QButtonGroup, QProgressBar,
    QLCDNumber, QTabWidget, QTextEdit
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QSize
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QPalette,
    QPixmap, QIcon, QPainterPath, QLinearGradient
)

SERVER_URL = "http://localhost:5001"

# ==================== 信号类 ====================

class GameSignals(QObject):
    """游戏信号类，用于线程间通信"""
    room_updated = pyqtSignal(dict)
    player_list_updated = pyqtSignal(list)
    challenge_list_updated = pyqtSignal(list)
    message_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    game_started = pyqtSignal()
    game_over = pyqtSignal(int)  # winner: 1=黑棋, 2=白棋
    coin_toss_phase = pyqtSignal()
    coin_result = pyqtSignal(str, bool)  # result, is_my_win
    turn_changed = pyqtSignal(int)  # current player color
    show_color_choice = pyqtSignal()  # 显示颜色选择对话框
    
    # 计时器相关信号
    start_waiting_timer = pyqtSignal()
    stop_waiting_timer = pyqtSignal()
    start_game_timer = pyqtSignal(int)  # current_player
    stop_game_timer = pyqtSignal()
    reset_timer = pyqtSignal()
    switch_timer_player = pyqtSignal()
    
    # 按钮状态信号
    disable_coin_button = pyqtSignal()
    enable_coin_button = pyqtSignal()
    disable_undo_button = pyqtSignal()
    enable_undo_button = pyqtSignal()
    disable_reset_button = pyqtSignal()
    enable_reset_button = pyqtSignal()
    
    # 棋盘状态信号
    enable_board_click = pyqtSignal()
    disable_board_click = pyqtSignal()
    
    # 游戏状态信号
    update_game_phase = pyqtSignal(str)  # phase
    update_status_label = pyqtSignal(str)  # text
    
    # 硬币结果详细信号
    coin_toss_completed = pyqtSignal(dict)  # {'winner_id': str, 'coin_result': str, 'is_my_win': bool}
    
    # 颜色选择后信号
    color_chosen = pyqtSignal(int)  # color (1=黑, 2=白)
    
    # 挑战相关信号
    show_challenge_received = pyqtSignal(dict)  # 收到挑战
    show_players_for_challenge = pyqtSignal(list)  # 显示可挑战的玩家
    
    # 对话框显示信号
    show_player_list_dialog = pyqtSignal(list)  # 显示玩家列表对话框
    show_challenge_list_dialog = pyqtSignal(list)  # 显示挑战列表对话框
    
    # 游戏状态更新信号（用于reset等操作）
    game_reset = pyqtSignal()  # 游戏重置
    update_my_color = pyqtSignal(int)  # 更新我的颜色显示 (1=黑, 2=白)
    enable_game_controls = pyqtSignal()  # 启用游戏控件
    disable_game_controls = pyqtSignal()  # 禁用游戏控件

# ==================== 棋盘控件 ====================

class BoardWidget(QWidget):
    """15x15棋盘控件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.board_size = 15
        self.cell_size = 35  # 每个格子大小
        self.margin = 20      # 边距
        self.board = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.current_player = 1
        self.last_move = None  # 最后落子位置 (row, col)
        self.hover_pos = None  # 鼠标悬停位置
        self.click_enabled = True
        
        # 设置最小尺寸
        min_size = self.margin * 2 + self.cell_size * (self.board_size - 1) + 20
        self.setMinimumSize(min_size, min_size)
        self.setMouseTracking(True)
        
    def update_board(self, board_data, current_player=None, last_move=None):
        """更新棋盘数据"""
        self.board = [row[:] for row in board_data]
        if current_player is not None:
            self.current_player = current_player
        self.last_move = last_move
        self.update()
        
    def clear_board(self):
        """清空棋盘"""
        self.board = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.last_move = None
        self.update()
        
    def set_click_enabled(self, enabled):
        """设置是否允许点击落子"""
        self.click_enabled = enabled
        
    def paintEvent(self, event):
        """绘制棋盘和棋子"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 计算棋盘的实际绘制区域（居中）
        total_size = self.cell_size * (self.board_size - 1)
        x_offset = (self.width() - total_size) // 2
        y_offset = (self.height() - total_size) // 2
        
        # 绘制棋盘背景
        board_rect = self.rect()
        board_gradient = QLinearGradient(board_rect.topLeft(), board_rect.bottomRight())
        board_gradient.setColorAt(0, QColor(245, 222, 179))  # 浅棕色
        board_gradient.setColorAt(1, QColor(222, 184, 135))  # 深棕色
        painter.fillRect(board_rect, board_gradient)
        
        # 绘制网格线
        pen = QPen(QColor(80, 50, 20), 1)
        painter.setPen(pen)
        
        for i in range(self.board_size):
            # 水平线
            start_x = x_offset
            start_y = y_offset + i * self.cell_size
            end_x = x_offset + (self.board_size - 1) * self.cell_size
            end_y = start_y
            painter.drawLine(start_x, start_y, end_x, end_y)
            
            # 垂直线
            start_x = x_offset + i * self.cell_size
            start_y = y_offset
            end_x = start_x
            end_y = y_offset + (self.board_size - 1) * self.cell_size
            painter.drawLine(start_x, start_y, end_x, end_y)
        
        # 绘制天元和星位
        star_positions = [
            (3, 3), (3, 7), (3, 11),
            (7, 3), (7, 7), (7, 11),
            (11, 3), (11, 7), (11, 11)
        ]
        
        star_radius = 3
        painter.setBrush(QBrush(QColor(80, 50, 20)))
        painter.setPen(Qt.NoPen)
        
        for row, col in star_positions:
            x = x_offset + col * self.cell_size
            y = y_offset + row * self.cell_size
            painter.drawEllipse(x - star_radius, y - star_radius, 
                                star_radius * 2, star_radius * 2)
        
        # 绘制棋子
        piece_radius = self.cell_size // 2 - 2
        
        for row in range(self.board_size):
            for col in range(self.board_size):
                if self.board[row][col] != 0:
                    x = x_offset + col * self.cell_size
                    y = y_offset + row * self.cell_size
                    
                    # 绘制棋子阴影
                    shadow_offset = 2
                    if self.board[row][col] == 1:  # 黑棋
                        shadow_color = QColor(0, 0, 0, 80)
                    else:  # 白棋
                        shadow_color = QColor(100, 100, 100, 60)
                    painter.setBrush(QBrush(shadow_color))
                    painter.drawEllipse(x - piece_radius + shadow_offset, 
                                        y - piece_radius + shadow_offset,
                                        piece_radius * 2, piece_radius * 2)
                    
                    # 绘制棋子主体
                    if self.board[row][col] == 1:  # 黑棋
                        gradient = QLinearGradient(
                            x - piece_radius, y - piece_radius,
                            x + piece_radius, y + piece_radius
                        )
                        gradient.setColorAt(0, QColor(80, 80, 80))
                        gradient.setColorAt(0.5, QColor(20, 20, 20))
                        gradient.setColorAt(1, QColor(0, 0, 0))
                        painter.setBrush(QBrush(gradient))
                    else:  # 白棋
                        gradient = QLinearGradient(
                            x - piece_radius, y - piece_radius,
                            x + piece_radius, y + piece_radius
                        )
                        gradient.setColorAt(0, QColor(255, 255, 255))
                        gradient.setColorAt(0.5, QColor(240, 240, 240))
                        gradient.setColorAt(1, QColor(200, 200, 200))
                        painter.setBrush(QBrush(gradient))
                    
                    painter.setPen(Qt.NoPen)
                    painter.drawEllipse(x - piece_radius, y - piece_radius,
                                        piece_radius * 2, piece_radius * 2)
                    
                    # 绘制棋子高光
                    highlight_radius = piece_radius // 3
                    highlight_offset = piece_radius // 4
                    if self.board[row][col] == 1:  # 黑棋高光
                        highlight_color = QColor(100, 100, 100, 120)
                    else:  # 白棋高光
                        highlight_color = QColor(255, 255, 255, 180)
                    painter.setBrush(QBrush(highlight_color))
                    painter.drawEllipse(
                        x - piece_radius + highlight_offset,
                        y - piece_radius + highlight_offset,
                        highlight_radius * 2, highlight_radius * 2
                    )
                    
                    # 标记最后落子位置
                    if self.last_move == (row, col):
                        marker_radius = 4
                        painter.setPen(QPen(QColor(255, 0, 0), 2))
                        painter.setBrush(Qt.NoBrush)
                        painter.drawEllipse(x - marker_radius, y - marker_radius,
                                            marker_radius * 2, marker_radius * 2)
        
        # 绘制悬停提示
        if self.hover_pos and self.click_enabled:
            row, col = self.hover_pos
            if 0 <= row < self.board_size and 0 <= col < self.board_size:
                if self.board[row][col] == 0:
                    x = x_offset + col * self.cell_size
                    y = y_offset + row * self.cell_size
                    
                    # 绘制半透明提示棋子
                    if self.current_player == 1:  # 黑棋
                        hover_color = QColor(0, 0, 0, 80)
                    else:  # 白棋
                        hover_color = QColor(255, 255, 255, 120)
                    
                    painter.setBrush(QBrush(hover_color))
                    painter.setPen(Qt.NoPen)
                    painter.drawEllipse(x - piece_radius, y - piece_radius,
                                        piece_radius * 2, piece_radius * 2)
        
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if not self.click_enabled:
            return
            
        # 计算棋盘的实际绘制区域
        total_size = self.cell_size * (self.board_size - 1)
        x_offset = (self.width() - total_size) // 2
        y_offset = (self.height() - total_size) // 2
        
        # 计算鼠标对应的棋盘坐标
        x = event.pos().x() - x_offset
        y = event.pos().y() - y_offset
        
        # 四舍五入到最近的交叉点
        col = round(x / self.cell_size)
        row = round(y / self.cell_size)
        
        # 检查是否在棋盘范围内
        if 0 <= row < self.board_size and 0 <= col < self.board_size:
            # 检查是否接近交叉点（在半个格子范围内）
            if abs(x - col * self.cell_size) < self.cell_size / 2 and \
               abs(y - row * self.cell_size) < self.cell_size / 2:
                self.hover_pos = (row, col)
            else:
                self.hover_pos = None
        else:
            self.hover_pos = None
        
        self.update()
        
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if not self.click_enabled or not self.hover_pos:
            return
            
        if event.button() == Qt.LeftButton:
            row, col = self.hover_pos
            if self.board[row][col] == 0:
                # 发出落子信号（通过父窗口处理）
                parent = self.parent()
                while parent:
                    if hasattr(parent, 'on_board_clicked'):
                        parent.on_board_clicked(row, col)
                        break
                    parent = parent.parent()

# ==================== 计时器控件 ====================

class TimerWidget(QWidget):
    """计时器控件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.player1_time = 0  # 黑棋时间（秒）
        self.player2_time = 0  # 白棋时间（秒）
        self.current_player = 1
        self.is_running = False
        self.wait_time = 0  # 等待时间
        
        self.init_ui()
        self.setup_timer()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 玩家时间显示
        time_group = QGroupBox("游戏计时")
        time_layout = QVBoxLayout(time_group)
        
        # 黑棋时间
        black_frame = QFrame()
        black_frame.setFrameStyle(QFrame.StyledPanel)
        black_layout = QHBoxLayout(black_frame)
        
        black_label = QLabel("黑棋:")
        black_label.setFont(QFont("Arial", 12, QFont.Bold))
        black_label.setStyleSheet("color: white; background-color: black; padding: 5px; border-radius: 5px;")
        
        self.black_lcd = QLCDNumber(8)
        self.black_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.black_lcd.setStyleSheet("color: black; background-color: #f0f0f0;")
        self.black_lcd.display("00:00:00")
        
        black_layout.addWidget(black_label)
        black_layout.addWidget(self.black_lcd)
        
        # 白棋时间
        white_frame = QFrame()
        white_frame.setFrameStyle(QFrame.StyledPanel)
        white_layout = QHBoxLayout(white_frame)
        
        white_label = QLabel("白棋:")
        white_label.setFont(QFont("Arial", 12, QFont.Bold))
        white_label.setStyleSheet("color: black; background-color: white; padding: 5px; border-radius: 5px; border: 1px solid gray;")
        
        self.white_lcd = QLCDNumber(8)
        self.white_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.white_lcd.setStyleSheet("color: black; background-color: #f0f0f0;")
        self.white_lcd.display("00:00:00")
        
        white_layout.addWidget(white_label)
        white_layout.addWidget(self.white_lcd)
        
        # 等待时间
        wait_frame = QFrame()
        wait_frame.setFrameStyle(QFrame.StyledPanel)
        wait_layout = QHBoxLayout(wait_frame)
        
        wait_label = QLabel("等待时间:")
        wait_label.setFont(QFont("Arial", 10))
        
        self.wait_lcd = QLCDNumber(8)
        self.wait_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.wait_lcd.setStyleSheet("color: darkblue; background-color: #e0e0ff;")
        self.wait_lcd.display("00:00:00")
        
        wait_layout.addWidget(wait_label)
        wait_layout.addWidget(self.wait_lcd)
        
        time_layout.addWidget(black_frame)
        time_layout.addWidget(white_frame)
        time_layout.addWidget(wait_frame)
        
        layout.addWidget(time_group)
        
    def setup_timer(self):
        """设置计时器"""
        self.game_timer = QTimer(self)
        self.game_timer.timeout.connect(self.update_game_time)
        
        self.wait_timer = QTimer(self)
        self.wait_timer.timeout.connect(self.update_wait_time)
        
    def start_timer(self, current_player=1):
        """开始游戏计时"""
        self.current_player = current_player
        self.is_running = True
        self.game_timer.start(1000)  # 每秒更新一次
        
    def stop_timer(self):
        """停止游戏计时"""
        self.is_running = False
        self.game_timer.stop()
        
    def reset_timer(self):
        """重置计时器"""
        self.stop_timer()
        self.player1_time = 0
        self.player2_time = 0
        self.wait_time = 0
        self.update_display()
        
    def update_game_time(self):
        """更新游戏时间"""
        if self.current_player == 1:
            self.player1_time += 1
        else:
            self.player2_time += 1
        self.update_display()
        
    def switch_player(self):
        """切换当前玩家"""
        self.current_player = 2 if self.current_player == 1 else 1
        
    def start_waiting(self):
        """开始等待计时"""
        self.wait_timer.start(1000)
        
    def stop_waiting(self):
        """停止等待计时"""
        self.wait_timer.stop()
        
    def update_wait_time(self):
        """更新等待时间"""
        self.wait_time += 1
        self.update_display()
        
    def update_display(self):
        """更新显示"""
        # 格式化时间
        def format_time(seconds):
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        
        self.black_lcd.display(format_time(self.player1_time))
        self.white_lcd.display(format_time(self.player2_time))
        self.wait_lcd.display(format_time(self.wait_time))
        
        # 高亮当前玩家
        if self.current_player == 1:
            self.black_lcd.setStyleSheet("color: red; background-color: #ffe0e0;")
            self.white_lcd.setStyleSheet("color: black; background-color: #f0f0f0;")
        else:
            self.black_lcd.setStyleSheet("color: black; background-color: #f0f0f0;")
            self.white_lcd.setStyleSheet("color: red; background-color: #ffe0e0;")

# ==================== 挑战弹窗 ====================

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
        
        # 标题
        title_label = QLabel("选择要挑战的玩家")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 玩家列表
        player_group = QGroupBox("在线玩家")
        player_layout = QVBoxLayout(player_group)
        
        self.player_list = QListWidget()
        self.player_list.itemClicked.connect(self.on_player_selected)
        
        # 填充玩家列表
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
        
        # 按钮
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

# ==================== 抛硬币对话框 ====================

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
        
        # 标题
        title_label = QLabel("🪙 猜硬币决定先手")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 说明
        desc_label = QLabel("请选择硬币的一面，猜对者可选择执子颜色")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # 选项组
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
        
        # 确认按钮
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

# ==================== 颜色选择对话框 ====================

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
        
        # 标题
        title_label = QLabel("🎉 恭喜！您猜对了！")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #4caf50;")
        layout.addWidget(title_label)
        
        # 说明
        desc_label = QLabel("请选择您想要执的棋子颜色")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # 颜色选择
        color_group = QGroupBox("选择颜色")
        color_layout = QHBoxLayout(color_group)
        
        # 黑棋按钮
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
        
        # 白棋按钮
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

# ==================== 玩家列表对话框 ====================

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
        """)
        
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel(f"在线玩家 (共 {len(self.players)} 人)")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title_label)
        
        # 玩家列表
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
        
        # 关闭按钮
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

# ==================== 主窗口 ====================

class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        
        self.server_url = SERVER_URL
        self.player_id = None
        self.player_name = None
        self.current_room_id = None
        self.my_color = None  # 1: 黑棋, 2: 白棋
        self.game_phase = "waiting"
        
        # 信号对象
        self.signals = GameSignals()
        self.setup_signal_connections()
        
        # 轮询线程
        self.polling_thread = None
        self.running = False
        
        self.init_ui()
        self.setup_menu()
        self.setup_status_bar()
        
        # 设置窗口
        self.setWindowTitle("五子棋 - 网络对战")
        self.setMinimumSize(900, 700)
        self.setStyleSheet("""
            QMainWindow {
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
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 80px;
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
            QLabel {
                font-size: 13px;
            }
        """)
        
    def init_ui(self):
        """初始化UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧：棋盘区域
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 游戏信息栏
        info_bar = QFrame()
        info_bar.setFrameStyle(QFrame.StyledPanel)
        info_bar.setStyleSheet("""
            QFrame {
                background-color: #e8f4fc;
                border: 2px solid #4a90d9;
                border-radius: 8px;
            }
        """)
        info_layout = QHBoxLayout(info_bar)
        
        self.turn_label = QLabel("当前: 等待开始")
        self.turn_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.turn_label.setStyleSheet("color: #4a90d9;")
        
        self.my_color_label = QLabel("")
        self.my_color_label.setFont(QFont("Arial", 12))
        
        info_layout.addWidget(self.turn_label)
        info_layout.addStretch()
        info_layout.addWidget(self.my_color_label)
        
        left_layout.addWidget(info_bar)
        
        # 棋盘
        self.board = BoardWidget()
        self.board.set_click_enabled(False)
        left_layout.addWidget(self.board, 1)
        
        # 游戏状态
        self.status_label = QLabel("游戏状态: 未开始")
        self.status_label.setFont(QFont("Arial", 11))
        self.status_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.status_label)
        
        main_layout.addWidget(left_widget, 3)
        
        # 右侧：控制面板
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 玩家信息
        player_group = QGroupBox("玩家信息")
        player_layout = QFormLayout(player_group)
        
        self.player_name_label = QLabel("未登录")
        self.player_id_label = QLabel("-")
        self.player_status_label = QLabel("-")
        
        player_layout.addRow("玩家名称:", self.player_name_label)
        player_layout.addRow("玩家ID:", self.player_id_label)
        player_layout.addRow("状态:", self.player_status_label)
        
        # 连接和登录按钮
        login_layout = QHBoxLayout()
        self.connect_btn = QPushButton("连接服务器")
        self.connect_btn.clicked.connect(self.connect_to_server)
        
        self.login_btn = QPushButton("注册/登录")
        self.login_btn.clicked.connect(self.show_login_dialog)
        self.login_btn.setEnabled(False)
        
        login_layout.addWidget(self.connect_btn)
        login_layout.addWidget(self.login_btn)
        player_layout.addRow(login_layout)
        
        right_layout.addWidget(player_group)
        
        # 游戏控制
        game_group = QGroupBox("游戏控制")
        game_layout = QVBoxLayout(game_group)
        
        # 第一排按钮
        row1_layout = QHBoxLayout()
        self.challenge_btn = QPushButton("发起挑战")
        self.challenge_btn.clicked.connect(self.show_challenge_dialog)
        self.challenge_btn.setEnabled(False)
        
        self.players_btn = QPushButton("玩家列表")
        self.players_btn.clicked.connect(self.show_player_list)
        self.players_btn.setEnabled(False)
        
        self.challenges_btn = QPushButton("挑战列表")
        self.challenges_btn.clicked.connect(self.show_my_challenges)
        self.challenges_btn.setEnabled(False)
        
        row1_layout.addWidget(self.challenge_btn)
        row1_layout.addWidget(self.players_btn)
        row1_layout.addWidget(self.challenges_btn)
        
        # 第二排按钮
        row2_layout = QHBoxLayout()
        self.undo_btn = QPushButton("悔棋")
        self.undo_btn.clicked.connect(self.request_undo)
        self.undo_btn.setEnabled(False)
        
        self.reset_btn = QPushButton("重置")
        self.reset_btn.clicked.connect(self.request_reset)
        self.reset_btn.setEnabled(False)
        
        self.coin_btn = QPushButton("猜硬币")
        self.coin_btn.clicked.connect(self.show_coin_dialog)
        self.coin_btn.setEnabled(False)
        
        row2_layout.addWidget(self.undo_btn)
        row2_layout.addWidget(self.reset_btn)
        row2_layout.addWidget(self.coin_btn)
        
        game_layout.addLayout(row1_layout)
        game_layout.addLayout(row2_layout)
        
        right_layout.addWidget(game_group)
        
        # 计时器
        self.timer_widget = TimerWidget()
        right_layout.addWidget(self.timer_widget)
        
        # 消息日志
        log_group = QGroupBox("消息日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 2px solid #cccccc;
                border-radius: 5px;
                font-family: Consolas, Monaco, monospace;
                font-size: 11px;
            }
        """)
        
        log_layout.addWidget(self.log_text)
        right_layout.addWidget(log_group)
        
        main_layout.addWidget(right_widget, 1)
        
    def setup_menu(self):
        """设置菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        connect_action = file_menu.addAction("连接服务器")
        connect_action.triggered.connect(self.connect_to_server)
        
        login_action = file_menu.addAction("注册/登录")
        login_action.triggered.connect(self.show_login_dialog)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("退出")
        exit_action.triggered.connect(self.close)
        
        # 游戏菜单
        game_menu = menubar.addMenu("游戏(&G)")
        
        challenge_action = game_menu.addAction("发起挑战")
        challenge_action.triggered.connect(self.show_challenge_dialog)
        
        player_list_action = game_menu.addAction("玩家列表")
        player_list_action.triggered.connect(self.show_player_list)
        
        game_menu.addSeparator()
        
        undo_action = game_menu.addAction("悔棋")
        undo_action.triggered.connect(self.request_undo)
        
        reset_action = game_menu.addAction("重置游戏")
        reset_action.triggered.connect(self.request_reset)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        about_action = help_menu.addAction("关于")
        about_action.triggered.connect(self.show_about)
        
    def setup_status_bar(self):
        """设置状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.server_status_label = QLabel("服务器: 未连接")
        self.status_bar.addWidget(self.server_status_label)
        
        self.status_bar.addPermanentWidget(QLabel(f"版本: 1.0.0"))
        
    def setup_signal_connections(self):
        """设置信号连接"""
        self.signals.message_received.connect(self.append_log)
        self.signals.error_occurred.connect(self.show_error)
        self.signals.room_updated.connect(self.on_room_updated)
        self.signals.player_list_updated.connect(self.on_player_list_updated)
        self.signals.challenge_list_updated.connect(self.on_challenge_list_updated)
        self.signals.game_over.connect(self.on_game_over)
        self.signals.coin_toss_phase.connect(self.on_coin_toss_phase)
        self.signals.show_color_choice.connect(self.on_show_color_choice)
        
        # 计时器相关信号
        self.signals.start_waiting_timer.connect(self.timer_widget.start_waiting)
        self.signals.stop_waiting_timer.connect(self.timer_widget.stop_waiting)
        self.signals.start_game_timer.connect(self.timer_widget.start_timer)
        self.signals.stop_game_timer.connect(self.timer_widget.stop_timer)
        self.signals.reset_timer.connect(self.timer_widget.reset_timer)
        self.signals.switch_timer_player.connect(self.timer_widget.switch_player)
        
        # 按钮状态信号
        self.signals.disable_coin_button.connect(lambda: self.coin_btn.setEnabled(False))
        self.signals.enable_coin_button.connect(lambda: self.coin_btn.setEnabled(True))
        self.signals.disable_undo_button.connect(lambda: self.undo_btn.setEnabled(False))
        self.signals.enable_undo_button.connect(lambda: self.undo_btn.setEnabled(True))
        self.signals.disable_reset_button.connect(lambda: self.reset_btn.setEnabled(False))
        self.signals.enable_reset_button.connect(lambda: self.reset_btn.setEnabled(True))
        
        # 棋盘状态信号
        self.signals.enable_board_click.connect(lambda: self.board.set_click_enabled(True))
        self.signals.disable_board_click.connect(lambda: self.board.set_click_enabled(False))
        
        # 游戏状态信号
        self.signals.update_game_phase.connect(self._update_game_phase)
        self.signals.update_status_label.connect(self.status_label.setText)
        
        # 硬币结果详细信号
        self.signals.coin_toss_completed.connect(self.on_coin_toss_completed)
        
        # 颜色选择后信号
        self.signals.color_chosen.connect(self.on_color_chosen)
        
        # 挑战相关信号
        self.signals.show_players_for_challenge.connect(self.show_players_for_challenge)
        
        # 对话框显示信号
        self.signals.show_player_list_dialog.connect(self._show_player_list_dialog)
        self.signals.show_challenge_list_dialog.connect(self._show_challenge_list_dialog)
        
        # 游戏状态更新信号
        self.signals.game_reset.connect(self._on_game_reset)
        self.signals.update_my_color.connect(self._update_my_color)
        self.signals.enable_game_controls.connect(self._enable_game_controls)
        self.signals.disable_game_controls.connect(self._disable_game_controls)
        
    # ==================== 网络请求方法 ====================
    
    def _request(self, method, endpoint, data=None, params=None):
        """发送HTTP请求"""
        url = f"{self.server_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, params=params, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, timeout=10)
            else:
                return False, f"不支持的HTTP方法: {method}"
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"请求失败，状态码: {response.status_code}"
        except requests.exceptions.RequestException as e:
            return False, f"连接错误: {e}"
            
    # ==================== UI事件处理 ====================
    
    def connect_to_server(self):
        """连接服务器"""
        self.append_log("正在连接服务器...")
        
        def check_connection():
            success, result = self._request('GET', '/api/health')
            if success:
                self.signals.message_received.emit("✓ 服务器连接成功！")
                self.signals.message_received.emit(f"  服务器状态: {result.get('message', '正常')}")
                self.server_status_label.setText("服务器: 已连接")
                self.server_status_label.setStyleSheet("color: green;")
                self.login_btn.setEnabled(True)
            else:
                self.signals.error_occurred.emit(f"无法连接服务器: {result}")
        
        thread = threading.Thread(target=check_connection, daemon=True)
        thread.start()
        
    def show_login_dialog(self):
        """显示登录对话框"""
        name, ok = QInputDialog.getText(
            self, "玩家注册", "请输入玩家名称:",
            QLineEdit.Normal, ""
        )
        
        if ok and name:
            self.register_player(name)
        elif ok:
            self.register_player(None)  # 使用默认名称
            
    def register_player(self, name=None):
        """注册玩家"""
        self.append_log(f"正在注册玩家: {name or '默认名称'}...")
        
        def do_register():
            data = {}
            if name:
                data['name'] = name
            
            success, result = self._request('POST', '/api/player/register', data)
            if success and result.get('success'):
                self.player_id = result.get('player_id')
                self.player_name = result.get('name')
                
                self.signals.message_received.emit(f"✓ 注册成功！")
                self.signals.message_received.emit(f"  玩家名称: {self.player_name}")
                self.signals.message_received.emit(f"  玩家ID: {self.player_id}")
                
                # 更新UI
                self.player_name_label.setText(self.player_name)
                self.player_id_label.setText(self.player_id[:8] + "...")
                self.player_status_label.setText("在线")
                
                # 启用按钮
                self.challenge_btn.setEnabled(True)
                self.players_btn.setEnabled(True)
                self.challenges_btn.setEnabled(True)
                
                # 开始轮询
                self.start_polling()
            else:
                self.signals.error_occurred.emit(f"注册失败: {result.get('message', '未知错误')}")
        
        thread = threading.Thread(target=do_register, daemon=True)
        thread.start()
        
    def show_challenge_dialog(self):
        """显示挑战对话框"""
        if not self.player_id:
            QMessageBox.warning(self, "提示", "请先登录！")
            return
            
        self.append_log("正在获取在线玩家列表...")
        
        def get_players_and_show():
            success, result = self._request('GET', '/api/player/list')
            if success and result.get('success'):
                players = result.get('players', [])
                
                # 过滤掉自己和非空闲玩家
                available_players = [
                    p for p in players 
                    if p.get('id') != self.player_id
                ]
                
                if not available_players:
                    self.signals.message_received.emit("没有可用的在线玩家")
                    return
                
                # 在主线程显示对话框
                QApplication.processEvents()
                
                # 使用QMetaObject.invokeMethod在主线程调用
                self.signals.player_list_updated.emit(available_players)
            else:
                self.signals.error_occurred.emit(f"获取玩家列表失败: {result.get('message', '未知错误')}")
        
        thread = threading.Thread(target=get_players_and_show, daemon=True)
        thread.start()
        
    def on_player_list_updated(self, players):
        """玩家列表更新"""
        # 显示挑战对话框
        dialog = ChallengeDialog(players, self)
        if dialog.exec_() == QDialog.Accepted:
            selected_player = dialog.get_selected_player()
            if selected_player:
                self.send_challenge(selected_player.get('id'))
                
    def send_challenge(self, challenged_id):
        """发送挑战"""
        if challenged_id == self.player_id:
            QMessageBox.warning(self, "提示", "不能挑战自己！")
            return
            
        self.append_log(f"正在向玩家发起挑战...")
        
        def do_challenge():
            data = {
                'challenger_id': self.player_id,
                'challenged_id': challenged_id
            }
            
            success, result = self._request('POST', '/api/challenge/send', data)
            if success and result.get('success'):
                self.signals.message_received.emit(f"✓ 挑战已发送！")
                self.signals.message_received.emit(f"  挑战ID: {result.get('challenge_id')}")
            else:
                self.signals.error_occurred.emit(f"发起挑战失败: {result.get('message', '未知错误')}")
        
        thread = threading.Thread(target=do_challenge, daemon=True)
        thread.start()
        
    def show_player_list(self):
        """显示玩家列表"""
        if not self.player_id:
            QMessageBox.warning(self, "提示", "请先登录！")
            return
            
        def get_players():
            success, result = self._request('GET', '/api/player/list')
            if success and result.get('success'):
                players = result.get('players', [])
                
                # 通过信号在主线程显示对话框
                self.signals.show_player_list_dialog.emit(players)
            else:
                self.signals.error_occurred.emit(f"获取玩家列表失败: {result.get('message', '未知错误')}")
        
        thread = threading.Thread(target=get_players, daemon=True)
        thread.start()
        
    def show_my_challenges(self):
        """显示我的挑战列表"""
        if not self.player_id:
            QMessageBox.warning(self, "提示", "请先登录！")
            return
            
        self.append_log("正在获取挑战列表...")
        
        def get_challenges():
            params = {'player_id': self.player_id}
            success, result = self._request('GET', '/api/challenge/list', params=params)
            
            if success and result.get('success'):
                challenges = result.get('challenges', [])
                self.signals.challenge_list_updated.emit(challenges)
            else:
                self.signals.error_occurred.emit(f"获取挑战列表失败: {result.get('message', '未知错误')}")
        
        thread = threading.Thread(target=get_challenges, daemon=True)
        thread.start()
        
    def on_challenge_list_updated(self, challenges):
        """挑战列表更新"""
        if not challenges:
            self.append_log("当前没有挑战")
            return
            
        # 显示挑战列表对话框
        dialog = ChallengeListDialog(challenges, self)
        if dialog.exec_() == QDialog.Accepted:
            action, challenge_id = dialog.get_result()
            if action == 'accept':
                self.accept_challenge(challenge_id)
            elif action == 'decline':
                self.decline_challenge(challenge_id)
                
    def accept_challenge(self, challenge_id):
        """接受挑战"""
        self.append_log("正在接受挑战...")
        
        def do_accept():
            data = {
                'challenge_id': challenge_id,
                'player_id': self.player_id
            }
            
            success, result = self._request('POST', '/api/challenge/accept', data)
            if success and result.get('success'):
                room_id = result.get('room_id')
                self.current_room_id = room_id
                
                self.signals.message_received.emit(f"✓ 挑战已接受！")
                self.signals.message_received.emit(f"  房间ID: {room_id}")
                self.signals.message_received.emit("进入抛硬币阶段，请选择硬币结果")
                
                # 启用硬币按钮
                self.coin_btn.setEnabled(True)
                self.game_phase = "coin_toss"
                self.status_label.setText("游戏状态: 抛硬币阶段")
                
            else:
                self.signals.error_occurred.emit(f"接受挑战失败: {result.get('message', '未知错误')}")
        
        thread = threading.Thread(target=do_accept, daemon=True)
        thread.start()
        
    def decline_challenge(self, challenge_id):
        """拒绝挑战"""
        self.append_log("正在拒绝挑战...")
        
        def do_decline():
            data = {
                'challenge_id': challenge_id,
                'player_id': self.player_id
            }
            
            success, result = self._request('POST', '/api/challenge/decline', data)
            if success and result.get('success'):
                self.signals.message_received.emit("✓ 已拒绝挑战")
            else:
                self.signals.error_occurred.emit(f"拒绝挑战失败: {result.get('message', '未知错误')}")
        
        thread = threading.Thread(target=do_decline, daemon=True)
        thread.start()
        
    def show_coin_dialog(self):
        """显示抛硬币对话框"""
        dialog = CoinTossDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            choice = dialog.get_choice()
            self.make_coin_choice(choice)
            
    def make_coin_choice(self, choice):
        """进行硬币猜测"""
        if not self.current_room_id:
            QMessageBox.warning(self, "提示", "当前没有房间！")
            return
            
        self.append_log(f"正在提交硬币选择: {'正面' if choice == 0 else '反面'}...")
        
        def do_choice():
            data = {
                'player_id': self.player_id,
                'room_id': self.current_room_id,
                'choice': choice
            }
            
            success, result = self._request('POST', '/api/game/coin_choice', data)
            if success and result.get('success'):
                # 检查是否自动分配了对方的选择
                auto_assigned = result.get('auto_assigned', False)
                
                if auto_assigned:
                    player_choice = result.get('player_choice', '正面' if choice == 0 else '反面')
                    other_choice = result.get('other_player_choice', '反面' if choice == 0 else '正面')
                    
                    self.signals.message_received.emit(f"✓ 您选择了: {player_choice}")
                    self.signals.message_received.emit(f"✓ 系统已自动为对方分配: {other_choice}")
                    
                    # 立即解析硬币结果
                    self.signals.message_received.emit("正在解析抛硬币结果...")
                    
                    # 调用resolve_coin_toss
                    resolve_data = {'room_id': self.current_room_id}
                    resolve_success, resolve_result = self._request('POST', '/api/game/resolve_coin', resolve_data)
                    
                    if resolve_success and resolve_result.get('success'):
                        coin_result = resolve_result.get('coin_result')
                        winner_id = resolve_result.get('winner_id')
                        winner_choice = resolve_result.get('winner_choice')
                        loser_choice = resolve_result.get('loser_choice')
                        
                        self.signals.message_received.emit(f"✓ 硬币结果: {coin_result}")
                        
                        is_my_win = winner_id == self.player_id
                        if is_my_win:
                            self.signals.message_received.emit(f"🎉 恭喜！您选择了{winner_choice}，猜对了！请选择执子颜色。")
                            
                            # 通过信号显示颜色选择对话框
                            self.signals.show_color_choice.emit()
                        else:
                            self.signals.message_received.emit(f"对方选择了{winner_choice}，猜对了。等待对方选择颜色...")
                            
                            # 通过信号启动等待计时器
                            self.signals.start_waiting_timer.emit()
                    else:
                        self.signals.error_occurred.emit(f"解析硬币结果失败: {resolve_result.get('message', '未知错误')}")
                else:
                    # 旧的逻辑：等待对方选择
                    self.signals.message_received.emit("✓ 硬币选择已提交")
                    self.signals.message_received.emit("等待对方选择...")
                    
                    # 通过信号禁用按钮和启动等待计时器
                    self.signals.disable_coin_button.emit()
                    self.signals.start_waiting_timer.emit()
            else:
                self.signals.error_occurred.emit(f"提交选择失败: {result.get('message', '未知错误')}")
        
        thread = threading.Thread(target=do_choice, daemon=True)
        thread.start()
        
    def on_coin_toss_phase(self):
        """进入抛硬币阶段"""
        self.coin_btn.setEnabled(True)
        self.game_phase = "coin_toss"
        self.status_label.setText("游戏状态: 抛硬币阶段")
        self.append_log("进入抛硬币阶段，请选择硬币结果")
        
    def on_show_color_choice(self):
        """显示颜色选择对话框"""
        self.append_log("请选择执子颜色...")
        
        # 停止等待计时
        self.timer_widget.stop_waiting()
        
        # 显示颜色选择对话框
        color_dialog = ColorChoiceDialog(self)
        if color_dialog.exec_() == QDialog.Accepted:
            color = color_dialog.get_color()
            self.choose_color(color)
    
    # ==================== 新增槽函数（线程安全） ====================
    
    def _show_player_list_dialog(self, players):
        """显示玩家列表对话框（主线程）"""
        if not players:
            self.append_log("当前没有其他在线玩家")
            return
        
        # 显示玩家列表对话框
        dialog = PlayerListDialog(players, self.player_id, self)
        if dialog.exec_() == QDialog.Accepted:
            target_player_id = dialog.get_selected_player()
            if target_player_id:
                self.challenge_player(target_player_id)
    
    def _show_challenge_list_dialog(self, challenges):
        """显示挑战列表对话框（主线程）"""
        if not challenges:
            self.append_log("当前没有挑战")
            return
        
        # 显示挑战列表对话框
        dialog = ChallengeListDialog(challenges, self)
        if dialog.exec_() == QDialog.Accepted:
            action, challenge_id = dialog.get_result()
            if action == 'accept':
                self.accept_challenge(challenge_id)
            elif action == 'decline':
                self.decline_challenge(challenge_id)
    
    def _update_game_phase(self, phase):
        """更新游戏阶段（主线程）"""
        self.game_phase = phase
        if phase == 'playing':
            self.status_label.setText("游戏状态: 游戏进行中")
        elif phase == 'coin_toss':
            self.status_label.setText("游戏状态: 抛硬币阶段")
        elif phase == 'waiting':
            self.status_label.setText("游戏状态: 等待开始")
        elif phase == 'finished':
            self.status_label.setText("游戏状态: 已结束")
    
    def on_coin_toss_completed(self, data):
        """硬币结果完成（主线程）"""
        winner_id = data.get('winner_id')
        coin_result = data.get('coin_result')
        winner_choice = data.get('winner_choice', coin_result)
        loser_choice = data.get('loser_choice')
        is_my_win = data.get('is_my_win', False)
        
        self.append_log(f"✓ 硬币结果: {coin_result}")
        
        if is_my_win:
            self.append_log(f"🎉 恭喜！您选择了{winner_choice}，猜对了！请选择执子颜色。")
            self.signals.show_color_choice.emit()
        else:
            self.append_log(f"对方选择了{winner_choice}，猜对了。等待对方选择颜色...")
            self.signals.start_waiting_timer.emit()
    
    def on_color_chosen(self, color):
        """颜色选择后（主线程）"""
        self.my_color = color
        self._update_my_color(color)
    
    def _update_my_color(self, color):
        """更新我的颜色显示（主线程）"""
        if color == 1:
            self.my_color_label.setText("⚫ 执黑棋")
            self.my_color_label.setStyleSheet("color: black; background-color: white; padding: 5px; border-radius: 3px;")
        else:
            self.my_color_label.setText("⚪ 执白棋")
            self.my_color_label.setStyleSheet("color: white; background-color: black; padding: 5px; border-radius: 3px;")
    
    def _on_game_reset(self):
        """游戏重置（主线程）"""
        self.board.clear_board()
        self.board.set_click_enabled(False)
        self.timer_widget.reset_timer()
        self.game_phase = "coin_toss"
        self.status_label.setText("游戏状态: 抛硬币阶段")
        self.coin_btn.setEnabled(True)
        self.undo_btn.setEnabled(False)
        self.reset_btn.setEnabled(False)
    
    def _enable_game_controls(self):
        """启用游戏控件（主线程）"""
        self.board.set_click_enabled(True)
        self.undo_btn.setEnabled(True)
        self.reset_btn.setEnabled(True)
        self.coin_btn.setEnabled(False)
    
    def _disable_game_controls(self):
        """禁用游戏控件（主线程）"""
        self.board.set_click_enabled(False)
        self.undo_btn.setEnabled(False)
        self.reset_btn.setEnabled(False)
    
    def show_players_for_challenge(self, players):
        """显示可挑战的玩家列表（主线程）"""
        self._show_player_list_dialog(players)
        
    def resolve_coin_toss(self):
        """解决抛硬币结果"""
        if not self.current_room_id:
            return
            
        self.append_log("正在解析抛硬币结果...")
        
        def do_resolve():
            data = {'room_id': self.current_room_id}
            success, result = self._request('POST', '/api/game/resolve_coin', data)
            
            if success and result.get('success'):
                coin_result = result.get('coin_result')
                winner_id = result.get('winner_id')
                winner_choice = result.get('winner_choice')
                loser_choice = result.get('loser_choice')
                
                is_my_win = winner_id == self.player_id
                
                # 通过信号传递结果到主线程处理
                self.signals.coin_toss_completed.emit({
                    'winner_id': winner_id,
                    'coin_result': coin_result,
                    'winner_choice': winner_choice,
                    'loser_choice': loser_choice,
                    'is_my_win': is_my_win
                })
            else:
                # 可能是平局，需要重新猜
                if "平局" in str(result):
                    self.signals.message_received.emit("平局！请重新选择硬币")
                    self.signals.enable_coin_button.emit()
                else:
                    self.signals.error_occurred.emit(f"解析硬币结果失败: {result}")
        
        thread = threading.Thread(target=do_resolve, daemon=True)
        thread.start()
        
    def choose_color(self, color_choice):
        """选择执子颜色"""
        if not self.current_room_id:
            return
            
        color_name = "黑棋" if color_choice == 1 else "白棋"
        self.append_log(f"正在选择执子颜色: {color_name}...")
        
        def do_choose():
            data = {
                'player_id': self.player_id,
                'room_id': self.current_room_id,
                'color_choice': color_choice
            }
            
            success, result = self._request('POST', '/api/game/choose_color', data)
            if success and result.get('success'):
                self.signals.message_received.emit(f"✓ 已选择{color_name}")
                
                # 通过信号更新颜色显示
                self.signals.update_my_color.emit(color_choice)
                
                # 确定第二个玩家颜色并开始游戏
                self.finalize_colors()
            else:
                self.signals.error_occurred.emit(f"选择颜色失败: {result.get('message', '未知错误')}")
        
        thread = threading.Thread(target=do_choose, daemon=True)
        thread.start()
        
    def finalize_colors(self):
        """确定所有玩家颜色"""
        if not self.current_room_id:
            return
            
        # 先获取房间信息找到另一个玩家
        def get_room_and_finalize():
            params = {'room_id': self.current_room_id, 'player_id': self.player_id}
            success, result = self._request('GET', '/api/room/info', params=params)
            
            if success and result.get('success'):
                room = result.get('room', {})
                player1 = room.get('player1')
                player2 = room.get('player2')
                
                # 找到另一个玩家
                other_player_id = None
                if player1 and player1 != self.player_id:
                    other_player_id = player1
                elif player2 and player2 != self.player_id:
                    other_player_id = player2
                
                if other_player_id:
                    # 确定颜色
                    data = {
                        'room_id': self.current_room_id,
                        'player2_id': other_player_id
                    }
                    
                    success2, result2 = self._request('POST', '/api/game/finalize_colors', data)
                    if success2 and result2.get('success'):
                        self.signals.message_received.emit("✓ 游戏开始！")
                        
                        # 通过信号启用游戏控件和开始计时
                        self.signals.update_game_phase.emit("playing")
                        self.signals.enable_game_controls.emit()
                        self.signals.stop_waiting_timer.emit()
                        self.signals.start_game_timer.emit(1)
                        
                        # 更新回合显示
                        self.update_turn_display()
                    else:
                        self.signals.error_occurred.emit(f"开始游戏失败: {result2.get('message', '未知错误')}")
                else:
                    self.signals.error_occurred.emit("无法找到另一个玩家")
            else:
                self.signals.error_occurred.emit(f"获取房间信息失败: {result.get('message', '未知错误')}")
        
        thread = threading.Thread(target=get_room_and_finalize, daemon=True)
        thread.start()
        
    def on_board_clicked(self, row, col):
        """棋盘被点击"""
        if self.game_phase != "playing":
            self.append_log("游戏尚未开始，无法落子")
            return
            
        self.append_log(f"尝试落子: 行={row}, 列={col}")
        
        def do_place():
            data = {
                'player_id': self.player_id,
                'room_id': self.current_room_id,
                'row': row,
                'col': col
            }
            
            success, result = self._request('POST', '/api/game/place_piece', data)
            if success and result.get('success'):
                self.signals.message_received.emit(f"✓ 落子成功: 行={row}, 列={col}")
                
                # 更新游戏状态
                game_state = result.get('game_state', {})
                self.signals.room_updated.emit({'game_state': game_state})
                
                # 通过信号切换计时器
                self.signals.switch_timer_player.emit()
            else:
                self.signals.error_occurred.emit(f"落子失败: {result.get('message', '未知错误')}")
        
        thread = threading.Thread(target=do_place, daemon=True)
        thread.start()
        
    def request_undo(self):
        """请求悔棋"""
        if not self.current_room_id:
            QMessageBox.warning(self, "提示", "当前没有游戏！")
            return
            
        self.append_log("正在请求悔棋...")
        
        def do_undo():
            data = {
                'player_id': self.player_id,
                'room_id': self.current_room_id
            }
            
            success, result = self._request('POST', '/api/game/undo', data)
            if success and result.get('success'):
                self.signals.message_received.emit("✓ 悔棋成功")
                
                # 更新游戏状态
                game_state = result.get('game_state', {})
                self.signals.room_updated.emit({'game_state': game_state})
            else:
                self.signals.error_occurred.emit(f"悔棋失败: {result.get('message', '未知错误')}")
        
        thread = threading.Thread(target=do_undo, daemon=True)
        thread.start()
        
    def request_reset(self):
        """请求重置游戏"""
        if not self.current_room_id:
            QMessageBox.warning(self, "提示", "当前没有游戏！")
            return
            
        reply = QMessageBox.question(
            self, "确认重置",
            "确定要重置游戏吗？这将重新开始抛硬币阶段。",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        self.append_log("正在重置游戏...")
        
        def do_reset():
            data = {
                'player_id': self.player_id,
                'room_id': self.current_room_id
            }
            
            success, result = self._request('POST', '/api/game/reset', data)
            if success and result.get('success'):
                self.signals.message_received.emit("✓ 游戏已重置")
                
                # 通过信号重置UI状态
                self.signals.game_reset.emit()
                
                # 更新游戏状态
                game_state = result.get('game_state', {})
                self.signals.room_updated.emit({'game_state': game_state})
            else:
                self.signals.error_occurred.emit(f"重置失败: {result.get('message', '未知错误')}")
        
        thread = threading.Thread(target=do_reset, daemon=True)
        thread.start()
        
    # ==================== 轮询和状态更新 ====================
    
    def start_polling(self):
        """开始轮询"""
        if self.polling_thread and self.polling_thread.is_alive():
            return
            
        self.running = True
        self.polling_thread = threading.Thread(target=self.polling_loop, daemon=True)
        self.polling_thread.start()
        
    def stop_polling(self):
        """停止轮询"""
        self.running = False
        
    def polling_loop(self):
        """轮询循环"""
        while self.running:
            try:
                # 如果有房间，获取房间信息
                if self.current_room_id:
                    params = {
                        'room_id': self.current_room_id,
                        'player_id': self.player_id
                    }
                    success, result = self._request('GET', '/api/room/info', params=params)
                    
                    if success and result.get('success'):
                        room = result.get('room', {})
                        self.signals.room_updated.emit(room)
                
                # 检查挑战（每5秒）
                if self.player_id:
                    params = {'player_id': self.player_id}
                    success, result = self._request('GET', '/api/challenge/list', params=params)
                    
                    if success and result.get('success'):
                        challenges = result.get('challenges', [])
                        # 检查是否有新的待处理挑战
                        pending = [c for c in challenges 
                                  if c.get('status') == 'pending' 
                                  and not c.get('is_my_challenge')]
                        if pending:
                            self.signals.message_received.emit(
                                f"📢 您收到了 {len(pending)} 个新挑战！"
                            )
                
                time.sleep(2)  # 每2秒轮询一次
                
            except Exception as e:
                self.signals.error_occurred.emit(f"轮询错误: {e}")
                time.sleep(5)
                
    def on_room_updated(self, room):
        """房间更新"""
        game_state = room.get('game_state', {})
        
        # 更新棋盘
        board = game_state.get('board', [])
        if board:
            current_player = game_state.get('current_player', 1)
            self.board.update_board(board, current_player)
            
        # 更新游戏阶段
        new_phase = game_state.get('game_phase', 'waiting')
        if new_phase != self.game_phase:
            self.game_phase = new_phase
            
            if new_phase == 'playing':
                self.status_label.setText("游戏状态: 游戏进行中")
                self.board.set_click_enabled(True)
                self.undo_btn.setEnabled(True)
                self.reset_btn.setEnabled(True)
                self.coin_btn.setEnabled(False)
                
                # 如果计时器还没开始，开始计时
                if not self.timer_widget.is_running:
                    self.timer_widget.stop_waiting()
                    self.timer_widget.start_timer(game_state.get('current_player', 1))
                    
            elif new_phase == 'coin_toss':
                self.status_label.setText("游戏状态: 抛硬币阶段")
                self.board.set_click_enabled(False)
                
            elif new_phase == 'waiting':
                self.status_label.setText("游戏状态: 等待开始")
                self.board.set_click_enabled(False)
                
        # 更新回合显示
        self.update_turn_display()
        
        # 检查游戏是否结束
        if game_state.get('game_over'):
            winner = game_state.get('winner')
            self.signals.game_over.emit(winner)
            
        # 更新我的颜色
        if 'player_color' in game_state:
            color = game_state.get('player_color')
            if color and color != self.my_color:
                self.my_color = color
                if self.my_color == 1:
                    self.my_color_label.setText("⚫ 执黑棋")
                else:
                    self.my_color_label.setText("⚪ 执白棋")
                    
    def update_turn_display(self):
        """更新回合显示"""
        if not self.current_room_id:
            self.turn_label.setText("当前: 等待开始")
            return
            
        # 获取当前房间信息
        params = {
            'room_id': self.current_room_id,
            'player_id': self.player_id
        }
        success, result = self._request('GET', '/api/room/info', params=params)
        
        if success and result.get('success'):
            room = result.get('room', {})
            game_state = room.get('game_state', {})
            
            current_player = game_state.get('current_player', 1)
            is_my_turn = game_state.get('is_my_turn', False)
            
            current_name = "黑棋" if current_player == 1 else "白棋"
            
            if is_my_turn:
                self.turn_label.setText(f"当前: {current_name}的回合 (您的回合!)")
                self.turn_label.setStyleSheet("color: green; font-weight: bold;")
                self.board.set_click_enabled(True)
            else:
                self.turn_label.setText(f"当前: {current_name}的回合")
                self.turn_label.setStyleSheet("color: #4a90d9; font-weight: bold;")
                
    def on_game_over(self, winner):
        """游戏结束"""
        self.timer_widget.stop_timer()
        self.board.set_click_enabled(False)
        self.game_phase = "finished"
        self.status_label.setText("游戏状态: 已结束")
        
        winner_name = "黑棋" if winner == 1 else "白棋"
        is_my_win = (winner == self.my_color)
        
        if is_my_win:
            message = f"🎉 恭喜！您获胜了！\n\n{winner_name}获胜！"
        else:
            message = f"😢 您输了...\n\n{winner_name}获胜！"
            
        self.append_log(f"★ 游戏结束！{winner_name}获胜！ ★")
        
        QMessageBox.information(self, "游戏结束", message)
        
    # ==================== 辅助方法 ====================
    
    def append_log(self, message):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        self.log_text.append(log_message)
        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def show_error(self, message):
        """显示错误消息"""
        self.append_log(f"✗ {message}")
        QMessageBox.critical(self, "错误", message)
        
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于五子棋",
            "<h3>五子棋 - 网络对战</h3>"
            "<p>版本: 1.0.0</p>"
            "<p>基于PyQt5开发的桌面端五子棋游戏</p>"
            "<p>支持:</p>"
            "<ul>"
            "<li>15x15标准棋盘</li>"
            "<li>网络对战</li>"
            "<li>抛硬币猜先</li>"
            "<li>悔棋、重置</li>"
            "<li>游戏计时</li>"
            "</ul>"
        )
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.stop_polling()
        
        # 如果玩家在线，尝试下线
        if self.player_id:
            try:
                data = {'player_id': self.player_id}
                self._request('POST', '/api/player/offline', data)
            except:
                pass
        
        event.accept()


# ==================== 挑战列表对话框 ====================

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
        
        # 标题
        title_label = QLabel(f"挑战列表 (共 {len(self.challenges)} 条)")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title_label)
        
        # 挑战列表
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
            
            # 只有待处理且不是我发起的挑战可以操作
            can_accept = status == 'pending' and not is_my
            
            item_text = f"[{challenge_type}] 对方: {opponent} - 状态: {status_name}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, challenge)
            
            if can_accept:
                item.setForeground(QColor('#4caf50'))  # 绿色表示可操作
            
            self.challenge_list.addItem(item)
        
        layout.addWidget(self.challenge_list)
        
        # 操作按钮
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
        
        # 只有待处理且不是我发起的挑战可以操作
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


# ==================== 主函数 ====================

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()