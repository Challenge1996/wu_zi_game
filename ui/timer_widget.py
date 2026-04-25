from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QFrame, QLabel, QLCDNumber
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from constants import PLAYER_BLACK, PLAYER_WHITE
from util import format_time


class TimerWidget(QWidget):
    """计时器控件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.player1_time = 0
        self.player2_time = 0
        self.current_player = PLAYER_BLACK
        self.is_running = False
        self.wait_time = 0
        
        self.init_ui()
        self.setup_timer()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        time_group = QGroupBox("游戏计时")
        time_layout = QVBoxLayout(time_group)
        
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
        
    def start_timer(self, current_player=PLAYER_BLACK):
        """开始游戏计时"""
        self.current_player = current_player
        self.is_running = True
        self.game_timer.start(1000)
        
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
        if self.current_player == PLAYER_BLACK:
            self.player1_time += 1
        else:
            self.player2_time += 1
        self.update_display()
        
    def switch_player(self):
        """切换当前玩家"""
        self.current_player = PLAYER_WHITE if self.current_player == PLAYER_BLACK else PLAYER_BLACK
        
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
        self.black_lcd.display(format_time(self.player1_time))
        self.white_lcd.display(format_time(self.player2_time))
        self.wait_lcd.display(format_time(self.wait_time))
        
        if self.current_player == PLAYER_BLACK:
            self.black_lcd.setStyleSheet("color: red; background-color: #ffe0e0;")
            self.white_lcd.setStyleSheet("color: black; background-color: #f0f0f0;")
        else:
            self.black_lcd.setStyleSheet("color: black; background-color: #f0f0f0;")
            self.white_lcd.setStyleSheet("color: red; background-color: #ffe0e0;")
