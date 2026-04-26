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
    PLAYER_STATUS_SPECTATING,
    RESIGN_REASON_TIMEOUT,
    RESIGN_REASON_OFFLINE,
    PLAYER_BLACK,
    PLAYER_WHITE,
    CHAT_MESSAGE_TYPE_TEXT,
    CHAT_MESSAGE_TYPE_SYSTEM,
    CHAT_MESSAGE_TYPE_SPECTATOR_JOIN,
    CHAT_MESSAGE_TYPE_SPECTATOR_LEAVE,
    ROOM_VISIBILITY_PUBLIC,
    HOT_GAME_SPECTATOR_THRESHOLD,
    CHAT_MAX_HISTORY
)
from util import get_timestamp, generate_id
from server.data_store import players, rooms, undo_requests, challenges, chat_messages


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
    
    chat_messages = get_room_chat_messages(room_id, player_id)
    
    spectator_count = room.get('spectator_count', 0)
    is_hot_game = spectator_count > HOT_GAME_SPECTATOR_THRESHOLD
    
    spectators_info = get_room_spectators_info(room_id)
    
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
        'visibility': room.get('visibility', ROOM_VISIBILITY_PUBLIC),
        'spectator_count': spectator_count,
        'is_hot_game': is_hot_game,
        'spectators': spectators_info,
        'game_state': game_state,
        'undo_request': undo_request_info,
        'chat_messages': chat_messages,
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


def init_room_chat(room_id):
    """初始化房间聊天
    Args:
        room_id: 房间ID
    """
    if room_id not in chat_messages:
        chat_messages[room_id] = []


def add_chat_message(room_id, player_id, message_type, content, extra_data=None):
    """添加聊天消息
    Args:
        room_id: 房间ID
        player_id: 发送者ID（系统消息为None）
        message_type: 消息类型
        content: 消息内容
        extra_data: 额外数据（如落子位置等）
    Returns:
        消息对象
    """
    init_room_chat(room_id)
    
    now = get_timestamp()
    message_id = generate_id()
    
    message = {
        'id': message_id,
        'room_id': room_id,
        'player_id': player_id,
        'player_name': players[player_id]['name'] if player_id in players else None,
        'type': message_type,
        'content': content,
        'extra_data': extra_data or {},
        'timestamp': now
    }
    
    chat_messages[room_id].append(message)
    
    if len(chat_messages[room_id]) > CHAT_MAX_HISTORY:
        chat_messages[room_id] = chat_messages[room_id][-CHAT_MAX_HISTORY:]
    
    return message


def get_room_chat_messages(room_id, player_id=None, since_id=None):
    """获取房间的聊天消息
    Args:
        room_id: 房间ID
        player_id: 玩家ID（用于判断消息是谁发的）
        since_id: 从指定消息ID之后获取（用于增量获取）
    Returns:
        消息列表
    """
    if room_id not in chat_messages:
        return []
    
    messages = chat_messages[room_id]
    
    if since_id:
        for i, msg in enumerate(messages):
            if msg['id'] == since_id:
                messages = messages[i+1:]
                break
    
    result = []
    for msg in messages:
        msg_info = {
            'id': msg['id'],
            'room_id': msg['room_id'],
            'player_id': msg['player_id'],
            'player_name': msg['player_name'],
            'type': msg['type'],
            'content': msg['content'],
            'extra_data': msg['extra_data'],
            'timestamp': msg['timestamp']
        }
        
        if player_id is not None:
            msg_info['is_my_message'] = (msg['player_id'] == player_id)
        
        result.append(msg_info)
    
    return result


def get_room_spectators_info(room_id):
    """获取房间观战者信息
    Args:
        room_id: 房间ID
    Returns:
        观战者信息列表
    """
    if room_id not in rooms:
        return []
    
    room = rooms[room_id]
    spectators = room.get('spectators', set())
    
    result = []
    for spectator_id in spectators:
        if spectator_id in players:
            player = players[spectator_id]
            result.append({
                'id': spectator_id,
                'name': player['name'],
                'online': player.get('online', True)
            })
    
    return result


