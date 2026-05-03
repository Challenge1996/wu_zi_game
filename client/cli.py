#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
五子棋游戏命令行客户端
支持多玩家匹配对战
"""

from constants import (
    SERVER_URL,
    PLAYER_BLACK,
    PLAYER_WHITE,
    COIN_HEAD,
    COIN_TAIL
)
from client.core import ClientCore


def print_main_menu():
    """打印主菜单"""
    print("\n" + "=" * 60)
    print("五子棋游戏客户端 - 支持多玩家匹配对战")
    print("=" * 60)
    
    print("\n【系统】")
    print("  1. 检查服务端状态")
    print("  2. 玩家注册")
    print("  3. 玩家下线")
    
    print("\n【玩家匹配】")
    print("  4. 查看在线玩家列表")
    print("  5. 发起挑战")
    print("  6. 查看我的挑战列表")
    print("  7. 接受挑战")
    print("  8. 拒绝挑战")
    
    print("\n【游戏操作】")
    print("  9. 查看当前房间信息")
    print("  10. 抛硬币猜测")
    print("  11. 解决抛硬币结果")
    print("  12. 选择执子颜色")
    print("  13. 落子")
    print("  14. 发起悔棋请求")
    print("  15. 查看悔棋请求状态")
    print("  16. 重置游戏")
    print("  17. 快速开始（跳过抛硬币）")
    
    print("\n【其他】")
    print("  0. 退出")
    print("=" * 60)


def print_board(board):
    """打印棋盘"""
    if not board:
        print("  (空棋盘)")
        return
    
    board_size = len(board)
    print("  " + " ".join([str(i % 10) for i in range(board_size)]))
    for i, row in enumerate(board):
        line = f"{i % 10} "
        for cell in row:
            if cell == 0:
                line += ". "
            elif cell == PLAYER_BLACK:
                line += "X "
            elif cell == PLAYER_WHITE:
                line += "O "
        print(line)


def display_room_info(room_info):
    """显示房间信息"""
    if not room_info:
        return
    
    print("\n" + "=" * 60)
    print(f"房间: {room_info.get('name')}")
    print("=" * 60)
    
    print(f"\n房间状态: {room_info.get('status')}")
    print(f"黑棋玩家: {room_info.get('player1_name', '未分配')}")
    print(f"白棋玩家: {room_info.get('player2_name', '未分配')}")
    
    game_state = room_info.get('game_state', {})
    print(f"\n游戏阶段: {game_state.get('game_phase')}")
    print(f"游戏时间: {game_state.get('game_time', 0)} 秒")
    print(f"已落子数: {game_state.get('move_count', 0)}")
    
    if 'player_color' in game_state:
        color = game_state.get('player_color')
        color_name = "黑棋" if color == PLAYER_BLACK else "白棋" if color == PLAYER_WHITE else "未分配"
        print(f"您的颜色: {color_name}")
        print(f"轮到您了: {'是' if game_state.get('is_my_turn') else '否'}")
    
    current_color = game_state.get('current_player')
    current_color_name = "黑棋" if current_color == PLAYER_BLACK else "白棋"
    print(f"当前玩家: {current_color_name}")
    
    print("\n棋盘:")
    print_board(game_state.get('board', []))
    
    if game_state.get('game_over'):
        winner = game_state.get('winner')
        winner_name = "黑棋" if winner == PLAYER_BLACK else "白棋"
        print(f"\n★ 游戏结束！{winner_name}获胜！ ★")
    elif room_info.get('status') == 'playing':
        print("\n游戏进行中...")
    
    print("=" * 60 + "\n")


def check_pending_undo_requests(client, room_id=None):
    """检查是否有待处理的悔棋请求"""
    room_to_use = room_id or client.current_room_id
    if not room_to_use:
        return False
    
    success, status = client.get_undo_status(room_to_use)
    if success and isinstance(status, dict) and status.get('success'):
        has_pending = status.get('has_pending_request', False)
        if has_pending:
            req = status.get('undo_request', {})
            is_requested_to_me = req.get('is_requested_to_me', False)
            
            if is_requested_to_me:
                requester_name = req.get('requester_name', '对手')
                print(f"\n📢 {requester_name} 向您请求悔棋！")
                print("请选择：")
                print("  1. 同意悔棋")
                print("  2. 拒绝悔棋")
                
                choice = input("请输入选项 (1/2): ").strip()
                if choice == '1':
                    client.respond_undo(True, room_to_use)
                    return True
                elif choice == '2':
                    client.respond_undo(False, room_to_use)
                    return True
        
    return False


def main():
    client = ClientCore()
    
    print("=" * 60)
    print("欢迎来到五子棋游戏！")
    print("=" * 60)
    print("请确保服务端已在运行 (python server.py)")
    print(f"服务端地址: {SERVER_URL}")
    print("=" * 60)
    print("\n对战流程：")
    print("1. 两个玩家分别注册（选项2）")
    print("2. 玩家A查看在线玩家列表（选项4）")
    print("3. 玩家A向玩家B发起挑战（选项5）")
    print("4. 玩家B查看挑战列表（选项6）并接受（选项7）或拒绝（选项8）")
    print("5. 接受挑战后，进入抛硬币阶段：")
    print("   - 两个玩家分别猜测（选项10）")
    print("   - 解决抛硬币结果（选项11）")
    print("   - 猜对的玩家选择执黑或执白（选项12）")
    print("   - 确定颜色后开始游戏（选项12完成后自动开始）")
    print("6. 轮流落子（选项13），连成5子获胜")
    print("=" * 60)
    
    while True:
        print_main_menu()
        
        if client.player_id:
            print(f"\n当前玩家: {client.player_name} ({client.player_id})")
        if client.current_room_id:
            print(f"当前房间: {client.current_room_id}")
        
        choice = input("\n请选择操作 (0-17): ").strip()
        
        if choice == '0':
            if client.player_id:
                client.go_offline()
            client.stop_heartbeat()
            print("感谢使用，再见！")
            break
        
        elif choice == '1':
            success, result = client.check_server_health()
            if success:
                print(f"✓ 服务端状态: {result.get('message', '正常')}")
            else:
                print(f"✗ 无法连接到服务端: {result}")
        
        elif choice == '2':
            name = input("请输入玩家名称（直接回车使用默认名称）: ").strip()
            success, result = client.register_player(name if name else None)
            if success:
                print(f"✓ 注册成功！")
                print(f"  玩家名称: {client.player_name}")
                print(f"  玩家ID: {client.player_id}")
            else:
                print(f"✗ 注册失败: {result}")
        
        elif choice == '3':
            success, result = client.go_offline()
            if success:
                print("✓ 已下线")
            else:
                print(f"✗ 下线失败: {result}")
        
        elif choice == '4':
            success, result = client.list_online_players()
            if success and result.get('success'):
                players = result.get('players', [])
                print(f"\n在线玩家列表 (共 {result.get('count', 0)} 人):")
                print("-" * 60)
                print(f"{'玩家ID':<40} {'名称':<15} {'状态':<10}")
                print("-" * 60)
                
                for p in players:
                    status_display = {
                        'idle': '空闲',
                        'waiting': '等待中',
                        'challenging': '挑战中',
                        'in_game': '游戏中'
                    }.get(p.get('status'), p.get('status'))
                    
                    is_self = p.get('id') == client.player_id
                    name_display = p.get('name', '未知') + (' (我)' if is_self else '')
                    print(f"{p.get('id'):<40} {name_display:<15} {status_display:<10}")
                
                print("-" * 60)
            else:
                print(f"✗ 获取玩家列表失败: {result}")
        
        elif choice == '5':
            if not client.player_id:
                print("✗ 请先注册玩家（选项2）")
                continue
            
            success, result = client.list_online_players()
            if not success or not result.get('success'):
                print("✗ 获取玩家列表失败")
                continue
            
            players = result.get('players', [])
            if not players:
                print("没有在线玩家")
                continue
            
            print("\n请输入要挑战的玩家ID:")
            challenged_id = input("玩家ID: ").strip()
            
            if challenged_id == client.player_id:
                print("✗ 不能挑战自己")
                continue
            
            valid = False
            for p in players:
                if p.get('id') == challenged_id:
                    valid = True
                    if p.get('status') != 'idle':
                        print("✗ 该玩家正忙，无法接受挑战")
                        valid = False
                    break
            
            if valid:
                success, result = client.send_challenge(challenged_id)
                if success and result.get('success'):
                    print(f"✓ {result.get('message')}")
                    print(f"  挑战ID: {result.get('challenge_id')}")
                else:
                    print(f"✗ 发起挑战失败: {result.get('message', '未知错误')}")
        
        elif choice == '6':
            if not client.player_id:
                print("✗ 请先注册玩家（选项2）")
                continue
            
            success, result = client.list_my_challenges()
            if success and result.get('success'):
                challenges = result.get('challenges', [])
                print(f"\n我的挑战列表 (共 {result.get('count', 0)} 条):")
                print("-" * 80)
                print(f"{'挑战ID':<40} {'类型':<10} {'对方':<15} {'状态':<10}")
                print("-" * 80)
                
                for c in challenges:
                    is_my_challenge = c.get('is_my_challenge')
                    challenge_type = '我发起的' if is_my_challenge else '收到的'
                    opponent = c.get('challenged_name') if is_my_challenge else c.get('challenger_name')
                    
                    status_display = {
                        'pending': '待处理',
                        'accepted': '已接受',
                        'declined': '已拒绝',
                        'expired': '已过期'
                    }.get(c.get('status'), c.get('status'))
                    
                    print(f"{c.get('id'):<40} {challenge_type:<10} {opponent:<15} {status_display:<10}")
                
                print("-" * 80)
            else:
                print(f"✗ 获取挑战列表失败: {result}")
        
        elif choice == '7':
            if not client.player_id:
                print("✗ 请先注册玩家（选项2）")
                continue
            
            success, result = client.list_my_challenges()
            if not success or not result.get('success'):
                print("✗ 获取挑战列表失败")
                continue
            
            challenges = result.get('challenges', [])
            pending_challenges = [c for c in challenges if c.get('status') == 'pending' and not c.get('is_my_challenge')]
            
            if not pending_challenges:
                print("没有待处理的挑战")
                continue
            
            print("\n请输入要接受的挑战ID:")
            challenge_id = input("挑战ID: ").strip()
            
            success, result = client.accept_challenge(challenge_id)
            if success and result.get('success'):
                print(f"✓ {result.get('message')}")
                print(f"  房间ID: {result.get('room_id')}")
            else:
                print(f"✗ 接受挑战失败: {result.get('message', '未知错误')}")
        
        elif choice == '8':
            if not client.player_id:
                print("✗ 请先注册玩家（选项2）")
                continue
            
            success, result = client.list_my_challenges()
            if not success or not result.get('success'):
                print("✗ 获取挑战列表失败")
                continue
            
            challenges = result.get('challenges', [])
            pending_challenges = [c for c in challenges if c.get('status') == 'pending' and not c.get('is_my_challenge')]
            
            if not pending_challenges:
                print("没有待处理的挑战")
                continue
            
            print("\n请输入要拒绝的挑战ID:")
            challenge_id = input("挑战ID: ").strip()
            
            success, result = client.decline_challenge(challenge_id)
            if success and result.get('success'):
                print(f"✓ {result.get('message')}")
            else:
                print(f"✗ 拒绝挑战失败: {result.get('message', '未知错误')}")
        
        elif choice == '9':
            if not client.current_room_id:
                print("✗ 您当前没有加入任何房间")
                continue
            
            success, result = client.get_room_info()
            if success and result.get('success'):
                room_info = result.get('room')
                if room_info:
                    display_room_info(room_info)
            else:
                print(f"✗ 获取房间信息失败: {result}")
        
        elif choice == '10':
            if not client.current_room_id:
                print("✗ 您当前没有加入任何房间")
                continue
            
            print("请选择硬币猜测：")
            print("0. 正面")
            print("1. 反面")
            coin_choice = input("请输入选项 (0/1): ").strip()
            
            if coin_choice in ['0', '1']:
                success, result = client.make_coin_choice(int(coin_choice))
                if success and result.get('success'):
                    print(f"✓ {result.get('message')}")
                    if result.get('auto_assigned'):
                        print(f"  您选择了: {result.get('player_choice')}")
                        print(f"  系统已自动为对方分配: {result.get('other_player_choice')}")
                else:
                    print(f"✗ 猜测失败: {result.get('message', '未知错误')}")
            else:
                print("✗ 无效的选项")
        
        elif choice == '11':
            if not client.current_room_id:
                print("✗ 您当前没有加入任何房间")
                continue
            
            success, result = client.resolve_coin_toss()
            if success and result.get('success'):
                print(f"✓ {result.get('message')}")
                print(f"  硬币结果: {result.get('coin_result')}")
                print(f"  获胜玩家ID: {result.get('winner_id')}")
                
                is_my_win = result.get('winner_id') == client.player_id
                if is_my_win:
                    print("\n恭喜！您猜对了！请选择执子颜色（选项12）。")
            else:
                print(f"✗ 解决抛硬币失败: {result.get('message', '未知错误')}")
        
        elif choice == '12':
            if not client.current_room_id:
                print("✗ 您当前没有加入任何房间")
                continue
            
            print("请选择执子颜色：")
            print("1. 黑棋（先手）")
            print("2. 白棋（后手）")
            color_choice = input("请输入选项 (1/2): ").strip()
            
            if color_choice in ['1', '2']:
                success, result = client.choose_color(int(color_choice))
                if success and result.get('success'):
                    print(f"✓ {result.get('message')}")
                else:
                    print(f"✗ 选择颜色失败: {result.get('message', '未知错误')}")
            else:
                print("✗ 无效的选项")
        
        elif choice == '13':
            if not client.current_room_id:
                print("✗ 您当前没有加入任何房间")
                continue
            
            success, result = client.get_room_info()
            if success and result.get('success'):
                room_info = result.get('room')
                if room_info:
                    display_room_info(room_info)
            
            try:
                row = int(input("请输入行号 (0-14): ").strip())
                col = int(input("请输入列号 (0-14): ").strip())
                
                success, result = client.place_piece(row, col)
                if success and result.get('success'):
                    print(f"✓ {result.get('message')}")
                    
                    success, result = client.get_room_info()
                    if success and result.get('success'):
                        room_info = result.get('room')
                        if room_info:
                            display_room_info(room_info)
                else:
                    print(f"✗ 落子失败: {result.get('message', '未知错误')}")
            except ValueError:
                print("✗ 请输入有效的数字")
        
        elif choice == '14':
            if not client.current_room_id:
                print("✗ 您当前没有加入任何房间")
                continue
            
            success, result = client.request_undo()
            if success and result.get('success'):
                print(f"✓ {result.get('message')}")
                print("  请等待对手回应...")
            else:
                print(f"✗ 发起悔棋请求失败: {result.get('message', '未知错误')}")
        
        elif choice == '15':
            if not client.current_room_id:
                print("✗ 您当前没有加入任何房间")
                continue
            
            success, status = client.get_undo_status()
            if success and isinstance(status, dict) and status.get('success'):
                has_pending = status.get('has_pending_request', False)
                if has_pending:
                    req = status.get('undo_request', {})
                    print(f"\n悔棋请求状态:")
                    print(f"  发起者: {req.get('requester_name', '未知')}")
                    print(f"  状态: {req.get('status', 'unknown')}")
                    print(f"  是否是我发起的: {'是' if req.get('is_my_request', False) else '否'}")
                    print(f"  是否发给我的: {'是' if req.get('is_requested_to_me', False) else '否'}")
                    
                    if req.get('is_requested_to_me', False) and req.get('status') == 'pending':
                        print("\n对手正在等待您的回应...")
                        check_pending_undo_requests(client)
                else:
                    print("\n当前没有待处理的悔棋请求")
            else:
                print(f"✗ 获取悔棋状态失败: {status}")
        
        elif choice == '16':
            if not client.current_room_id:
                print("✗ 您当前没有加入任何房间")
                continue
            
            confirm = input("确定要重置游戏吗？(y/n): ").strip().lower()
            if confirm == 'y':
                success, result = client.reset_game()
                if success and result.get('success'):
                    print(f"✓ {result.get('message')}")
                else:
                    print(f"✗ 重置失败: {result.get('message', '未知错误')}")
        
        elif choice == '17':
            if not client.player_id:
                print("✗ 请先注册玩家（选项2）")
                continue
            
            success, result = client.list_online_players()
            if not success or not result.get('success'):
                print("✗ 获取玩家列表失败")
                continue
            
            players = result.get('players', [])
            if not players:
                print("没有在线玩家")
                continue
            
            print("\n快速开始模式：您执黑棋（先手），对方执白棋（后手）")
            print("请输入对手的玩家ID:")
            player2_id = input("玩家ID: ").strip()
            
            if player2_id == client.player_id:
                print("✗ 不能和自己对战")
                continue
            
            valid = False
            for p in players:
                if p.get('id') == player2_id:
                    valid = True
                    if p.get('status') != 'idle':
                        print("✗ 该玩家正忙")
                        valid = False
                    break
            
            if valid:
                success, result = client.quick_start(player2_id)
                if success and result.get('success'):
                    print(f"✓ {result.get('message')}")
                    print(f"  房间ID: {result.get('room_id')}")
                else:
                    print(f"✗ 快速开始失败: {result.get('message', '未知错误')}")
        
        else:
            print("✗ 无效的选项，请重新选择")
        
        input("\n按回车键继续...")


if __name__ == '__main__':
    main()
