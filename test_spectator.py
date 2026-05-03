#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
观战功能单元测试
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from constants import (
    ROOM_VISIBILITY_PUBLIC,
    ROOM_VISIBILITY_PRIVATE,
    HOT_GAME_SPECTATOR_THRESHOLD,
    PLAYER_STATUS_SPECTATING,
    PLAYER_STATUS_IDLE,
    ROOM_STATUS_PLAYING,
    ROOM_STATUS_FINISHED,
    PLAYER_BLACK,
    PLAYER_WHITE,
    CHAT_MESSAGE_TYPE_SPECTATOR_JOIN,
    CHAT_MESSAGE_TYPE_SPECTATOR_LEAVE
)
from util import get_timestamp, generate_id
from game import WuziqiGame
from server.data_store import players, rooms, challenges, undo_requests, chat_messages
from server.utils import (
    get_player_info,
    get_room_info,
    add_spectator,
    remove_spectator,
    get_public_rooms,
    is_room_player,
    is_room_spectator,
    get_room_spectators_info
)


class TestSpectatorFunctions(unittest.TestCase):
    """观战功能测试"""

    def setUp(self):
        """测试前的准备工作"""
        players.clear()
        rooms.clear()
        challenges.clear()
        undo_requests.clear()
        chat_messages.clear()
        
        self.player1_id = generate_id()
        self.player2_id = generate_id()
        self.spectator1_id = generate_id()
        self.spectator2_id = generate_id()
        self.spectator3_id = generate_id()
        
        now = get_timestamp()
        
        players[self.player1_id] = {
            'id': self.player1_id,
            'name': '玩家1',
            'online': True,
            'status': PLAYER_STATUS_IDLE,
            'current_room': None,
            'last_heartbeat': now,
            'registered_at': now
        }
        
        players[self.player2_id] = {
            'id': self.player2_id,
            'name': '玩家2',
            'online': True,
            'status': PLAYER_STATUS_IDLE,
            'current_room': None,
            'last_heartbeat': now,
            'registered_at': now
        }
        
        players[self.spectator1_id] = {
            'id': self.spectator1_id,
            'name': '观战者1',
            'online': True,
            'status': PLAYER_STATUS_IDLE,
            'current_room': None,
            'last_heartbeat': now,
            'registered_at': now
        }
        
        players[self.spectator2_id] = {
            'id': self.spectator2_id,
            'name': '观战者2',
            'online': True,
            'status': PLAYER_STATUS_IDLE,
            'current_room': None,
            'last_heartbeat': now,
            'registered_at': now
        }
        
        players[self.spectator3_id] = {
            'id': self.spectator3_id,
            'name': '观战者3',
            'online': True,
            'status': PLAYER_STATUS_IDLE,
            'current_room': None,
            'last_heartbeat': now,
            'registered_at': now
        }
        
        self.room_id = generate_id()
        game = WuziqiGame()
        game.players[PLAYER_BLACK] = self.player1_id
        game.players[PLAYER_WHITE] = self.player2_id
        game.start_game()
        
        rooms[self.room_id] = {
            'id': self.room_id,
            'name': '玩家1 vs 玩家2',
            'creator': self.player1_id,
            'player1': self.player1_id,
            'player2': self.player2_id,
            'status': ROOM_STATUS_PLAYING,
            'game': game,
            'created_at': get_timestamp(),
            'started_at': get_timestamp(),
            'finished_at': None,
            'winner': None,
            'visibility': ROOM_VISIBILITY_PUBLIC,
            'spectators': set(),
            'spectator_count': 0
        }
        
        players[self.player1_id]['status'] = 'in_game'
        players[self.player1_id]['current_room'] = self.room_id
        players[self.player2_id]['status'] = 'in_game'
        players[self.player2_id]['current_room'] = self.room_id

    def test_is_room_player(self):
        """测试判断是否是房间玩家"""
        self.assertTrue(is_room_player(self.room_id, self.player1_id))
        self.assertTrue(is_room_player(self.room_id, self.player2_id))
        self.assertFalse(is_room_player(self.room_id, self.spectator1_id))
        self.assertFalse(is_room_player('non_existent_room', self.player1_id))

    def test_is_room_spectator(self):
        """测试判断是否是房间观战者"""
        self.assertFalse(is_room_spectator(self.room_id, self.spectator1_id))
        
        room = rooms[self.room_id]
        room['spectators'].add(self.spectator1_id)
        room['spectator_count'] = 1
        
        self.assertTrue(is_room_spectator(self.room_id, self.spectator1_id))
        self.assertFalse(is_room_spectator(self.room_id, self.spectator2_id))
        self.assertFalse(is_room_spectator('non_existent_room', self.spectator1_id))

    def test_add_spectator_success(self):
        """测试成功添加观战者"""
        success, message = add_spectator(self.room_id, self.spectator1_id)
        
        self.assertTrue(success)
        self.assertIn('成功加入观战', message)
        
        room = rooms[self.room_id]
        self.assertIn(self.spectator1_id, room['spectators'])
        self.assertEqual(room['spectator_count'], 1)
        
        spectator = players[self.spectator1_id]
        self.assertEqual(spectator['status'], PLAYER_STATUS_SPECTATING)
        self.assertEqual(spectator['current_room'], self.room_id)

    def test_add_spectator_player_cannot_spectate(self):
        """测试对局玩家不能作为观战者加入"""
        success, message = add_spectator(self.room_id, self.player1_id)
        
        self.assertFalse(success)
        self.assertIn('对局玩家', message)
        
        room = rooms[self.room_id]
        self.assertNotIn(self.player1_id, room['spectators'])

    def test_add_spectator_already_spectating(self):
        """测试已经在观战的玩家不能重复加入"""
        add_spectator(self.room_id, self.spectator1_id)
        
        success, message = add_spectator(self.room_id, self.spectator1_id)
        
        self.assertFalse(success)
        self.assertIn('已经在观战', message)
        
        room = rooms[self.room_id]
        self.assertEqual(room['spectator_count'], 1)

    def test_add_spectator_room_not_exist(self):
        """测试加入不存在的房间"""
        success, message = add_spectator('non_existent_room', self.spectator1_id)
        
        self.assertFalse(success)
        self.assertIn('房间不存在', message)

    def test_add_spectator_player_not_exist(self):
        """测试不存在的玩家加入观战"""
        success, message = add_spectator(self.room_id, 'non_existent_player')
        
        self.assertFalse(success)
        self.assertIn('玩家不存在', message)

    def test_remove_spectator_success(self):
        """测试成功移除观战者"""
        add_spectator(self.room_id, self.spectator1_id)
        
        success, message = remove_spectator(self.room_id, self.spectator1_id)
        
        self.assertTrue(success)
        self.assertIn('成功离开', message)
        
        room = rooms[self.room_id]
        self.assertNotIn(self.spectator1_id, room['spectators'])
        self.assertEqual(room['spectator_count'], 0)
        
        spectator = players[self.spectator1_id]
        self.assertEqual(spectator['status'], PLAYER_STATUS_IDLE)
        self.assertIsNone(spectator['current_room'])

    def test_remove_spectator_not_spectating(self):
        """测试移除不在观战的玩家"""
        success, message = remove_spectator(self.room_id, self.spectator1_id)
        
        self.assertFalse(success)
        self.assertIn('不是该房间的观战者', message)

    def test_get_room_spectators_info(self):
        """测试获取观战者信息"""
        add_spectator(self.room_id, self.spectator1_id)
        add_spectator(self.room_id, self.spectator2_id)
        
        spectators_info = get_room_spectators_info(self.room_id)
        
        self.assertEqual(len(spectators_info), 2)
        
        spectator_names = [s['name'] for s in spectators_info]
        self.assertIn('观战者1', spectator_names)
        self.assertIn('观战者2', spectator_names)

    def test_get_room_info_includes_spectator_info(self):
        """测试房间信息包含观战者信息"""
        add_spectator(self.room_id, self.spectator1_id)
        add_spectator(self.room_id, self.spectator2_id)
        
        room_info = get_room_info(self.room_id)
        
        self.assertIn('spectator_count', room_info)
        self.assertEqual(room_info['spectator_count'], 2)
        
        self.assertIn('is_hot_game', room_info)
        
        self.assertIn('spectators', room_info)
        self.assertEqual(len(room_info['spectators']), 2)
        
        self.assertIn('visibility', room_info)
        self.assertEqual(room_info['visibility'], ROOM_VISIBILITY_PUBLIC)

    def test_hot_game_detection(self):
        """测试热门游戏检测"""
        self.assertEqual(HOT_GAME_SPECTATOR_THRESHOLD, 1)
        
        room_info = get_room_info(self.room_id)
        self.assertFalse(room_info['is_hot_game'])
        
        add_spectator(self.room_id, self.spectator1_id)
        room_info = get_room_info(self.room_id)
        self.assertFalse(room_info['is_hot_game'])
        
        add_spectator(self.room_id, self.spectator2_id)
        room_info = get_room_info(self.room_id)
        self.assertTrue(room_info['is_hot_game'])

    def test_get_public_rooms(self):
        """测试获取公开房间列表"""
        private_room_id = generate_id()
        game2 = WuziqiGame()
        game2.players[PLAYER_BLACK] = self.spectator1_id
        game2.players[PLAYER_WHITE] = self.spectator2_id
        game2.start_game()
        
        rooms[private_room_id] = {
            'id': private_room_id,
            'name': '私有房间',
            'creator': self.spectator1_id,
            'player1': self.spectator1_id,
            'player2': self.spectator2_id,
            'status': ROOM_STATUS_PLAYING,
            'game': game2,
            'created_at': get_timestamp(),
            'started_at': get_timestamp(),
            'finished_at': None,
            'winner': None,
            'visibility': ROOM_VISIBILITY_PRIVATE,
            'spectators': set(),
            'spectator_count': 0
        }
        
        public_rooms = get_public_rooms()
        
        self.assertEqual(len(public_rooms), 1)
        self.assertEqual(public_rooms[0]['id'], self.room_id)
        self.assertEqual(public_rooms[0]['visibility'], ROOM_VISIBILITY_PUBLIC)

    def test_public_rooms_sorted_by_spectator_count(self):
        """测试公开房间按观战人数降序排列"""
        room2_id = generate_id()
        game2 = WuziqiGame()
        game2.players[PLAYER_BLACK] = self.spectator1_id
        game2.players[PLAYER_WHITE] = self.spectator2_id
        game2.start_game()
        
        rooms[room2_id] = {
            'id': room2_id,
            'name': '房间2',
            'creator': self.spectator1_id,
            'player1': self.spectator1_id,
            'player2': self.spectator2_id,
            'status': ROOM_STATUS_PLAYING,
            'game': game2,
            'created_at': get_timestamp(),
            'started_at': get_timestamp(),
            'finished_at': None,
            'winner': None,
            'visibility': ROOM_VISIBILITY_PUBLIC,
            'spectators': set(),
            'spectator_count': 0
        }
        
        add_spectator(room2_id, self.spectator3_id)
        
        public_rooms = get_public_rooms()
        
        self.assertEqual(len(public_rooms), 2)
        self.assertEqual(public_rooms[0]['id'], room2_id)
        self.assertEqual(public_rooms[0]['spectator_count'], 1)
        self.assertEqual(public_rooms[1]['id'], self.room_id)
        self.assertEqual(public_rooms[1]['spectator_count'], 0)

    def test_spectator_chat_message_generated(self):
        """测试观战者加入/离开时生成聊天消息"""
        self.room_id
        add_spectator(self.room_id, self.spectator1_id)
        
        room_messages = chat_messages.get(self.room_id, [])
        join_messages = [m for m in room_messages if m['type'] == CHAT_MESSAGE_TYPE_SPECTATOR_JOIN]
        
        self.assertEqual(len(join_messages), 1)
        self.assertIn('观战者1', join_messages[0]['content'])
        
        remove_spectator(self.room_id, self.spectator1_id)
        
        room_messages = chat_messages.get(self.room_id, [])
        leave_messages = [m for m in room_messages if m['type'] == CHAT_MESSAGE_TYPE_SPECTATOR_LEAVE]
        
        self.assertEqual(len(leave_messages), 1)
        self.assertIn('观战者1', leave_messages[0]['content'])


