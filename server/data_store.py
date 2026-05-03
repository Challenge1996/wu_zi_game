#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务端数据存储
混合模式：内存字典 + 数据库持久化
"""

import os

# 检查是否启用数据库持久化
USE_DATABASE = os.environ.get('USE_DATABASE', 'false').lower() == 'true'

# 内存字典（主存储，保持与原代码兼容）
players = {}
rooms = {}
challenges = {}
undo_requests = {}
chat_messages = {}
game_records = {}

# 房间游戏实例存储（WuziqiGame对象，无法序列化到数据库）
room_games = {}

# 数据库模块（仅在USE_DATABASE=true时使用）
if USE_DATABASE:
    from server.database import (
        get_player, get_all_players, create_player, update_player, update_player_stats,
        get_room, get_all_rooms, create_room, update_room,
        get_challenge, get_all_challenges, create_challenge, update_challenge,
        get_undo_request, get_all_undo_requests, create_undo_request, update_undo_request,
        get_room_chat_messages, get_all_chat_messages, create_chat_message,
        get_game_record_db, get_all_game_records, create_game_record_db,
        get_room_spectators_set, add_spectator_to_db, remove_spectator_from_db,
        get_player_game_records_db,
        init_tables
    )


def load_from_database():
    """
    从数据库加载数据到内存
    服务启动时调用
    """
    if not USE_DATABASE:
        return
    
    print("正在从数据库加载数据...")
    
    # 初始化表
    init_tables()
    
    # 加载玩家
    db_players = get_all_players()
    players.update(db_players)
    print(f"已加载 {len(players)} 个玩家")
    
    # 加载房间（不包含game对象）
    db_rooms = get_all_rooms()
    rooms.update(db_rooms)
    print(f"已加载 {len(rooms)} 个房间")
    
    # 加载挑战
    db_challenges = get_all_challenges()
    challenges.update(db_challenges)
    print(f"已加载 {len(challenges)} 个挑战")
    
    # 加载悔棋请求
    db_undo_requests = get_all_undo_requests()
    undo_requests.update(db_undo_requests)
    print(f"已加载 {len(undo_requests)} 个悔棋请求")
    
    # 加载游戏记录
    db_game_records = get_all_game_records()
    game_records.update(db_game_records)
    print(f"已加载 {len(game_records)} 条游戏记录")
    
    # 加载聊天消息
    db_chat_messages = get_all_chat_messages()
    chat_messages.update(db_chat_messages)
    print(f"已加载聊天消息")


# ========== 玩家同步函数 ==========

def sync_player(player_id):
    """
    将内存中的玩家数据同步到数据库
    """
    if not USE_DATABASE:
        return
    
    if player_id not in players:
        return
    
    player_data = players[player_id]
    
    # 检查玩家是否已存在
    existing = get_player(player_id)
    if existing is None:
        # 创建新玩家
        create_player(
            player_id,
            player_data.get('name', ''),
            player_data.get('registered_at', 0)
        )
    
    # 更新玩家信息
    update_player(
        player_id,
        name=player_data.get('name'),
        online=player_data.get('online'),
        status=player_data.get('status'),
        current_room=player_data.get('current_room'),
        last_heartbeat=player_data.get('last_heartbeat')
    )
    
    # 更新玩家战绩
    stats = player_data.get('stats', {})
    if stats:
        update_player_stats(
            player_id,
            total_games=stats.get('total_games'),
            wins=stats.get('wins'),
            losses=stats.get('losses'),
            draws=stats.get('draws'),
            win_rate=stats.get('win_rate'),
            current_streak=stats.get('current_streak'),
            max_streak=stats.get('max_streak'),
            score=stats.get('score'),
            rank=stats.get('rank')
        )


def sync_all_players():
    """同步所有玩家到数据库"""
    if not USE_DATABASE:
        return
    for player_id in players:
        sync_player(player_id)


# ========== 房间同步函数 ==========

def sync_room(room_id):
    """
    将内存中的房间数据同步到数据库
    """
    if not USE_DATABASE:
        return
    
    if room_id not in rooms:
        return
    
    room_data = rooms[room_id]
    
    existing = get_room(room_id)
    if existing is None:
        # 创建新房间
        create_room(
            room_id,
            room_data.get('name', ''),
            room_data.get('creator', ''),
            challenger_id=room_data.get('challenger_id'),
            challenged_id=room_data.get('challenged_id'),
            player1=room_data.get('player1'),
            player2=room_data.get('player2'),
            status=room_data.get('status'),
            visibility=room_data.get('visibility'),
            spectator_count=room_data.get('spectator_count'),
            created_at=room_data.get('created_at'),
            started_at=room_data.get('started_at'),
            finished_at=room_data.get('finished_at'),
            winner=room_data.get('winner')
        )
    else:
        # 更新房间
        update_room(
            room_id,
            name=room_data.get('name'),
            creator=room_data.get('creator'),
            challenger_id=room_data.get('challenger_id'),
            challenged_id=room_data.get('challenged_id'),
            player1=room_data.get('player1'),
            player2=room_data.get('player2'),
            status=room_data.get('status'),
            visibility=room_data.get('visibility'),
            spectator_count=room_data.get('spectator_count'),
            started_at=room_data.get('started_at'),
            finished_at=room_data.get('finished_at'),
            winner=room_data.get('winner')
        )


def sync_all_rooms():
    """同步所有房间到数据库"""
    if not USE_DATABASE:
        return
    for room_id in rooms:
        sync_room(room_id)


# ========== 挑战同步函数 ==========

def sync_challenge(challenge_id):
    """
    将内存中的挑战数据同步到数据库
    """
    if not USE_DATABASE:
        return
    
    if challenge_id not in challenges:
        return
    
    challenge_data = challenges[challenge_id]
    
    existing = get_challenge(challenge_id)
    if existing is None:
        create_challenge(
            challenge_id,
            challenge_data.get('challenger', ''),
            challenge_data.get('challenged', ''),
            challenge_data.get('created_at', 0),
            challenge_data.get('expires_at', 0)
        )
    else:
        update_challenge(
            challenge_id,
            status=challenge_data.get('status'),
            room_id=challenge_data.get('room_id')
        )


def sync_all_challenges():
    """同步所有挑战到数据库"""
    if not USE_DATABASE:
        return
    for challenge_id in challenges:
        sync_challenge(challenge_id)


# ========== 悔棋请求同步函数 ==========

def sync_undo_request(undo_id):
    """
    将内存中的悔棋请求同步到数据库
    """
    if not USE_DATABASE:
        return
    
    if undo_id not in undo_requests:
        return
    
    undo_data = undo_requests[undo_id]
    
    existing = get_undo_request(undo_id)
    if existing is None:
        create_undo_request(
            undo_id,
            undo_data.get('room_id', ''),
            undo_data.get('requester', ''),
            undo_data.get('requested', ''),
            undo_data.get('created_at', 0),
            undo_data.get('expires_at', 0)
        )
    else:
        update_undo_request(
            undo_id,
            status=undo_data.get('status')
        )


def sync_all_undo_requests():
    """同步所有悔棋请求到数据库"""
    if not USE_DATABASE:
        return
    for undo_id in undo_requests:
        sync_undo_request(undo_id)


# ========== 聊天消息同步函数 ==========

def sync_chat_message(msg_id, room_id):
    """
    将内存中的聊天消息同步到数据库
    """
    if not USE_DATABASE:
        return
    
    if room_id not in chat_messages:
        return
    
    # 找到对应的消息
    msg_data = None
    for msg in chat_messages[room_id]:
        if msg.get('id') == msg_id:
            msg_data = msg
            break
    
    if msg_data is None:
        return
    
    create_chat_message(
        msg_id,
        msg_data.get('room_id', ''),
        msg_data.get('player_id'),
        msg_data.get('player_name'),
        msg_data.get('type', 'text'),
        msg_data.get('content', ''),
        msg_data.get('extra_data', {}),
        msg_data.get('timestamp', 0)
    )


def sync_room_chat_messages(room_id):
    """同步房间的所有聊天消息"""
    if not USE_DATABASE:
        return
    if room_id in chat_messages:
        for msg in chat_messages[room_id]:
            sync_chat_message(msg.get('id'), room_id)


# ========== 游戏记录同步函数 ==========

def sync_game_record(record_id):
    """
    将内存中的游戏记录同步到数据库
    """
    if not USE_DATABASE:
        return
    
    if record_id not in game_records:
        return
    
    record_data = game_records[record_id]
    
    create_game_record_db(
        record_id,
        record_data.get('room_id', ''),
        record_data.get('room_name'),
        record_data.get('player1_id', ''),
        record_data.get('player1_name'),
        record_data.get('player2_id', ''),
        record_data.get('player2_name'),
        record_data.get('player1_color', 1),
        record_data.get('player2_color', 2),
        record_data.get('winner_color'),
        record_data.get('winner_id'),
        record_data.get('created_at', 0),
        record_data.get('started_at'),
        record_data.get('finished_at'),
        record_data.get('total_moves', 0),
        record_data.get('game_over', False),
        record_data.get('resign_reason'),
        record_data.get('move_history', [])
    )


def sync_all_game_records():
    """同步所有游戏记录到数据库"""
    if not USE_DATABASE:
        return
    for record_id in game_records:
        sync_game_record(record_id)


# ========== 观战者同步函数 ==========

def sync_spectator_add(room_id, player_id, joined_at):
    """添加观战者到数据库"""
    if not USE_DATABASE:
        return
    add_spectator_to_db(room_id, player_id, joined_at)


def sync_spectator_remove(room_id, player_id):
    """从数据库移除观战者"""
    if not USE_DATABASE:
        return
    remove_spectator_from_db(room_id, player_id)


# ========== 便捷同步函数 ==========

def sync_all():
    """同步所有数据到数据库"""
    if not USE_DATABASE:
        return
    
    sync_all_players()
    sync_all_rooms()
    sync_all_challenges()
    sync_all_undo_requests()
    sync_all_game_records()
