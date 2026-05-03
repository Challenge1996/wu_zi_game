#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的游戏历史记录测试（不依赖Flask）
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from constants import PLAYER_BLACK, PLAYER_WHITE
from game import WuziqiGame

game_records = {}
players = {}
rooms = {}

import time


def get_timestamp():
    return int(time.time())


def generate_id():
    import uuid
    return uuid.uuid4().hex[:16]


def create_game_record(room_id):
    """创建游戏历史记录"""
    if room_id not in rooms:
        return None
    
    room = rooms[room_id]
    game = room.get('game')
    
    if not game:
        return None
    
    player1_id = room.get('player1')
    player2_id = room.get('player2')
    
    if not player1_id or not player2_id:
        return None
    
    player1_name = players[player1_id]['name'] if player1_id in players else None
    player2_name = players[player2_id]['name'] if player2_id in players else None
    
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
    
    game_records[record_id] = game_record
    
    for player_id in [player1_id, player2_id]:
        if player_id not in players:
            continue
        
        player = players[player_id]
        if 'game_record_ids' not in player:
            player['game_record_ids'] = []
        
        if record_id not in player['game_record_ids']:
            player['game_record_ids'].append(record_id)
    
    return record_id


def get_game_record(record_id):
    """获取游戏记录详情"""
    if record_id not in game_records:
        return None
    
    record = game_records[record_id]
    
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
    """获取玩家的历史对局记录列表"""
    if player_id not in players:
        return []
    
    player = players[player_id]
    record_ids = player.get('game_record_ids', [])
    
    records = []
    for record_id in reversed(record_ids):
        if record_id not in game_records:
            continue
        
        record = game_records[record_id]
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


def test_game_record_creation():
    """测试游戏记录创建"""
    print("=" * 60)
    print("测试 1: 创建游戏记录")
    print("=" * 60)
    
    player1_id = generate_id()
    player2_id = generate_id()
    
    players[player1_id] = {
        'id': player1_id,
        'name': '测试玩家1',
        'online': True,
        'status': 'idle',
        'current_room': None,
        'last_heartbeat': get_timestamp(),
        'registered_at': get_timestamp(),
        'stats': {
            'total_games': 0,
            'wins': 0,
            'losses': 0,
            'draws': 0,
            'win_rate': 0.0,
            'current_streak': 0,
            'max_streak': 0,
            'score': 0,
            'rank': '新手'
        }
    }
    
    players[player2_id] = {
        'id': player2_id,
        'name': '测试玩家2',
        'online': True,
        'status': 'idle',
        'current_room': None,
        'last_heartbeat': get_timestamp(),
        'registered_at': get_timestamp(),
        'stats': {
            'total_games': 0,
            'wins': 0,
            'losses': 0,
            'draws': 0,
            'win_rate': 0.0,
            'current_streak': 0,
            'max_streak': 0,
            'score': 0,
            'rank': '新手'
        }
    }
    
    room_id = generate_id()
    
    game = WuziqiGame()
    game.players[PLAYER_BLACK] = player1_id
    game.players[PLAYER_WHITE] = player2_id
    game.start_game()
    
    rooms[room_id] = {
        'id': room_id,
        'name': '测试玩家1 vs 测试玩家2',
        'creator': player1_id,
        'player1': player1_id,
        'player2': player2_id,
        'status': 'playing',
        'game': game,
        'created_at': get_timestamp(),
        'started_at': get_timestamp(),
        'finished_at': None,
        'winner': None
    }
    
    game.place_piece(7, 7, PLAYER_BLACK)
    game.place_piece(7, 8, PLAYER_WHITE)
    game.place_piece(8, 7, PLAYER_BLACK)
    game.place_piece(8, 8, PLAYER_WHITE)
    game.place_piece(9, 7, PLAYER_BLACK)
    game.place_piece(9, 8, PLAYER_WHITE)
    game.place_piece(10, 7, PLAYER_BLACK)
    game.place_piece(10, 8, PLAYER_WHITE)
    game.place_piece(11, 7, PLAYER_BLACK)
    
    print(f"  - 游戏结束: {game.game_over}")
    print(f"  - 获胜者: {game.get_winner()}")
    print(f"  - 总步数: {len(game.move_history)}")
    
    rooms[room_id]['status'] = 'finished'
    rooms[room_id]['finished_at'] = get_timestamp()
    rooms[room_id]['winner'] = game.get_winner()
    
    record_id = create_game_record(room_id)
    
    print(f"  - 记录ID: {record_id}")
    print(f"  - 记录总数: {len(game_records)}")
    
    assert record_id is not None, "记录创建失败"
    assert len(game_records) == 1, "记录数量不正确"
    
    print("  ✓ 测试通过!")
    
    return player1_id, player2_id, record_id


