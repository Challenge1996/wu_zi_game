#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
五子棋游戏客户端 - 支持多玩家匹配对战
命令行界面，连接到服务端进行游戏
"""

import requests
import json
import time
import threading

SERVER_URL = "http://localhost:5001"


class WuziqiClient:
    def __init__(self, server_url=SERVER_URL):
        self.server_url = server_url
        self.player_id = None
        self.player_name = None
        self.current_room_id = None
        self.heartbeat_thread = None
        self.running = False

    def _request(self, method, endpoint, data=None, params=None):
        """发送HTTP请求到服务端"""
        url = f"{self.server_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, params=params, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, timeout=10)
            else:
                return False, f"不支持的HTTP方法: {method}"
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"请求失败，状态码: {response.status_code}, 响应: {response.text}"
        except requests.exceptions.RequestException as e:
            return False, f"连接错误: {e}"

    def _heartbeat_loop(self):
        """心跳循环"""
        while self.running and self.player_id:
            time.sleep(30)  # 每30秒发送一次心跳
            if self.player_id:
                self._request('POST', '/api/player/heartbeat', {'player_id': self.player_id})

    def start_heartbeat(self):
        """启动心跳"""
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            return
        
        self.running = True
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()

    def stop_heartbeat(self):
        """停止心跳"""
        self.running = False

    # ==================== 玩家相关 ====================

    def check_server_health(self):
        """检查服务端状态"""
        success, result = self._request('GET', '/api/health')
        if success:
            print(f"✓ 服务端状态: {result.get('message', '正常')}")
            return True
        else:
            print(f"✗ 无法连接到服务端: {result}")
            return False

    def register_player(self, name=None):
        """玩家注册"""
        data = {}
        if name:
            data['name'] = name
        
        success, result = self._request('POST', '/api/player/register', data)
        if success and result.get('success'):
            self.player_id = result.get('player_id')
            self.player_name = result.get('name')
            print(f"✓ 注册成功！")
            print(f"  玩家ID: {self.player_id}")
            print(f"  玩家名称: {self.player_name}")
            
            # 启动心跳
            self.start_heartbeat()
            return True
        else:
            print(f"✗ 注册失败: {result.get('message', '未知错误')}")
            return False

    def go_offline(self):
        """玩家下线"""
        if not self.player_id:
            print("✗ 您还未注册")
            return False
        
        success, result = self._request('POST', '/api/player/offline', {'player_id': self.player_id})
        if success and result.get('success'):
            print(f"✓ 已下线")
            self.stop_heartbeat()
            self.player_id = None
            self.current_room_id = None
            return True
        else:
            print(f"✗ 下线失败: {result.get('message', '未知错误')}")
            return False

    def list_online_players(self):
        """获取在线玩家列表"""
        success, result = self._request('GET', '/api/player/list')
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
                
                is_self = p.get('id') == self.player_id
                name_display = p.get('name', '未知') + (' (我)' if is_self else '')
                print(f"{p.get('id'):<40} {name_display:<15} {status_display:<10}")
            
            print("-" * 60)
            return players
        else:
            print(f"✗ 获取玩家列表失败: {result.get('message', '未知错误')}")
            return []

    # ==================== 挑战相关 ====================

    def send_challenge(self, challenged_id):
        """发起挑战"""
        if not self.player_id:
            print("✗ 请先注册玩家")
            return False
        
        data = {
            'challenger_id': self.player_id,
            'challenged_id': challenged_id
        }
        
        success, result = self._request('POST', '/api/challenge/send', data)
        if success and result.get('success'):
            print(f"✓ {result.get('message')}")
            print(f"  挑战ID: {result.get('challenge_id')}")
            return True
        else:
            print(f"✗ 发起挑战失败: {result.get('message', '未知错误')}")
            return False

    def list_my_challenges(self):
        """获取我的挑战列表"""
        if not self.player_id:
            print("✗ 请先注册玩家")
            return []
        
        params = {'player_id': self.player_id}
        success, result = self._request('GET', '/api/challenge/list', params=params)
        
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
            return challenges
        else:
            print(f"✗ 获取挑战列表失败: {result.get('message', '未知错误')}")
            return []

    def accept_challenge(self, challenge_id):
        """接受挑战"""
        if not self.player_id:
            print("✗ 请先注册玩家")
            return None
        
        data = {
            'challenge_id': challenge_id,
            'player_id': self.player_id
        }
        
        success, result = self._request('POST', '/api/challenge/accept', data)
        if success and result.get('success'):
            print(f"✓ {result.get('message')}")
            room_id = result.get('room_id')
            if room_id:
                self.current_room_id = room_id
                print(f"  房间ID: {room_id}")
            return room_id
        else:
            print(f"✗ 接受挑战失败: {result.get('message', '未知错误')}")
            return None

    def decline_challenge(self, challenge_id):
        """拒绝挑战"""
        if not self.player_id:
            print("✗ 请先注册玩家")
            return False
        
        data = {
            'challenge_id': challenge_id,
            'player_id': self.player_id
        }
        
        success, result = self._request('POST', '/api/challenge/decline', data)
        if success and result.get('success'):
            print(f"✓ {result.get('message')}")
            return True
        else:
            print(f"✗ 拒绝挑战失败: {result.get('message', '未知错误')}")
            return False

    # ==================== 房间/游戏相关 ====================

    def get_room_info(self, room_id=None):
        """获取房间信息"""
        room_to_check = room_id or self.current_room_id
        if not room_to_check:
            print("✗ 没有指定房间ID")
            return None
        
        params = {'room_id': room_to_check}
        if self.player_id:
            params['player_id'] = self.player_id
        
        success, result = self._request('GET', '/api/room/info', params=params)
        
        if success and result.get('success'):
            return result.get('room')
        else:
            print(f"✗ 获取房间信息失败: {result.get('message', '未知错误')}")
            return None

    def display_room_info(self, room_info):
        """显示房间信息"""
        if not room_info:
            return
        
        print("\n" + "=" * 60)
        print(f"房间: {room_info.get('name')}")
        print("=" * 60)
        
        print(f"\n房间状态: {self._get_room_status_name(room_info.get('status'))}")
        print(f"黑棋玩家: {room_info.get('player1_name', '未分配')}")
        print(f"白棋玩家: {room_info.get('player2_name', '未分配')}")
        
        # 显示游戏状态
        game_state = room_info.get('game_state', {})
        print(f"\n游戏阶段: {self._get_phase_name(game_state.get('game_phase'))}")
        print(f"游戏时间: {game_state.get('game_time', 0)} 秒")
        print(f"已落子数: {game_state.get('move_count', 0)}")
        
        # 显示玩家信息
        if 'player_color' in game_state:
            color = game_state.get('player_color')
            color_name = "黑棋" if color == 1 else "白棋" if color == 2 else "未分配"
            print(f"您的颜色: {color_name}")
            print(f"轮到您了: {'是' if game_state.get('is_my_turn') else '否'}")
        
        # 显示当前玩家
        current_color = game_state.get('current_player')
        current_color_name = "黑棋" if current_color == 1 else "白棋"
        print(f"当前玩家: {current_color_name}")
        
        # 显示棋盘
        print("\n棋盘:")
        self.print_board(game_state.get('board', []))
        
        # 显示游戏结束状态
        if game_state.get('game_over'):
            winner = game_state.get('winner')
            winner_name = "黑棋" if winner == 1 else "白棋"
            print(f"\n★ 游戏结束！{winner_name}获胜！ ★")
        elif room_info.get('status') == 'playing':
            print("\n游戏进行中...")
        
        print("=" * 60 + "\n")

    def _get_room_status_name(self, status):
        """获取房间状态名称"""
        names = {
            'waiting': '等待中',
            'coin_toss': '抛硬币阶段',
            'playing': '游戏中',
            'finished': '已结束'
        }
        return names.get(status, status)

    def _get_phase_name(self, phase):
        """获取游戏阶段名称"""
        phase_names = {
            'waiting': '等待中',
            'coin_toss': '抛硬币阶段',
            'playing': '游戏进行中'
        }
        return phase_names.get(phase, phase)

    def print_board(self, board):
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
                elif cell == 1:
                    line += "X "
                elif cell == 2:
                    line += "O "
            print(line)

    def make_coin_choice(self, choice, room_id=None):
        """抛硬币阶段进行猜测"""
        room_to_use = room_id or self.current_room_id
        if not room_to_use:
            print("✗ 没有指定房间ID")
            return False
        
        if not self.player_id:
            print("✗ 请先注册玩家")
            return False
        
        data = {
            'player_id': self.player_id,
            'room_id': room_to_use,
            'choice': choice
        }
        
        success, result = self._request('POST', '/api/game/coin_choice', data)
        if success and result.get('success'):
            print(f"✓ {result.get('message')}")
            return True
        else:
            print(f"✗ 猜测失败: {result.get('message', '未知错误')}")
            return False

    def resolve_coin_toss(self, room_id=None):
        """解决抛硬币结果"""
        room_to_use = room_id or self.current_room_id
        if not room_to_use:
            print("✗ 没有指定房间ID")
            return False, None
        
        data = {'room_id': room_to_use}
        success, result = self._request('POST', '/api/game/resolve_coin', data)
        
        if success and result.get('success'):
            print(f"✓ {result.get('message')}")
            print(f"  硬币结果: {result.get('coin_result')}")
            print(f"  获胜玩家ID: {result.get('winner_id')}")
            
            # 检查是否是我猜对了
            is_my_win = result.get('winner_id') == self.player_id
            if is_my_win:
                print("\n恭喜！您猜对了！请选择执子颜色。")
            
            return True, result
        else:
            print(f"✗ 解决抛硬币失败: {result.get('message', '未知错误')}")
            return False, None

    def choose_color(self, color_choice, room_id=None):
        """选择执子颜色"""
        room_to_use = room_id or self.current_room_id
        if not room_to_use:
            print("✗ 没有指定房间ID")
            return False
        
        if not self.player_id:
            print("✗ 请先注册玩家")
            return False
        
        data = {
            'player_id': self.player_id,
            'room_id': room_to_use,
            'color_choice': color_choice
        }
        
        success, result = self._request('POST', '/api/game/choose_color', data)
        if success and result.get('success'):
            print(f"✓ {result.get('message')}")
            return True
        else:
            print(f"✗ 选择颜色失败: {result.get('message', '未知错误')}")
            return False

    def finalize_colors(self, player2_id, room_id=None):
        """确定第二个玩家颜色并开始游戏"""
        room_to_use = room_id or self.current_room_id
        if not room_to_use:
            print("✗ 没有指定房间ID")
            return False
        
        data = {
            'room_id': room_to_use,
            'player2_id': player2_id
        }
        
        success, result = self._request('POST', '/api/game/finalize_colors', data)
        if success and result.get('success'):
            print(f"✓ {result.get('message', '游戏开始！')}")
            return True
        else:
            print(f"✗ 确定颜色失败: {result.get('message', '未知错误')}")
            return False

    def place_piece(self, row, col, room_id=None):
        """落子"""
        room_to_use = room_id or self.current_room_id
        if not room_to_use:
            print("✗ 没有指定房间ID")
            return False
        
        if not self.player_id:
            print("✗ 请先注册玩家")
            return False
        
        data = {
            'player_id': self.player_id,
            'room_id': room_to_use,
            'row': row,
            'col': col
        }
        
        success, result = self._request('POST', '/api/game/place_piece', data)
        if success and result.get('success'):
            print(f"✓ {result.get('message')}")
            return True
        else:
            print(f"✗ 落子失败: {result.get('message', '未知错误')}")
            return False

    def undo_move(self, room_id=None):
        """悔棋"""
        room_to_use = room_id or self.current_room_id
        if not room_to_use:
            print("✗ 没有指定房间ID")
            return False
        
        if not self.player_id:
            print("✗ 请先注册玩家")
            return False
        
        data = {
            'player_id': self.player_id,
            'room_id': room_to_use
        }
        
        success, result = self._request('POST', '/api/game/undo', data)
        if success and result.get('success'):
            print(f"✓ {result.get('message')}")
            return True
        else:
            print(f"✗ 悔棋失败: {result.get('message', '未知错误')}")
            return False

    def reset_game(self, room_id=None):
        """重置游戏"""
        room_to_use = room_id or self.current_room_id
        if not room_to_use:
            print("✗ 没有指定房间ID")
            return False
        
        if not self.player_id:
            print("✗ 请先注册玩家")
            return False
        
        data = {
            'player_id': self.player_id,
            'room_id': room_to_use
        }
        
        success, result = self._request('POST', '/api/game/reset', data)
        if success and result.get('success'):
            print(f"✓ {result.get('message')}")
            return True
        else:
            print(f"✗ 重置失败: {result.get('message', '未知错误')}")
            return False

    def quick_start(self, player2_id):
        """快速开始游戏（跳过抛硬币）"""
        if not self.player_id:
            print("✗ 请先注册玩家")
            return None
        
        data = {
            'player1_id': self.player_id,  # 我执黑棋
            'player2_id': player2_id       # 对方执白棋
        }
        
        success, result = self._request('POST', '/api/game/quick_start', data)
        if success and result.get('success'):
            print(f"✓ {result.get('message')}")
            room_id = result.get('room_id')
            if room_id:
                self.current_room_id = room_id
                print(f"  房间ID: {room_id}")
            return room_id
        else:
            print(f"✗ 快速开始失败: {result.get('message', '未知错误')}")
            return None


# ==================== 主程序 ====================

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
    print("  14. 悔棋")
    print("  15. 重置游戏")
    print("  16. 快速开始（跳过抛硬币）")
    
    print("\n【其他】")
    print("  0. 退出")
    print("=" * 60)


def main():
    client = WuziqiClient()
    
    print("=" * 60)
    print("欢迎来到五子棋游戏！")
    print("=" * 60)
    print("请确保服务端已在运行 (python server.py)")
    print("服务端地址: http://localhost:5000")
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
        
        # 显示当前玩家状态
        if client.player_id:
            print(f"\n当前玩家: {client.player_name} ({client.player_id})")
        if client.current_room_id:
            print(f"当前房间: {client.current_room_id}")
        
        choice = input("\n请选择操作 (0-16): ").strip()
        
        # 系统操作
        if choice == '0':
            if client.player_id:
                client.go_offline()
            client.stop_heartbeat()
            print("感谢使用，再见！")
            break
        
        elif choice == '1':
            client.check_server_health()
        
        elif choice == '2':
            name = input("请输入玩家名称（直接回车使用默认名称）: ").strip()
            client.register_player(name if name else None)
        
        elif choice == '3':
            client.go_offline()
        
        # 玩家匹配
        elif choice == '4':
            client.list_online_players()
        
        elif choice == '5':
            if not client.player_id:
                print("✗ 请先注册玩家（选项2）")
                continue
            
            players = client.list_online_players()
            if not players:
                print("没有在线玩家")
                continue
            
            print("\n请输入要挑战的玩家ID:")
            challenged_id = input("玩家ID: ").strip()
            
            if challenged_id == client.player_id:
                print("✗ 不能挑战自己")
                continue
            
            # 验证玩家是否存在且在线
            valid = False
            for p in players:
                if p.get('id') == challenged_id:
                    valid = True
                    if p.get('status') != 'idle':
                        print("✗ 该玩家正忙，无法接受挑战")
                        valid = False
                    break
            
            if valid:
                client.send_challenge(challenged_id)
        
        elif choice == '6':
            if not client.player_id:
                print("✗ 请先注册玩家（选项2）")
                continue
            client.list_my_challenges()
        
        elif choice == '7':
            if not client.player_id:
                print("✗ 请先注册玩家（选项2）")
                continue
            
            challenges = client.list_my_challenges()
            pending_challenges = [c for c in challenges if c.get('status') == 'pending' and not c.get('is_my_challenge')]
            
            if not pending_challenges:
                print("没有待处理的挑战")
                continue
            
            print("\n请输入要接受的挑战ID:")
            challenge_id = input("挑战ID: ").strip()
            
            client.accept_challenge(challenge_id)
        
        elif choice == '8':
            if not client.player_id:
                print("✗ 请先注册玩家（选项2）")
                continue
            
            challenges = client.list_my_challenges()
            pending_challenges = [c for c in challenges if c.get('status') == 'pending' and not c.get('is_my_challenge')]
            
            if not pending_challenges:
                print("没有待处理的挑战")
                continue
            
            print("\n请输入要拒绝的挑战ID:")
            challenge_id = input("挑战ID: ").strip()
            
            client.decline_challenge(challenge_id)
        
        # 游戏操作
        elif choice == '9':
            if not client.current_room_id:
                print("✗ 您当前没有加入任何房间")
                continue
            
            room_info = client.get_room_info()
            if room_info:
                client.display_room_info(room_info)
        
        elif choice == '10':
            if not client.current_room_id:
                print("✗ 您当前没有加入任何房间")
                continue
            
            print("请选择硬币猜测：")
            print("0. 正面")
            print("1. 反面")
            coin_choice = input("请输入选项 (0/1): ").strip()
            
            if coin_choice in ['0', '1']:
                client.make_coin_choice(int(coin_choice))
            else:
                print("✗ 无效的选项")
        
        elif choice == '11':
            if not client.current_room_id:
                print("✗ 您当前没有加入任何房间")
                continue
            
            client.resolve_coin_toss()
        
        elif choice == '12':
            if not client.current_room_id:
                print("✗ 您当前没有加入任何房间")
                continue
            
            print("请选择执子颜色：")
            print("1. 黑棋（先手）")
            print("2. 白棋（后手）")
            color_choice = input("请输入选项 (1/2): ").strip()
            
            if color_choice in ['1', '2']:
                client.choose_color(int(color_choice))
            else:
                print("✗ 无效的选项")
        
        elif choice == '13':
            if not client.current_room_id:
                print("✗ 您当前没有加入任何房间")
                continue
            
            # 先显示房间信息
            room_info = client.get_room_info()
            if room_info:
                client.display_room_info(room_info)
            
            try:
                row = int(input("请输入行号 (0-14): ").strip())
                col = int(input("请输入列号 (0-14): ").strip())
                
                if client.place_piece(row, col):
                    # 显示落子后的状态
                    room_info = client.get_room_info()
                    if room_info:
                        client.display_room_info(room_info)
            except ValueError:
                print("✗ 请输入有效的数字")
        
        elif choice == '14':
            if not client.current_room_id:
                print("✗ 您当前没有加入任何房间")
                continue
            
            if client.undo_move():
                room_info = client.get_room_info()
                if room_info:
                    client.display_room_info(room_info)
        
        elif choice == '15':
            if not client.current_room_id:
                print("✗ 您当前没有加入任何房间")
                continue
            
            confirm = input("确定要重置游戏吗？(y/n): ").strip().lower()
            if confirm == 'y':
                client.reset_game()
                print("游戏已重置")
        
        elif choice == '16':
            if not client.player_id:
                print("✗ 请先注册玩家（选项2）")
                continue
            
            players = client.list_online_players()
            if not players:
                print("没有在线玩家")
                continue
            
            print("\n快速开始模式：您执黑棋（先手），对方执白棋（后手）")
            print("请输入对手的玩家ID:")
            player2_id = input("玩家ID: ").strip()
            
            if player2_id == client.player_id:
                print("✗ 不能和自己对战")
                continue
            
            # 验证玩家是否存在且在线
            valid = False
            for p in players:
                if p.get('id') == player2_id:
                    valid = True
                    if p.get('status') != 'idle':
                        print("✗ 该玩家正忙")
                        valid = False
                    break
            
            if valid:
                client.quick_start(player2_id)
        
        else:
            print("✗ 无效的选项，请重新选择")
        
        # 等待用户按回车继续
        input("\n按回车键继续...")


if __name__ == '__main__':
    main()
