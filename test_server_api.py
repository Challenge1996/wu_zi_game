#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务端API接口单元测试
测试悔棋双向确认机制
"""

import unittest
import sys
import os
import time
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import server
from wuziqi import WuziqiGame


class TestUndoRequestServer(unittest.TestCase):
    """测试悔棋请求服务端功能"""
    
    def setUp(self):
        """测试前准备"""
        server.app.config['TESTING'] = True
        self.client = server.app.test_client()
        
        server.players = {}
        server.rooms = {}
        server.challenges = {}
        server.undo_requests = {}
        
        self.player1_id = 'test_player_1'
        self.player2_id = 'test_player_2'
        self.room_id = 'test_room_1'
        
        server.players[self.player1_id] = {
            'id': self.player1_id,
            'name': '测试玩家1',
            'online': True,
            'status': 'in_game',
            'current_room': self.room_id,
            'last_heartbeat': int(time.time()),
            'registered_at': int(time.time())
        }
        
        server.players[self.player2_id] = {
            'id': self.player2_id,
            'name': '测试玩家2',
            'online': True,
            'status': 'in_game',
            'current_room': self.room_id,
            'last_heartbeat': int(time.time()),
            'registered_at': int(time.time())
        }
        
        game = WuziqiGame()
        game.players[1] = self.player1_id
        game.players[2] = self.player2_id
        game.start_game()
        
        server.rooms[self.room_id] = {
            'id': self.room_id,
            'name': '测试房间',
            'creator': self.player1_id,
            'player1': self.player1_id,
            'player2': self.player2_id,
            'status': 'playing',
            'game': game,
            'created_at': int(time.time()),
            'started_at': int(time.time()),
            'finished_at': None,
            'winner': None
        }
    
    def test_get_undo_status_no_request(self):
        """测试获取悔棋状态 - 没有待处理请求"""
        response = self.client.get(
            '/api/game/undo/status',
            query_string={'room_id': self.room_id, 'player_id': self.player1_id}
        )
        
        data = response.get_json()
        self.assertTrue(data.get('success'))
        self.assertFalse(data.get('has_pending_request'))
        self.assertIsNone(data.get('undo_request'))
    
    def test_request_undo_success(self):
        """测试发起悔棋请求成功"""
        room = server.rooms[self.room_id]
        game = room['game']
        game.place_piece(7, 7, 1)
        
        response = self.client.post(
            '/api/game/undo/request',
            json={'player_id': self.player1_id, 'room_id': self.room_id}
        )
        
        data = response.get_json()
        self.assertTrue(data.get('success'))
        self.assertIn('undo_request_id', data)
        
        undo_request_id = data.get('undo_request_id')
        self.assertIn(undo_request_id, server.undo_requests)
        
        req = server.undo_requests[undo_request_id]
        self.assertEqual(req['requester'], self.player1_id)
        self.assertEqual(req['requested'], self.player2_id)
        self.assertEqual(req['status'], 'pending')
    
    def test_request_undo_no_moves(self):
        """测试发起悔棋请求 - 没有可悔的棋"""
        response = self.client.post(
            '/api/game/undo/request',
            json={'player_id': self.player1_id, 'room_id': self.room_id}
        )
        
        data = response.get_json()
        self.assertFalse(data.get('success'))
        self.assertIn('没有可悔的棋', data.get('message', ''))
    
    def test_request_undo_room_not_exist(self):
        """测试发起悔棋请求 - 房间不存在"""
        response = self.client.post(
            '/api/game/undo/request',
            json={'player_id': self.player1_id, 'room_id': 'non_existent_room'}
        )
        
        data = response.get_json()
        self.assertFalse(data.get('success'))
        self.assertIn('房间不存在', data.get('message', ''))
    
    def test_request_undo_missing_params(self):
        """测试发起悔棋请求 - 缺少参数"""
        response = self.client.post(
            '/api/game/undo/request',
            json={'player_id': self.player1_id}
        )
        
        data = response.get_json()
        self.assertFalse(data.get('success'))
        self.assertIn('缺少必要参数', data.get('message', ''))
    
    def test_request_undo_duplicate(self):
        """测试重复发起悔棋请求"""
        room = server.rooms[self.room_id]
        game = room['game']
        game.place_piece(7, 7, 1)
        
        response1 = self.client.post(
            '/api/game/undo/request',
            json={'player_id': self.player1_id, 'room_id': self.room_id}
        )
        
        data1 = response1.get_json()
        self.assertTrue(data1.get('success'))
        
        response2 = self.client.post(
            '/api/game/undo/request',
            json={'player_id': self.player1_id, 'room_id': self.room_id}
        )
        
        data2 = response2.get_json()
        self.assertFalse(data2.get('success'))
        self.assertIn('您已发起悔棋请求', data2.get('message', ''))
    
    def test_respond_undo_accept(self):
        """测试响应悔棋请求 - 同意"""
        room = server.rooms[self.room_id]
        game = room['game']
        game.place_piece(7, 7, 1)
        
        response1 = self.client.post(
            '/api/game/undo/request',
            json={'player_id': self.player1_id, 'room_id': self.room_id}
        )
        
        data1 = response1.get_json()
        self.assertTrue(data1.get('success'))
        
        self.assertEqual(game.board[7][7], 1)
        
        response2 = self.client.post(
            '/api/game/undo/respond',
            json={'player_id': self.player2_id, 'room_id': self.room_id, 'accept': True}
        )
        
        data2 = response2.get_json()
        self.assertTrue(data2.get('success'))
        self.assertTrue(data2.get('undo_accepted'))
        
        self.assertEqual(game.board[7][7], 0)
        self.assertEqual(game.current_player, 1)
        
        undo_request_id = data1.get('undo_request_id')
        self.assertEqual(server.undo_requests[undo_request_id]['status'], 'accepted')
    
    def test_respond_undo_decline(self):
        """测试响应悔棋请求 - 拒绝"""
        room = server.rooms[self.room_id]
        game = room['game']
        game.place_piece(7, 7, 1)
        
        response1 = self.client.post(
            '/api/game/undo/request',
            json={'player_id': self.player1_id, 'room_id': self.room_id}
        )
        
        data1 = response1.get_json()
        self.assertTrue(data1.get('success'))
        
        self.assertEqual(game.board[7][7], 1)
        
        response2 = self.client.post(
            '/api/game/undo/respond',
            json={'player_id': self.player2_id, 'room_id': self.room_id, 'accept': False}
        )
        
        data2 = response2.get_json()
        self.assertTrue(data2.get('success'))
        self.assertFalse(data2.get('undo_accepted'))
        
        self.assertEqual(game.board[7][7], 1)
        
        undo_request_id = data1.get('undo_request_id')
        self.assertEqual(server.undo_requests[undo_request_id]['status'], 'declined')
    
    def test_respond_undo_no_request(self):
        """测试响应悔棋请求 - 没有待处理请求"""
        response = self.client.post(
            '/api/game/undo/respond',
            json={'player_id': self.player2_id, 'room_id': self.room_id, 'accept': True}
        )
        
        data = response.get_json()
        self.assertFalse(data.get('success'))
        self.assertIn('没有待处理的悔棋请求', data.get('message', ''))
    
    def test_respond_undo_not_requested(self):
        """测试响应悔棋请求 - 不是被请求的玩家"""
        room = server.rooms[self.room_id]
        game = room['game']
        game.place_piece(7, 7, 1)
        
        response1 = self.client.post(
            '/api/game/undo/request',
            json={'player_id': self.player1_id, 'room_id': self.room_id}
        )
        
        data1 = response1.get_json()
        self.assertTrue(data1.get('success'))
        
        response2 = self.client.post(
            '/api/game/undo/respond',
            json={'player_id': self.player1_id, 'room_id': self.room_id, 'accept': True}
        )
        
        data2 = response2.get_json()
        self.assertFalse(data2.get('success'))
        self.assertIn('您不是被请求的玩家', data2.get('message', ''))
    
    def test_get_undo_status_with_request(self):
        """测试获取悔棋状态 - 有待处理请求"""
        room = server.rooms[self.room_id]
        game = room['game']
        game.place_piece(7, 7, 1)
        
        response1 = self.client.post(
            '/api/game/undo/request',
            json={'player_id': self.player1_id, 'room_id': self.room_id}
        )
        
        data1 = response1.get_json()
        self.assertTrue(data1.get('success'))
        
        response2 = self.client.get(
            '/api/game/undo/status',
            query_string={'room_id': self.room_id, 'player_id': self.player1_id}
        )
        
        data2 = response2.get_json()
        self.assertTrue(data2.get('success'))
        self.assertTrue(data2.get('has_pending_request'))
        
        undo_request = data2.get('undo_request')
        self.assertIsNotNone(undo_request)
        self.assertEqual(undo_request['requester'], self.player1_id)
        self.assertEqual(undo_request['requested'], self.player2_id)
        self.assertEqual(undo_request['status'], 'pending')
        self.assertTrue(undo_request.get('is_my_request'))
        self.assertFalse(undo_request.get('is_requested_to_me'))
    
    def test_get_undo_status_requested_to_me(self):
        """测试获取悔棋状态 - 请求发给我"""
        room = server.rooms[self.room_id]
        game = room['game']
        game.place_piece(7, 7, 1)
        
        response1 = self.client.post(
            '/api/game/undo/request',
            json={'player_id': self.player1_id, 'room_id': self.room_id}
        )
        
        data1 = response1.get_json()
        self.assertTrue(data1.get('success'))
        
        response2 = self.client.get(
            '/api/game/undo/status',
            query_string={'room_id': self.room_id, 'player_id': self.player2_id}
        )
        
        data2 = response2.get_json()
        self.assertTrue(data2.get('success'))
        self.assertTrue(data2.get('has_pending_request'))
        
        undo_request = data2.get('undo_request')
        self.assertIsNotNone(undo_request)
        self.assertFalse(undo_request.get('is_my_request'))
        self.assertTrue(undo_request.get('is_requested_to_me'))
    
    def test_cleanup_expired_undo_requests(self):
        """测试清理过期的悔棋请求"""
        now = int(time.time())
        expired_time = now - 100
        
        expired_request_id = 'expired_request_1'
        server.undo_requests[expired_request_id] = {
            'id': expired_request_id,
            'room_id': self.room_id,
            'requester': self.player1_id,
            'requested': self.player2_id,
            'status': 'pending',
            'created_at': expired_time,
            'expires_at': expired_time + 30
        }
        
        active_request_id = 'active_request_1'
        server.undo_requests[active_request_id] = {
            'id': active_request_id,
            'room_id': self.room_id,
            'requester': self.player1_id,
            'requested': self.player2_id,
            'status': 'pending',
            'created_at': now,
            'expires_at': now + 30
        }
        
        expired = server.cleanup_expired_undo_requests()
        
        self.assertIn(expired_request_id, expired)
        self.assertEqual(server.undo_requests[expired_request_id]['status'], 'expired')
        self.assertEqual(server.undo_requests[active_request_id]['status'], 'pending')
    
    def test_get_room_info_includes_undo_request(self):
        """测试房间信息包含悔棋请求状态"""
        room = server.rooms[self.room_id]
        game = room['game']
        game.place_piece(7, 7, 1)
        
        response1 = self.client.post(
            '/api/game/undo/request',
            json={'player_id': self.player1_id, 'room_id': self.room_id}
        )
        
        data1 = response1.get_json()
        self.assertTrue(data1.get('success'))
        
        response2 = self.client.get(
            '/api/room/info',
            query_string={'room_id': self.room_id, 'player_id': self.player2_id}
        )
        
        data2 = response2.get_json()
        self.assertTrue(data2.get('success'))
        
        room_info = data2.get('room', {})
        self.assertIn('undo_request', room_info)
        
        undo_request = room_info.get('undo_request')
        self.assertIsNotNone(undo_request)
        self.assertTrue(undo_request.get('is_requested_to_me'))


class TestUndoRequestEdgeCases(unittest.TestCase):
    """测试悔棋请求的边界情况"""
    
    def setUp(self):
        """测试前准备"""
        server.app.config['TESTING'] = True
        self.client = server.app.test_client()
        
        server.players = {}
        server.rooms = {}
        server.challenges = {}
        server.undo_requests = {}
        
        self.player1_id = 'test_player_1'
        self.player2_id = 'test_player_2'
        self.room_id = 'test_room_1'
        
        server.players[self.player1_id] = {
            'id': self.player1_id,
            'name': '测试玩家1',
            'online': True,
            'status': 'in_game',
            'current_room': self.room_id,
            'last_heartbeat': int(time.time()),
            'registered_at': int(time.time())
        }
        
        server.players[self.player2_id] = {
            'id': self.player2_id,
            'name': '测试玩家2',
            'online': True,
            'status': 'in_game',
            'current_room': self.room_id,
            'last_heartbeat': int(time.time()),
            'registered_at': int(time.time())
        }
        
        game = WuziqiGame()
        game.players[1] = self.player1_id
        game.players[2] = self.player2_id
        game.start_game()
        
        server.rooms[self.room_id] = {
            'id': self.room_id,
            'name': '测试房间',
            'creator': self.player1_id,
            'player1': self.player1_id,
            'player2': self.player2_id,
            'status': 'playing',
            'game': game,
            'created_at': int(time.time()),
            'started_at': int(time.time()),
            'finished_at': None,
            'winner': None
        }
    
    def test_undo_after_win(self):
        """测试获胜后发起悔棋请求"""
        room = server.rooms[self.room_id]
        game = room['game']
        
        for col in range(5):
            game.current_player = 1
            game.place_piece(0, col, 1)
        
        self.assertTrue(game.game_over)
        self.assertEqual(game.winner, 1)
        
        response = self.client.post(
            '/api/game/undo/request',
            json={'player_id': self.player1_id, 'room_id': self.room_id}
        )
        
        data = response.get_json()
        self.assertTrue(data.get('success'))
        
        response2 = self.client.post(
            '/api/game/undo/respond',
            json={'player_id': self.player2_id, 'room_id': self.room_id, 'accept': True}
        )
        
        data2 = response2.get_json()
        self.assertTrue(data2.get('success'))
        
        self.assertFalse(game.game_over)
        self.assertIsNone(game.winner)
    
    def test_multiple_moves_undo(self):
        """测试多步落子后的悔棋"""
        room = server.rooms[self.room_id]
        game = room['game']
        
        game.place_piece(7, 7, 1)
        game.place_piece(7, 8, 2)
        game.place_piece(8, 7, 1)
        
        self.assertEqual(game.board[7][7], 1)
        self.assertEqual(game.board[7][8], 2)
        self.assertEqual(game.board[8][7], 1)
        self.assertEqual(game.current_player, 2)
        
        response1 = self.client.post(
            '/api/game/undo/request',
            json={'player_id': self.player1_id, 'room_id': self.room_id}
        )
        
        data1 = response1.get_json()
        self.assertTrue(data1.get('success'))
        
        response2 = self.client.post(
            '/api/game/undo/respond',
            json={'player_id': self.player2_id, 'room_id': self.room_id, 'accept': True}
        )
        
        data2 = response2.get_json()
        self.assertTrue(data2.get('success'))
        
        self.assertEqual(game.board[8][7], 0)
        self.assertEqual(game.current_player, 1)
        
        self.assertEqual(game.board[7][7], 1)
        self.assertEqual(game.board[7][8], 2)
    
    def test_room_not_playing(self):
        """测试游戏未开始时发起悔棋请求"""
        room = server.rooms[self.room_id]
        room['status'] = 'coin_toss'
        
        response = self.client.post(
            '/api/game/undo/request',
            json={'player_id': self.player1_id, 'room_id': self.room_id}
        )
        
        data = response.get_json()
        self.assertFalse(data.get('success'))
        self.assertIn('游戏未开始', data.get('message', ''))
    
    def test_player_not_in_room(self):
        """测试不是房间玩家发起悔棋请求"""
        room = server.rooms[self.room_id]
        game = room['game']
        game.place_piece(7, 7, 1)
        
        other_player_id = 'other_player'
        server.players[other_player_id] = {
            'id': other_player_id,
            'name': '其他玩家',
            'online': True,
            'status': 'idle',
            'current_room': None,
            'last_heartbeat': int(time.time()),
            'registered_at': int(time.time())
        }
        
        response = self.client.post(
            '/api/game/undo/request',
            json={'player_id': other_player_id, 'room_id': self.room_id}
        )
        
        data = response.get_json()
        self.assertFalse(data.get('success'))
        self.assertIn('您不是该房间的玩家', data.get('message', ''))


if __name__ == "__main__":
    unittest.main(verbosity=2)
