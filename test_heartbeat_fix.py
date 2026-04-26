#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
心跳机制和离线检测测试
测试修复：客户端不发送心跳导致玩家被判定为离线的问题
"""

import unittest
import sys
import os
import time
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import server
from server.data_store import players, rooms, challenges, undo_requests, chat_messages
from wuziqi import WuziqiGame
from constants import PLAYER_OFFLINE_TIMEOUT


class TestHeartbeatMechanism(unittest.TestCase):
    """测试心跳机制"""
    
    def setUp(self):
        """测试前准备"""
        server.app.config['TESTING'] = True
        self.client = server.app.test_client()
        
        players.clear()
        rooms.clear()
        challenges.clear()
        undo_requests.clear()
        chat_messages.clear()
        
        self.player1_id = 'test_player_1'
        self.player2_id = 'test_player_2'
        self.room_id = 'test_room_1'
        
        now = int(time.time())
        
        players[self.player1_id] = {
            'id': self.player1_id,
            'name': '测试玩家1',
            'online': True,
            'status': 'in_game',
            'current_room': self.room_id,
            'last_heartbeat': now,
            'registered_at': now
        }
        
        players[self.player2_id] = {
            'id': self.player2_id,
            'name': '测试玩家2',
            'online': True,
            'status': 'in_game',
            'current_room': self.room_id,
            'last_heartbeat': now,
            'registered_at': now
        }
        
        game = WuziqiGame()
        game.players[1] = self.player1_id
        game.players[2] = self.player2_id
        game.start_game()
        
        rooms[self.room_id] = {
            'id': self.room_id,
            'name': '测试房间',
            'creator': self.player1_id,
            'player1': self.player1_id,
            'player2': self.player2_id,
            'status': 'playing',
            'game': game,
            'created_at': now,
            'started_at': now,
            'finished_at': None,
            'winner': None
        }
    
    def test_heartbeat_updates_last_heartbeat(self):
        """测试心跳接口更新last_heartbeat"""
        player = players[self.player1_id]
        original_heartbeat = player['last_heartbeat']
        
        player['last_heartbeat'] = original_heartbeat - 10
        
        response = self.client.post(
            '/api/player/heartbeat',
            json={'player_id': self.player1_id}
        )
        
        data = response.get_json()
        self.assertTrue(data.get('success'))
        
        updated_heartbeat = player['last_heartbeat']
        self.assertGreater(updated_heartbeat, original_heartbeat - 10)
    
    def test_heartbeat_player_not_exist(self):
        """测试心跳接口 - 玩家不存在"""
        response = self.client.post(
            '/api/player/heartbeat',
            json={'player_id': 'non_existent_player'}
        )
        
        data = response.get_json()
        self.assertFalse(data.get('success'))
        self.assertIn('玩家不存在', data.get('message', ''))
    
    def test_no_heartbeat_leads_to_offline_detection(self):
        """测试不发送心跳会导致离线检测"""
        now = int(time.time())
        
        player1 = players[self.player1_id]
        player2 = players[self.player2_id]
        
        player1['last_heartbeat'] = now - PLAYER_OFFLINE_TIMEOUT - 10
        player2['last_heartbeat'] = now - PLAYER_OFFLINE_TIMEOUT - 10
        
        response = self.client.get(
            '/api/room/info',
            query_string={'room_id': self.room_id, 'player_id': self.player1_id}
        )
        
        data = response.get_json()
        self.assertTrue(data.get('success'))
        
        room = rooms[self.room_id]
        self.assertEqual(room['status'], 'finished')
        
        game = room['game']
        self.assertTrue(game.game_over)
        self.assertEqual(game.resign_reason, 'offline')
    
    def test_single_player_offline_detection(self):
        """测试单个玩家离线检测 - 玩家2（白棋）离线"""
        now = int(time.time())
        
        player1 = players[self.player1_id]
        player2 = players[self.player2_id]
        
        player1['last_heartbeat'] = now
        player2['last_heartbeat'] = now - PLAYER_OFFLINE_TIMEOUT - 10
        
        response = self.client.get(
            '/api/room/info',
            query_string={'room_id': self.room_id, 'player_id': self.player1_id}
        )
        
        data = response.get_json()
        self.assertTrue(data.get('success'))
        
        room = rooms[self.room_id]
        self.assertEqual(room['status'], 'finished')
        self.assertEqual(room['winner'], 1)
        
        game = room['game']
        self.assertTrue(game.game_over)
        self.assertEqual(game.winner, 1)
        self.assertEqual(game.resign_reason, 'offline')
    
    def test_regular_heartbeat_prevents_offline(self):
        """测试定期发送心跳防止离线检测"""
        now = int(time.time())
        
        for i in range(5):
            simulated_time = now + i * 10
            
            players[self.player1_id]['last_heartbeat'] = simulated_time
            players[self.player2_id]['last_heartbeat'] = simulated_time
            
            self.client.get(
                '/api/room/info',
                query_string={'room_id': self.room_id, 'player_id': self.player1_id}
            )
            
            room = rooms[self.room_id]
            self.assertEqual(room['status'], 'playing')
            
            game = room['game']
            self.assertFalse(game.game_over)
    
    def test_player1_offline_player2_wins(self):
        """测试玩家1（黑棋）离线，玩家2（白棋）获胜"""
        now = int(time.time())
        
        player1 = players[self.player1_id]
        player2 = players[self.player2_id]
        
        player1['last_heartbeat'] = now - PLAYER_OFFLINE_TIMEOUT - 10
        player2['last_heartbeat'] = now
        
        response = self.client.get(
            '/api/room/info',
            query_string={'room_id': self.room_id, 'player_id': self.player2_id}
        )
        
        data = response.get_json()
        self.assertTrue(data.get('success'))
        
        room = rooms[self.room_id]
        self.assertEqual(room['status'], 'finished')
        self.assertEqual(room['winner'], 2)
        
        game = room['game']
        self.assertTrue(game.game_over)
        self.assertEqual(game.winner, 2)
        self.assertEqual(game.resign_reason, 'offline')
    
    def test_white_player_offline_scenario(self):
        """测试白棋玩家离线场景（模拟用户报告的bug）"""
        now = int(time.time())
        
        white_player_id = self.player2_id
        black_player_id = self.player1_id
        
        players[white_player_id]['last_heartbeat'] = now - PLAYER_OFFLINE_TIMEOUT - 10
        players[black_player_id]['last_heartbeat'] = now
        
        room = rooms[self.room_id]
        game = room['game']
        
        self.assertEqual(game.get_player_color(white_player_id), 2)
        self.assertEqual(game.get_player_color(black_player_id), 1)
        
        response = self.client.get(
            '/api/room/info',
            query_string={'room_id': self.room_id, 'player_id': black_player_id}
        )
        
        data = response.get_json()
        self.assertTrue(data.get('success'))
        
        room_info = data.get('room', {})
        game_state = room_info.get('game_state', {})
        
        self.assertTrue(game_state.get('game_over'))
        self.assertEqual(game_state.get('winner'), 1)
        self.assertEqual(game_state.get('resign_reason'), 'offline')


class TestHeartbeatEdgeCases(unittest.TestCase):
    """测试心跳机制的边界情况"""
    
    def setUp(self):
        """测试前准备"""
        server.app.config['TESTING'] = True
        self.client = server.app.test_client()
        
        players.clear()
        rooms.clear()
        challenges.clear()
        undo_requests.clear()
        chat_messages.clear()
    
    def test_player_registration_sets_heartbeat(self):
        """测试玩家注册时设置last_heartbeat"""
        response = self.client.post(
            '/api/player/register',
            json={'name': '测试玩家'}
        )
        
        data = response.get_json()
        self.assertTrue(data.get('success'))
        
        player_id = data.get('player_id')
        self.assertIn(player_id, players)
        
        player = players[player_id]
        self.assertEqual(player['online'], True)
        self.assertGreater(player['last_heartbeat'], 0)
    
    def test_player_offline_sets_online_false(self):
        """测试玩家下线接口设置online为False"""
        response1 = self.client.post(
            '/api/player/register',
            json={'name': '测试玩家'}
        )
        
        data1 = response1.get_json()
        player_id = data1.get('player_id')
        
        response2 = self.client.post(
            '/api/player/offline',
            json={'player_id': player_id}
        )
        
        data2 = response2.get_json()
        self.assertTrue(data2.get('success'))
        
        player = players[player_id]
        self.assertEqual(player['online'], False)
    
    def test_heartbeat_resets_online_status(self):
        """测试心跳可以重置online状态"""
        response1 = self.client.post(
            '/api/player/register',
            json={'name': '测试玩家'}
        )
        
        data1 = response1.get_json()
        player_id = data1.get('player_id')
        
        players[player_id]['online'] = False
        
        response2 = self.client.post(
            '/api/player/heartbeat',
            json={'player_id': player_id}
        )
        
        data2 = response2.get_json()
        self.assertTrue(data2.get('success'))
        
        player = players[player_id]
        self.assertEqual(player['online'], True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
