from PyQt5.QtCore import pyqtSignal, QObject


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
