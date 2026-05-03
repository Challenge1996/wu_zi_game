#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
战绩统计调试脚本 - 验证整个流程
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from constants import (
    PLAYER_BLACK,
    PLAYER_WHITE,
    RANK_NEWBIE,
    RANK_IRON,
    RANK_BRONZE,
    SCORE_WIN,
    SCORE_LOSE
)
from server.data_store import players, rooms
from server.utils import (
    calculate_rank,
    update_player_stats,
    update_game_stats
)
from util import get_timestamp, generate_id
from game import WuziqiGame


def debug_full_flow():
    """调试完整的游戏结束和战绩更新流程"""
    print("=" * 60)
    print("调试完整的游戏结束和战绩更新流程")
    print("=" * 60)
    
    # 清空数据
    players.clear()
    rooms.clear()
    
    # 创建两个玩家
    player1_id = generate_id()
    player2_id = generate_id()
    
    now = get_timestamp()
    
    players[player1_id] = {
        'id': player1_id,
        'name': '玩家A',
        'online': True,
        'status': 'idle',
        'current_room': None,
        'last_heartbeat': now,
        'registered_at': now,
        'stats': {
            'total_games': 0,
            'wins': 0,
            'losses': 0,
            'draws': 0,
            'win_rate': 0.0,
            'current_streak': 0,
            'max_streak': 0,
            'score': 0,
            'rank': RANK_NEWBIE
        }
    }
    
    players[player2_id] = {
        'id': player2_id,
        'name': '玩家B',
        'online': True,
        'status': 'idle',
        'current_room': None,
        'last_heartbeat': now,
        'registered_at': now,
        'stats': {
            'total_games': 0,
            'wins': 0,
            'losses': 0,
            'draws': 0,
            'win_rate': 0.0,
            'current_streak': 0,
            'max_streak': 0,
            'score': 0,
            'rank': RANK_NEWBIE
        }
    }
    
    print(f"\n创建玩家:")
    print(f"  玩家A (ID: {player1_id[:8]}...)")
    print(f"  玩家B (ID: {player2_id[:8]}...)")
    
    # 创建房间
    room_id = generate_id()
    game = WuziqiGame()
    
    # 模拟游戏开始时的颜色分配
    game.players[PLAYER_BLACK] = player1_id  # 玩家A执黑
    game.players[PLAYER_WHITE] = player2_id  # 玩家B执白
    game.start_game()
    
    rooms[room_id] = {
        'id': room_id,
        'name': '玩家A vs 玩家B',
        'status': 'playing',
        'visibility': 'public',
        'player1': player1_id,  # 黑棋玩家
        'player2': player2_id,  # 白棋玩家
        'game': game,
        'spectators': set(),
        'spectator_count': 0,
        'created_at': now
    }
    
    print(f"\n创建房间:")
    print(f"  房间ID: {room_id[:8]}...")
    print(f"  player1 (黑棋): {rooms[room_id]['player1']} = 玩家A? {rooms[room_id]['player1'] == player1_id}")
    print(f"  player2 (白棋): {rooms[room_id]['player2']} = 玩家B? {rooms[room_id]['player2'] == player2_id}")
    
    print(f"\n初始战绩:")
    print(f"  玩家A: 总对局={players[player1_id]['stats']['total_games']}, 胜={players[player1_id]['stats']['wins']}, 负={players[player1_id]['stats']['losses']}, 积分={players[player1_id]['stats']['score']}")
    print(f"  玩家B: 总对局={players[player2_id]['stats']['total_games']}, 胜={players[player2_id]['stats']['wins']}, 负={players[player2_id]['stats']['losses']}, 积分={players[player2_id]['stats']['score']}")
    
    # 模拟游戏结束：黑棋（玩家A）获胜
    print("\n" + "-" * 40)
    print("模拟游戏结束：黑棋（玩家A）获胜")
    print("-" * 40)
    
    # 这是游戏结束时的逻辑（模拟 routes.py 中的代码）
    winner_color = PLAYER_BLACK  # 黑棋获胜
    
    print(f"  winner_color (获胜颜色): {winner_color}")
    print(f"  房间player1 (黑棋): {rooms[room_id]['player1']}")
    print(f"  房间player2 (白棋): {rooms[room_id]['player2']}")
    
    # 这是 routes.py 中计算 winner_id 的代码
    winner_id = None
    if winner_color == PLAYER_BLACK:
        winner_id = rooms[room_id].get('player1')
    elif winner_color == PLAYER_WHITE:
        winner_id = rooms[room_id].get('player2')
    
    print(f"  计算出的 winner_id: {winner_id}")
    print(f"  winner_id == player1_id? {winner_id == player1_id}")
    print(f"  winner_id == player2_id? {winner_id == player2_id}")
    
    # 调用 update_game_stats
    print(f"\n  调用 update_game_stats(room_id, winner_id)...")
    update_game_stats(room_id, winner_id)
    
    # 检查结果
    print("\n更新后战绩:")
    print(f"  玩家A (应该获胜):")
    print(f"    总对局: {players[player1_id]['stats']['total_games']} (期望: 1)")
    print(f"    胜: {players[player1_id]['stats']['wins']} (期望: 1)")
    print(f"    负: {players[player1_id]['stats']['losses']} (期望: 0)")
    print(f"    积分: {players[player1_id]['stats']['score']} (期望: 1)")
    print(f"    段位: {players[player1_id]['stats']['rank']} (期望: 黑铁)")
    print(f"    胜率: {players[player1_id]['stats']['win_rate']}% (期望: 100.0%)")
    
    print(f"\n  玩家B (应该失败):")
    print(f"    总对局: {players[player2_id]['stats']['total_games']} (期望: 1)")
    print(f"    胜: {players[player2_id]['stats']['wins']} (期望: 0)")
    print(f"    负: {players[player2_id]['stats']['losses']} (期望: 1)")
    print(f"    积分: {players[player2_id]['stats']['score']} (期望: -1)")
    print(f"    段位: {players[player2_id]['stats']['rank']} (期望: 新手)")
    print(f"    胜率: {players[player2_id]['stats']['win_rate']}% (期望: 0.0%)")
    
    # 验证
    print("\n" + "=" * 60)
    print("验证结果:")
    print("=" * 60)
    
    player1_stats = players[player1_id]['stats']
    player2_stats = players[player2_id]['stats']
    
    errors = []
    
    if player1_stats['wins'] != 1:
        errors.append(f"玩家A胜场数错误: 期望1，实际{player1_stats['wins']}")
    if player1_stats['losses'] != 0:
        errors.append(f"玩家A负场数错误: 期望0，实际{player1_stats['losses']}")
    if player1_stats['score'] != 1:
        errors.append(f"玩家A积分错误: 期望1，实际{player1_stats['score']}")
    if player1_stats['rank'] != RANK_IRON:
        errors.append(f"玩家A段位错误: 期望{RANK_IRON}，实际{player1_stats['rank']}")
    
    if player2_stats['wins'] != 0:
        errors.append(f"玩家B胜场数错误: 期望0，实际{player2_stats['wins']}")
    if player2_stats['losses'] != 1:
        errors.append(f"玩家B负场数错误: 期望1，实际{player2_stats['losses']}")
    if player2_stats['score'] != -1:
        errors.append(f"玩家B积分错误: 期望-1，实际{player2_stats['score']}")
    if player2_stats['rank'] != RANK_NEWBIE:
        errors.append(f"玩家B段位错误: 期望{RANK_NEWBIE}，实际{player2_stats['rank']}")
    
    if errors:
        print("❌ 发现错误:")
        for error in errors:
            print(f"   - {error}")
        return False
    else:
        print("✅ 所有验证通过！")
        return True


