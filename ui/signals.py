#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏信号类 - 用于线程间通信
"""

from PyQt5.QtCore import pyqtSignal, QObject


class GameSignals(QObject):
    """游戏信号类，用于线程间通信"""
    room_updated = pyqtSignal(dict)
    player_list_updated = pyqtSignal(list)
    challenge_list_updated = pyqtSignal(list)
    message_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    game_started = pyqtSignal()
    game_over = pyqtSignal(int)
    coin_toss_phase = pyqtSignal()
    coin_result = pyqtSignal(str, bool)
    turn_changed = pyqtSignal(int)
    show_color_choice = pyqtSignal()
    
    start_game_timer = pyqtSignal(int)
    stop_game_timer = pyqtSignal()
    reset_timer = pyqtSignal()
    switch_timer_player = pyqtSignal()
    
    chat_message_received = pyqtSignal(dict)
    chat_messages_updated = pyqtSignal(list)
    
    disable_coin_button = pyqtSignal()
    enable_coin_button = pyqtSignal()
    disable_undo_button = pyqtSignal()
    enable_undo_button = pyqtSignal()
    disable_reset_button = pyqtSignal()
    enable_reset_button = pyqtSignal()
    
    enable_board_click = pyqtSignal()
    disable_board_click = pyqtSignal()
    
    update_game_phase = pyqtSignal(str)
    update_status_label = pyqtSignal(str)
    
    coin_toss_completed = pyqtSignal(dict)
    
    color_chosen = pyqtSignal(int)
    
    show_challenge_received = pyqtSignal(dict)
    show_players_for_challenge = pyqtSignal(list)
    
    show_player_list_dialog = pyqtSignal(list)
    show_challenge_list_dialog = pyqtSignal(list)
    
    game_reset = pyqtSignal()
    update_my_color = pyqtSignal(int)
    enable_game_controls = pyqtSignal()
    disable_game_controls = pyqtSignal()
    
    undo_request_received = pyqtSignal(dict)
    undo_request_accepted = pyqtSignal(dict)
    undo_request_declined = pyqtSignal(dict)
    undo_request_expired = pyqtSignal(dict)
    show_undo_request_dialog = pyqtSignal(dict)
    
    resign_received = pyqtSignal(dict)
    resign_accepted = pyqtSignal(dict)
    show_resign_confirmation = pyqtSignal()
    update_countdown = pyqtSignal(int, int)
    timeout_warning = pyqtSignal(int)