class TestSpectatorPermissions(unittest.TestCase):
    """观战者权限测试"""

    def setUp(self):
        """测试前的准备工作"""
        players.clear()
        rooms.clear()
        chat_messages.clear()
        
        self.player1_id = generate_id()
        self.player2_id = generate_id()
        self.spectator_id = generate_id()
        
        now = get_timestamp()
        
        players[self.player1_id] = {
            'id': self.player1_id,
            'name': '玩家1',
            'online': True,
            'status': 'in_game',
            'current_room': None,
            'last_heartbeat': now,
            'registered_at': now
        }
        
        players[self.player2_id] = {
            'id': self.player2_id,
            'name': '玩家2',
            'online': True,
            'status': 'in_game',
            'current_room': None,
            'last_heartbeat': now,
            'registered_at': now
        }
        
        players[self.spectator_id] = {
            'id': self.spectator_id,
            'name': '观战者',
            'online': True,
            'status': PLAYER_STATUS_SPECTATING,
            'current_room': None,
            'last_heartbeat': now,
            'registered_at': now
        }
        
        self.room_id = generate_id()
        game = WuziqiGame()
        game.players[PLAYER_BLACK] = self.player1_id
        game.players[PLAYER_WHITE] = self.player2_id
        game.start_game()
        
        rooms[self.room_id] = {
            'id': self.room_id,
            'name': '玩家1 vs 玩家2',
            'creator': self.player1_id,
            'player1': self.player1_id,
            'player2': self.player2_id,
            'status': ROOM_STATUS_PLAYING,
            'game': game,
            'created_at': get_timestamp(),
            'started_at': get_timestamp(),
            'finished_at': None,
            'winner': None,
            'visibility': ROOM_VISIBILITY_PUBLIC,
            'spectators': {self.spectator_id},
            'spectator_count': 1
        }
        
        players[self.player1_id]['current_room'] = self.room_id
        players[self.player2_id]['current_room'] = self.room_id
        players[self.spectator_id]['current_room'] = self.room_id

    def test_spectator_cannot_get_player_color(self):
        """测试观战者没有分配棋子颜色"""
        room = rooms[self.room_id]
        game = room['game']
        
        player1_color = game.get_player_color(self.player1_id)
        self.assertIsNotNone(player1_color)
        
        player2_color = game.get_player_color(self.player2_id)
        self.assertIsNotNone(player2_color)
        
        spectator_color = game.get_player_color(self.spectator_id)
        self.assertIsNone(spectator_color)

    def test_is_room_player_vs_spectator(self):
        """测试对局玩家和观战者的区分"""
        self.assertTrue(is_room_player(self.room_id, self.player1_id))
        self.assertTrue(is_room_player(self.room_id, self.player2_id))
        self.assertFalse(is_room_player(self.room_id, self.spectator_id))
        
        self.assertTrue(is_room_spectator(self.room_id, self.spectator_id))
        self.assertFalse(is_room_spectator(self.room_id, self.player1_id))
        self.assertFalse(is_room_spectator(self.room_id, self.player2_id))


if __name__ == '__main__':
    unittest.main()