def is_room_player(room_id, player_id):
    """检查玩家是否是房间的对局玩家
    Args:
        room_id: 房间ID
        player_id: 玩家ID
    Returns:
        bool: 是否是对局玩家
    """
    if room_id not in rooms:
        return False
    
    room = rooms[room_id]
    return (player_id == room.get('player1') or 
            player_id == room.get('player2') or
            player_id == room.get('challenger_id') or
            player_id == room.get('challenged_id'))


def is_room_spectator(room_id, player_id):
    """检查玩家是否是房间的观战者
    Args:
        room_id: 房间ID
        player_id: 玩家ID
    Returns:
        bool: 是否是观战者
    """
    if room_id not in rooms:
        return False
    
    room = rooms[room_id]
    spectators = room.get('spectators', set())
    return player_id in spectators


def add_spectator(room_id, player_id):
    """添加观战者
    Args:
        room_id: 房间ID
        player_id: 玩家ID
    Returns:
        (success, message)
    """
    if room_id not in rooms:
        return False, "房间不存在"
    
    if player_id not in players:
        return False, "玩家不存在"
    
    room = rooms[room_id]
    player = players[player_id]
    
    if is_room_player(room_id, player_id):
        return False, "您是该房间的对局玩家，不能作为观战者加入"
    
    spectators = room.get('spectators', set())
    
    if player_id in spectators:
        return False, "您已经在观战此对局"
    
    spectators.add(player_id)
    room['spectators'] = spectators
    room['spectator_count'] = len(spectators)
    
    player['status'] = PLAYER_STATUS_SPECTATING
    player['current_room'] = room_id
    
    spectator_name = player['name']
    add_chat_message(
        room_id,
        None,
        CHAT_MESSAGE_TYPE_SPECTATOR_JOIN,
        f"{spectator_name} 进入了观战",
        {'spectator_id': player_id, 'spectator_name': spectator_name}
    )
    
    return True, f"成功加入观战，当前共有 {len(spectators)} 人观战"


def remove_spectator(room_id, player_id):
    """移除观战者
    Args:
        room_id: 房间ID
        player_id: 玩家ID
    Returns:
        (success, message)
    """
    if room_id not in rooms:
        return False, "房间不存在"
    
    room = rooms[room_id]
    spectators = room.get('spectators', set())
    
    if player_id not in spectators:
        return False, "您不是该房间的观战者"
    
    spectators.remove(player_id)
    room['spectators'] = spectators
    room['spectator_count'] = len(spectators)
    
    if player_id in players:
        player = players[player_id]
        player['status'] = PLAYER_STATUS_IDLE
        player['current_room'] = None
        
        spectator_name = player['name']
        add_chat_message(
            room_id,
            None,
            CHAT_MESSAGE_TYPE_SPECTATOR_LEAVE,
            f"{spectator_name} 离开了观战",
            {'spectator_id': player_id, 'spectator_name': spectator_name}
        )
    
    return True, "成功离开观战"


def get_public_rooms():
    """获取公开房间列表
    Returns:
        公开房间列表（包含观战人数和热门标识）
    """
    public_rooms = []
    
    for room_id, room in rooms.items():
        visibility = room.get('visibility', ROOM_VISIBILITY_PUBLIC)
        if visibility != ROOM_VISIBILITY_PUBLIC:
            continue
        
        spectator_count = room.get('spectator_count', 0)
        is_hot_game = spectator_count > HOT_GAME_SPECTATOR_THRESHOLD
        
        room_info = {
            'id': room['id'],
            'name': room['name'],
            'creator': room['creator'],
            'player1': room['player1'],
            'player2': room['player2'],
            'player1_name': players[room['player1']]['name'] if room['player1'] in players else None,
            'player2_name': players[room['player2']]['name'] if room['player2'] in players else None,
            'status': room['status'],
            'visibility': visibility,
            'spectator_count': spectator_count,
            'is_hot_game': is_hot_game,
            'created_at': room['created_at'],
            'started_at': room['started_at'],
            'finished_at': room['finished_at'],
            'winner': room['winner']
        }
        
        public_rooms.append(room_info)
    
    public_rooms.sort(key=lambda x: x['spectator_count'], reverse=True)
    
    return public_rooms
