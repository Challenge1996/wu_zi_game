#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对局复盘播放对话框
自动播放历史对局的走棋过程
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QWidget, QGroupBox, QFrame
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QLinearGradient
)
from constants import BOARD_SIZE, PLAYER_BLACK, PLAYER_WHITE


class ReplayBoardWidget(QWidget):
    """复盘专用棋盘控件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.board_size = BOARD_SIZE
        self.cell_size = 32
        self.margin = 20
        self.board = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.last_move = None
        self.setMinimumSize(550, 550)
        
    def set_board_state(self, board_data, last_move=None):
        """设置棋盘状态"""
        self.board = [row[:] for row in board_data]
        self.last_move = last_move
        self.update()
        
    def clear_board(self):
        """清空棋盘"""
        self.board = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.last_move = None
        self.update()
        
    def paintEvent(self, event):
        """绘制棋盘和棋子"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        total_size = self.cell_size * (self.board_size - 1)
        x_offset = (self.width() - total_size) // 2
        y_offset = (self.height() - total_size) // 2
        
        board_rect = self.rect()
        board_gradient = QLinearGradient(board_rect.topLeft(), board_rect.bottomRight())
        board_gradient.setColorAt(0, QColor(245, 222, 179))
        board_gradient.setColorAt(1, QColor(222, 184, 135))
        painter.fillRect(board_rect, board_gradient)
        
        pen = QPen(QColor(80, 50, 20), 1)
        painter.setPen(pen)
        
        for i in range(self.board_size):
            start_x = x_offset
            start_y = y_offset + i * self.cell_size
            end_x = x_offset + (self.board_size - 1) * self.cell_size
            end_y = start_y
            painter.drawLine(start_x, start_y, end_x, end_y)
            
            start_x = x_offset + i * self.cell_size
            start_y = y_offset
            end_x = start_x
            end_y = y_offset + (self.board_size - 1) * self.cell_size
            painter.drawLine(start_x, start_y, end_x, end_y)
        
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
                                star_radius * 2, 2)
        
        piece_radius = self.cell_size // 2 - 3
        
        for row in range(self.board_size):
            for col in range(self.board_size):
                if self.board[row][col] != 0:
                    x = x_offset + col * self.cell_size
                    y = y_offset + row * self.cell_size
                    
                    shadow_offset = 2
                    if self.board[row][col] == PLAYER_BLACK:
                        shadow_color = QColor(0, 0, 0, 80)
                    else:
                        shadow_color = QColor(100, 100, 100, 60)
                    painter.setBrush(QBrush(shadow_color))
                    painter.drawEllipse(x - piece_radius + shadow_offset, 
                                        y - piece_radius + shadow_offset,
                                        piece_radius * 2, piece_radius * 2)
                    
                    if self.board[row][col] == PLAYER_BLACK:
                        gradient = QLinearGradient(
                            x - piece_radius, y - piece_radius,
                            x + piece_radius, y + piece_radius
                        )
                        gradient.setColorAt(0, QColor(80, 80, 80))
                        gradient.setColorAt(0.5, QColor(20, 20, 20))
                        gradient.setColorAt(1, QColor(0, 0, 0))
                        painter.setBrush(QBrush(gradient))
                    else:
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
                    
                    highlight_radius = piece_radius // 3
                    highlight_offset = piece_radius // 4
                    if self.board[row][col] == PLAYER_BLACK:
                        highlight_color = QColor(100, 100, 100, 120)
                    else:
                        highlight_color = QColor(255, 255, 255, 180)
                    painter.setBrush(QBrush(highlight_color))
                    painter.drawEllipse(
                        x - piece_radius + highlight_offset,
                        y - piece_radius + highlight_offset,
                        highlight_radius * 2, highlight_radius * 2
                    )
                    
                    if self.last_move == (row, col):
                        marker_radius = 5
                        painter.setPen(QPen(QColor(255, 0, 0), 2))
                        painter.setBrush(Qt.NoBrush)
                        painter.drawEllipse(x - marker_radius, y - marker_radius,
                                            marker_radius * 2, marker_radius * 2)


