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
    CHAT_MAX_HISTORY,
    RANK_LIST,
    RANK_THRESHOLDS,
    SCORE_WIN,
    SCORE_LOSE,
    SCORE_DRAW
)
from util import get_timestamp, generate_id
import server
from server.data_store import (
    sync_player, sync_room, sync_chat_message, sync_game_record,
    sync_spectator_add, sync_spectator_remove,
    USE_DATABASE
)

if USE_DATABASE:
    from server.database import (
        get_game_record_db,
        get_player_game_records_db,
        get_player as get_player_from_db
    )


def get_player_info(player_id):
    """获取玩家公开信息"""
    if player_id not in server.players:
        return None
    player = server.players[player_id]
    return {
        'id': player['id'],
        'name': player['name'],
        'online': player['online'],
        'status': player['status'],
        'current_room': player['current_room']
    }


def get_room_info(room_id, player_id=None):
    """获取房间信息"""
    if room_id not in server.rooms:
        return None
    room = server.rooms[room_id]
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
        'player1_name': server.players[room['player1']]['name'] if room['player1'] in server.players else None,
        'player2_name': server.players[room['player2']]['name'] if room['player2'] in server.players else None,
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
    for cid, challenge in server.challenges.items():
        if challenge['status'] == 'pending' and now > challenge['expires_at']:
            challenge['status'] = 'expired'
            expired.append(cid)
    return expired


def cleanup_expired_undo_requests():
    """清理过期的悔棋请求"""
    now = get_timestamp()
    expired = []
    for uid, req in server.undo_requests.items():
        if req['status'] == 'pending' and now > req['expires_at']:
            req['status'] = 'expired'
            expired.append(uid)
    return expired


def get_room_undo_request(room_id):
    """获取房间的悔棋请求状态"""
    pending_requests = []
    for uid, req in server.undo_requests.items():
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
        'requester_name': server.players[req['requester']]['name'] if req['requester'] in server.players else None,
        'requested': req['requested'],
        'requested_name': server.players[req['requested']]['name'] if req['requested'] in server.players else None,
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
            
            if room['player1'] in server.players:
                server.players[room['player1']]['status'] = PLAYER_STATUS_IDLE
                server.players[room['player1']]['current_room'] = None
            if room['player2'] in server.players:
                server.players[room['player2']]['status'] = PLAYER_STATUS_IDLE
                server.players[room['player2']]['current_room'] = None
            
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
    
    if player1_id in server.players:
        player1 = server.players[player1_id]
        if not player1.get('online', False):
            player1_offline = True
        else:
            last_heartbeat = player1.get('last_heartbeat', 0)
            if now - last_heartbeat > PLAYER_OFFLINE_TIMEOUT:
                player1_offline = True
    
    if player2_id in server.players:
        player2 = server.players[player2_id]
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
        
        if player1_id in server.players:
            server.players[player1_id]['status'] = PLAYER_STATUS_IDLE
            server.players[player1_id]['current_room'] = None
        if player2_id in server.players:
            server.players[player2_id]['status'] = PLAYER_STATUS_IDLE
            server.players[player2_id]['current_room'] = None
        
        return True, "双方玩家均已离线，游戏结束"
    
    if player1_offline:
        player1_color = game.get_player_color(player1_id)
        if player1_color:
            success, message = game.resign(player1_color, RESIGN_REASON_OFFLINE)
            if success:
                room['status'] = ROOM_STATUS_FINISHED
                room['finished_at'] = get_timestamp()
                room['winner'] = game.get_winner()
                
                if player1_id in server.players:
                    server.players[player1_id]['status'] = PLAYER_STATUS_IDLE
                    server.players[player1_id]['current_room'] = None
                if player2_id in server.players:
                    server.players[player2_id]['status'] = PLAYER_STATUS_IDLE
                    server.players[player2_id]['current_room'] = None
                
                return True, message
    
    if player2_offline:
        player2_color = game.get_player_color(player2_id)
        if player2_color:
            success, message = game.resign(player2_color, RESIGN_REASON_OFFLINE)
            if success:
                room['status'] = ROOM_STATUS_FINISHED
                room['finished_at'] = get_timestamp()
                room['winner'] = game.get_winner()
                
                if player1_id in server.players:
                    server.players[player1_id]['status'] = PLAYER_STATUS_IDLE
                    server.players[player1_id]['current_room'] = None
                if player2_id in server.players:
                    server.players[player2_id]['status'] = PLAYER_STATUS_IDLE
                    server.players[player2_id]['current_room'] = None
                
                return True, message
    
    return False, None


