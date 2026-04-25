#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户端核心逻辑
"""

import threading
import time
from constants import (
    SERVER_URL,
    HEARTBEAT_INTERVAL,
    PLAYER_BLACK,
    PLAYER_WHITE,
    GAME_PHASE_WAITING,
    GAME_PHASE_COIN_TOSS,
    GAME_PHASE_PLAYING,
    ROOM_STATUS_WAITING,
    ROOM_STATUS_COIN_TOSS,
    ROOM_STATUS_PLAYING,
    ROOM_STATUS_FINISHED
)
from network import NetworkClient
from util import get_player_color_name


class ClientCore:
    """客户端核心逻辑类"""
    
    def __init__(self, server_url=None):
        self.server_url = server_url or SERVER_URL
        self.network_client = NetworkClient(self.server_url)
        self.player_id = None
        self.player_name = None
        self.current_room_id = None
        self.heartbeat_thread = None
        self.running = False
    
    def _request(self, method, endpoint, data=None, params=None):
        """发送HTTP请求到服务端"""
        return self.network_client._request(method, endpoint, data, params)
    
    def _heartbeat_loop(self):
        """心跳循环"""
        while self.running and self.player_id:
            time.sleep(HEARTBEAT_INTERVAL)
            if self.player_id:
                self._request('POST', '/api/player/heartbeat', {'player_id': self.player_id})
    
    def start_heartbeat(self):
        """启动心跳"""
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            return
        
        self.running = True
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
    
    def stop_heartbeat(self):
        """停止心跳"""
        self.running = False
    
    def check_server_health(self):
        """检查服务端状态"""
        return self._request('GET', '/api/health')
    
    def register_player(self, name=None):
        """玩家注册"""
        data = {}
        if name:
            data['name'] = name
        
        success, result = self._request('POST', '/api/player/register', data)
        if success and result.get('success'):
            self.player_id = result.get('player_id')
            self.player_name = result.get('name')
            self.start_heartbeat()
            return True, result
        return False, result
    
    def go_offline(self):
        """玩家下线"""
        if not self.player_id:
            return False, "您还未注册"
        
        success, result = self._request('POST', '/api/player/offline', {'player_id': self.player_id})
        if success and result.get('success'):
            self.stop_heartbeat()
            self.player_id = None
            self.current_room_id = None
            return True, result
        return False, result
    
    def list_online_players(self):
        """获取在线玩家列表"""
        return self._request('GET', '/api/player/list')
    
    def send_challenge(self, challenged_id):
        """发起挑战"""
        if not self.player_id:
            return False, "请先注册玩家"
        
        data = {
            'challenger_id': self.player_id,
            'challenged_id': challenged_id
        }
        
        return self._request('POST', '/api/challenge/send', data)
    
    def list_my_challenges(self):
        """获取我的挑战列表"""
        if not self.player_id:
            return False, "请先注册玩家"
        
        params = {'player_id': self.player_id}
        return self._request('GET', '/api/challenge/list', params=params)
    
    def accept_challenge(self, challenge_id):
        """接受挑战"""
        if not self.player_id:
            return False, "请先注册玩家"
        
        data = {
            'challenge_id': challenge_id,
            'player_id': self.player_id
        }
        
        success, result = self._request('POST', '/api/challenge/accept', data)
        if success and result.get('success'):
            room_id = result.get('room_id')
            if room_id:
                self.current_room_id = room_id
        return success, result
    
    def decline_challenge(self, challenge_id):
        """拒绝挑战"""
        if not self.player_id:
            return False, "请先注册玩家"
        
        data = {
            'challenge_id': challenge_id,
            'player_id': self.player_id
        }
        
        return self._request('POST', '/api/challenge/decline', data)
    
    def get_room_info(self, room_id=None):
        """获取房间信息"""
        room_to_check = room_id or self.current_room_id
        if not room_to_check:
            return False, "没有指定房间ID"
        
        params = {'room_id': room_to_check}
        if self.player_id:
            params['player_id'] = self.player_id
        
        return self._request('GET', '/api/room/info', params=params)
    
    def make_coin_choice(self, choice, room_id=None):
        """抛硬币阶段进行猜测"""
        room_to_use = room_id or self.current_room_id
        if not room_to_use:
            return False, "没有指定房间ID"
        
        if not self.player_id:
            return False, "请先注册玩家"
        
        data = {
            'player_id': self.player_id,
            'room_id': room_to_use,
            'choice': choice
        }
        
        return self._request('POST', '/api/game/coin_choice', data)
    
    def resolve_coin_toss(self, room_id=None):
        """解决抛硬币结果"""
        room_to_use = room_id or self.current_room_id
        if not room_to_use:
            return False, "没有指定房间ID"
        
        data = {'room_id': room_to_use}
        return self._request('POST', '/api/game/resolve_coin', data)
    
    def choose_color(self, color_choice, room_id=None):
        """选择执子颜色"""
        room_to_use = room_id or self.current_room_id
        if not room_to_use:
            return False, "没有指定房间ID"
        
        if not self.player_id:
            return False, "请先注册玩家"
        
        data = {
            'player_id': self.player_id,
            'room_id': room_to_use,
            'color_choice': color_choice
        }
        
        return self._request('POST', '/api/game/choose_color', data)
    
    def finalize_colors(self, player2_id, room_id=None):
        """确定第二个玩家颜色并开始游戏"""
        room_to_use = room_id or self.current_room_id
        if not room_to_use:
            return False, "没有指定房间ID"
        
        data = {
            'room_id': room_to_use,
            'player2_id': player2_id
        }
        
        return self._request('POST', '/api/game/finalize_colors', data)
    
    def place_piece(self, row, col, room_id=None):
        """落子"""
        room_to_use = room_id or self.current_room_id
        if not room_to_use:
            return False, "没有指定房间ID"
        
        if not self.player_id:
            return False, "请先注册玩家"
        
        data = {
            'player_id': self.player_id,
            'room_id': room_to_use,
            'row': row,
            'col': col
        }
        
        return self._request('POST', '/api/game/place_piece', data)
    
    def request_undo(self, room_id=None):
        """发起悔棋请求"""
        room_to_use = room_id or self.current_room_id
        if not room_to_use:
            return False, "没有指定房间ID"
        
        if not self.player_id:
            return False, "请先注册玩家"
        
        data = {
            'player_id': self.player_id,
            'room_id': room_to_use
        }
        
        return self._request('POST', '/api/game/undo/request', data)
    
    def respond_undo(self, accept, room_id=None):
        """响应悔棋请求"""
        room_to_use = room_id or self.current_room_id
        if not room_to_use:
            return False, "没有指定房间ID"
        
        if not self.player_id:
            return False, "请先注册玩家"
        
        data = {
            'player_id': self.player_id,
            'room_id': room_to_use,
            'accept': accept
        }
        
        return self._request('POST', '/api/game/undo/respond', data)
    
    def get_undo_status(self, room_id=None):
        """获取悔棋请求状态"""
        room_to_use = room_id or self.current_room_id
        if not room_to_use:
            return False, "没有指定房间ID"
        
        params = {
            'room_id': room_to_use,
            'player_id': self.player_id
        }
        
        return self._request('GET', '/api/game/undo/status', params=params)
    
    def undo_move(self, room_id=None):
        """悔棋（已废弃，使用 request_undo 代替）"""
        print("⚠️  直接悔棋功能已废弃，现在需要对手同意才能悔棋。")
        return self.request_undo(room_id)
    
    def reset_game(self, room_id=None):
        """重置游戏"""
        room_to_use = room_id or self.current_room_id
        if not room_to_use:
            return False, "没有指定房间ID"
        
        if not self.player_id:
            return False, "请先注册玩家"
        
        data = {
            'player_id': self.player_id,
            'room_id': room_to_use
        }
        
        return self._request('POST', '/api/game/reset', data)
    
    def quick_start(self, player2_id):
        """快速开始游戏（跳过抛硬币）"""
        if not self.player_id:
            return False, "请先注册玩家"
        
        data = {
            'player1_id': self.player_id,
            'player2_id': player2_id
        }
        
        success, result = self._request('POST', '/api/game/quick_start', data)
        if success and result.get('success'):
            room_id = result.get('room_id')
            if room_id:
                self.current_room_id = room_id
        return success, result
    
    def resign(self, room_id=None):
        """认输
        Args:
            room_id: 房间ID，如果为None则使用当前房间
        Returns:
            (success, result)
        """
        room_to_use = room_id or self.current_room_id
        if not room_to_use:
            return False, "没有指定房间ID"
        
        if not self.player_id:
            return False, "请先注册玩家"
        
        data = {
            'player_id': self.player_id,
            'room_id': room_to_use
        }
        
        return self._request('POST', '/api/game/resign', data)
    
    def get_room_status_name(self, status):
        """获取房间状态名称"""
        names = {
            ROOM_STATUS_WAITING: '等待中',
            ROOM_STATUS_COIN_TOSS: '抛硬币阶段',
            ROOM_STATUS_PLAYING: '游戏中',
            ROOM_STATUS_FINISHED: '已结束'
        }
        return names.get(status, status)
    
    def get_game_phase_name(self, phase):
        """获取游戏阶段名称"""
        phase_names = {
            GAME_PHASE_WAITING: '等待中',
            GAME_PHASE_COIN_TOSS: '抛硬币阶段',
            GAME_PHASE_PLAYING: '游戏进行中'
        }
        return phase_names.get(phase, phase)