class GameReplayDialog(QDialog):
    """对局复盘播放对话框"""
    
    REPLAY_INTERVAL = 3000
    
    def __init__(self, game_record, parent=None):
        super().__init__(parent)
        self.game_record = game_record
        self.move_history = game_record.get('move_history', [])
        self.total_moves = len(self.move_history)
        self.current_move_index = -1
        self.is_playing = False
        self.timer = None
        
        self.board_data = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("对局复盘 - 自动播放")
        self.setMinimumSize(800, 700)
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
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 70px;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: white;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #4a90d9;
                border: 1px solid #357abd;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #357abd;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        info_group = QGroupBox("对局信息")
        info_layout = QVBoxLayout(info_group)
        
        player1_name = self.game_record.get('player1_name', '玩家1')
        player2_name = self.game_record.get('player2_name', '玩家2')
        winner_color = self.game_record.get('winner_color')
        resign_reason = self.game_record.get('resign_reason')
        
        winner_text = ""
        if winner_color == PLAYER_BLACK:
            winner_text = f"{player1_name}（黑棋）获胜"
        elif winner_color == PLAYER_WHITE:
            winner_text = f"{player2_name}（白棋）获胜"
        
        if resign_reason:
            reason_names = {
                'user': '对方认输',
                'timeout': '对方超时',
                'offline': '对方离线'
            }
            winner_text += f" ({reason_names.get(resign_reason, resign_reason)})"
        
        info_row1 = QHBoxLayout()
        self.player1_label = QLabel(f"⚫ 黑棋: {player1_name}")
        self.player1_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.player2_label = QLabel(f"⚪ 白棋: {player2_name}")
        self.player2_label.setFont(QFont("Arial", 12, QFont.Bold))
        info_row1.addWidget(self.player1_label)
        info_row1.addStretch()
        info_row1.addWidget(self.player2_label)
        info_layout.addLayout(info_row1)
        
        if winner_text:
            winner_label = QLabel(f"🏆 {winner_text}")
            winner_label.setFont(QFont("Arial", 12, QFont.Bold))
            winner_label.setStyleSheet("color: #4caf50;")
            winner_label.setAlignment(Qt.AlignCenter)
            info_layout.addWidget(winner_label)
        
        self.move_count_label = QLabel(f"总步数: {self.total_moves} | 当前: 第 0 步")
        self.move_count_label.setFont(QFont("Arial", 11))
        self.move_count_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.move_count_label)
        
        layout.addWidget(info_group)
        
        board_frame = QFrame()
        board_frame.setFrameStyle(QFrame.StyledPanel)
        board_frame.setStyleSheet("""
            QFrame {
                background-color: #e8f4fc;
                border: 2px solid #4a90d9;
                border-radius: 8px;
            }
        """)
        board_layout = QVBoxLayout(board_frame)
        
        self.board = ReplayBoardWidget()
        board_layout.addWidget(self.board)
        
        layout.addWidget(board_frame, 1)
        
        control_group = QGroupBox("播放控制")
        control_layout = QVBoxLayout(control_group)
        
        slider_layout = QHBoxLayout()
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setMinimum(0)
        self.progress_slider.setMaximum(self.total_moves)
        self.progress_slider.setValue(0)
        self.progress_slider.setEnabled(self.total_moves > 0)
        self.progress_slider.valueChanged.connect(self.on_slider_changed)
        slider_layout.addWidget(self.progress_slider)
        control_layout.addLayout(slider_layout)
        
        btn_layout = QHBoxLayout()
        
        self.restart_btn = QPushButton("⏮ 重新开始")
        self.restart_btn.clicked.connect(self.restart)
        self.restart_btn.setEnabled(self.total_moves > 0)
        
        self.prev_btn = QPushButton("◀ 上一步")
        self.prev_btn.clicked.connect(self.prev_step)
        self.prev_btn.setEnabled(False)
        
        self.play_btn = QPushButton("▶ 播放")
        self.play_btn.clicked.connect(self.toggle_play)
        self.play_btn.setEnabled(self.total_moves > 0)
        
        self.next_btn = QPushButton("下一步 ▶")
        self.next_btn.clicked.connect(self.next_step)
        self.next_btn.setEnabled(self.total_moves > 0)
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.close_replay)
        
        btn_layout.addWidget(self.restart_btn)
        btn_layout.addWidget(self.prev_btn)
        btn_layout.addWidget(self.play_btn)
        btn_layout.addWidget(self.next_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)
        
        control_layout.addLayout(btn_layout)
        
        speed_layout = QHBoxLayout()
        speed_label = QLabel("播放速度:")
        speed_label.setFont(QFont("Arial", 10))
        speed_layout.addWidget(speed_label)
        
        self.slow_btn = QPushButton("慢 (5s)")
        self.slow_btn.clicked.connect(lambda: self.set_speed(5000))
        self.slow_btn.setCheckable(True)
        
        self.normal_btn = QPushButton("正常 (3s)")
        self.normal_btn.clicked.connect(lambda: self.set_speed(3000))
        self.normal_btn.setCheckable(True)
        self.normal_btn.setChecked(True)
        
        self.fast_btn = QPushButton("快 (1s)")
        self.fast_btn.clicked.connect(lambda: self.set_speed(1000))
        self.fast_btn.setCheckable(True)
        
        self.replay_interval = self.REPLAY_INTERVAL
        
        speed_layout.addWidget(self.slow_btn)
        speed_layout.addWidget(self.normal_btn)
        speed_layout.addWidget(self.fast_btn)
        speed_layout.addStretch()
        
        control_layout.addLayout(speed_layout)
        
        layout.addWidget(control_group)
        
    def set_speed(self, interval):
        """设置播放速度"""
        self.replay_interval = interval
        
        self.slow_btn.setChecked(interval == 5000)
        self.normal_btn.setChecked(interval == 3000)
        self.fast_btn.setChecked(interval == 1000)
        
        if self.timer and self.timer.isActive():
            self.timer.setInterval(self.replay_interval)
    
    def toggle_play(self):
        """切换播放/暂停状态"""
        if self.is_playing:
            self.stop_play()
        else:
            self.start_play()
    
    def start_play(self):
        """开始自动播放"""
        if self.current_move_index >= self.total_moves - 1:
            self.restart()
            return
        
        self.is_playing = True
        self.play_btn.setText("⏸ 暂停")
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self.restart_btn.setEnabled(False)
        self.progress_slider.setEnabled(False)
        self.slow_btn.setEnabled(False)
        self.normal_btn.setEnabled(False)
        self.fast_btn.setEnabled(False)
        
        if self.timer is None:
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.on_timer)
        
        self.timer.start(self.replay_interval)
    
    def stop_play(self):
        """停止自动播放"""
        self.is_playing = False
        self.play_btn.setText("▶ 播放")
        
        if self.timer:
            self.timer.stop()
        
        self.prev_btn.setEnabled(self.current_move_index > 0)
        self.next_btn.setEnabled(self.current_move_index < self.total_moves - 1)
        self.restart_btn.setEnabled(True)
        self.progress_slider.setEnabled(True)
        self.slow_btn.setEnabled(True)
        self.normal_btn.setEnabled(True)
        self.fast_btn.setEnabled(True)
    
    def on_timer(self):
        """定时器回调 - 执行下一步"""
        if self.current_move_index < self.total_moves - 1:
            self.next_step()
        else:
            self.stop_play()
    
    def next_step(self):
        """下一步"""
        if self.current_move_index >= self.total_moves - 1:
            return
        
        self.current_move_index += 1
        
        row, col, player = self.move_history[self.current_move_index]
        self.board_data[row][col] = player
        
        self.board.set_board_state(self.board_data, (row, col))
        
        self.update_move_label()
        self.progress_slider.blockSignals(True)
        self.progress_slider.setValue(self.current_move_index + 1)
        self.progress_slider.blockSignals(False)
        
        if not self.is_playing:
            self.prev_btn.setEnabled(True)
            self.next_btn.setEnabled(self.current_move_index < self.total_moves - 1)
    
    def prev_step(self):
        """上一步"""
        if self.current_move_index <= 0:
            return
        
        row, col, player = self.move_history[self.current_move_index]
        self.board_data[row][col] = 0
        
        self.current_move_index -= 1
        
        if self.current_move_index >= 0:
            last_row, last_col, _ = self.move_history[self.current_move_index]
            self.board.set_board_state(self.board_data, (last_row, last_col))
        else:
            self.board.set_board_state(self.board_data, None)
        
        self.update_move_label()
        self.progress_slider.blockSignals(True)
        self.progress_slider.setValue(self.current_move_index + 1)
        self.progress_slider.blockSignals(False)
        
        self.prev_btn.setEnabled(self.current_move_index > 0)
        self.next_btn.setEnabled(True)
    
    def restart(self):
        """重新开始"""
        self.stop_play()
        
        self.current_move_index = -1
        self.board_data = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.board.clear_board()
        
        self.update_move_label()
        self.progress_slider.setValue(0)
        
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(self.total_moves > 0)
    
    def on_slider_changed(self, value):
        """滑块值改变"""
        if self.is_playing:
            return
        
        target_index = value - 1
        
        if target_index < self.current_move_index:
            while self.current_move_index > target_index:
                self.prev_step()
        elif target_index > self.current_move_index:
            while self.current_move_index < target_index:
                self.next_step()
    
    def update_move_label(self):
        """更新步数标签"""
        if self.current_move_index < 0:
            text = f"总步数: {self.total_moves} | 当前: 第 0 步（准备开始）"
        else:
            row, col, player = self.move_history[self.current_move_index]
            color_name = "黑棋" if player == PLAYER_BLACK else "白棋"
            text = f"总步数: {self.total_moves} | 当前: 第 {self.current_move_index + 1} 步 ({color_name}在({row},{col}))"
        
        self.move_count_label.setText(text)
    
    def close_replay(self):
        """关闭复盘"""
        self.stop_play()
        self.reject()
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.stop_play()
        event.accept()
