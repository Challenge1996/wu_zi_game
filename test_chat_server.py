#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聊天系统服务器端单元测试
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.data_store import players, rooms, challenges, undo_requests, chat_messages
from server.utils import (
    init_room_chat,
    add_chat_message,
    get_room_chat_messages
)
from constants import (
    CHAT_MESSAGE_TYPE_TEXT,
    CHAT_MESSAGE_TYPE_SYSTEM,
    CHAT_MESSAGE_TYPE_MOVE,
    CHAT_MESSAGE_TYPE_UNDO,
    CHAT_MAX_HISTORY
)


class TestChatServer(unittest.TestCase):
    """聊天系统服务器端测试"""
    
    def setUp(self):
        """测试前初始化"""
        chat_messages.clear()
        players.clear()
        rooms.clear()
        
        players['player1'] = {
            'id': 'player1',
            'name': '测试玩家1',
            'online': True,
            'status': 'idle',
            'current_room': None
        }
        players['player2'] = {
            'id': 'player2',
            'name': '测试玩家2',
            'online': True,
            'status': 'idle',
            'current_room': None
        }
        
        rooms['room1'] = {
            'id': 'room1',
            'name': '测试房间',
            'player1': 'player1',
            'player2': 'player2',
            'status': 'playing'
        }
    
    def test_init_room_chat(self):
        """测试初始化房间聊天"""
        self.assertNotIn('new_room', chat_messages)
        
        init_room_chat('new_room')
        
        self.assertIn('new_room', chat_messages)
        self.assertEqual(chat_messages['new_room'], [])
    
    def test_init_room_chat_already_exists(self):
        """测试初始化已存在的房间聊天"""
        init_room_chat('room1')
        chat_messages['room1'].append({'id': 'test_msg'})
        
        init_room_chat('room1')
        
        self.assertEqual(len(chat_messages['room1']), 1)
    
    def test_add_chat_message_text(self):
        """测试添加文本聊天消息"""
        init_room_chat('room1')
        
        message = add_chat_message(
            'room1',
            'player1',
            CHAT_MESSAGE_TYPE_TEXT,
            '你好，准备开始游戏吧！'
        )
        
        self.assertIsNotNone(message)
        self.assertIn('id', message)
        self.assertEqual(message['room_id'], 'room1')
        self.assertEqual(message['player_id'], 'player1')
        self.assertEqual(message['player_name'], '测试玩家1')
        self.assertEqual(message['type'], CHAT_MESSAGE_TYPE_TEXT)
        self.assertEqual(message['content'], '你好，准备开始游戏吧！')
        
        self.assertEqual(len(chat_messages['room1']), 1)
    
    def test_add_chat_message_system(self):
        """测试添加系统消息"""
        init_room_chat('room1')
        
        message = add_chat_message(
            'room1',
            None,
            CHAT_MESSAGE_TYPE_SYSTEM,
            '游戏开始！黑棋先下。'
        )
        
        self.assertIsNotNone(message)
        self.assertEqual(message['type'], CHAT_MESSAGE_TYPE_SYSTEM)
        self.assertEqual(message['content'], '游戏开始！黑棋先下。')
        self.assertIsNone(message['player_id'])
    
    def test_add_chat_message_move(self):
        """测试添加落子消息"""
        init_room_chat('room1')
        
        message = add_chat_message(
            'room1',
            'player1',
            CHAT_MESSAGE_TYPE_MOVE,
            '测试玩家1（黑棋）在 (7, 7) 落子',
            {'row': 7, 'col': 7, 'color': 1}
        )
        
        self.assertIsNotNone(message)
        self.assertEqual(message['type'], CHAT_MESSAGE_TYPE_MOVE)
        self.assertIn('row', message['extra_data'])
        self.assertIn('col', message['extra_data'])
        self.assertIn('color', message['extra_data'])
        self.assertEqual(message['extra_data']['row'], 7)
        self.assertEqual(message['extra_data']['col'], 7)
        self.assertEqual(message['extra_data']['color'], 1)
    
    def test_add_chat_message_undo(self):
        """测试添加悔棋消息"""
        init_room_chat('room1')
        
        message = add_chat_message(
            'room1',
            None,
            CHAT_MESSAGE_TYPE_UNDO,
            '测试玩家2 同意了 测试玩家1 的悔棋请求',
            {'accepted': True}
        )
        
        self.assertIsNotNone(message)
        self.assertEqual(message['type'], CHAT_MESSAGE_TYPE_UNDO)
        self.assertIn('accepted', message['extra_data'])
        self.assertTrue(message['extra_data']['accepted'])
    
    def test_get_room_chat_messages_empty(self):
        """测试获取空房间的聊天消息"""
        messages = get_room_chat_messages('non_existent_room')
        self.assertEqual(messages, [])
    
    def test_get_room_chat_messages(self):
        """测试获取房间聊天消息"""
        init_room_chat('room1')
        
        add_chat_message('room1', 'player1', CHAT_MESSAGE_TYPE_TEXT, '消息1')
        add_chat_message('room1', 'player2', CHAT_MESSAGE_TYPE_TEXT, '消息2')
        add_chat_message('room1', None, CHAT_MESSAGE_TYPE_SYSTEM, '系统消息')
        
        messages = get_room_chat_messages('room1')
        
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0]['content'], '消息1')
        self.assertEqual(messages[1]['content'], '消息2')
        self.assertEqual(messages[2]['content'], '系统消息')
    
    def test_get_room_chat_messages_with_player_id(self):
        """测试带玩家ID获取聊天消息"""
        init_room_chat('room1')
        
        add_chat_message('room1', 'player1', CHAT_MESSAGE_TYPE_TEXT, '玩家1的消息')
        add_chat_message('room1', 'player2', CHAT_MESSAGE_TYPE_TEXT, '玩家2的消息')
        
        messages = get_room_chat_messages('room1', player_id='player1')
        
        self.assertEqual(len(messages), 2)
        self.assertTrue(messages[0]['is_my_message'])
        self.assertFalse(messages[1]['is_my_message'])
    
    def test_get_room_chat_messages_since_id(self):
        """测试从指定ID后获取聊天消息"""
        init_room_chat('room1')
        
        msg1 = add_chat_message('room1', 'player1', CHAT_MESSAGE_TYPE_TEXT, '消息1')
        msg2 = add_chat_message('room1', 'player2', CHAT_MESSAGE_TYPE_TEXT, '消息2')
        msg3 = add_chat_message('room1', 'player1', CHAT_MESSAGE_TYPE_TEXT, '消息3')
        
        messages = get_room_chat_messages('room1', since_id=msg1['id'])
        
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]['id'], msg2['id'])
        self.assertEqual(messages[1]['id'], msg3['id'])
    
    def test_chat_max_history(self):
        """测试聊天消息最大历史记录限制"""
        init_room_chat('room1')
        
        for i in range(CHAT_MAX_HISTORY + 10):
            add_chat_message('room1', 'player1', CHAT_MESSAGE_TYPE_TEXT, f'消息{i}')
        
        messages = get_room_chat_messages('room1')
        
        self.assertEqual(len(messages), CHAT_MAX_HISTORY)
        self.assertEqual(messages[0]['content'], f'消息{10}')
        self.assertEqual(messages[-1]['content'], f'消息{CHAT_MAX_HISTORY + 9}')
    
    def test_add_chat_message_with_nonexistent_player(self):
        """测试添加不存在玩家的消息"""
        init_room_chat('room1')
        
        message = add_chat_message(
            'room1',
            'nonexistent_player',
            CHAT_MESSAGE_TYPE_TEXT,
            '测试消息'
        )
        
        self.assertIsNotNone(message)
        self.assertIsNone(message['player_name'])
    
    def test_multiple_rooms_chat(self):
        """测试多个房间的聊天消息隔离"""
        init_room_chat('room1')
        init_room_chat('room2')
        
        add_chat_message('room1', 'player1', CHAT_MESSAGE_TYPE_TEXT, '房间1的消息')
        add_chat_message('room2', 'player2', CHAT_MESSAGE_TYPE_TEXT, '房间2的消息')
        
        room1_messages = get_room_chat_messages('room1')
        room2_messages = get_room_chat_messages('room2')
        
        self.assertEqual(len(room1_messages), 1)
        self.assertEqual(len(room2_messages), 1)
        self.assertEqual(room1_messages[0]['content'], '房间1的消息')
        self.assertEqual(room2_messages[0]['content'], '房间2的消息')


