from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QLinearGradient
)
from constants import BOARD_SIZE, PLAYER_BLACK, PLAYER_WHITE


class BoardWidget(QWidget):
    """15x15棋盘控件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.board_size = BOARD_SIZE
        self.cell_size = 35
        self.margin = 20
        self.board = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.current_player = PLAYER_BLACK
        self.last_move = None
        self.hover_pos = None
        self.click_enabled = True
        
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
                                star_radius * 2, star_radius * 2)
        
        piece_radius = self.cell_size // 2 - 2
        
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
                        marker_radius = 4
                        painter.setPen(QPen(QColor(255, 0, 0), 2))
                        painter.setBrush(Qt.NoBrush)
                        painter.drawEllipse(x - marker_radius, y - marker_radius,
                                            marker_radius * 2, marker_radius * 2)
        
        if self.hover_pos and self.click_enabled:
            row, col = self.hover_pos
            if 0 <= row < self.board_size and 0 <= col < self.board_size:
                if self.board[row][col] == 0:
                    x = x_offset + col * self.cell_size
                    y = y_offset + row * self.cell_size
                    
                    if self.current_player == PLAYER_BLACK:
                        hover_color = QColor(0, 0, 0, 80)
                    else:
                        hover_color = QColor(255, 255, 255, 120)
                    
                    painter.setBrush(QBrush(hover_color))
                    painter.setPen(Qt.NoPen)
                    painter.drawEllipse(x - piece_radius, y - piece_radius,
                                        piece_radius * 2, piece_radius * 2)
        
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if not self.click_enabled:
            return
            
        total_size = self.cell_size * (self.board_size - 1)
        x_offset = (self.width() - total_size) // 2
        y_offset = (self.height() - total_size) // 2
        
        x = event.pos().x() - x_offset
        y = event.pos().y() - y_offset
        
        col = round(x / self.cell_size)
        row = round(y / self.cell_size)
        
        if 0 <= row < self.board_size and 0 <= col < self.board_size:
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
                parent = self.parent()
                while parent:
                    if hasattr(parent, 'on_board_clicked'):
                        parent.on_board_clicked(row, col)
                        break
                    parent = parent.parent()