def cleanup_all_timeouts():
    """清理所有超时的房间
    Returns:
        超时处理的房间列表
    """
    results = []
    
    for room_id, room in server.rooms.items():
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
    if room_id not in server.chat_messages:
        server.chat_messages[room_id] = []


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
        'player_name': server.players[player_id]['name'] if player_id in server.players else None,
        'type': message_type,
        'content': content,
        'extra_data': extra_data or {},
        'timestamp': now
    }
    
    server.chat_messages[room_id].append(message)
    
    if len(server.chat_messages[room_id]) > CHAT_MAX_HISTORY:
        server.chat_messages[room_id] = server.chat_messages[room_id][-CHAT_MAX_HISTORY:]
    
    # 同步到数据库
    sync_chat_message(message_id, room_id)
    
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
    if room_id not in server.chat_messages:
        return []
    
    messages = server.chat_messages[room_id]
    
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
    if room_id not in server.rooms:
        return []
    
    room = server.rooms[room_id]
    spectators = room.get('spectators', set())
    
    result = []
    for spectator_id in spectators:
        if spectator_id in server.players:
            player = server.players[spectator_id]
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
    if room_id not in server.rooms:
        return False
    
    room = server.rooms[room_id]
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
    if room_id not in server.rooms:
        return False
    
    room = server.rooms[room_id]
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
    if room_id not in server.rooms:
        return False, "房间不存在"
    
    if player_id not in server.players:
        return False, "玩家不存在"
    
    room = server.rooms[room_id]
    player = server.players[player_id]
    
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
    
    # 同步到数据库
    sync_room(room_id)
    sync_player(player_id)
    sync_spectator_add(room_id, player_id, get_timestamp())
    
    return True, f"成功加入观战，当前共有 {len(spectators)} 人观战"


def remove_spectator(room_id, player_id):
    """移除观战者
    Args:
        room_id: 房间ID
        player_id: 玩家ID
    Returns:
        (success, message)
    """
    if room_id not in server.rooms:
        return False, "房间不存在"
    
    room = server.rooms[room_id]
    spectators = room.get('spectators', set())
    
    if player_id not in spectators:
        return False, "您不是该房间的观战者"
    
    spectators.remove(player_id)
    room['spectators'] = spectators
    room['spectator_count'] = len(spectators)
    
    if player_id in server.players:
        player = server.players[player_id]
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
    
    # 同步到数据库
    sync_room(room_id)
    sync_player(player_id)
    sync_spectator_remove(room_id, player_id)
    
    return True, "成功离开观战"


def get_public_rooms():
    """获取公开房间列表
    Returns:
        公开房间列表（包含观战人数和热门标识）
    """
    public_rooms = []
    
    for room_id, room in server.rooms.items():
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
            'player1_name': server.players[room['player1']]['name'] if room['player1'] in server.players else None,
            'player2_name': server.players[room['player2']]['name'] if room['player2'] in server.players else None,
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


def calculate_rank(score):
    """根据积分计算段位
    Args:
        score: 玩家积分
    Returns:
        段位名称
    """
    for rank in reversed(RANK_LIST):
        if score >= RANK_THRESHOLDS.get(rank, 0):
            return rank
    return RANK_LIST[0]