def debug_update_game_stats_directly():
    """直接调试 update_game_stats 函数"""
    print("\n" + "=" * 60)
    print("直接调试 update_game_stats 函数")
    print("=" * 60)
    
    players.clear()
    rooms.clear()
    
    player1_id = generate_id()
    player2_id = generate_id()
    
    now = get_timestamp()
    
    players[player1_id] = {
        'id': player1_id,
        'name': '玩家A',
        'online': True,
        'status': 'idle',
        'current_room': None,
        'last_heartbeat': now,
        'registered_at': now,
        'stats': {
            'total_games': 0, 'wins': 0, 'losses': 0, 'draws': 0,
            'win_rate': 0.0, 'current_streak': 0, 'max_streak': 0,
            'score': 0, 'rank': RANK_NEWBIE
        }
    }
    
    players[player2_id] = {
        'id': player2_id,
        'name': '玩家B',
        'online': True,
        'status': 'idle',
        'current_room': None,
        'last_heartbeat': now,
        'registered_at': now,
        'stats': {
            'total_games': 0, 'wins': 0, 'losses': 0, 'draws': 0,
            'win_rate': 0.0, 'current_streak': 0, 'max_streak': 0,
            'score': 0, 'rank': RANK_NEWBIE
        }
    }
    
    room_id = generate_id()
    game = WuziqiGame()
    game.players[PLAYER_BLACK] = player1_id
    game.players[PLAYER_WHITE] = player2_id
    
    rooms[room_id] = {
        'id': room_id,
        'player1': player1_id,  # 黑棋
        'player2': player2_id,  # 白棋
        'game': game
    }
    
    print(f"\n测试场景: 玩家A (player1, 黑棋) 获胜")
    print(f"  room['player1'] = {room_id[:8]}... (player1_id)")
    print(f"  room['player2'] = {player2_id[:8]}... (player2_id)")
    
    # 情况1: winner_id = player1_id (直接传玩家ID)
    print(f"\n情况1: 直接传 winner_id = player1_id")
    update_game_stats(room_id, player1_id)
    
    print(f"  玩家A胜场: {players[player1_id]['stats']['wins']}")
    print(f"  玩家B负场: {players[player2_id]['stats']['losses']}")
    
    # 重置
    players[player1_id]['stats']['total_games'] = 0
    players[player1_id]['stats']['wins'] = 0
    players[player1_id]['stats']['losses'] = 0
    players[player1_id]['stats']['score'] = 0
    players[player1_id]['stats']['rank'] = RANK_NEWBIE
    
    players[player2_id]['stats']['total_games'] = 0
    players[player2_id]['stats']['wins'] = 0
    players[player2_id]['stats']['losses'] = 0
    players[player2_id]['stats']['score'] = 0
    players[player2_id]['stats']['rank'] = RANK_NEWBIE
    
    # 情况2: 交换 player1 和 player2
    print(f"\n情况2: 交换 player1 和 player2（player1_id 是白棋，player2_id 是黑棋）")
    
    # 修改房间数据：player2 是黑棋，player1 是白棋
    rooms[room_id]['player1'] = player2_id  # 黑棋
    rooms[room_id]['player2'] = player1_id  # 白棋
    game.players[PLAYER_BLACK] = player2_id
    game.players[PLAYER_WHITE] = player1_id
    
    print(f"  room['player1'] = {rooms[room_id]['player1'][:8]}... (player2_id)")
    print(f"  room['player2'] = {rooms[room_id]['player2'][:8]}... (player1_id)")
    print(f"  现在 winner_id = player2_id（黑棋获胜）")
    
    update_game_stats(room_id, player2_id)
    
    print(f"  玩家B (player2_id) 胜场: {players[player2_id]['stats']['wins']}")
    print(f"  玩家A (player1_id) 负场: {players[player1_id]['stats']['losses']}")
    
    print("\n✅ 函数调试完成")


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("战绩统计调试脚本")
    print("=" * 60)
    
    # 先直接调试函数
    debug_update_game_stats_directly()
    
    # 再调试完整流程
    success = debug_full_flow()
    
    if success:
        print("\n🎉 所有测试通过！")
    else:
        print("\n❌ 测试失败！")
        sys.exit(1)
