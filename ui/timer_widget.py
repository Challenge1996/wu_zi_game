from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QFrame, QLabel, QLCDNumber
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from constants import PLAYER_BLACK, PLAYER_WHITE, MOVE_TIMEOUT_SECONDS
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
        
        self.countdown_time = MOVE_TIMEOUT_SECONDS
        self.countdown_running = False
        self.my_color = None
        
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
        
        countdown_frame = QFrame()
        countdown_frame.setFrameStyle(QFrame.StyledPanel)
        countdown_layout = QVBoxLayout(countdown_frame)
        
        countdown_title_layout = QHBoxLayout()
        self.countdown_label = QLabel("落子倒计时:")
        self.countdown_label.setFont(QFont("Arial", 11, QFont.Bold))
        
        self.countdown_status_label = QLabel("")
        self.countdown_status_label.setFont(QFont("Arial", 10))
        
        countdown_title_layout.addWidget(self.countdown_label)
        countdown_title_layout.addStretch()
        countdown_title_layout.addWidget(self.countdown_status_label)
        
        countdown_display_layout = QHBoxLayout()
        self.countdown_lcd = QLCDNumber(5)
        self.countdown_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.countdown_lcd.setStyleSheet("color: green; background-color: #e0ffe0; font-size: 24px;")
        self.countdown_lcd.display("02:00")
        self.countdown_lcd.setMinimumHeight(50)
        
        countdown_display_layout.addWidget(self.countdown_lcd)
        
        countdown_layout.addLayout(countdown_title_layout)
        countdown_layout.addLayout(countdown_display_layout)
        
        time_layout.addWidget(black_frame)
        time_layout.addWidget(white_frame)
        time_layout.addWidget(wait_frame)
        time_layout.addWidget(countdown_frame)
        
        layout.addWidget(time_group)
        
    def setup_timer(self):
        """设置计时器"""
        self.game_timer = QTimer(self)
        self.game_timer.timeout.connect(self.update_game_time)
        
        self.wait_timer = QTimer(self)
        self.wait_timer.timeout.connect(self.update_wait_time)
        
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_countdown)
        
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
        self.stop_countdown()
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
    
    def start_countdown(self, player_color, time_remaining=None):
        """开始倒计时
        Args:
            player_color: 当前落子的玩家颜色
            time_remaining: 剩余时间（秒），如果为None则使用默认值
        """
        self.current_player = player_color
        if time_remaining is not None:
            self.countdown_time = time_remaining
        else:
            self.countdown_time = MOVE_TIMEOUT_SECONDS
        
        self.countdown_running = True
        self.update_countdown_display()
        
        if not self.countdown_timer.isActive():
            self.countdown_timer.stop()
        self.countdown_timer.start(1000)
        
        if self.my_color is not None:
            if player_color == self.my_color:
                self.countdown_status_label.setText("轮到您落子")
                self.countdown_status_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.countdown_status_label.setText("等待对手")
                self.countdown_status_label.setStyleSheet("color: blue;")
        
    def stop_countdown(self):
        """停止倒计时"""
        self.countdown_running = False
        if self.countdown_timer.isActive():
            self.countdown_timer.stop()
        self.countdown_status_label.setText("")
        
    def update_countdown(self):
        """更新倒计时"""
        if self.countdown_time > 0:
            self.countdown_time -= 1
            self.update_countdown_display()
        else:
            self.stop_countdown()
    
    def update_countdown_display(self):
        """更新倒计时显示"""
        minutes = self.countdown_time // 60
        seconds = self.countdown_time % 60
        time_str = f"{minutes:02d}:{seconds:02d}"
        self.countdown_lcd.display(time_str)
        
        if self.countdown_time <= 10:
            self.countdown_lcd.setStyleSheet("color: red; background-color: #ffe0e0;")
        elif self.countdown_time <= 30:
            self.countdown_lcd.setStyleSheet("color: orange; background-color: #fff0e0;")
        else:
            self.countdown_lcd.setStyleSheet("color: green; background-color: #e0ffe0;")
    
    def set_my_color(self, color):
        """设置当前玩家颜色，用于判断倒计时提示
        """
        self.my_color = color
