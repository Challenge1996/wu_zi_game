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

from constants import SERVER_URL
from ui import (
    BoardWidget,
    TimerWidget,
    GameSignals,
    ChallengeDialog,
    CoinTossDialog,
    ColorChoiceDialog,
    PlayerListDialog,
    UndoRequestDialog,
    ChallengeListDialog
)

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
        
        # 弹窗状态跟踪（避免重复弹窗）
        self.shown_undo_request_id = None  # 已显示的悔棋请求ID
        self.game_over_shown = False  # 游戏结束弹窗是否已显示
        self.pending_undo_request_id = None  # 当前待处理的悔棋请求ID
        
        # 认输相关
        self.last_resign_reason = None  # 最后一次认输原因
        self.last_move_count = 0  # 上一次的落子数，用于检测落子变化
        
        # 轮询线程
        self.polling_thread = None
        self.running = False
        
        self.init_ui()
        self.setup_menu()
        self.setup_status_bar()
        
        # 必须在init_ui之后连接信号，因为timer_widget等控件在init_ui中创建
        self.setup_signal_connections()
        
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
        
        # 第三排按钮
        row3_layout = QHBoxLayout()
        self.resign_btn = QPushButton("认输")
        self.resign_btn.clicked.connect(self.request_resign)
        self.resign_btn.setEnabled(False)
        self.resign_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        
        row3_layout.addStretch()
        row3_layout.addWidget(self.resign_btn)
        row3_layout.addStretch()
        
        game_layout.addLayout(row1_layout)
        game_layout.addLayout(row2_layout)
        game_layout.addLayout(row3_layout)
        
        right_layout.addWidget(game_group)
        
        # 计时器
        self.timer_widget = TimerWidget()
        right_layout.addWidget(self.timer_widget)
        
        # 聊天系统
        chat_group = QGroupBox("聊天")
        chat_layout = QVBoxLayout(chat_group)
        
        self.chat_text = QTextEdit()
        self.chat_text.setReadOnly(True)
        self.chat_text.setMinimumHeight(120)
        self.chat_text.setStyleSheet("""
            QTextEdit {
                background-color: #fafafa;
                border: 2px solid #cccccc;
                border-radius: 5px;
                font-family: Arial, sans-serif;
                font-size: 12px;
            }
        """)
        
        chat_layout.addWidget(self.chat_text)
        
        # 聊天输入区域
        input_layout = QHBoxLayout()
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("输入消息...")
        self.chat_input.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 2px solid #cccccc;
                border-radius: 5px;
            }
            QLineEdit:focus {
                border-color: #4a90d9;
            }
        """)
        self.chat_input.returnPressed.connect(self.send_chat_message)
        
        self.send_btn = QPushButton("发送")
        self.send_btn.setMinimumWidth(60)
        self.send_btn.clicked.connect(self.send_chat_message)
        self.send_btn.setEnabled(False)
        
        input_layout.addWidget(self.chat_input, 3)
        input_layout.addWidget(self.send_btn, 1)
        
        chat_layout.addLayout(input_layout)
        right_layout.addWidget(chat_group)
        
        self.last_chat_message_id = None
        self.chat_messages = []
        
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
        self.signals.start_game_timer.connect(self.timer_widget.start_timer)
        self.signals.stop_game_timer.connect(self.timer_widget.stop_timer)
        self.signals.reset_timer.connect(self.timer_widget.reset_timer)
        self.signals.switch_timer_player.connect(self.timer_widget.switch_player)
        
        # 聊天相关信号
        self.signals.chat_message_received.connect(self.on_chat_message_received)
        self.signals.chat_messages_updated.connect(self.on_chat_messages_updated)
        
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
        
        # 悔棋请求相关信号
        self.signals.undo_request_received.connect(self.on_undo_request_received)
        self.signals.undo_request_accepted.connect(self.on_undo_request_accepted)
        self.signals.undo_request_declined.connect(self.on_undo_request_declined)
        self.signals.undo_request_expired.connect(self.on_undo_request_expired)
        self.signals.show_undo_request_dialog.connect(self._show_undo_request_dialog)
        
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
        """显示玩家列表并可发起挑战"""
        if not self.player_id:
            QMessageBox.warning(self, "提示", "请先登录！")
            return
            
        def get_players():
            success, result = self._request('GET', '/api/player/list')
            if success and result.get('success'):
                players = result.get('players', [])
                
                # 过滤掉自己
                available_players = [
                    p for p in players 
                    if p.get('id') != self.player_id
                ]
                
                if not available_players:
                    self.signals.message_received.emit("没有可用的在线玩家")
                    return
                
                # 通过信号在主线程显示挑战对话框
                self.signals.player_list_updated.emit(available_players)
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
                        loser_id = resolve_result.get('loser_id')
                        winner_choice = resolve_result.get('winner_choice')
                        loser_choice = resolve_result.get('loser_choice')
                        winner_color = resolve_result.get('winner_color', 1)
                        loser_color = resolve_result.get('loser_color', 2)
                        
                        self.signals.message_received.emit(f"✓ 硬币结果: {coin_result}")
                        
                        is_my_win = winner_id == self.player_id
                        
                        if is_my_win:
                            # 我赢了，执黑棋
                            self.my_color = winner_color  # 1 = 黑棋
                            self.signals.message_received.emit(f"🎉 恭喜！您选择了{winner_choice}，猜对了！您执黑棋（先手）。")
                            self.signals.update_my_color.emit(self.my_color)
                        else:
                            # 我输了，执白棋
                            self.my_color = loser_color  # 2 = 白棋
                            self.signals.message_received.emit(f"对方选择了{winner_choice}，猜对了。您执白棋（后手）。")
                            self.signals.update_my_color.emit(self.my_color)
                        
                        # 游戏正式开始
                        self.signals.message_received.emit("✓ 游戏开始！黑棋先下。")
                        
                        # 更新游戏状态
                        self.signals.update_game_phase.emit("playing")
                        
                        # 启用游戏控件
                        self.signals.enable_game_controls.emit()
                        
                        # 启动游戏计时器（从黑棋开始）
                        self.signals.start_game_timer.emit(1)
                        
                        # 更新回合显示
                        self.update_turn_display()
                    else:
                        self.signals.error_occurred.emit(f"解析硬币结果失败: {resolve_result.get('message', '未知错误')}")
                else:
                    # 等待对方选择
                    self.signals.message_received.emit("✓ 硬币选择已提交")
                    self.signals.message_received.emit("等待对方选择...")
                    
                    # 通过信号禁用按钮
                    self.signals.disable_coin_button.emit()
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
        
        # 显示玩家列表对话框（只读，用于查看）
        dialog = PlayerListDialog(players, self.player_id, self)
        dialog.exec_()
    
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
        self.resign_btn.setEnabled(False)
        # 重置游戏结束弹窗状态
        self.game_over_shown = False
        # 重置悔棋请求相关状态
        self.shown_undo_request_id = None
        self.pending_undo_request_id = None
        # 重置认输相关状态
        self.last_resign_reason = None
        self.last_move_count = 0
    
    def _enable_game_controls(self):
        """启用游戏控件（主线程）"""
        self.board.set_click_enabled(True)
        self.undo_btn.setEnabled(True)
        self.reset_btn.setEnabled(True)
        self.coin_btn.setEnabled(False)
        self.resign_btn.setEnabled(True)
        
        if self.my_color:
            self.timer_widget.set_my_color(self.my_color)
    
    def _disable_game_controls(self):
        """禁用游戏控件（主线程）"""
        self.board.set_click_enabled(False)
        self.undo_btn.setEnabled(False)
        self.reset_btn.setEnabled(False)
        self.resign_btn.setEnabled(False)
    
    # ==================== 悔棋请求相关槽函数 ====================
    
    def on_undo_request_received(self, undo_request):
        """收到悔棋请求"""
        requester_name = undo_request.get('requester_name', '对手')
        self.append_log(f"📢 {requester_name} 向您请求悔棋！")
        
        self.signals.show_undo_request_dialog.emit(undo_request)
    
    def on_undo_request_accepted(self, data):
        """悔棋请求被接受"""
        self.append_log("✓ 悔棋成功！对手已同意悔棋。")
        
        game_state = data.get('game_state', {})
        if game_state:
            self.signals.room_updated.emit({'game_state': game_state})
        
        self.signals.enable_undo_button.emit()
        self.signals.enable_reset_button.emit()
    
    def on_undo_request_declined(self, data):
        """悔棋请求被拒绝"""
        self.append_log("✗ 对手拒绝了您的悔棋请求。")
        self.signals.enable_undo_button.emit()
        self.signals.enable_reset_button.emit()
    
    def on_undo_request_expired(self, data):
        """悔棋请求过期"""
        self.append_log("⏰ 悔棋请求已过期，对手未回应。")
        self.signals.enable_undo_button.emit()
        self.signals.enable_reset_button.emit()
    
    def _show_undo_request_dialog(self, undo_request):
        """显示悔棋请求对话框（主线程）"""
        dialog = UndoRequestDialog(undo_request, self)
        
        if dialog.exec_() == QDialog.Accepted:
            accept = dialog.get_result()
            if accept is not None:
                self.respond_undo_request(accept, undo_request.get('id'))
    
    def respond_undo_request(self, accept, undo_request_id=None):
        """响应悔棋请求"""
        self.append_log(f"正在{'同意' if accept else '拒绝'}悔棋请求...")
        
        def do_respond():
            data = {
                'player_id': self.player_id,
                'room_id': self.current_room_id,
                'accept': accept
            }
            
            success, result = self._request('POST', '/api/game/undo/respond', data)
            
            if success and result.get('success'):
                undo_accepted = result.get('undo_accepted', False)
                
                if undo_accepted:
                    self.signals.message_received.emit("✓ 已同意悔棋请求")
                    
                    game_state = result.get('game_state', {})
                    if game_state:
                        self.signals.room_updated.emit({'game_state': game_state})
                else:
                    self.signals.message_received.emit("✓ 已拒绝悔棋请求")
            else:
                self.signals.error_occurred.emit(f"响应悔棋请求失败: {result.get('message', '未知错误')}")
        
        thread = threading.Thread(target=do_respond, daemon=True)
        thread.start()
    
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
                
                # 找到另一个玩家
                other_player_id = None
                
                # 优先使用 challenger_id 和 challenged_id（新字段）
                challenger_id = room.get('challenger_id')
                challenged_id = room.get('challenged_id')
                
                if challenger_id and challenged_id:
                    if self.player_id == challenger_id:
                        other_player_id = challenged_id
                    elif self.player_id == challenged_id:
                        other_player_id = challenger_id
                else:
                    # 向后兼容：使用 player1 和 player2
                    player1 = room.get('player1')
                    player2 = room.get('player2')
                    
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
        """请求悔棋（发起悔棋请求，需要对手同意）"""
        if not self.current_room_id:
            QMessageBox.warning(self, "提示", "当前没有游戏！")
            return
        
        reply = QMessageBox.question(
            self, "确认悔棋",
            "确定要向对手发起悔棋请求吗？\n对手需要同意才能悔棋。",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        self.append_log("正在向对手发起悔棋请求...")
        
        def do_request_undo():
            data = {
                'player_id': self.player_id,
                'room_id': self.current_room_id
            }
            
            success, result = self._request('POST', '/api/game/undo/request', data)
            if success and result.get('success'):
                self.signals.message_received.emit("✓ 悔棋请求已发送，等待对手同意...")
                self.signals.message_received.emit("请等待对手回应...")
                
                self.signals.disable_undo_button.emit()
                self.signals.disable_reset_button.emit()
            else:
                self.signals.error_occurred.emit(f"发起悔棋请求失败: {result.get('message', '未知错误')}")
        
        thread = threading.Thread(target=do_request_undo, daemon=True)
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
    
    def request_resign(self):
        """请求认输"""
        if not self.current_room_id:
            QMessageBox.warning(self, "提示", "当前没有游戏！")
            return
        
        reply = QMessageBox.question(
            self, "确认认输",
            "确定要认输吗？这将直接判负，对手获胜。\n此操作不可撤销！",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        self.append_log("正在认输...")
        
        def do_resign():
            data = {
                'player_id': self.player_id,
                'room_id': self.current_room_id
            }
            
            success, result = self._request('POST', '/api/game/resign', data)
            if success and result.get('success'):
                self.signals.message_received.emit("✓ 认输成功")
                self.signals.message_received.emit(result.get('message', '您已认输'))
                
                winner = result.get('winner')
                if winner:
                    self.signals.game_over.emit(winner)
            else:
                self.signals.error_occurred.emit(f"认输失败: {result.get('message', '未知错误')}")
        
        thread = threading.Thread(target=do_resign, daemon=True)
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
                        
                        # 检查我发起的挑战是否已被接受
                        if not self.current_room_id:
                            accepted = [c for c in challenges
                                      if c.get('status') == 'accepted'
                                      and c.get('is_my_challenge')
                                      and c.get('room_id')]
                            if accepted:
                                # 挑战已被接受，获取room_id
                                challenge = accepted[0]
                                room_id = challenge.get('room_id')
                                self.current_room_id = room_id
                                
                                self.signals.message_received.emit("✓ 您的挑战已被接受！")
                                self.signals.message_received.emit(f"  房间ID: {room_id}")
                                self.signals.message_received.emit("进入抛硬币阶段，请选择硬币结果")
                                
                                # 启用硬币按钮
                                self.signals.enable_coin_button.emit()
                                self.signals.update_game_phase.emit("coin_toss")
                
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
        old_phase = self.game_phase
        
        if new_phase != self.game_phase:
            self.game_phase = new_phase
            
            # 当游戏阶段从 finished 变为非 finished 时，重置游戏结束弹窗状态
            if old_phase == 'finished' and new_phase != 'finished':
                self.game_over_shown = False
                self.shown_undo_request_id = None
                self.pending_undo_request_id = None
                self.last_resign_reason = None
                self.last_move_count = 0
                self.timer_widget.stop_countdown()
            
            if new_phase == 'playing':
                self.status_label.setText("游戏状态: 游戏进行中")
                self.board.set_click_enabled(True)
                self.undo_btn.setEnabled(True)
                self.reset_btn.setEnabled(True)
                self.coin_btn.setEnabled(False)
                self.resign_btn.setEnabled(True)
                
                if self.my_color:
                    self.timer_widget.set_my_color(self.my_color)
                
                self.send_btn.setEnabled(True)
                
                if not self.timer_widget.is_running:
                    self.timer_widget.start_timer(game_state.get('current_player', 1))
                    
            elif new_phase == 'coin_toss':
                self.status_label.setText("游戏状态: 抛硬币阶段")
                self.board.set_click_enabled(False)
                
            elif new_phase == 'waiting':
                self.status_label.setText("游戏状态: 等待开始")
                self.board.set_click_enabled(False)
                
            elif new_phase == 'finished':
                self.status_label.setText("游戏状态: 已结束")
                self.timer_widget.stop_countdown()
        
        # 游戏进行中时更新倒计时
        if new_phase == 'playing':
            current_player = game_state.get('current_player', 1)
            time_since_last_move = game_state.get('time_since_last_move', 0)
            move_count = game_state.get('move_count', 0)
            
            # 检测落子数变化，重置倒计时
            if move_count != self.last_move_count:
                self.last_move_count = move_count
                # 落子变化，重置倒计时
                self.timer_widget.start_countdown(current_player)
            else:
                # 继续倒计时，计算剩余时间
                from constants import MOVE_TIMEOUT_SECONDS
                remaining = max(0, MOVE_TIMEOUT_SECONDS - time_since_last_move)
                # 只有当倒计时没在运行时才启动，或者同步时间
                if not self.timer_widget.countdown_running:
                    self.timer_widget.start_countdown(current_player, remaining)
                else:
                    # 同步显示
                    if self.timer_widget.current_player != current_player:
                        self.timer_widget.start_countdown(current_player, remaining)
        
        # 更新回合显示
        self.update_turn_display()
        
        # 检查游戏是否结束（只弹窗一次）
        if game_state.get('game_over') and not self.game_over_shown:
            winner = game_state.get('winner')
            self.last_resign_reason = game_state.get('resign_reason')
            self.game_over_shown = True  # 标记已显示游戏结束弹窗
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
                self.timer_widget.set_my_color(self.my_color)
        
        # 处理悔棋请求
        undo_request = room.get('undo_request')
        if undo_request:
            is_requested_to_me = undo_request.get('is_requested_to_me', False)
            is_my_request = undo_request.get('is_my_request', False)
            status = undo_request.get('status')
            undo_request_id = undo_request.get('id')
            
            # 我是被请求方，且请求状态为 pending
            if is_requested_to_me and status == 'pending':
                # 只有当请求ID与已显示的不同时才触发弹窗（避免重复弹窗）
                if undo_request_id != self.shown_undo_request_id:
                    self.shown_undo_request_id = undo_request_id
                    self.pending_undo_request_id = undo_request_id
                    self.signals.undo_request_received.emit(undo_request)
            
            # 我是发起方，检查请求状态变化
            elif is_my_request:
                # 如果请求已被处理（accepted/declined/expired），且之前是 pending 状态
                if status in ['accepted', 'declined', 'expired']:
                    if self.pending_undo_request_id == undo_request_id:
                        # 重置待处理请求状态
                        self.pending_undo_request_id = None
                        # 触发对应信号
                        if status == 'accepted':
                            self.signals.undo_request_accepted.emit(undo_request)
                        elif status == 'declined':
                            self.signals.undo_request_declined.emit(undo_request)
                        elif status == 'expired':
                            self.signals.undo_request_expired.emit(undo_request)
        
        # 如果没有悔棋请求了，重置已显示的请求ID
        else:
            self.shown_undo_request_id = None
        
        # 处理聊天消息
        chat_messages = room.get('chat_messages', [])
        if chat_messages:
            self.signals.chat_messages_updated.emit(chat_messages)
                    
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
                self.board.set_click_enabled(False)  # 禁用棋盘点击
                
    def on_game_over(self, winner):
        """游戏结束"""
        self.timer_widget.stop_timer()
        self.timer_widget.stop_countdown()
        self.board.set_click_enabled(False)
        self.game_phase = "finished"
        self.status_label.setText("游戏状态: 已结束")
        
        self.undo_btn.setEnabled(False)
        self.reset_btn.setEnabled(False)
        self.resign_btn.setEnabled(False)
        
        winner_name = "黑棋" if winner == 1 else "白棋"
        is_my_win = (winner == self.my_color)
        
        resign_reason = self.last_resign_reason
        
        reason_text = ""
        log_suffix = ""
        
        if resign_reason == 'user':
            if is_my_win:
                reason_text = "对手主动认输"
            else:
                reason_text = "您主动认输"
            log_suffix = "（认输）"
        elif resign_reason == 'timeout':
            if is_my_win:
                reason_text = "对手超时未下子"
            else:
                reason_text = "您超时未下子"
            log_suffix = "（超时）"
        elif resign_reason == 'offline':
            if is_my_win:
                reason_text = "对手已离线"
            else:
                reason_text = "您已离线"
            log_suffix = "（离线）"
        
        if is_my_win:
            if reason_text:
                message = f"🎉 恭喜！您获胜了！\n\n{reason_text}\n{winner_name}获胜！"
            else:
                message = f"🎉 恭喜！您获胜了！\n\n{winner_name}获胜！"
        else:
            if reason_text:
                message = f"😢 您输了...\n\n{reason_text}\n{winner_name}获胜！"
            else:
                message = f"😢 您输了...\n\n{winner_name}获胜！"
            
        self.append_log(f"★ 游戏结束！{winner_name}获胜！{log_suffix} ★")
        
        QMessageBox.information(self, "游戏结束", message)
        
    # ==================== 聊天相关方法 ====================
    
    def send_chat_message(self):
        """发送聊天消息"""
        message = self.chat_input.text().strip()
        if not message:
            return
        
        if not self.current_room_id:
            QMessageBox.warning(self, "提示", "当前没有游戏房间，无法发送消息！")
            return
        
        self.chat_input.clear()
        
        def do_send():
            data = {
                'player_id': self.player_id,
                'room_id': self.current_room_id,
                'content': message
            }
            
            success, result = self._request('POST', '/api/chat/send', data)
            if success and result.get('success'):
                chat_message = result.get('chat_message', {})
                chat_message['is_my_message'] = True
                self.signals.chat_message_received.emit(chat_message)
            else:
                self.append_log(f"发送消息失败: {result.get('message', '未知错误')}")
        
        thread = threading.Thread(target=do_send, daemon=True)
        thread.start()
    
    def on_chat_message_received(self, message):
        """收到聊天消息"""
        self.append_chat_message(message)
    
    def on_chat_messages_updated(self, messages):
        """聊天消息列表更新"""
        for msg in messages:
            if msg.get('id') not in [m.get('id') for m in self.chat_messages]:
                self.chat_messages.append(msg)
                self.append_chat_message(msg)
        
        if messages:
            self.last_chat_message_id = messages[-1].get('id')
    
    def append_chat_message(self, message):
        """添加聊天消息到显示"""
        timestamp = datetime.fromtimestamp(message.get('timestamp', datetime.now().timestamp())).strftime("%H:%M:%S")
        msg_type = message.get('type', 'text')
        is_my = message.get('is_my_message', False)
        player_name = message.get('player_name', '系统')
        content = message.get('content', '')
        
        formatted_msg = ""
        
        if msg_type == 'system':
            formatted_msg = f'<div style="color: #888888; font-style: italic; text-align: center; margin: 5px 0;">' \
                           f'[{timestamp}] {content}</div>'
        elif msg_type == 'move':
            formatted_msg = f'<div style="color: #6666cc; margin: 3px 0;">' \
                           f'<span style="font-weight: bold;">[系统]</span> ' \
                           f'<span style="color: #999999;">[{timestamp}]</span><br/>' \
                           f'&nbsp;&nbsp;{content}</div>'
        elif msg_type == 'undo':
            formatted_msg = f'<div style="color: #cc6666; margin: 3px 0;">' \
                           f'<span style="font-weight: bold;">[系统]</span> ' \
                           f'<span style="color: #999999;">[{timestamp}]</span><br/>' \
                           f'&nbsp;&nbsp;{content}</div>'
        elif msg_type == 'resign':
            formatted_msg = f'<div style="color: #cc3333; margin: 3px 0;">' \
                           f'<span style="font-weight: bold;">[系统]</span> ' \
                           f'<span style="color: #999999;">[{timestamp}]</span><br/>' \
                           f'&nbsp;&nbsp;{content}</div>'
        else:
            if is_my:
                formatted_msg = f'<div style="text-align: right; margin: 5px 0;">' \
                               f'<span style="color: #999999; font-size: 10px;">[{timestamp}]</span> ' \
                               f'<span style="font-weight: bold; color: #4a90d9;">我</span><br/>' \
                               f'<span style="background-color: #4a90d9; color: white; padding: 5px 10px; ' \
                               f'border-radius: 10px; display: inline-block; margin-top: 2px; ' \
                               f'max-width: 80%; word-wrap: break-word;">{content}</span></div>'
            else:
                formatted_msg = f'<div style="text-align: left; margin: 5px 0;">' \
                               f'<span style="font-weight: bold; color: #555555;">{player_name}</span> ' \
                               f'<span style="color: #999999; font-size: 10px;">[{timestamp}]</span><br/>' \
                               f'<span style="background-color: #e8e8e8; color: #333333; padding: 5px 10px; ' \
                               f'border-radius: 10px; display: inline-block; margin-top: 2px; ' \
                               f'max-width: 80%; word-wrap: break-word;">{content}</span></div>'
        
        cursor = self.chat_text.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertHtml(formatted_msg + '<br/>')
        
        scrollbar = self.chat_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    # ==================== 辅助方法 ====================
    
    def append_log(self, message):
        """添加日志消息（同时显示为系统聊天消息）"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        chat_msg = {
            'id': f'log_{int(datetime.now().timestamp() * 1000000)}',
            'type': 'system',
            'content': message,
            'timestamp': datetime.now().timestamp(),
            'is_my_message': False
        }
        self.append_chat_message(chat_msg)
        
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