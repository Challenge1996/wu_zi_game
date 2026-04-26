#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
五子棋游戏核心逻辑
"""

import time
import random
from constants import (
    BOARD_SIZE,
    PLAYER_BLACK,
    PLAYER_WHITE,
    GAME_PHASE_WAITING,
    GAME_PHASE_COIN_TOSS,
    GAME_PHASE_PLAYING,
    GAME_PHASE_FINISHED,
    COIN_HEAD,
    COIN_TAIL
)


class WuziqiGame:
    def __init__(self):
        self.board_size = BOARD_SIZE
        self.board = None
        self.current_player = PLAYER_BLACK
        self.game_over = False
        self.winner = None
        self.move_history = []
        self.start_time = None
        self.game_phase = GAME_PHASE_WAITING
        self.players = {PLAYER_BLACK: None, PLAYER_WHITE: None}
        self.player_choices = {}
        self.coin_result = None
        self.last_move_time = None
        self.resign_reason = None
        self.initialize_board()

    def initialize_board(self):
        self.board = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.current_player = PLAYER_BLACK
        self.game_over = False
        self.winner = None
        self.move_history = []
        self.start_time = None
        self.game_phase = GAME_PHASE_WAITING
        self.players = {PLAYER_BLACK: None, PLAYER_WHITE: None}
        self.player_choices = {}
        self.coin_result = None
        self.last_move_time = None
        self.resign_reason = None

    def check_win(self, row, col, player):
        """检查玩家是否获胜"""
        directions = [
            (0, 1),
            (1, 0),
            (1, 1),
            (1, -1)
        ]
        
        for dr, dc in directions:
            count = 1
            r, c = row + dr, col + dc
            while 0 <= r < self.board_size and 0 <= c < self.board_size and self.board[r][c] == player:
                count += 1
                r, c = r + dr, c + dc
            r, c = row - dr, col - dc
            while 0 <= r < self.board_size and 0 <= c < self.board_size and self.board[r][c] == player:
                count += 1
                r, c = r - dr, c - dc
            if count >= 5:
                return True
        return False

    def place_piece(self, row, col, player):
        if player not in [PLAYER_BLACK, PLAYER_WHITE]:
            return False, "无效的玩家编号"
        
        if self.game_over:
            return False, "游戏已结束"
        
        if self.game_phase != GAME_PHASE_PLAYING:
            return False, "游戏尚未开始"
        
        if player != self.current_player:
            return False, "不是当前玩家的回合"
        
        if row < 0 or row >= self.board_size:
            return False, "行号超出范围"
        if col < 0 or col >= self.board_size:
            return False, "列号超出范围"
        if self.board[row][col] != 0:
            return False, "该位置已有棋子"
        
        self.move_history.append((row, col, player))
        self.board[row][col] = player
        self.last_move_time = time.time()
        
        if self.check_win(row, col, player):
            self.game_over = True
            self.winner = player
            self.game_phase = GAME_PHASE_FINISHED
            return True, f"恭喜！玩家{'黑棋' if player == PLAYER_BLACK else '白棋'}获胜！"
        
        self.current_player = PLAYER_WHITE if self.current_player == PLAYER_BLACK else PLAYER_BLACK
        return True, "落子成功"

    def clear_board(self):
        self.initialize_board()

    def undo_move(self):
        """悔棋功能"""
        if len(self.move_history) == 0:
            return False, "没有可悔的棋"
        
        row, col, player = self.move_history.pop()
        self.board[row][col] = 0
        self.current_player = player
        
        if self.game_over:
            self.game_over = False
            self.winner = None
            self.game_phase = GAME_PHASE_PLAYING
        
        return True, f"已悔棋：行={row}, 列={col}, 玩家={'黑棋' if player == PLAYER_BLACK else '白棋'}"

    def resign(self, player_color, reason='user'):
        """玩家认输
        Args:
            player_color: 认输的玩家颜色
            reason: 认输原因 ('user', 'timeout', 'offline')
        Returns:
            (success, message)
        """
        if self.game_over:
            return False, "游戏已结束"
        
        if self.game_phase != GAME_PHASE_PLAYING:
            return False, "游戏尚未开始"
        
        if player_color not in [PLAYER_BLACK, PLAYER_WHITE]:
            return False, "无效的玩家颜色"
        
        self.game_over = True
        self.game_phase = GAME_PHASE_FINISHED
        self.resign_reason = reason
        
        if player_color == PLAYER_BLACK:
            self.winner = PLAYER_WHITE
            loser_name = '黑棋'
            winner_name = '白棋'
        else:
            self.winner = PLAYER_BLACK
            loser_name = '白棋'
            winner_name = '黑棋'
        
        reason_message = {
            'user': f'{loser_name}认输，{winner_name}获胜！',
            'timeout': f'{loser_name}超时未下子，{winner_name}获胜！',
            'offline': f'{loser_name}离线，{winner_name}获胜！'
        }
        
        return True, reason_message.get(reason, f'{loser_name}认输，{winner_name}获胜！')

    def get_opponent_color(self, player_color):
        """获取对手颜色"""
        if player_color == PLAYER_BLACK:
            return PLAYER_WHITE
        elif player_color == PLAYER_WHITE:
            return PLAYER_BLACK
        return None

    def get_time_since_last_move(self):
        """获取距上次落子的时间（秒）"""
        if self.last_move_time is None:
            if self.start_time is not None:
                return int(time.time() - self.start_time)
            return 0
        return int(time.time() - self.last_move_time)

    def get_resign_reason(self):
        """获取认输原因"""
        return self.resign_reason

    def start_game(self):
        """开始游戏"""
        if self.game_phase == GAME_PHASE_PLAYING:
            return False, "游戏已经在进行中"
        
        self.start_time = time.time()
        self.game_phase = GAME_PHASE_PLAYING
        return True, "游戏开始！"

    def get_game_time(self):
        """获取游戏时间（秒）"""
        if self.start_time is None:
            return 0
        return int(time.time() - self.start_time)

    def is_game_over(self):
        """检查游戏是否结束"""
        return self.game_over

    def get_winner(self):
        """获取获胜者"""
        return self.winner

    def get_current_player(self):
        """获取当前玩家"""
        return self.current_player

    def get_game_phase(self):
        """获取游戏阶段"""
        return self.game_phase

    def start_coin_toss(self):
        """开始抛硬币阶段"""
        if self.game_phase != GAME_PHASE_WAITING:
            return False, "游戏阶段不正确，无法开始抛硬币"
        
        self.game_phase = GAME_PHASE_COIN_TOSS
        self.coin_result = random.randint(COIN_HEAD, COIN_TAIL)
        return True, "抛硬币阶段开始，请玩家猜测硬币结果"

    def player_make_choice(self, player_id, choice):
        """玩家进行硬币猜测"""
        if self.game_phase != GAME_PHASE_COIN_TOSS:
            return False, "不在抛硬币阶段"
        
        if choice not in [COIN_HEAD, COIN_TAIL]:
            return False, "无效的猜测，只能选择0(正面)或1(反面)"
        
        if player_id in self.player_choices:
            return False, "您已经进行了猜测"
        
        self.player_choices[player_id] = choice
        choice_name = "正面" if choice == COIN_HEAD else "反面"
        
        all_players = [p for p in self.players.values() if p is not None]
        
        if len(all_players) == 2 and len(self.player_choices) == 1:
            other_player = None
            for p in all_players:
                if p != player_id:
                    other_player = p
                    break
            
            if other_player:
                other_choice = 1 - choice
                self.player_choices[other_player] = other_choice
                other_choice_name = "正面" if other_choice == COIN_HEAD else "反面"
                
                return True, {
                    "auto_assigned": True,
                    "player_choice": choice_name,
                    "other_player_choice": other_choice_name,
                    "other_player_id": other_player,
                    "message": f"您选择了{choice_name}，系统已自动为对方分配{other_choice_name}"
                }
        
        return True, f"玩家 {player_id} 猜测：{choice_name}"

    def resolve_coin_toss(self):
        """解决抛硬币结果"""
        if self.game_phase != GAME_PHASE_COIN_TOSS:
            return False, "不在抛硬币阶段"
        
        all_players = [p for p in self.players.values() if p is not None]
        if len(all_players) == 2 and len(self.player_choices) == 1:
            player_id = list(self.player_choices.keys())[0]
            choice = self.player_choices[player_id]
            
            other_player = None
            for p in all_players:
                if p != player_id:
                    other_player = p
                    break
            
            if other_player:
                other_choice = 1 - choice
                self.player_choices[other_player] = other_choice
        
        if len(self.player_choices) < 2:
            return False, "还有玩家未进行猜测"
        
        player_ids = list(self.player_choices.keys())
        player1_id, player2_id = player_ids[0], player_ids[1]
        
        winner_id = random.choice(player_ids)
        loser_id = player2_id if winner_id == player1_id else player1_id
        
        self.coin_result = self.player_choices[winner_id]
        
        self.players[PLAYER_BLACK] = winner_id
        self.players[PLAYER_WHITE] = loser_id
        
        self.current_player = PLAYER_BLACK
        
        self.game_phase = GAME_PHASE_PLAYING
        self.start_time = time.time()
        
        return True, {
            "winner_id": winner_id,
            "loser_id": loser_id,
            "coin_result": "正面" if self.coin_result == COIN_HEAD else "反面",
            "winner_choice": "正面" if self.coin_result == COIN_HEAD else "反面",
            "loser_choice": "正面" if self.player_choices[loser_id] == COIN_HEAD else "反面",
            "winner_color": PLAYER_BLACK,
            "loser_color": PLAYER_WHITE,
            "message": f"玩家 {winner_id} 赢得猜先！硬币结果是{'正面' if self.coin_result == COIN_HEAD else '反面'}。赢家执黑棋，输家执白棋。游戏开始！"
        }

    def player_choose_color(self, player_id, color_choice):
        """玩家选择执子颜色"""
        if self.game_phase != GAME_PHASE_COIN_TOSS:
            return False, "不在抛硬币阶段"
        
        if color_choice not in [PLAYER_BLACK, PLAYER_WHITE]:
            return False, "无效的颜色选择，只能选择1(黑棋)或2(白棋)"
        
        self.players[color_choice] = player_id
        
        return True, f"玩家 {player_id} 选择了{'黑棋' if color_choice == PLAYER_BLACK else '白棋'}"

    def finalize_player_colors(self, player2_id):
        """确定第二个玩家的颜色"""
        if self.game_phase != GAME_PHASE_COIN_TOSS:
            return False, "不在抛硬币阶段"
        
        unassigned_color = None
        for color, p_id in self.players.items():
            if p_id is None:
                unassigned_color = color
                break
        
        if unassigned_color is None:
            return False, "所有颜色已分配"
        
        self.players[unassigned_color] = player2_id
        
        self.current_player = PLAYER_BLACK
        
        self.game_phase = GAME_PHASE_PLAYING
        self.start_time = time.time()
        
        return True, {
            "players": self.players.copy(),
            "message": f"玩家分配完成！黑棋: {self.players[PLAYER_BLACK]}, 白棋: {self.players[PLAYER_WHITE]}。游戏开始！"
        }

    def get_player_color(self, player_id):
        """获取玩家的颜色"""
        for color, p_id in self.players.items():
            if p_id == player_id:
                return color
        return None

    def get_board_state(self):
        return [row[:] for row in self.board]

    def get_game_state(self, player_id=None):
        """获取完整的游戏状态"""
        state = {
            "board": self.get_board_state(),
            "board_size": self.board_size,
            "current_player": self.current_player,
            "game_over": self.game_over,
            "winner": self.winner,
            "game_phase": self.game_phase,
            "game_time": self.get_game_time(),
            "move_count": len(self.move_history),
            "time_since_last_move": self.get_time_since_last_move(),
            "resign_reason": self.resign_reason
        }
        
        if player_id is not None:
            state["player_color"] = self.get_player_color(player_id)
            state["is_my_turn"] = (self.get_player_color(player_id) == self.current_player) if self.game_phase == GAME_PHASE_PLAYING else False
        
        return state

    def print_board(self):
        print("  " + " ".join([str(i % 10) for i in range(self.board_size)]))
        for i, row in enumerate(self.board):
            print(f"{i % 10} " + " ".join(["." if cell == 0 else "X" if cell == 1 else "O" for cell in row]))
