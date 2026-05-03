#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL数据库模块
提供数据库连接、表初始化和基础操作
"""

import pymysql
from pymysql.cursors import DictCursor
import json
import os
from datetime import datetime
from constants import (
    PLAYER_STATUS_IDLE,
    ROOM_STATUS_WAITING,
    ROOM_VISIBILITY_PUBLIC,
    CHALLENGE_STATUS_PENDING,
    UNDO_REQUEST_STATUS_PENDING,
    RANK_NEWBIE
)


class Database:
    """数据库连接管理类"""
    
    _instance = None
    _connection = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._connection is None:
            self._connect()
    
    def _connect(self):
        """建立数据库连接"""
        db_host = os.environ.get('DB_HOST', 'localhost')
        db_port = int(os.environ.get('DB_PORT', 3306))
        db_user = os.environ.get('DB_USER', 'root')
        db_password = os.environ.get('DB_PASSWORD', '123456')
        db_name = os.environ.get('DB_NAME', 'wuziqi_game')
        
        self._connection = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
            charset='utf8mb4',
            cursorclass=DictCursor,
            autocommit=True
        )
    
    def get_connection(self):
        """获取数据库连接，如果连接断开则重新连接"""
        try:
            self._connection.ping(reconnect=True)
        except:
            self._connect()
        return self._connection
    
    def cursor(self):
        """获取游标"""
        return self.get_connection().cursor()


def get_db():
    """获取数据库实例"""
    return Database()


def init_tables():
    """初始化数据库表"""
    db = get_db()
    conn = db.get_connection()
    
    with conn.cursor() as cursor:
        # 玩家表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id VARCHAR(64) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            online BOOLEAN DEFAULT FALSE,
            status VARCHAR(50) DEFAULT 'idle',
            current_room VARCHAR(64) NULL,
            last_heartbeat BIGINT DEFAULT 0,
            registered_at BIGINT DEFAULT 0,
            INDEX idx_status (status),
            INDEX idx_online (online)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        
        # 玩家战绩表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_stats (
            player_id VARCHAR(64) PRIMARY KEY,
            total_games INT DEFAULT 0,
            wins INT DEFAULT 0,
            losses INT DEFAULT 0,
            draws INT DEFAULT 0,
            win_rate DECIMAL(5,2) DEFAULT 0.00,
            current_streak INT DEFAULT 0,
            max_streak INT DEFAULT 0,
            score INT DEFAULT 0,
            `rank` VARCHAR(50) DEFAULT '新手',
            FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        
        # 房间表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id VARCHAR(64) PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            creator VARCHAR(64) NOT NULL,
            challenger_id VARCHAR(64) NULL,
            challenged_id VARCHAR(64) NULL,
            player1 VARCHAR(64) NULL,
            player2 VARCHAR(64) NULL,
            status VARCHAR(50) DEFAULT 'waiting',
            visibility VARCHAR(50) DEFAULT 'public',
            spectator_count INT DEFAULT 0,
            created_at BIGINT DEFAULT 0,
            started_at BIGINT NULL,
            finished_at BIGINT NULL,
            winner INT NULL,
            INDEX idx_status (status),
            INDEX idx_creator (creator),
            INDEX idx_player1 (player1),
            INDEX idx_player2 (player2)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        
        # 挑战表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS challenges (
            id VARCHAR(64) PRIMARY KEY,
            challenger VARCHAR(64) NOT NULL,
            challenged VARCHAR(64) NOT NULL,
            status VARCHAR(50) DEFAULT 'pending',
            room_id VARCHAR(64) NULL,
            created_at BIGINT DEFAULT 0,
            expires_at BIGINT DEFAULT 0,
            INDEX idx_challenger (challenger),
            INDEX idx_challenged (challenged),
            INDEX idx_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        
        # 悔棋请求表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS undo_requests (
            id VARCHAR(64) PRIMARY KEY,
            room_id VARCHAR(64) NOT NULL,
            requester VARCHAR(64) NOT NULL,
            requested VARCHAR(64) NOT NULL,
            status VARCHAR(50) DEFAULT 'pending',
            created_at BIGINT DEFAULT 0,
            expires_at BIGINT DEFAULT 0,
            INDEX idx_room_id (room_id),
            INDEX idx_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        
        # 聊天消息表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id VARCHAR(64) PRIMARY KEY,
            room_id VARCHAR(64) NOT NULL,
            player_id VARCHAR(64) NULL,
            player_name VARCHAR(100) NULL,
            type VARCHAR(50) DEFAULT 'text',
            content TEXT,
            extra_data JSON NULL,
            timestamp BIGINT DEFAULT 0,
            INDEX idx_room_id (room_id),
            INDEX idx_timestamp (timestamp)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        
        # 观战者表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS spectators (
            id INT AUTO_INCREMENT PRIMARY KEY,
            room_id VARCHAR(64) NOT NULL,
            player_id VARCHAR(64) NOT NULL,
            joined_at BIGINT DEFAULT 0,
            UNIQUE KEY uk_room_player (room_id, player_id),
            INDEX idx_room_id (room_id),
            INDEX idx_player_id (player_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        
        # 游戏记录表（用于历史记录查询）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_records (
            id VARCHAR(64) PRIMARY KEY,
            room_id VARCHAR(64) NOT NULL,
            room_name VARCHAR(200) NULL,
            player1_id VARCHAR(64) NOT NULL,
            player1_name VARCHAR(100) NULL,
            player2_id VARCHAR(64) NOT NULL,
            player2_name VARCHAR(100) NULL,
            player1_color INT DEFAULT 1,
            player2_color INT DEFAULT 2,
            winner_color INT NULL,
            winner_id VARCHAR(64) NULL,
            created_at BIGINT DEFAULT 0,
            started_at BIGINT NULL,
            finished_at BIGINT NULL,
            total_moves INT DEFAULT 0,
            game_over BOOLEAN DEFAULT FALSE,
            resign_reason VARCHAR(50) NULL,
            move_history JSON NULL,
            INDEX idx_player1_id (player1_id),
            INDEX idx_player2_id (player2_id),
            INDEX idx_winner_id (winner_id),
            INDEX idx_finished_at (finished_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        
        # 玩家游戏记录关联表（方便查询玩家的历史对局）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_game_relations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            player_id VARCHAR(64) NOT NULL,
            game_record_id VARCHAR(64) NOT NULL,
            player_color INT NOT NULL,
            is_winner BOOLEAN DEFAULT FALSE,
            UNIQUE KEY uk_player_record (player_id, game_record_id),
            INDEX idx_player_id (player_id),
            INDEX idx_game_record_id (game_record_id),
            FOREIGN KEY (game_record_id) REFERENCES game_records(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
    
    conn.commit()
    print("数据库表初始化完成")


# ========== 玩家相关操作 ==========

def create_player(player_id, name, registered_at):
    """创建新玩家"""
    db = get_db()
    conn = db.get_connection()
    
    with conn.cursor() as cursor:
        # 插入玩家基本信息
        cursor.execute('''
            INSERT INTO players (id, name, online, status, current_room, last_heartbeat, registered_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (player_id, name, True, PLAYER_STATUS_IDLE, None, registered_at, registered_at))
        
        # 插入玩家战绩
        cursor.execute('''
            INSERT INTO player_stats (player_id, total_games, wins, losses, draws, win_rate, 
                                      current_streak, max_streak, score, `rank`)
            VALUES (%s, 0, 0, 0, 0, 0.00, 0, 0, 0, %s)
        ''', (player_id, RANK_NEWBIE))
    
    return get_player(player_id)


def get_player(player_id):
    """获取玩家信息（包含战绩）"""
    db = get_db()
    conn = db.get_connection()
    
    with conn.cursor() as cursor:
        cursor.execute('''
            SELECT p.*, ps.total_games, ps.wins, ps.losses, ps.draws, 
                   ps.win_rate, ps.current_streak, ps.max_streak, ps.score, ps.`rank`
            FROM players p
            LEFT JOIN player_stats ps ON p.id = ps.player_id
            WHERE p.id = %s
        ''', (player_id,))
        
        row = cursor.fetchone()
        if row:
            # 构建与原内存结构兼容的格式
            player = {
                'id': row['id'],
                'name': row['name'],
                'online': bool(row['online']),
                'status': row['status'],
                'current_room': row['current_room'],
                'last_heartbeat': row['last_heartbeat'],
                'registered_at': row['registered_at'],
                'stats': {
                    'total_games': row['total_games'] or 0,
                    'wins': row['wins'] or 0,
                    'losses': row['losses'] or 0,
                    'draws': row['draws'] or 0,
                    'win_rate': float(row['win_rate']) if row['win_rate'] else 0.0,
                    'current_streak': row['current_streak'] or 0,
                    'max_streak': row['max_streak'] or 0,
                    'score': row['score'] or 0,
                    'rank': row['rank'] or RANK_NEWBIE
                },
                'game_record_ids': get_player_game_record_ids(player_id)
            }
            return player
        return None


def update_player(player_id, **kwargs):
    """更新玩家信息"""
    db = get_db()
    conn = db.get_connection()
    
    allowed_fields = ['name', 'online', 'status', 'current_room', 'last_heartbeat']
    updates = []
    values = []
    
    for key, value in kwargs.items():
        if key in allowed_fields:
            updates.append(f'{key} = %s')
            values.append(value)
    
    if updates:
        values.append(player_id)
        with conn.cursor() as cursor:
            cursor.execute(f'''
                UPDATE players SET {', '.join(updates)} WHERE id = %s
            ''', values)


def update_player_stats(player_id, **kwargs):
    """更新玩家战绩"""
    db = get_db()
    conn = db.get_connection()
    
    allowed_fields = ['total_games', 'wins', 'losses', 'draws', 'win_rate', 
                       'current_streak', 'max_streak', 'score', 'rank']
    updates = []
    values = []
    
    for key, value in kwargs.items():
        if key in allowed_fields:
            # rank 是 MySQL 保留关键字，需要使用反引号包裹
            field_name = f'`{key}`' if key == 'rank' else key
            updates.append(f'{field_name} = %s')
            values.append(value)
    
    if updates:
        values.append(player_id)
        with conn.cursor() as cursor:
            cursor.execute(f'''
                UPDATE player_stats SET {', '.join(updates)} WHERE player_id = %s
            ''', values)


def get_all_players():
    """获取所有玩家（用于兼容原代码）"""
    db = get_db()
    conn = db.get_connection()
    
    with conn.cursor() as cursor:
        cursor.execute('SELECT id FROM players')
        rows = cursor.fetchall()
        
        players = {}
        for row in rows:
            player = get_player(row['id'])
            if player:
                players[row['id']] = player
        
        return players


def get_online_players():
    """获取在线玩家"""
    db = get_db()
    conn = db.get_connection()
    
    with conn.cursor() as cursor:
        cursor.execute('SELECT id FROM players WHERE online = TRUE')
        rows = cursor.fetchall()
        
        players = {}
        for row in rows:
            player = get_player(row['id'])
            if player:
                players[row['id']] = player
        
        return players


# ========== 房间相关操作 ==========

def create_room(room_id, name, creator, **kwargs):
    """创建新房间"""
    db = get_db()
    conn = db.get_connection()
    
    with conn.cursor() as cursor:
        cursor.execute('''
            INSERT INTO rooms (id, name, creator, challenger_id, challenged_id, 
                              player1, player2, status, visibility, spectator_count,
                              created_at, started_at, finished_at, winner)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            room_id, name, creator, 
            kwargs.get('challenger_id'), kwargs.get('challenged_id'),
            kwargs.get('player1'), kwargs.get('player2'),
            kwargs.get('status', ROOM_STATUS_WAITING),
            kwargs.get('visibility', ROOM_VISIBILITY_PUBLIC),
            kwargs.get('spectator_count', 0),
            kwargs.get('created_at', 0),
            kwargs.get('started_at'),
            kwargs.get('finished_at'),
            kwargs.get('winner')
        ))
    
    return get_room(room_id)


def get_room(room_id):
    """获取房间信息"""
    db = get_db()
    conn = db.get_connection()
    
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM rooms WHERE id = %s', (room_id,))
        row = cursor.fetchone()
        
        if row:
            room = {
                'id': row['id'],
                'name': row['name'],
                'creator': row['creator'],
                'challenger_id': row['challenger_id'],
                'challenged_id': row['challenged_id'],
                'player1': row['player1'],
                'player2': row['player2'],
                'status': row['status'],
                'visibility': row['visibility'],
                'spectator_count': row['spectator_count'] or 0,
                'created_at': row['created_at'],
                'started_at': row['started_at'],
                'finished_at': row['finished_at'],
                'winner': row['winner'],
                'spectators': get_room_spectators_set(room_id)
            }
            return room
        return None


def update_room(room_id, **kwargs):
    """更新房间信息"""
    db = get_db()
    conn = db.get_connection()
    
    allowed_fields = ['name', 'creator', 'challenger_id', 'challenged_id',
                       'player1', 'player2', 'status', 'visibility', 'spectator_count',
                       'started_at', 'finished_at', 'winner']
    updates = []
    values = []
    
    for key, value in kwargs.items():
        if key in allowed_fields:
            updates.append(f'{key} = %s')
            values.append(value)
    
    if updates:
        values.append(room_id)
        with conn.cursor() as cursor:
            cursor.execute(f'''
                UPDATE rooms SET {', '.join(updates)} WHERE id = %s
            ''', values)


def get_all_rooms():
    """获取所有房间"""
    db = get_db()
    conn = db.get_connection()
    
    with conn.cursor() as cursor:
        cursor.execute('SELECT id FROM rooms')
        rows = cursor.fetchall()
        
        rooms = {}
        for row in rows:
            room = get_room(row['id'])
            if room:
                rooms[row['id']] = room
        
        return rooms


# ========== 挑战相关操作 ==========

def create_challenge(challenge_id, challenger, challenged, created_at, expires_at):
    """创建挑战"""
    db = get_db()
    conn = db.get_connection()
    
    with conn.cursor() as cursor:
        cursor.execute('''
            INSERT INTO challenges (id, challenger, challenged, status, room_id, created_at, expires_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (challenge_id, challenger, challenged, CHALLENGE_STATUS_PENDING, None, created_at, expires_at))
    
    return get_challenge(challenge_id)


def get_challenge(challenge_id):
    """获取挑战信息"""
    db = get_db()
    conn = db.get_connection()
    
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM challenges WHERE id = %s', (challenge_id,))
        row = cursor.fetchone()
        
        if row:
            return {
                'id': row['id'],
                'challenger': row['challenger'],
                'challenged': row['challenged'],
                'status': row['status'],
                'room_id': row['room_id'],
                'created_at': row['created_at'],
                'expires_at': row['expires_at']
            }
        return None


def update_challenge(challenge_id, **kwargs):
    """更新挑战信息"""
    db = get_db()
    conn = db.get_connection()
    
    allowed_fields = ['status', 'room_id']
    updates = []
    values = []
    
    for key, value in kwargs.items():
        if key in allowed_fields:
            updates.append(f'{key} = %s')
            values.append(value)
    
    if updates:
        values.append(challenge_id)
        with conn.cursor() as cursor:
            cursor.execute(f'''
                UPDATE challenges SET {', '.join(updates)} WHERE id = %s
            ''', values)


def get_all_challenges():
    """获取所有挑战"""
    db = get_db()
    conn = db.get_connection()
    
    with conn.cursor() as cursor:
        cursor.execute('SELECT id FROM challenges')
        rows = cursor.fetchall()
        
        challenges = {}
        for row in rows:
            challenge = get_challenge(row['id'])
            if challenge:
                challenges[row['id']] = challenge
        
        return challenges


# ========== 悔棋请求相关操作 ==========

def create_undo_request(undo_id, room_id, requester, requested, created_at, expires_at):
    """创建悔棋请求"""
    db = get_db()
    conn = db.get_connection()
    
    with conn.cursor() as cursor:
        cursor.execute('''
            INSERT INTO undo_requests (id, room_id, requester, requested, status, created_at, expires_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (undo_id, room_id, requester, requested, UNDO_REQUEST_STATUS_PENDING, created_at, expires_at))
    
    return get_undo_request(undo_id)


def get_undo_request(undo_id):
    """获取悔棋请求"""
    db = get_db()
    conn = db.get_connection()
    
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM undo_requests WHERE id = %s', (undo_id,))
        row = cursor.fetchone()
        
        if row:
            return {
                'id': row['id'],
                'room_id': row['room_id'],
                'requester': row['requester'],
                'requested': row['requested'],
                'status': row['status'],
                'created_at': row['created_at'],
                'expires_at': row['expires_at']
            }
        return None


def update_undo_request(undo_id, **kwargs):
    """更新悔棋请求"""
    db = get_db()
    conn = db.get_connection()
    
    allowed_fields = ['status']
    updates = []
    values = []
    
    for key, value in kwargs.items():
        if key in allowed_fields:
            updates.append(f'{key} = %s')
            values.append(value)
    
    if updates:
        values.append(undo_id)
        with conn.cursor() as cursor:
            cursor.execute(f'''
                UPDATE undo_requests SET {', '.join(updates)} WHERE id = %s
            ''', values)


def get_room_undo_requests(room_id, status=None):
    """获取房间的悔棋请求"""
    db = get_db()
    conn = db.get_connection()
    
    with conn.cursor() as cursor:
        if status:
            cursor.execute('''
                SELECT id FROM undo_requests WHERE room_id = %s AND status = %s ORDER BY created_at DESC
            ''', (room_id, status))
        else:
            cursor.execute('''
                SELECT id FROM undo_requests WHERE room_id = %s ORDER BY created_at DESC
            ''', (room_id,))
        
        rows = cursor.fetchall()
        requests = []
        for row in rows:
            req = get_undo_request(row['id'])
            if req:
                requests.append(req)
        
        return requests


def get_all_undo_requests():
    """获取所有悔棋请求"""
    db = get_db()
    conn = db.get_connection()
    
    with conn.cursor() as cursor:
        cursor.execute('SELECT id FROM undo_requests')
        rows = cursor.fetchall()
        
        undo_requests = {}
        for row in rows:
            req = get_undo_request(row['id'])
            if req:
                undo_requests[row['id']] = req
        
        return undo_requests


# ========== 聊天消息相关操作 ==========

def create_chat_message(msg_id, room_id, player_id, player_name, msg_type, content, extra_data, timestamp):
    """创建聊天消息"""
    db = get_db()
    conn = db.get_connection()
    
    with conn.cursor() as cursor:
        cursor.execute('''
            INSERT INTO chat_messages (id, room_id, player_id, player_name, type, content, extra_data, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (msg_id, room_id, player_id, player_name, msg_type, content, 
              json.dumps(extra_data) if extra_data else None, timestamp))
    
    return get_chat_message(msg_id)


def get_chat_message(msg_id):
    """获取聊天消息"""
    db = get_db()
    conn = db.get_connection()
    
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM chat_messages WHERE id = %s', (msg_id,))
        row = cursor.fetchone()
        
        if row:
            return {
                'id': row['id'],
                'room_id': row['room_id'],
                'player_id': row['player_id'],
                'player_name': row['player_name'],
                'type': row['type'],
                'content': row['content'],
                'extra_data': json.loads(row['extra_data']) if row['extra_data'] else {},
                'timestamp': row['timestamp']
            }
        return None


def get_room_chat_messages(room_id, since_id=None, limit=None):
    """获取房间的聊天消息"""
    db = get_db()
    conn = db.get_connection()
    
    with conn.cursor() as cursor:
        query = '''
            SELECT id FROM chat_messages 
            WHERE room_id = %s 
        '''
        params = [room_id]
        
        if since_id:
            # 获取since_id之后的消息
            since_msg = get_chat_message(since_id)
            if since_msg:
                query += ' AND timestamp > %s'
                params.append(since_msg['timestamp'])
        
        query += ' ORDER BY timestamp ASC'
        
        if limit:
            query += f' LIMIT {limit}'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        messages = []
        for row in rows:
            msg = get_chat_message(row['id'])
            if msg:
                messages.append(msg)
        
        return messages


def get_all_chat_messages():
    """获取所有聊天消息（按房间分组）"""
    db = get_db()
    conn = db.get_connection()
    
    with conn.cursor() as cursor:
        cursor.execute('SELECT DISTINCT room_id FROM chat_messages')
        rows = cursor.fetchall()
        
        chat_messages = {}
        for row in rows:
            room_id = row['room_id']
            chat_messages[room_id] = get_room_chat_messages(room_id)
        
        return chat_messages


# ========== 观战者相关操作 ==========

def add_spectator_to_db(room_id, player_id, joined_at):
    """添加观战者"""
    db = get_db()
    conn = db.get_connection()
    
    with conn.cursor() as cursor:
        try:
            cursor.execute('''
                INSERT INTO spectators (room_id, player_id, joined_at)
                VALUES (%s, %s, %s)
            ''', (room_id, player_id, joined_at))
            
            # 更新房间观战人数
            cursor.execute('''
                UPDATE rooms SET spectator_count = spectator_count + 1 WHERE id = %s
            ''', (room_id,))
            return True
        except pymysql.IntegrityError:
            # 已存在
            return False


def remove_spectator_from_db(room_id, player_id):
    """移除观战者"""
    db = get_db()
    conn = db.get_connection()
    
    with conn.cursor() as cursor:
        cursor.execute('''
            DELETE FROM spectators WHERE room_id = %s AND player_id = %s
        ''', (room_id, player_id))
        
        if cursor.rowcount > 0:
            # 更新房间观战人数
            cursor.execute('''
                UPDATE rooms SET spectator_count = spectator_count - 1 WHERE id = %s
            ''', (room_id,))
            return True
        return False


def get_room_spectators_set(room_id):
    """获取房间观战者集合"""
    db = get_db()
    conn = db.get_connection()
    
    with conn.cursor() as cursor:
        cursor.execute('''
            SELECT player_id FROM spectators WHERE room_id = %s
        ''', (room_id,))
        rows = cursor.fetchall()
        
        return set(row['player_id'] for row in rows)


def get_room_spectators_info(room_id):
    """获取房间观战者信息"""
    db = get_db()
    conn = db.get_connection()
    
    with conn.cursor() as cursor:
        cursor.execute('''
            SELECT s.player_id, p.name, p.online
            FROM spectators s
            JOIN players p ON s.player_id = p.id
            WHERE s.room_id = %s
        ''', (room_id,))
        rows = cursor.fetchall()
        
        return [
            {
                'id': row['player_id'],
                'name': row['name'],
                'online': bool(row['online'])
            }
            for row in rows
        ]


# ========== 游戏记录相关操作 ==========

def create_game_record_db(record_id, room_id, room_name, 
                          player1_id, player1_name, 
                          player2_id, player2_name,
                          player1_color, player2_color,
                          winner_color, winner_id,
                          created_at, started_at, finished_at,
                          total_moves, game_over, resign_reason, move_history):
    """创建游戏记录"""
    db = get_db()
    conn = db.get_connection()
    
    with conn.cursor() as cursor:
        cursor.execute('''
            INSERT INTO game_records (id, room_id, room_name, 
                                      player1_id, player1_name, 
                                      player2_id, player2_name,
                                      player1_color, player2_color,
                                      winner_color, winner_id,
                                      created_at, started_at, finished_at,
                                      total_moves, game_over, resign_reason, move_history)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (record_id, room_id, room_name,
              player1_id, player1_name,
              player2_id, player2_name,
              player1_color, player2_color,
              winner_color, winner_id,
              created_at, started_at, finished_at,
              total_moves, game_over, resign_reason,
              json.dumps(move_history) if move_history else None))
        
        # 创建玩家游戏记录关联
        # 玩家1
        cursor.execute('''
            INSERT INTO player_game_relations (player_id, game_record_id, player_color, is_winner)
            VALUES (%s, %s, %s, %s)
        ''', (player1_id, record_id, player1_color, winner_id == player1_id))
        
        # 玩家2
        cursor.execute('''
            INSERT INTO player_game_relations (player_id, game_record_id, player_color, is_winner)
            VALUES (%s, %s, %s, %s)
        ''', (player2_id, record_id, player2_color, winner_id == player2_id))
    
    return get_game_record_db(record_id)


def get_game_record_db(record_id):
    """获取游戏记录"""
    db = get_db()
    conn = db.get_connection()
    
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM game_records WHERE id = %s', (record_id,))
        row = cursor.fetchone()
        
        if row:
            return {
                'id': row['id'],
                'room_id': row['room_id'],
                'room_name': row['room_name'],
                'player1_id': row['player1_id'],
                'player1_name': row['player1_name'],
                'player2_id': row['player2_id'],
                'player2_name': row['player2_name'],
                'player1_color': row['player1_color'],
                'player2_color': row['player2_color'],
                'winner_color': row['winner_color'],
                'winner_id': row['winner_id'],
                'created_at': row['created_at'],
                'started_at': row['started_at'],
                'finished_at': row['finished_at'],
                'total_moves': row['total_moves'] or 0,
                'game_over': bool(row['game_over']),
                'resign_reason': row['resign_reason'],
                'move_history': json.loads(row['move_history']) if row['move_history'] else []
            }
        return None


def get_player_game_record_ids(player_id):
    """获取玩家的游戏记录ID列表"""
    db = get_db()
    conn = db.get_connection()
    
    with conn.cursor() as cursor:
        cursor.execute('''
            SELECT game_record_id FROM player_game_relations 
            WHERE player_id = %s ORDER BY id ASC
        ''', (player_id,))
        rows = cursor.fetchall()
        
        return [row['game_record_id'] for row in rows]


def get_player_game_records_db(player_id):
    """获取玩家的游戏记录列表"""
    db = get_db()
    conn = db.get_connection()
    
    with conn.cursor() as cursor:
        cursor.execute('''
            SELECT gr.*, pgr.player_color, pgr.is_winner
            FROM game_records gr
            JOIN player_game_relations pgr ON gr.id = pgr.game_record_id
            WHERE pgr.player_id = %s
            ORDER BY gr.finished_at DESC
        ''', (player_id,))
        rows = cursor.fetchall()
        
        records = []
        for row in rows:
            # 确定对手信息
            if row['player1_id'] == player_id:
                opponent_name = row['player2_name']
                my_color = row['player1_color']
            else:
                opponent_name = row['player1_name']
                my_color = row['player2_color']
            
            records.append({
                'id': row['id'],
                'room_name': row['room_name'],
                'opponent_name': opponent_name,
                'my_color': my_color,
                'is_winner': bool(row['is_winner']),
                'total_moves': row['total_moves'] or 0,
                'resign_reason': row['resign_reason'],
                'finished_at': row['finished_at']
            })
        
        return records


def get_all_game_records():
    """获取所有游戏记录"""
    db = get_db()
    conn = db.get_connection()
    
    with conn.cursor() as cursor:
        cursor.execute('SELECT id FROM game_records')
        rows = cursor.fetchall()
        
        game_records = {}
        for row in rows:
            record = get_game_record_db(row['id'])
            if record:
                game_records[row['id']] = record
        
        return game_records
