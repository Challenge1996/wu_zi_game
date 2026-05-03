#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
战绩和积分系统单元测试
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from constants import (
    RANK_NEWBIE,
    RANK_IRON,
    RANK_BRONZE,
    RANK_SILVER,
    RANK_GOLD,
    RANK_PLATINUM,
    RANK_DIAMOND,
    RANK_MASTER,
    RANK_KING,
    RANK_THRESHOLDS,
    SCORE_WIN,
    SCORE_LOSE,
    SCORE_DRAW
)
from server.data_store import players, rooms
from server.utils import (
    calculate_rank,
    update_player_stats,
    update_game_stats
)
from util import get_timestamp, generate_id
from game import WuziqiGame


class TestRankAndScoreSystem(unittest.TestCase):
    """战绩和积分系统测试"""

    def setUp(self):
        """测试前的准备工作"""
        players.clear()
        rooms.clear()
        
        self.player1_id = generate_id()
        self.player2_id = generate_id()
        
        now = get_timestamp()
        
        players[self.player1_id] = {
            'id': self.player1_id,
            'name': '玩家1',
            'online': True,
            'status': 'idle',
            'current_room': None,
            'last_heartbeat': now,
            'registered_at': now,
            'stats': {
                'total_games': 0,
                'wins': 0,
                'losses': 0,
                'draws': 0,
                'win_rate': 0.0,
                'current_streak': 0,
                'max_streak': 0,
                'score': 0,
                'rank': RANK_NEWBIE
            }
        }
        
        players[self.player2_id] = {
            'id': self.player2_id,
            'name': '玩家2',
            'online': True,
            'status': 'idle',
            'current_room': None,
            'last_heartbeat': now,
            'registered_at': now,
            'stats': {
                'total_games': 0,
                'wins': 0,
                'losses': 0,
                'draws': 0,
                'win_rate': 0.0,
                'current_streak': 0,
                'max_streak': 0,
                'score': 0,
                'rank': RANK_NEWBIE
            }
        }

    def test_calculate_rank(self):
        """测试段位计算"""
        # 测试各段位的积分阈值
        self.assertEqual(calculate_rank(-10), RANK_NEWBIE)
        self.assertEqual(calculate_rank(0), RANK_NEWBIE)
        self.assertEqual(calculate_rank(1), RANK_IRON)
        self.assertEqual(calculate_rank(4), RANK_IRON)
        self.assertEqual(calculate_rank(5), RANK_BRONZE)
        self.assertEqual(calculate_rank(9), RANK_BRONZE)
        self.assertEqual(calculate_rank(10), RANK_SILVER)
        self.assertEqual(calculate_rank(19), RANK_SILVER)
        self.assertEqual(calculate_rank(20), RANK_GOLD)
        self.assertEqual(calculate_rank(34), RANK_GOLD)
        self.assertEqual(calculate_rank(35), RANK_PLATINUM)
        self.assertEqual(calculate_rank(54), RANK_PLATINUM)
        self.assertEqual(calculate_rank(55), RANK_DIAMOND)
        self.assertEqual(calculate_rank(79), RANK_DIAMOND)
        self.assertEqual(calculate_rank(80), RANK_MASTER)
        self.assertEqual(calculate_rank(109), RANK_MASTER)
        self.assertEqual(calculate_rank(110), RANK_KING)
        self.assertEqual(calculate_rank(200), RANK_KING)

    def test_update_player_stats_win(self):
        """测试玩家获胜时的战绩更新"""
        player = players[self.player1_id]
        
        # 初始状态
        self.assertEqual(player['stats']['total_games'], 0)
        self.assertEqual(player['stats']['wins'], 0)
        self.assertEqual(player['stats']['score'], 0)
        self.assertEqual(player['stats']['rank'], RANK_NEWBIE)
        
        # 第一次获胜
        update_player_stats(self.player1_id, 'win')
        self.assertEqual(player['stats']['total_games'], 1)
        self.assertEqual(player['stats']['wins'], 1)
        self.assertEqual(player['stats']['score'], 1)
        self.assertEqual(player['stats']['rank'], RANK_IRON)
        self.assertEqual(player['stats']['current_streak'], 1)
        self.assertEqual(player['stats']['max_streak'], 1)
        self.assertEqual(player['stats']['win_rate'], 100.0)
        
        # 第二次获胜
        update_player_stats(self.player1_id, 'win')
        self.assertEqual(player['stats']['total_games'], 2)
        self.assertEqual(player['stats']['wins'], 2)
        self.assertEqual(player['stats']['score'], 2)
        self.assertEqual(player['stats']['rank'], RANK_IRON)
        self.assertEqual(player['stats']['current_streak'], 2)
        self.assertEqual(player['stats']['max_streak'], 2)
        self.assertEqual(player['stats']['win_rate'], 100.0)

    def test_update_player_stats_lose(self):
        """测试玩家失败时的战绩更新"""
        player = players[self.player1_id]
        
        # 先赢两次
        update_player_stats(self.player1_id, 'win')
        update_player_stats(self.player1_id, 'win')
        self.assertEqual(player['stats']['current_streak'], 2)
        
        # 失败
        update_player_stats(self.player1_id, 'lose')
        self.assertEqual(player['stats']['total_games'], 3)
        self.assertEqual(player['stats']['losses'], 1)
        self.assertEqual(player['stats']['score'], 2 - 1)
        self.assertEqual(player['stats']['current_streak'], 0)
        self.assertEqual(player['stats']['win_rate'], 66.7)

    def test_update_player_stats_draw(self):
        """测试玩家平局时的战绩更新"""
        player = players[self.player1_id]
        
        # 先赢一次
        update_player_stats(self.player1_id, 'win')
        self.assertEqual(player['stats']['current_streak'], 1)
        
        # 平局
        update_player_stats(self.player1_id, 'draw')
        self.assertEqual(player['stats']['total_games'], 2)
        self.assertEqual(player['stats']['draws'], 1)
        self.assertEqual(player['stats']['score'], 1)
        self.assertEqual(player['stats']['current_streak'], 0)
        self.assertEqual(player['stats']['win_rate'], 50.0)

    def test_update_game_stats_player1_win(self):
        """测试游戏结束后玩家1获胜的战绩更新"""
        room_id = generate_id()
        game = WuziqiGame()
        game.players[1] = self.player1_id  # 黑棋
        game.players[2] = self.player2_id  # 白棋
        
        rooms[room_id] = {
            'id': room_id,
            'player1': self.player1_id,
            'player2': self.player2_id,
            'game': game
        }
        
        # 玩家1获胜
        update_game_stats(room_id, self.player1_id)
        
        player1 = players[self.player1_id]
        player2 = players[self.player2_id]
        
        # 玩家1的战绩
        self.assertEqual(player1['stats']['total_games'], 1)
        self.assertEqual(player1['stats']['wins'], 1)
        self.assertEqual(player1['stats']['score'], 1)
        
        # 玩家2的战绩
        self.assertEqual(player2['stats']['total_games'], 1)
        self.assertEqual(player2['stats']['losses'], 1)
        self.assertEqual(player2['stats']['score'], -1)

    def test_update_game_stats_player2_win(self):
        """测试游戏结束后玩家2获胜的战绩更新"""
        room_id = generate_id()
        game = WuziqiGame()
        game.players[1] = self.player1_id  # 黑棋
        game.players[2] = self.player2_id  # 白棋
        
        rooms[room_id] = {
            'id': room_id,
            'player1': self.player1_id,
            'player2': self.player2_id,
            'game': game
        }
        
        # 玩家2获胜
        update_game_stats(room_id, self.player2_id)
        
        player1 = players[self.player1_id]
        player2 = players[self.player2_id]
        
        # 玩家1的战绩
        self.assertEqual(player1['stats']['total_games'], 1)
        self.assertEqual(player1['stats']['losses'], 1)
        self.assertEqual(player1['stats']['score'], -1)
        
        # 玩家2的战绩
        self.assertEqual(player2['stats']['total_games'], 1)
        self.assertEqual(player2['stats']['wins'], 1)
        self.assertEqual(player2['stats']['score'], 1)

    def test_update_game_stats_draw(self):
        """测试游戏结束平局的战绩更新"""
        room_id = generate_id()
        game = WuziqiGame()
        game.players[1] = self.player1_id  # 黑棋
        game.players[2] = self.player2_id  # 白棋
        
        rooms[room_id] = {
            'id': room_id,
            'player1': self.player1_id,
            'player2': self.player2_id,
            'game': game
        }
        
        # 平局
        update_game_stats(room_id, None)
        
        player1 = players[self.player1_id]
        player2 = players[self.player2_id]
        
        # 玩家1的战绩
        self.assertEqual(player1['stats']['total_games'], 1)
        self.assertEqual(player1['stats']['draws'], 1)
        self.assertEqual(player1['stats']['score'], 0)
        
        # 玩家2的战绩
        self.assertEqual(player2['stats']['total_games'], 1)
        self.assertEqual(player2['stats']['draws'], 1)
        self.assertEqual(player2['stats']['score'], 0)

    def test_rank_upgrade(self):
        """测试段位升级"""
        player = players[self.player1_id]
        
        # 从新手到黑铁
        update_player_stats(self.player1_id, 'win')
        self.assertEqual(player['stats']['rank'], RANK_IRON)
        
        # 从黑铁到青铜（需要5分）
        for _ in range(4):
            update_player_stats(self.player1_id, 'win')
        self.assertEqual(player['stats']['score'], 5)
        self.assertEqual(player['stats']['rank'], RANK_BRONZE)
        
        # 从青铜到白银（需要10分）
        for _ in range(5):
            update_player_stats(self.player1_id, 'win')
        self.assertEqual(player['stats']['score'], 10)
        self.assertEqual(player['stats']['rank'], RANK_SILVER)

    def test_rank_downgrade(self):
        """测试段位降级"""
        player = players[self.player1_id]
        
        # 先升到黑铁
        update_player_stats(self.player1_id, 'win')
        self.assertEqual(player['stats']['rank'], RANK_IRON)
        
        # 输掉两局，积分变为-1，应该降回新手
        update_player_stats(self.player1_id, 'lose')
        update_player_stats(self.player1_id, 'lose')
        self.assertEqual(player['stats']['score'], -1)
        self.assertEqual(player['stats']['rank'], RANK_NEWBIE)

    def test_max_streak(self):
        """测试最高连胜"""
        player = players[self.player1_id]
        
        # 3连胜
        for _ in range(3):
            update_player_stats(self.player1_id, 'win')
        self.assertEqual(player['stats']['current_streak'], 3)
        self.assertEqual(player['stats']['max_streak'], 3)
        
        # 输掉一局
        update_player_stats(self.player1_id, 'lose')
        self.assertEqual(player['stats']['current_streak'], 0)
        self.assertEqual(player['stats']['max_streak'], 3)  # 最高连胜保持
        
        # 4连胜，超过之前的最高
        for _ in range(4):
            update_player_stats(self.player1_id, 'win')
        self.assertEqual(player['stats']['current_streak'], 4)
        self.assertEqual(player['stats']['max_streak'], 4)  # 最高连胜更新

    def test_compatibility_with_old_data(self):
        """测试与旧数据的兼容性"""
        # 创建一个没有stats字段的玩家（旧数据）
        old_player_id = generate_id()
        players[old_player_id] = {
            'id': old_player_id,
            'name': '旧玩家',
            'online': True,
            'status': 'idle',
            'current_room': None,
            'last_heartbeat': get_timestamp(),
            'registered_at': get_timestamp()
        }
        
        # 调用update_player_stats，应该自动初始化stats
        update_player_stats(old_player_id, 'win')
        
        player = players[old_player_id]
        self.assertIn('stats', player)
        self.assertEqual(player['stats']['total_games'], 1)
        self.assertEqual(player['stats']['wins'], 1)
        self.assertEqual(player['stats']['score'], 1)
        self.assertEqual(player['stats']['rank'], RANK_IRON)


if __name__ == '__main__':
    unittest.main()