class TestChatMessageTypes(unittest.TestCase):
    """聊天消息类型测试"""
    
    def setUp(self):
        """测试前初始化"""
        chat_messages.clear()
        players.clear()
        
        players['player1'] = {
            'id': 'player1',
            'name': '玩家1',
            'online': True,
            'status': 'idle',
            'current_room': None
        }
        
        init_room_chat('room1')
    
    def test_text_message_type(self):
        """测试文本消息类型"""
        msg = add_chat_message('room1', 'player1', CHAT_MESSAGE_TYPE_TEXT, '你好')
        self.assertEqual(msg['type'], CHAT_MESSAGE_TYPE_TEXT)
    
    def test_system_message_type(self):
        """测试系统消息类型"""
        msg = add_chat_message('room1', None, CHAT_MESSAGE_TYPE_SYSTEM, '系统提示')
        self.assertEqual(msg['type'], CHAT_MESSAGE_TYPE_SYSTEM)
    
    def test_move_message_type(self):
        """测试落子消息类型"""
        msg = add_chat_message('room1', 'player1', CHAT_MESSAGE_TYPE_MOVE, '落子', {'row': 7, 'col': 7})
        self.assertEqual(msg['type'], CHAT_MESSAGE_TYPE_MOVE)
    
    def test_undo_message_type(self):
        """测试悔棋消息类型"""
        msg = add_chat_message('room1', None, CHAT_MESSAGE_TYPE_UNDO, '悔棋', {'accepted': True})
        self.assertEqual(msg['type'], CHAT_MESSAGE_TYPE_UNDO)