def test_game_record_retrieval(record_id):
    """测试游戏记录获取"""
    print("\n" + "=" * 60)
    print("测试 2: 获取游戏记录详情")
    print("=" * 60)
    
    record = get_game_record(record_id)
    
    assert record is not None, "获取记录失败"
    
    print(f"  - 记录ID: {record.get('id')}")
    print(f"  - 对局名称: {record.get('room_name')}")
    print(f"  - 黑棋玩家: {record.get('player1_name')}")
    print(f"  - 白棋玩家: {record.get('player2_name')}")
    print(f"  - 获胜者颜色: {record.get('winner_color')}")
    print(f"  - 总步数: {record.get('total_moves')}")
    print(f"  - 走棋历史长度: {len(record.get('move_history', []))}")
    
    move_history = record.get('move_history', [])
    for i, move in enumerate(move_history):
        row, col, player = move
        color_name = "黑棋" if player == PLAYER_BLACK else "白棋"
        print(f"    第 {i+1} 步: {color_name} 在 ({row}, {col})")
    
    print("  ✓ 测试通过!")


def test_player_records(player1_id, player2_id):
    """测试获取玩家的历史记录列表"""
    print("\n" + "=" * 60)
    print("测试 3: 获取玩家历史记录列表")
    print("=" * 60)
    
    records1 = get_player_game_records(player1_id)
    records2 = get_player_game_records(player2_id)
    
    print(f"  - 玩家1记录数: {len(records1)}")
    print(f"  - 玩家2记录数: {len(records2)}")
    
    assert len(records1) == 1, "玩家1记录数不正确"
    assert len(records2) == 1, "玩家2记录数不正确"
    
    for record in records1:
        print(f"    记录: {record.get('room_name')}")
        print(f"    对手: {record.get('opponent_name')}")
        print(f"    执子: {'黑棋' if record.get('my_color') == 1 else '白棋'}")
        print(f"    结果: {'胜利' if record.get('is_winner') else '失败'}")
        print(f"    步数: {record.get('total_moves')}")
    
    print("  ✓ 测试通过!")


def test_replay_data_structure(record_id):
    """测试复盘数据结构"""
    print("\n" + "=" * 60)
    print("测试 4: 验证复盘数据结构")
    print("=" * 60)
    
    record = get_game_record(record_id)
    
    required_fields = [
        'id', 'player1_id', 'player1_name', 'player2_id', 'player2_name',
        'player1_color', 'player2_color', 'winner_color', 'winner_id',
        'move_history', 'total_moves', 'game_over'
    ]
    
    all_present = True
    for field in required_fields:
        if field not in record:
            print(f"  ✗ 缺少字段: {field}")
            all_present = False
        else:
            print(f"  ✓ 字段存在: {field}")
    
    move_history = record.get('move_history', [])
    for i, move in enumerate(move_history):
        assert len(move) == 3, f"第 {i+1} 步格式错误"
        row, col, player = move
        assert isinstance(row, int), f"第 {i+1} 步行不是整数"
        assert isinstance(col, int), f"第 {i+1} 步列不是整数"
        assert player in [PLAYER_BLACK, PLAYER_WHITE], f"第 {i+1} 步玩家颜色无效"
    
    print("  ✓ 测试通过!")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("游戏历史记录功能测试")
    print("=" * 60)
    
    try:
        player1_id, player2_id, record_id = test_game_record_creation()
        test_game_record_retrieval(record_id)
        test_player_records(player1_id, player2_id)
        test_replay_data_structure(record_id)
        
        print("\n" + "=" * 60)
        print("所有测试通过! ✓")
        print("=" * 60)
        
        return True
    except AssertionError as e:
        print(f"\n  ✗ 测试失败: {e}")
        return False
    except Exception as e:
        print(f"\n  ✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