def update_player_stats(player_id, result):
    """更新玩家战绩统计
    Args:
        player_id: 玩家ID
        result: 结果 ('win', 'lose', 'draw')
    """
    if player_id not in server.players:
        return
    
    player = server.players[player_id]
    if 'stats' not in player:
        # 初始化战绩数据（为了兼容旧数据）
        player['stats'] = {
            'total_games': 0,
            'wins': 0,
            'losses': 0,
            'draws': 0,
            'win_rate': 0.0,
            'current_streak': 0,
            'max_streak': 0,
            'score': 0,
            'rank': RANK_LIST[0]
        }
    
    stats = player['stats']
    stats['total_games'] += 1
    
    if result == 'win':
        stats['wins'] += 1
        stats['current_streak'] += 1
        stats['score'] += SCORE_WIN
        if stats['current_streak'] > stats['max_streak']:
            stats['max_streak'] = stats['current_streak']
    elif result == 'lose':
        stats['losses'] += 1
        stats['current_streak'] = 0
        stats['score'] += SCORE_LOSE
    elif result == 'draw':
        stats['draws'] += 1
        stats['current_streak'] = 0
        stats['score'] += SCORE_DRAW
    
    # 计算胜率
    if stats['total_games'] > 0:
        stats['win_rate'] = round(stats['wins'] / stats['total_games'] * 100, 1)
    
    # 更新段位
    stats['rank'] = calculate_rank(stats['score'])
    
    # 同步到数据库
    sync_player(player_id)


def update_game_stats(room_id, winner_id):
    """更新游戏结束后的战绩统计
    Args:
        room_id: 房间ID
        winner_id: 获胜者ID（None表示平局）
    """
    if room_id not in server.rooms:
        return
    
    room = server.rooms[room_id]
    player1_id = room.get('player1')
    player2_id = room.get('player2')
    
    if not player1_id or not player2_id:
        return
    
    if winner_id == player1_id:
        update_player_stats(player1_id, 'win')
        update_player_stats(player2_id, 'lose')
    elif winner_id == player2_id:
        update_player_stats(player2_id, 'win')
        update_player_stats(player1_id, 'lose')
    else:
        # 平局
        update_player_stats(player1_id, 'draw')
        update_player_stats(player2_id, 'draw')


def create_game_record(room_id):
    """创建游戏历史记录
    Args:
        room_id: 房间ID
    Returns:
        游戏记录ID（如果成功创建），否则返回None
    """
    if room_id not in server.rooms:
        return None
    
    room = server.rooms[room_id]
    game = room.get('game')
    
    if not game:
        return None
    
    player1_id = room.get('player1')
    player2_id = room.get('player2')
    
    if not player1_id or not player2_id:
        return None
    
    player1_name = server.players[player1_id]['name'] if player1_id in server.players else None
    player2_name = server.players[player2_id]['name'] if player2_id in server.players else None
    
    winner_color = room.get('winner')
    winner_id = None
    
    if winner_color == PLAYER_BLACK:
        winner_id = player1_id
    elif winner_color == PLAYER_WHITE:
        winner_id = player2_id
    
    now = get_timestamp()
    record_id = generate_id()
    
    game_record = {
        'id': record_id,
        'room_id': room_id,
        'room_name': room.get('name'),
        
        'player1_id': player1_id,
        'player1_name': player1_name,
        'player2_id': player2_id,
        'player2_name': player2_name,
        
        'player1_color': PLAYER_BLACK,
        'player2_color': PLAYER_WHITE,
        
        'winner_color': winner_color,
        'winner_id': winner_id,
        
        'created_at': room.get('created_at', now),
        'started_at': room.get('started_at', now),
        'finished_at': room.get('finished_at', now),
        
        'move_history': game.move_history[:],
        'total_moves': len(game.move_history),
        
        'game_over': game.game_over,
        'resign_reason': game.resign_reason,
        
    }
    
    server.game_records[record_id] = game_record
    
    for player_id in [player1_id, player2_id]:
        if player_id not in server.players:
            continue
        
        player = server.players[player_id]
        if 'game_record_ids' not in player:
            player['game_record_ids'] = []
        
        if record_id not in player['game_record_ids']:
            player['game_record_ids'].append(record_id)
    
    # 同步到数据库
    sync_game_record(record_id)
    # 同步玩家（因为更新了 game_record_ids）
    sync_player(player1_id)
    sync_player(player2_id)
    
    return record_id


