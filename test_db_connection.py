#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据库连接和基本操作
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 首先测试直接连接数据库
print("=" * 60)
print("测试1：直接测试数据库连接")
print("=" * 60)

try:
    import pymysql
    from pymysql.cursors import DictCursor
    
    # 使用默认参数
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_port = int(os.environ.get('DB_PORT', 3306))
    db_user = os.environ.get('DB_USER', 'root')
    db_password = os.environ.get('DB_PASSWORD', '123456')
    db_name = os.environ.get('DB_NAME', 'wuziqi_game')
    
    print(f"连接参数：")
    print(f"  主机: {db_host}")
    print(f"  端口: {db_port}")
    print(f"  用户: {db_user}")
    print(f"  密码: {'*' * len(db_password)}")
    print(f"  数据库: {db_name}")
    
    # 尝试连接
    connection = pymysql.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name,
        charset='utf8mb4',
        cursorclass=DictCursor,
        autocommit=True
    )
    
    print("\n✓ 数据库连接成功！")
    
    # 测试执行查询
    with connection.cursor() as cursor:
        # 查看所有表
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"\n数据库中的表：")
        for table in tables:
            for key, value in table.items():
                print(f"  - {value}")
        
        # 测试插入和查询
        print("\n" + "=" * 60)
        print("测试2：测试插入和查询操作")
        print("=" * 60)
        
        # 先检查players表是否为空
        cursor.execute("SELECT COUNT(*) as count FROM players")
        result = cursor.fetchone()
        print(f"players表当前记录数: {result['count']}")
        
        # 插入一条测试数据
        test_player_id = 'test_player_001'
        test_player_name = '测试玩家'
        
        # 先删除可能存在的测试数据
        cursor.execute("DELETE FROM player_stats WHERE player_id = %s", (test_player_id,))
        cursor.execute("DELETE FROM players WHERE id = %s", (test_player_id,))
        
        # 插入新数据
        cursor.execute('''
            INSERT INTO players (id, name, online, status, current_room, last_heartbeat, registered_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (test_player_id, test_player_name, True, 'idle', None, 1234567890, 1234567890))
        
        cursor.execute('''
            INSERT INTO player_stats (player_id, total_games, wins, losses, draws, win_rate, 
                                      current_streak, max_streak, score, rank)
            VALUES (%s, 0, 0, 0, 0, 0.00, 0, 0, 0, '新手')
        ''', (test_player_id,))
        
        print("✓ 测试数据插入成功！")
        
        # 查询插入的数据
        cursor.execute('''
            SELECT p.*, ps.total_games, ps.wins, ps.losses, ps.draws, 
                   ps.win_rate, ps.current_streak, ps.max_streak, ps.score, ps.rank
            FROM players p
            LEFT JOIN player_stats ps ON p.id = ps.player_id
            WHERE p.id = %s
        ''', (test_player_id,))
        
        row = cursor.fetchone()
        if row:
            print(f"\n查询到的测试数据：")
            print(f"  玩家ID: {row['id']}")
            print(f"  玩家名称: {row['name']}")
            print(f"  在线状态: {row['online']}")
            print(f"  状态: {row['status']}")
            print(f"  总对局数: {row['total_games']}")
            print(f"  胜场数: {row['wins']}")
            print(f"  积分: {row['score']}")
            print(f"  段位: {row['rank']}")
            print("\n✓ 数据查询成功！")
        
        # 清理测试数据
        cursor.execute("DELETE FROM player_stats WHERE player_id = %s", (test_player_id,))
        cursor.execute("DELETE FROM players WHERE id = %s", (test_player_id,))
        print("\n✓ 测试数据清理完成！")
    
    connection.close()
    print("\n" + "=" * 60)
    print("数据库连接测试完成！")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ 数据库连接失败：")
    print(f"  错误类型: {type(e).__name__}")
    print(f"  错误信息: {e}")
    import traceback
    traceback.print_exc()

# 测试USE_DATABASE环境变量
print("\n" + "=" * 60)
print("测试3：检查USE_DATABASE环境变量设置")
print("=" * 60)

use_database_env = os.environ.get('USE_DATABASE', 'false')
print(f"USE_DATABASE 环境变量值: '{use_database_env}'")
print(f"USE_DATABASE 计算结果: {use_database_env.lower() == 'true'}")

if use_database_env.lower() != 'true':
    print("\n⚠️  警告：USE_DATABASE 环境变量未设置为 'true'")
    print("   这意味着数据库持久化功能当前是关闭的！")
    print("   所有的同步操作（sync_player, sync_room, sync_game_record 等）都会被跳过。")
    print("\n   解决方案：")
    print("   1. 在启动服务器前设置环境变量：")
    print("      export USE_DATABASE=true")
    print("   2. 或者修改 server/data_store.py 中的默认值")
else:
    print("\n✓ USE_DATABASE 环境变量已正确设置为 'true'")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