class TestChatMessageFormat(unittest.TestCase):
    """聊天消息格式测试"""
    
    def setUp(self):
        """测试前初始化"""
        chat_messages.clear()
        players.clear()
        
        players['player1'] = {
            'id': 'player1',
            'name': '测试玩家',
            'online': True,
            'status': 'idle',
            'current_room': None
        }
        
        init_room_chat('room1')
    
    def test_message_has_all_fields(self):
        """测试消息包含所有必要字段"""
        msg = add_chat_message('room1', 'player1', CHAT_MESSAGE_TYPE_TEXT, '测试')
        
        required_fields = ['id', 'room_id', 'player_id', 'player_name', 'type', 'content', 'extra_data', 'timestamp']
        for field in required_fields:
            self.assertIn(field, msg)
    
    def test_message_extra_data_default(self):
        """测试额外数据默认为空字典"""
        msg = add_chat_message('room1', 'player1', CHAT_MESSAGE_TYPE_TEXT, '测试')
        self.assertEqual(msg['extra_data'], {})
    
    def test_message_id_is_unique(self):
        """测试消息ID唯一"""
        msg1 = add_chat_message('room1', 'player1', CHAT_MESSAGE_TYPE_TEXT, '消息1')
        msg2 = add_chat_message('room1', 'player1', CHAT_MESSAGE_TYPE_TEXT, '消息2')
        
        self.assertNotEqual(msg1['id'], msg2['id'])
    
    def test_message_timestamp(self):
        """测试消息时间戳"""
        import time
        import math
        
        before = math.floor(time.time())
        msg = add_chat_message('room1', 'player1', CHAT_MESSAGE_TYPE_TEXT, '测试')
        after = math.ceil(time.time())
        
        self.assertGreaterEqual(msg['timestamp'], before)
        self.assertLessEqual(msg['timestamp'], after)


if __name__ == '__main__':
    unittest.main()
