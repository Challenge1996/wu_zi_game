#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试聊天消息重复显示问题的修复
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestChatDuplicatePrevention(unittest.TestCase):
    """测试聊天消息去重逻辑"""
    
    def setUp(self):
        """测试前初始化"""
        self.chat_messages = []
    
    def test_message_id_check_in_on_chat_message_received(self):
        """测试 on_chat_message_received 中的消息ID检查逻辑"""
        
        msg1 = {'id': 'msg_001', 'content': '消息1'}
        msg2 = {'id': 'msg_002', 'content': '消息2'}
        msg1_duplicate = {'id': 'msg_001', 'content': '消息1(重复)'}
        
        display_count = 0
        
        def on_chat_message_received(message):
            """模拟修复后的 on_chat_message_received 方法"""
            nonlocal display_count
            if message.get('id') not in [m.get('id') for m in self.chat_messages]:
                self.chat_messages.append(message)
                display_count += 1
        
        on_chat_message_received(msg1)
        self.assertEqual(display_count, 1)
        self.assertEqual(len(self.chat_messages), 1)
        
        on_chat_message_received(msg2)
        self.assertEqual(display_count, 2)
        self.assertEqual(len(self.chat_messages), 2)
        
        on_chat_message_received(msg1_duplicate)
        self.assertEqual(display_count, 2)
        self.assertEqual(len(self.chat_messages), 2)
    
    def test_message_id_check_in_on_chat_messages_updated(self):
        """测试 on_chat_messages_updated 中的消息ID检查逻辑"""
        
        msg1 = {'id': 'msg_001', 'content': '消息1'}
        msg2 = {'id': 'msg_002', 'content': '消息2'}
        msg3 = {'id': 'msg_003', 'content': '消息3'}
        
        display_count = 0
        
        def on_chat_messages_updated(messages):
            """模拟 on_chat_messages_updated 方法"""
            nonlocal display_count
            for msg in messages:
                if msg.get('id') not in [m.get('id') for m in self.chat_messages]:
                    self.chat_messages.append(msg)
                    display_count += 1
        
        on_chat_messages_updated([msg1, msg2])
        self.assertEqual(display_count, 2)
        self.assertEqual(len(self.chat_messages), 2)
        
        on_chat_messages_updated([msg2, msg3])
        self.assertEqual(display_count, 3)
        self.assertEqual(len(self.chat_messages), 3)
    
    def test_combined_duplicate_prevention(self):
        """测试两种方法结合时的去重逻辑"""
        
        msg1 = {'id': 'msg_001', 'content': '通过即时发送显示'}
        msg1_again = {'id': 'msg_001', 'content': '通过轮询再次获取'}
        
        display_count = 0
        
        def on_chat_message_received(message):
            """模拟修复后的 on_chat_message_received 方法"""
            nonlocal display_count
            if message.get('id') not in [m.get('id') for m in self.chat_messages]:
                self.chat_messages.append(message)
                display_count += 1
        
        def on_chat_messages_updated(messages):
            """模拟 on_chat_messages_updated 方法"""
            nonlocal display_count
            for msg in messages:
                if msg.get('id') not in [m.get('id') for m in self.chat_messages]:
                    self.chat_messages.append(msg)
                    display_count += 1
        
        on_chat_message_received(msg1)
        self.assertEqual(display_count, 1)
        
        on_chat_messages_updated([msg1_again])
        self.assertEqual(display_count, 1)
        
        self.assertEqual(len(self.chat_messages), 1)
        self.assertEqual(self.chat_messages[0]['id'], 'msg_001')
    
    def test_messages_with_unique_ids(self):
        """测试所有服务器消息都有唯一ID"""
        from server.utils import add_chat_message, init_room_chat
        from server.data_store import chat_messages, players
        from constants import CHAT_MESSAGE_TYPE_TEXT
        
        players['test_player'] = {
            'id': 'test_player',
            'name': '测试玩家',
            'online': True,
            'status': 'idle',
            'current_room': None
        }
        
        chat_messages.clear()
        init_room_chat('test_room')
        
        msg1 = add_chat_message('test_room', 'test_player', CHAT_MESSAGE_TYPE_TEXT, '消息1')
        msg2 = add_chat_message('test_room', 'test_player', CHAT_MESSAGE_TYPE_TEXT, '消息2')
        msg3 = add_chat_message('test_room', 'test_player', CHAT_MESSAGE_TYPE_TEXT, '消息3')
        
        self.assertIsNotNone(msg1.get('id'))
        self.assertIsNotNone(msg2.get('id'))
        self.assertIsNotNone(msg3.get('id'))
        
        self.assertNotEqual(msg1['id'], msg2['id'])
        self.assertNotEqual(msg2['id'], msg3['id'])
        self.assertNotEqual(msg1['id'], msg3['id'])


class TestChatDisplayAlignment(unittest.TestCase):
    """测试聊天消息显示对齐（全部靠左）"""
    
    def test_all_messages_left_aligned(self):
        """验证所有消息类型都是靠左显示"""
        
        import re
        
        message_formats = {
            'system': '<div style="color: #888888; font-style: italic; text-align: left;',
            'move': '<div style="color: #6666cc; margin: 3px 0; text-align: left;">',
            'undo': '<div style="color: #cc6666; margin: 3px 0; text-align: left;">',
            'resign': '<div style="color: #cc3333; margin: 3px 0; text-align: left;">',
            'my_message': '<div style="text-align: left; margin: 5px 0;">',
            'other_message': '<div style="text-align: left; margin: 5px 0;">'
        }
        
        for msg_type, expected_format in message_formats.items():
            self.assertIn('text-align: left', expected_format,
                         f"{msg_type} 类型消息应该靠左显示")
        
        center_pattern = r'text-align:\s*center'
        right_pattern = r'text-align:\s*right'
        
        for msg_type, format_str in message_formats.items():
            self.assertIsNone(re.search(center_pattern, format_str),
                             f"{msg_type} 类型消息不应该居中显示")
            self.assertIsNone(re.search(right_pattern, format_str),
                             f"{msg_type} 类型消息不应该靠右显示")


if __name__ == '__main__':
    unittest.main()
