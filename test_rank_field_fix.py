#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 rank 字段修复是否成功
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 确保 USE_DATABASE 是启用的
os.environ['USE_DATABASE'] = 'true'

print("=" * 60)
print("测试 rank 字段修复")
print("=" * 60)

# 导入模块
try:
    import server
    from server.data_store import (
        USE_DATABASE,
        sync_player,
        load_from_database
    )
    from server.database import (
        get_player,
        create_player,
        update_player_stats
    )
    from util import get_timestamp, generate_id
    from constants import RANK_NEWBIE
    
    print(f"✓ 模块导入成功")
    print(f"✓ USE_DATABASE = {USE_DATABASE}")
    
except Exception as e:
    print(f"✗ 模块导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试1：直接测试 create_player 函数
print("\n" + "=" * 60)
print("测试1：直接测试 create_player 函数（包含 rank 字段）")
print("=" * 60)

try:
    # 加载数据库（初始化表）
    load_from_database()
    print("✓ 数据库表初始化成功")
    
    # 创建测试玩家
    test_player_id = generate_id()
    test_player_name = "测试玩家_rank"
    now = get_timestamp()
    
    print(f"\n尝试创建玩家: {test_player_name} ({test_player_id})")
    
    # 直接调用 create_player 函数
    player = create_player(test_player_id, test_player_name, now)
    
    if player:
        print(f"✓ 玩家创建成功！")
        print(f"  - 玩家ID: {player['id']}")
        print(f"  - 玩家名称: {player['name']}")
        print(f"  - 段位: {player['stats']['rank']}")
        print(f"  - 总对局数: {player['stats']['total_games']}")
    else:
        print("✗ 玩家创建失败")
        
except Exception as e:
    print(f"✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()

# 测试2：测试 update_player_stats 函数
print("\n" + "=" * 60)
print("测试2：测试 update_player_stats 函数（更新 rank 字段）")
print("=" * 60)

try:
    # 更新玩家的段位和积分
    print(f"\n尝试更新玩家的段位和积分...")
    
    update_player_stats(
        test_player_id,
        total_games=5,
        wins=3,
        losses=2,
        score=10,
        rank='青铜'
    )
    
    print("✓ update_player_stats 调用成功")
    
    # 重新查询玩家信息
    updated_player = get_player(test_player_id)
    
    if updated_player:
        print(f"\n✓ 玩家信息更新成功！")
        print(f"  - 总对局数: {updated_player['stats']['total_games']} (期望: 5)")
        print(f"  - 胜场数: {updated_player['stats']['wins']} (期望: 3)")
        print(f"  - 负场数: {updated_player['stats']['losses']} (期望: 2)")
        print(f"  - 积分: {updated_player['stats']['score']} (期望: 10)")
        print(f"  - 段位: {updated_player['stats']['rank']} (期望: 青铜)")
        
        # 验证更新是否正确
        if (updated_player['stats']['total_games'] == 5 and
            updated_player['stats']['wins'] == 3 and
            updated_player['stats']['losses'] == 2 and
            updated_player['stats']['score'] == 10 and
            updated_player['stats']['rank'] == '青铜'):
            print("\n✓ 所有字段更新正确！")
        else:
            print("\n⚠️  部分字段更新不正确")
    else:
        print("✗ 无法查询到更新后的玩家信息")
        
except Exception as e:
    print(f"✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()

# 测试3：测试 sync_player 函数（完整的同步流程）
print("\n" + "=" * 60)
print("测试3：测试 sync_player 函数（完整的同步流程）")
print("=" * 60)

try:
    # 创建另一个测试玩家到内存中
    test_player2_id = generate_id()
    test_player2_name = "测试玩家_sync"
    now = get_timestamp()
    
    # 先在内存中创建玩家
    server.players[test_player2_id] = {
        'id': test_player2_id,
        'name': test_player2_name,
        'online': True,
        'status': 'idle',
        'current_room': None,
        'last_heartbeat': now,
        'registered_at': now,
        'stats': {
            'total_games': 10,
            'wins': 7,
            'losses': 3,
            'draws': 0,
            'win_rate': 70.0,
            'current_streak': 2,
            'max_streak': 5,
            'score': 25,
            'rank': '白银'
        }
    }
    
    print(f"\n内存中创建玩家: {test_player2_name} ({test_player2_id})")
    print(f"  - 段位: {server.players[test_player2_id]['stats']['rank']}")
    
    # 调用 sync_player 同步到数据库
    print(f"\n调用 sync_player 同步到数据库...")
    sync_player(test_player2_id)
    print("✓ sync_player 调用成功")
    
    # 从数据库查询
    db_player = get_player(test_player2_id)
    
    if db_player:
        print(f"\n✓ 从数据库查询到玩家信息！")
        print(f"  - 玩家ID: {db_player['id']}")
        print(f"  - 玩家名称: {db_player['name']}")
        print(f"  - 总对局数: {db_player['stats']['total_games']} (期望: 10)")
        print(f"  - 胜场数: {db_player['stats']['wins']} (期望: 7)")
        print(f"  - 积分: {db_player['stats']['score']} (期望: 25)")
        print(f"  - 段位: {db_player['stats']['rank']} (期望: 白银)")
        
        # 验证
        if (db_player['stats']['total_games'] == 10 and
            db_player['stats']['wins'] == 7 and
            db_player['stats']['score'] == 25 and
            db_player['stats']['rank'] == '白银'):
            print("\n✓ sync_player 同步成功！所有字段正确！")
        else:
            print("\n⚠️  sync_player 同步可能有问题")
    else:
        print("✗ 无法从数据库查询到玩家信息")
        
except Exception as e:
    print(f"✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()

# 清理测试数据
print("\n" + "=" * 60)
print("测试4：清理测试数据")
print("=" * 60)

try:
    from server.database import get_db
    
    db = get_db()
    conn = db.get_connection()
    
    with conn.cursor() as cursor:
        # 删除测试玩家
        cursor.execute("DELETE FROM player_stats WHERE player_id = %s", (test_player_id,))
        cursor.execute("DELETE FROM players WHERE id = %s", (test_player_id,))
        print(f"✓ 已删除测试玩家1: {test_player_id}")
        
        cursor.execute("DELETE FROM player_stats WHERE player_id = %s", (test_player2_id,))
        cursor.execute("DELETE FROM players WHERE id = %s", (test_player2_id,))
        print(f"✓ 已删除测试玩家2: {test_player2_id}")
        
    print("\n✓ 所有测试数据已清理")
    
except Exception as e:
    print(f"⚠️  清理测试数据失败: {e}")
    print("   您可以手动执行以下 SQL 清理：")
    print(f"   DELETE FROM player_stats WHERE player_id IN ('{test_player_id}', '{test_player2_id}');")
    print(f"   DELETE FROM players WHERE id IN ('{test_player_id}', '{test_player2_id}');")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)
print("\n总结：")
print("1. rank 字段是 MySQL 的保留关键字，需要使用反引号（`）包裹")
print("2. 已修复以下位置的 SQL 语句：")
print("   - 建表语句: `rank` VARCHAR(50) DEFAULT '新手'")
print("   - INSERT 语句: ..., score, `rank`)")
print("   - SELECT 语句: ..., ps.`rank`")
print("   - UPDATE 语句: 动态构建时对 rank 字段使用反引号")
print("\n3. 现在玩家注册、更新段位等操作应该可以正常工作了！")
