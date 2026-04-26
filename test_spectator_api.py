#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
观战功能API联调测试脚本
"""

import requests
import json

SERVER_URL = 'http://localhost:5001'


def test_api():
    print("=" * 60)
    print("观战功能API联调测试")
    print("=" * 60)
    
    # 1. 检查服务端健康
    print("\n[1] 检查服务端健康")
    r = requests.get(f'{SERVER_URL}/api/health')
    result = r.json()
    print(f"  健康检查: {result}")
    assert result.get('status') == 'ok', "服务端健康检查失败"
    print("  ✓ 服务端运行正常")
    
    # 2. 注册5个玩家
    print("\n[2] 注册玩家")
    players = []
    for name in ['玩家A', '玩家B', '观战者1', '观战者2', '观战者3']:
        r = requests.post(f'{SERVER_URL}/api/player/register', json={'name': name})
        result = r.json()
        if result.get('success'):
            player = {
                'id': result.get('player_id'),
                'name': result.get('name')
            }
            players.append(player)
            print(f"  ✓ 注册成功: {player['name']} (ID: {player['id'][:8]}...)")
        else:
            print(f"  ✗ 注册失败: {result}")
            return False
    
    player1, player2, spectator1, spectator2, spectator3 = players
    
    # 3. 玩家A向玩家B发起挑战
    print("\n[3] 玩家A向玩家B发起挑战")
    r = requests.post(f'{SERVER_URL}/api/challenge/send', json={
        'challenger_id': player1['id'],
        'challenged_id': player2['id']
    })
    result = r.json()
    assert result.get('success'), f"发起挑战失败: {result}"
    challenge_id = result.get('challenge_id')
    print(f"  ✓ 挑战已发送，挑战ID: {challenge_id[:8]}...")
    
    # 4. 玩家B接受挑战
    print("\n[4] 玩家B接受挑战")
    r = requests.post(f'{SERVER_URL}/api/challenge/accept', json={
        'challenge_id': challenge_id,
        'player_id': player2['id']
    })
    result = r.json()
    assert result.get('success'), f"接受挑战失败: {result}"
    room_id = result.get('room_id')
    print(f"  ✓ 挑战已接受，房间ID: {room_id[:8]}...")
    
    # 5. 获取公开房间列表（游戏开始前）
    print("\n[5] 获取公开房间列表（游戏开始前）")
    r = requests.get(f'{SERVER_URL}/api/room/public_list')
    result = r.json()
    assert result.get('success'), f"获取公开房间列表失败: {result}"
    rooms = result.get('rooms', [])
    print(f"  找到 {len(rooms)} 个公开房间")
    for room in rooms:
        print(f"    - {room['name']} | 状态: {room['status']} | 观战人数: {room['spectator_count']}")
    
    # 6. 快速开始游戏
    print("\n[6] 快速开始游戏")
    r = requests.post(f'{SERVER_URL}/api/game/quick_start', json={
        'player1_id': player1['id'],
        'player2_id': player2['id']
    })
    result = r.json()
    if result.get('success'):
        room_id = result.get('room_id')
        print(f"  ✓ 游戏已开始，房间ID: {room_id[:8]}...")
    else:
        print(f"  快速开始失败（可能游戏已开始）: {result.get('message')}")
    
    # 7. 获取公开房间列表（游戏进行中）
    print("\n[7] 获取公开房间列表（游戏进行中）")
    r = requests.get(f'{SERVER_URL}/api/room/public_list')
    result = r.json()
    assert result.get('success'), f"获取公开房间列表失败: {result}"
    rooms = result.get('rooms', [])
    print(f"  找到 {len(rooms)} 个公开房间")
    for room in rooms:
        hot_text = "🔥 热门" if room.get('is_hot_game') else ""
        print(f"    - {room['name']} | 状态: {room['status']} | 观战人数: {room['spectator_count']} | {hot_text}")
    
    # 8. 玩家A落子
    print("\n[8] 玩家A落子")
    r = requests.post(f'{SERVER_URL}/api/game/place_piece', json={
        'player_id': player1['id'],
        'room_id': room_id,
        'row': 7,
        'col': 7
    })
    result = r.json()
    if result.get('success'):
        print("  ✓ 落子成功")
    else:
        print(f"  落子失败（可能不是轮到他）: {result.get('message')}")
    
    # 9. 观战者1加入观战
    print("\n[9] 观战者1加入观战")
    r = requests.post(f'{SERVER_URL}/api/room/spectate', json={
        'player_id': spectator1['id'],
        'room_id': room_id
    })
    result = r.json()
    assert result.get('success'), f"加入观战失败: {result}"
    print(f"  ✓ {spectator1['name']}加入观战成功: {result.get('message')}")
    
    # 10. 获取公开房间列表（有1个观战者）
    print("\n[10] 获取公开房间列表（1个观战者）")
    r = requests.get(f'{SERVER_URL}/api/room/public_list')
    result = r.json()
    rooms = result.get('rooms', [])
    for room in rooms:
        hot_text = "🔥 热门" if room.get('is_hot_game') else ""
        print(f"    - {room['name']} | 观战人数: {room['spectator_count']} | {hot_text}")
        assert room.get('spectator_count') == 1, "观战人数应该是1"
        assert not room.get('is_hot_game'), "不应该是热门对局（需要>1人）"
    print("  ✓ 观战人数正确，热门标识正确")
    
    # 11. 观战者2加入观战（现在有2个观战者，应该成为热门对局）
    print("\n[11] 观战者2加入观战")
    r = requests.post(f'{SERVER_URL}/api/room/spectate', json={
        'player_id': spectator2['id'],
        'room_id': room_id
    })
    result = r.json()
    assert result.get('success'), f"加入观战失败: {result}"
    print(f"  ✓ {spectator2['name']}加入观战成功: {result.get('message')}")
    
    # 12. 获取公开房间列表（有2个观战者，应该是热门）
    print("\n[12] 获取公开房间列表（2个观战者，热门对局）")
    r = requests.get(f'{SERVER_URL}/api/room/public_list')
    result = r.json()
    rooms = result.get('rooms', [])
    for room in rooms:
        hot_text = "🔥 热门" if room.get('is_hot_game') else ""
        print(f"    - {room['name']} | 观战人数: {room['spectator_count']} | {hot_text}")
        assert room.get('spectator_count') == 2, "观战人数应该是2"
        assert room.get('is_hot_game'), "应该是热门对局（>1人）"
    print("  ✓ 观战人数正确，热门标识正确")
    
    # 13. 测试观战者不能操作棋局
    print("\n[13] 测试观战者不能操作棋局")
    r = requests.post(f'{SERVER_URL}/api/game/place_piece', json={
        'player_id': spectator1['id'],
        'room_id': room_id,
        'row': 8,
        'col': 8
    })
    result = r.json()
    if not result.get('success'):
        print(f"  ✓ 观战者落子被正确拒绝: {result.get('message')}")
    else:
        print("  ✗ 观战者落子成功（这是错误的！）")
        return False
    
    # 14. 测试观战者可以聊天
    print("\n[14] 测试观战者可以聊天")
    r = requests.post(f'{SERVER_URL}/api/chat/send', json={
        'player_id': spectator1['id'],
        'room_id': room_id,
        'content': '大家好，我是观战者！'
    })
    result = r.json()
    if result.get('success'):
        print("  ✓ 观战者聊天成功")
    else:
        print(f"  ✗ 观战者聊天失败: {result.get('message')}")
        return False
    
    # 15. 获取房间详细信息
    print("\n[15] 获取房间详细信息")
    r = requests.get(f'{SERVER_URL}/api/room/info', params={
        'room_id': room_id,
        'player_id': spectator1['id']
    })
    result = r.json()
    assert result.get('success'), f"获取房间信息失败: {result}"
    room = result.get('room', {})
    print(f"    房间名称: {room.get('name')}")
    print(f"    房间状态: {room.get('status')}")
    print(f"    可见性: {room.get('visibility')}")
    print(f"    观战人数: {room.get('spectator_count')}")
    print(f"    是否热门: {room.get('is_hot_game')}")
    print(f"    观战者列表: {[s['name'] for s in room.get('spectators', [])]}")
    
    # 验证
    assert room.get('visibility') == 'public', "房间应该是公开的"
    assert room.get('spectator_count') == 2, "观战人数应该是2"
    assert room.get('is_hot_game') == True, "应该是热门对局"
    print("  ✓ 房间信息正确")
    
    # 16. 测试对局玩家不能作为观战者加入
    print("\n[16] 测试对局玩家不能作为观战者加入")
    r = requests.post(f'{SERVER_URL}/api/room/spectate', json={
        'player_id': player1['id'],
        'room_id': room_id
    })
    result = r.json()
    if not result.get('success'):
        print(f"  ✓ 对局玩家加入观战被正确拒绝: {result.get('message')}")
    else:
        print("  ✗ 对局玩家可以作为观战者加入（这是错误的！）")
        return False
    
    # 17. 测试已经在观战的玩家不能重复加入
    print("\n[17] 测试已经在观战的玩家不能重复加入")
    r = requests.post(f'{SERVER_URL}/api/room/spectate', json={
        'player_id': spectator1['id'],
        'room_id': room_id
    })
    result = r.json()
    if not result.get('success'):
        print(f"  ✓ 重复加入观战被正确拒绝: {result.get('message')}")
    else:
        print("  ✗ 重复加入观战成功（这是错误的！）")
        return False
    
    # 18. 观战者1离开观战
    print("\n[18] 观战者1离开观战")
    r = requests.post(f'{SERVER_URL}/api/room/leave_spectate', json={
        'player_id': spectator1['id'],
        'room_id': room_id
    })
    result = r.json()
    assert result.get('success'), f"离开观战失败: {result}"
    print(f"  ✓ {spectator1['name']}离开观战成功: {result.get('message')}")
    
    # 19. 再次获取公开房间列表（现在只有1个观战者，应该不是热门）
    print("\n[19] 获取公开房间列表（1个观战者，不是热门）")
    r = requests.get(f'{SERVER_URL}/api/room/public_list')
    result = r.json()
    rooms = result.get('rooms', [])
    for room in rooms:
        hot_text = "🔥 热门" if room.get('is_hot_game') else ""
        print(f"    - {room['name']} | 观战人数: {room['spectator_count']} | {hot_text}")
        assert room.get('spectator_count') == 1, "观战人数应该是1"
        assert not room.get('is_hot_game'), "不应该是热门对局"
    print("  ✓ 观战人数正确，热门标识正确")
    
    print("\n" + "=" * 60)
    print("🎉 所有API测试通过！")
    print("=" * 60)
    
    print("\n功能验证总结:")
    print("  ✓ 玩家可以注册并创建公开房间")
    print("  ✓ 其他玩家可以查看公开房间列表")
    print("  ✓ 观战者可以加入观战")
    print("  ✓ 观战者不能操作棋局（落子被拒绝）")
    print("  ✓ 观战者可以聊天")
    print("  ✓ 对局玩家不能作为观战者加入")
    print("  ✓ 观战人数大于1时显示热门标识")
    print("  ✓ 观战者可以离开观战")
    print("  ✓ 房间信息包含完整的观战信息")
    
    return True


if __name__ == '__main__':
    try:
        test_api()
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
