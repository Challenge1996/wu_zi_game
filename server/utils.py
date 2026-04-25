#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务端工具函数
"""

from constants import (
    CHALLENGE_EXPIRE_SECONDS,
    UNDO_REQUEST_EXPIRE_SECONDS,
    MOVE_TIMEOUT_SECONDS,
    PLAYER_OFFLINE_TIMEOUT,
    ROOM_STATUS_WAITING,
    ROOM_STATUS_COIN_TOSS,
    ROOM_STATUS_PLAYING,
    ROOM_STATUS_FINISHED,
    PLAYER_STATUS_IDLE,
    RESIGN_REASON_TIMEOUT,
    RESIGN_REASON_OFFLINE,
    PLAYER_BLACK,
    PLAYER_WHITE
)
from util import get_timestamp
from server.data_store import players, rooms, undo_requests, challenges


def get_player_info(player_id):
    """获取玩家公开信息"""
    if player_id not in players:
        return None
    player = players[player_id]
    return {
        'id': player['id'],
        'name': player['name'],
        'online': player['online'],
        'status': player['status'],
        'current_room': player['current_room']
    }


def get_room_info(room_id, player_id=None):
    """获取房间信息"""
    if room_id not in rooms:
        return None
    room = rooms[room_id]
    game = room['game']
    game_state = game.get_game_state(player_id)
    
    undo_request = get_room_undo_request(room_id)
    undo_request_info = get_undo_request_info(undo_request, player_id)
    
    return {
        'id': room['id'],
        'name': room['name'],
        'creator': room['creator'],
        'challenger_id': room.get('challenger_id'),
        'challenged_id': room.get('challenged_id'),
        'player1': room['player1'],
        'player2': room['player2'],
        'player1_name': players[room['player1']]['name'] if room['player1'] in players else None,
        'player2_name': players[room['player2']]['name'] if room['player2'] in players else None,
        'status': room['status'],
        'game_state': game_state,
        'undo_request': undo_request_info,
        'created_at': room['created_at'],
        'started_at': room['started_at'],
        'finished_at': room['finished_at'],
        'winner': room['winner']
    }


def cleanup_expired_challenges():
    """清理过期的挑战"""
    now = get_timestamp()
    expired = []
    for cid, challenge in challenges.items():
        if challenge['status'] == 'pending' and now > challenge['expires_at']:
            challenge['status'] = 'expired'
            expired.append(cid)
    return expired


def cleanup_expired_undo_requests():
    """清理过期的悔棋请求"""
    now = get_timestamp()
    expired = []
    for uid, req in undo_requests.items():
        if req['status'] == 'pending' and now > req['expires_at']:
            req['status'] = 'expired'
            expired.append(uid)
    return expired


def get_room_undo_request(room_id):
    """获取房间的悔棋请求状态"""
    pending_requests = []
    for uid, req in undo_requests.items():
        if req['room_id'] == room_id and req['status'] == 'pending':
            pending_requests.append(req)
    
    if not pending_requests:
        return None
    
    return pending_requests[-1]


def get_undo_request_info(req, player_id=None):
    """获取悔棋请求信息"""
    if req is None:
        return None
    
    info = {
        'id': req['id'],
        'room_id': req['room_id'],
        'requester': req['requester'],
        'requester_name': players[req['requester']]['name'] if req['requester'] in players else None,
        'requested': req['requested'],
        'requested_name': players[req['requested']]['name'] if req['requested'] in players else None,
        'status': req['status'],
        'created_at': req['created_at'],
        'expires_at': req['expires_at']
    }
    
    if player_id is not None:
        info['is_my_request'] = (req['requester'] == player_id)
        info['is_requested_to_me'] = (req['requested'] == player_id)
    
    return info


def get_room_status_name(status):
    """获取房间状态名称"""
    names = {
        ROOM_STATUS_WAITING: '等待中',
        ROOM_STATUS_COIN_TOSS: '抛硬币阶段',
        ROOM_STATUS_PLAYING: '游戏中',
        ROOM_STATUS_FINISHED: '已结束'
    }
    return names.get(status, status)


def check_move_timeout(room):
    """检查当前玩家是否超时未下子
    Args:
        room: 房间对象
    Returns:
        (是否超时, 消息)
    """
    if room['status'] != ROOM_STATUS_PLAYING:
        return False, None
    
    game = room['game']
    if game.game_over:
        return False, None
    
    time_since_last_move = game.get_time_since_last_move()
    
    if time_since_last_move >= MOVE_TIMEOUT_SECONDS:
        current_player_color = game.get_current_player()
        
        success, message = game.resign(current_player_color, RESIGN_REASON_TIMEOUT)
        
        if success:
            room['status'] = ROOM_STATUS_FINISHED
            room['finished_at'] = get_timestamp()
            room['winner'] = game.get_winner()
            
            if room['player1'] in players:
                players[room['player1']]['status'] = PLAYER_STATUS_IDLE
                players[room['player1']]['current_room'] = None
            if room['player2'] in players:
                players[room['player2']]['status'] = PLAYER_STATUS_IDLE
                players[room['player2']]['current_room'] = None
            
            return True, message
    
    return False, None


def check_player_offline(room):
    """检查房间中的玩家是否离线
    Args:
        room: 房间对象
    Returns:
        (是否有玩家离线, 消息)
    """
    if room['status'] != ROOM_STATUS_PLAYING:
        return False, None
    
    game = room['game']
    if game.game_over:
        return False, None
    
    now = get_timestamp()
    
    player1_id = room['player1']
    player2_id = room['player2']
    
    player1_offline = False
    player2_offline = False
    
    if player1_id in players:
        player1 = players[player1_id]
        if not player1.get('online', False):
            player1_offline = True
        else:
            last_heartbeat = player1.get('last_heartbeat', 0)
            if now - last_heartbeat > PLAYER_OFFLINE_TIMEOUT:
                player1_offline = True
    
    if player2_id in players:
        player2 = players[player2_id]
        if not player2.get('online', False):
            player2_offline = True
        else:
            last_heartbeat = player2.get('last_heartbeat', 0)
            if now - last_heartbeat > PLAYER_OFFLINE_TIMEOUT:
                player2_offline = True
    
    if player1_offline and player2_offline:
        room['status'] = ROOM_STATUS_FINISHED
        room['finished_at'] = get_timestamp()
        game.game_over = True
        game.game_phase = 'finished'
        game.winner = None
        game.resign_reason = RESIGN_REASON_OFFLINE
        
        if player1_id in players:
            players[player1_id]['status'] = PLAYER_STATUS_IDLE
            players[player1_id]['current_room'] = None
        if player2_id in players:
            players[player2_id]['status'] = PLAYER_STATUS_IDLE
            players[player2_id]['current_room'] = None
        
        return True, "双方玩家均已离线，游戏结束"
    
    if player1_offline:
        player1_color = game.get_player_color(player1_id)
        if player1_color:
            success, message = game.resign(player1_color, RESIGN_REASON_OFFLINE)
            if success:
                room['status'] = ROOM_STATUS_FINISHED
                room['finished_at'] = get_timestamp()
                room['winner'] = game.get_winner()
                
                if player1_id in players:
                    players[player1_id]['status'] = PLAYER_STATUS_IDLE
                    players[player1_id]['current_room'] = None
                if player2_id in players:
                    players[player2_id]['status'] = PLAYER_STATUS_IDLE
                    players[player2_id]['current_room'] = None
                
                return True, message
    
    if player2_offline:
        player2_color = game.get_player_color(player2_id)
        if player2_color:
            success, message = game.resign(player2_color, RESIGN_REASON_OFFLINE)
            if success:
                room['status'] = ROOM_STATUS_FINISHED
                room['finished_at'] = get_timestamp()
                room['winner'] = game.get_winner()
                
                if player1_id in players:
                    players[player1_id]['status'] = PLAYER_STATUS_IDLE
                    players[player1_id]['current_room'] = None
                if player2_id in players:
                    players[player2_id]['status'] = PLAYER_STATUS_IDLE
                    players[player2_id]['current_room'] = None
                
                return True, message
    
    return False, None


def cleanup_all_timeouts():
    """清理所有超时的房间
    Returns:
        超时处理的房间列表
    """
    results = []
    
    for room_id, room in rooms.items():
        if room['status'] == ROOM_STATUS_PLAYING:
            timeout, msg = check_move_timeout(room)
            if timeout:
                results.append({
                    'room_id': room_id,
                    'type': 'timeout',
                    'message': msg
                })
                continue
            
            offline, msg = check_player_offline(room)
            if offline:
                results.append({
                    'room_id': room_id,
                    'type': 'offline',
                    'message': msg
                })
    
    return results