def get_game_record(record_id):
    """获取游戏记录详情
    Args:
        record_id: 游戏记录ID
    Returns:
        游戏记录对象，不存在返回None
    """
    if USE_DATABASE:
        db_record = get_game_record_db(record_id)
        if db_record:
            return {
                'id': db_record['id'],
                'room_id': db_record.get('room_id'),
                'room_name': db_record.get('room_name'),
                
                'player1_id': db_record.get('player1_id'),
                'player1_name': db_record.get('player1_name'),
                'player2_id': db_record.get('player2_id'),
                'player2_name': db_record.get('player2_name'),
                
                'player1_color': db_record.get('player1_color'),
                'player2_color': db_record.get('player2_color'),
                
                'winner_color': db_record.get('winner_color'),
                'winner_id': db_record.get('winner_id'),
                
                'created_at': db_record.get('created_at'),
                'started_at': db_record.get('started_at'),
                'finished_at': db_record.get('finished_at'),
                
                'move_history': db_record.get('move_history', []),
                'total_moves': db_record.get('total_moves', 0),
                
                'game_over': db_record.get('game_over', False),
                'resign_reason': db_record.get('resign_reason')
            }
        return None
    
    if record_id not in server.game_records:
        return None
    
    record = server.game_records[record_id]
    
    return {
        'id': record['id'],
        'room_id': record.get('room_id'),
        'room_name': record.get('room_name'),
        
        'player1_id': record.get('player1_id'),
        'player1_name': record.get('player1_name'),
        'player2_id': record.get('player2_id'),
        'player2_name': record.get('player2_name'),
        
        'player1_color': record.get('player1_color'),
        'player2_color': record.get('player2_color'),
        
        'winner_color': record.get('winner_color'),
        'winner_id': record.get('winner_id'),
        
        'created_at': record.get('created_at'),
        'started_at': record.get('started_at'),
        'finished_at': record.get('finished_at'),
        
        'move_history': record.get('move_history', []),
        'total_moves': record.get('total_moves', 0),
        
        'game_over': record.get('game_over', False),
        'resign_reason': record.get('resign_reason')
    }


def get_player_game_records(player_id):
    """获取玩家的历史对局记录列表
    Args:
        player_id: 玩家ID
    Returns:
        游戏记录列表（简要信息）
    """
    if USE_DATABASE:
        db_records = get_player_game_records_db(player_id)
        return db_records
    
    if player_id not in server.players:
        return []
    
    player = server.players[player_id]
    record_ids = player.get('game_record_ids', [])
    
    records = []
    for record_id in reversed(record_ids):
        if record_id not in server.game_records:
            continue
        
        record = server.game_records[record_id]
        is_winner = (record.get('winner_id') == player_id)
        
        opponent_name = None
        if player_id == record.get('player1_id'):
            opponent_name = record.get('player2_name')
        else:
            opponent_name = record.get('player1_name')
        
        my_color = None
        if player_id == record.get('player1_id'):
            my_color = record.get('player1_color')
        else:
            my_color = record.get('player2_color')
        
        records.append({
            'id': record['id'],
            'room_name': record.get('room_name'),
            'opponent_name': opponent_name,
            'my_color': my_color,
            'is_winner': is_winner,
            'total_moves': record.get('total_moves', 0),
            'resign_reason': record.get('resign_reason'),
            'finished_at': record.get('finished_at')
        })
    
    return records
