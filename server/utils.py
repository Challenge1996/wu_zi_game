#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务端工具函数
"""

from constants import (
    CHALLENGE_EXPIRE_SECONDS,
    UNDO_REQUEST_EXPIRE_SECONDS,
    ROOM_STATUS_WAITING,
    ROOM_STATUS_COIN_TOSS,
    ROOM_STATUS_PLAYING,
    ROOM_STATUS_FINISHED
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
