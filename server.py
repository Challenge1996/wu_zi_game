#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
五子棋游戏服务端
基于Flask的HTTP服务，支持多玩家匹配和对战
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from wuziqi import WuziqiGame
import uuid
import time
from datetime import datetime

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# ==================== 数据结构 ====================

# 玩家管理
# player_id -> {
#     'id': player_id,
#     'name': player_name,
#     'online': bool,           # 在线状态
#     'status': 'idle'|'waiting'|'challenging'|'in_game',  # 玩家状态
#     'current_room': room_id or None,  # 当前所在房间
#     'last_heartbeat': timestamp,
#     'registered_at': timestamp
# }
players = {}

# 房间管理
# room_id -> {
#     'id': room_id,
#     'name': room_name,
#     'creator': player_id,      # 房间创建者
#     'player1': player_id,      # 黑棋玩家
#     'player2': player_id,      # 白棋玩家
#     'status': 'waiting'|'coin_toss'|'playing'|'finished',  # 房间状态
#     'game': WuziqiGame instance,  # 游戏实例
#     'created_at': timestamp,
#     'started_at': timestamp or None,
#     'finished_at': timestamp or None,
#     'winner': None or 1 or 2
# }
rooms = {}

# 挑战管理
# challenge_id -> {
#     'id': challenge_id,
#     'challenger': player_id,   # 挑战者
#     'challenged': player_id,   # 被挑战者
#     'status': 'pending'|'accepted'|'declined'|'expired',
#     'created_at': timestamp,
#     'expires_at': timestamp
# }
challenges = {}

# 挑战过期时间（秒）
CHALLENGE_EXPIRE_SECONDS = 60

# ==================== 工具函数 ====================

def get_timestamp():
    """获取当前时间戳"""
    return int(time.time())

def generate_id():
    """生成唯一ID"""
    return str(uuid.uuid4())

def get_player_info(player_id):
    """获取玩家公开信息"""
    if player_id not in players:
        return None
    player = players[player_id]
    return {
        'id': player['id'],
        'name': player['name'],
        'online': player['online'],
        'status': player['status'],
        'current_room': player['current_room']
    }

def get_room_info(room_id, player_id=None):
    """获取房间信息"""
    if room_id not in rooms:
        return None
    room = rooms[room_id]
    game = room['game']
    game_state = game.get_game_state(player_id)
    
    return {
        'id': room['id'],
        'name': room['name'],
        'creator': room['creator'],
        'player1': room['player1'],
        'player2': room['player2'],
        'player1_name': players[room['player1']]['name'] if room['player1'] in players else None,
        'player2_name': players[room['player2']]['name'] if room['player2'] in players else None,
        'status': room['status'],
        'game_state': game_state,
        'created_at': room['created_at'],
        'started_at': room['started_at'],
        'finished_at': room['finished_at'],
        'winner': room['winner']
    }

def cleanup_expired_challenges():
    """清理过期的挑战"""
    now = get_timestamp()
    expired = []
    for cid, challenge in challenges.items():
        if challenge['status'] == 'pending' and now > challenge['expires_at']:
            challenge['status'] = 'expired'
            expired.append(cid)
    return expired

# ==================== API 接口 ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        "status": "ok",
        "timestamp": get_timestamp(),
        "message": "服务端运行正常"
    })

# ==================== 玩家相关接口 ====================

@app.route('/api/player/register', methods=['POST'])
def register_player():
    """玩家注册接口"""
    data = request.get_json() or {}
    player_name = data.get('name', '').strip()
    
    if not player_name:
        player_name = f'玩家{len(players) + 1}'
    
    # 生成唯一玩家ID
    player_id = generate_id()
    now = get_timestamp()
    
    players[player_id] = {
        'id': player_id,
        'name': player_name,
        'online': True,
        'status': 'idle',
        'current_room': None,
        'last_heartbeat': now,
        'registered_at': now
    }
    
    return jsonify({
        "success": True,
        "player_id": player_id,
        "name": player_name,
        "message": f"玩家 {player_name} 注册成功！"
    })

@app.route('/api/player/heartbeat', methods=['POST'])
def player_heartbeat():
    """玩家心跳接口（维持在线状态）"""
    data = request.get_json() or {}
    player_id = data.get('player_id')
    
    if not player_id or player_id not in players:
        return jsonify({
            "success": False,
            "message": "玩家不存在"
        }), 400
    
    players[player_id]['online'] = True
    players[player_id]['last_heartbeat'] = get_timestamp()
    
    return jsonify({
        "success": True,
        "message": "心跳更新成功"
    })

@app.route('/api/player/offline', methods=['POST'])
def player_offline():
    """玩家下线接口"""
    data = request.get_json() or {}
    player_id = data.get('player_id')
    
    if not player_id or player_id not in players:
        return jsonify({
            "success": False,
            "message": "玩家不存在"
        }), 400
    
    players[player_id]['online'] = False
    players[player_id]['status'] = 'idle'
    
    # 如果玩家在房间中，需要处理
    room_id = players[player_id]['current_room']
    if room_id and room_id in rooms:
        room = rooms[room_id]
        if room['status'] in ['playing', 'coin_toss']:
            # 游戏进行中，对方获胜
            if room['player1'] == player_id:
                room['winner'] = 2
            else:
                room['winner'] = 1
            room['status'] = 'finished'
            room['finished_at'] = get_timestamp()
            
            # 通知另一个玩家
            other_player_id = room['player2'] if room['player1'] == player_id else room['player1']
            if other_player_id in players:
                players[other_player_id]['status'] = 'idle'
                players[other_player_id]['current_room'] = None
    
    players[player_id]['current_room'] = None
    
    return jsonify({
        "success": True,
        "message": "玩家已下线"
    })

@app.route('/api/player/list', methods=['GET'])
def list_players():
    """获取在线玩家列表"""
    online_players = []
    for pid, player in players.items():
        if player['online']:
            online_players.append(get_player_info(pid))
    
    return jsonify({
        "success": True,
        "players": online_players,
        "count": len(online_players)
    })

@app.route('/api/player/info', methods=['GET'])
def get_player_info_api():
    """获取玩家详细信息"""
    player_id = request.args.get('player_id')
    
    if not player_id or player_id not in players:
        return jsonify({
            "success": False,
            "message": "玩家不存在"
        }), 400
    
    return jsonify({
        "success": True,
        "player": get_player_info(player_id)
    })

# ==================== 挑战相关接口 ====================

@app.route('/api/challenge/send', methods=['POST'])
def send_challenge():
    """发起挑战"""
    data = request.get_json() or {}
    challenger_id = data.get('challenger_id')
    challenged_id = data.get('challenged_id')
    
    # 验证参数
    if not challenger_id or not challenged_id:
        return jsonify({
            "success": False,
            "message": "缺少必要参数"
        }), 400
    
    if challenger_id == challenged_id:
        return jsonify({
            "success": False,
            "message": "不能挑战自己"
        }), 400
    
    if challenger_id not in players or challenged_id not in players:
        return jsonify({
            "success": False,
            "message": "玩家不存在"
        }), 400
    
    challenger = players[challenger_id]
    challenged = players[challenged_id]
    
    # 检查挑战者状态
    if challenger['status'] != 'idle':
        return jsonify({
            "success": False,
            "message": "您当前状态无法发起挑战"
        }), 400
    
    # 检查被挑战者状态
    if not challenged['online']:
        return jsonify({
            "success": False,
            "message": "对方不在线"
        }), 400
    
    if challenged['status'] != 'idle':
        return jsonify({
            "success": False,
            "message": "对方正忙，无法接受挑战"
        }), 400
    
    # 检查是否已有未处理的挑战
    for cid, challenge in challenges.items():
        if challenge['status'] == 'pending':
            if (challenge['challenger'] == challenger_id and challenge['challenged'] == challenged_id) or \
               (challenge['challenger'] == challenged_id and challenge['challenged'] == challenger_id):
                return jsonify({
                    "success": False,
                    "message": "已有未处理的挑战"
                }), 400
    
    # 创建挑战
    now = get_timestamp()
    challenge_id = generate_id()
    challenges[challenge_id] = {
        'id': challenge_id,
        'challenger': challenger_id,
        'challenged': challenged_id,
        'status': 'pending',
        'created_at': now,
        'expires_at': now + CHALLENGE_EXPIRE_SECONDS
    }
    
    # 更新玩家状态
    players[challenger_id]['status'] = 'challenging'
    players[challenged_id]['status'] = 'challenging'
    
    return jsonify({
        "success": True,
        "challenge_id": challenge_id,
        "message": f"已向 {challenged['name']} 发起挑战！"
    })

@app.route('/api/challenge/list', methods=['GET'])
def list_challenges():
    """获取玩家的挑战列表"""
    player_id = request.args.get('player_id')
    
    if not player_id or player_id not in players:
        return jsonify({
            "success": False,
            "message": "玩家不存在"
        }), 400
    
    # 清理过期挑战
    cleanup_expired_challenges()
    
    # 获取该玩家相关的挑战
    player_challenges = []
    for cid, challenge in challenges.items():
        if challenge['challenger'] == player_id or challenge['challenged'] == player_id:
            player_challenges.append({
                'id': challenge['id'],
                'challenger': challenge['challenger'],
                'challenger_name': players[challenge['challenger']]['name'] if challenge['challenger'] in players else None,
                'challenged': challenge['challenged'],
                'challenged_name': players[challenge['challenged']]['name'] if challenge['challenged'] in players else None,
                'status': challenge['status'],
                'created_at': challenge['created_at'],
                'expires_at': challenge['expires_at'],
                'is_my_challenge': challenge['challenger'] == player_id
            })
    
    return jsonify({
        "success": True,
        "challenges": player_challenges,
        "count": len(player_challenges)
    })

@app.route('/api/challenge/accept', methods=['POST'])
def accept_challenge():
    """接受挑战"""
    data = request.get_json() or {}
    challenge_id = data.get('challenge_id')
    player_id = data.get('player_id')
    
    if not challenge_id or not player_id:
        return jsonify({
            "success": False,
            "message": "缺少必要参数"
        }), 400
    
    if challenge_id not in challenges:
        return jsonify({
            "success": False,
            "message": "挑战不存在"
        }), 400
    
    challenge = challenges[challenge_id]
    
    if challenge['status'] != 'pending':
        return jsonify({
            "success": False,
            "message": "挑战已处理或已过期"
        }), 400
    
    if challenge['challenged'] != player_id:
        return jsonify({
            "success": False,
            "message": "您不是被挑战者"
        }), 400
    
    # 标记挑战为已接受
    challenge['status'] = 'accepted'
    
    # 创建房间
    room_id = generate_id()
    challenger_name = players[challenge['challenger']]['name']
    challenged_name = players[player_id]['name']
    
    rooms[room_id] = {
        'id': room_id,
        'name': f"{challenger_name} vs {challenged_name}",
        'creator': challenge['challenger'],
        'player1': None,  # 抛硬币后确定
        'player2': None,
        'status': 'coin_toss',
        'game': WuziqiGame(),
        'created_at': get_timestamp(),
        'started_at': None,
        'finished_at': None,
        'winner': None
    }
    
    # 初始化游戏的抛硬币阶段
    game = rooms[room_id]['game']
    game.start_coin_toss()
    
    # 更新玩家状态
    players[challenge['challenger']]['status'] = 'in_game'
    players[challenge['challenger']]['current_room'] = room_id
    players[player_id]['status'] = 'in_game'
    players[player_id]['current_room'] = room_id
    
    return jsonify({
        "success": True,
        "room_id": room_id,
        "message": "挑战已接受，房间已创建！请进入抛硬币阶段决定先手。"
    })

@app.route('/api/challenge/decline', methods=['POST'])
def decline_challenge():
    """拒绝挑战"""
    data = request.get_json() or {}
    challenge_id = data.get('challenge_id')
    player_id = data.get('player_id')
    
    if not challenge_id or not player_id:
        return jsonify({
            "success": False,
            "message": "缺少必要参数"
        }), 400
    
    if challenge_id not in challenges:
        return jsonify({
            "success": False,
            "message": "挑战不存在"
        }), 400
    
    challenge = challenges[challenge_id]
    
    if challenge['status'] != 'pending':
        return jsonify({
            "success": False,
            "message": "挑战已处理或已过期"
        }), 400
    
    if challenge['challenged'] != player_id:
        return jsonify({
            "success": False,
            "message": "您不是被挑战者"
        }), 400
    
    # 标记挑战为已拒绝
    challenge['status'] = 'declined'
    
    # 恢复玩家状态
    players[challenge['challenger']]['status'] = 'idle'
    players[player_id]['status'] = 'idle'
    
    return jsonify({
        "success": True,
        "message": "已拒绝挑战"
    })

# ==================== 房间/游戏相关接口 ====================

@app.route('/api/room/info', methods=['GET'])
def get_room_info_api():
    """获取房间信息"""
    room_id = request.args.get('room_id')
    player_id = request.args.get('player_id')
    
    if not room_id or room_id not in rooms:
        return jsonify({
            "success": False,
            "message": "房间不存在"
        }), 400
    
    return jsonify({
        "success": True,
        "room": get_room_info(room_id, player_id)
    })

@app.route('/api/room/list', methods=['GET'])
def list_rooms():
    """获取房间列表"""
    room_list = []
    for rid, room in rooms.items():
        room_list.append(get_room_info(rid))
    
    return jsonify({
        "success": True,
        "rooms": room_list,
        "count": len(room_list)
    })

@app.route('/api/game/coin_choice', methods=['POST'])
def make_coin_choice():
    """抛硬币阶段进行猜测"""
    data = request.get_json() or {}
    player_id = data.get('player_id')
    room_id = data.get('room_id')
    choice = data.get('choice')  # 0: 正面, 1: 反面
    
    if not player_id or not room_id:
        return jsonify({
            "success": False,
            "message": "缺少必要参数"
        }), 400
    
    if room_id not in rooms:
        return jsonify({
            "success": False,
            "message": "房间不存在"
        }), 400
    
    room = rooms[room_id]
    if room['status'] != 'coin_toss':
        return jsonify({
            "success": False,
            "message": "不在抛硬币阶段"
        }), 400
    
    game = room['game']
    result = game.player_make_choice(player_id, choice)
    
    # 处理返回值
    if isinstance(result, tuple):
        success, data = result
        if isinstance(data, dict):
            # 自动分配的情况
            return jsonify({
                "success": success,
                "auto_assigned": data.get('auto_assigned', False),
                "player_choice": data.get('player_choice'),
                "other_player_choice": data.get('other_player_choice'),
                "other_player_id": data.get('other_player_id'),
                "message": data.get('message')
            })
        else:
            return jsonify({
                "success": success,
                "message": data
            })
    else:
        # 不应该到达这里
        return jsonify({
            "success": False,
            "message": "处理选择时发生错误"
        })

@app.route('/api/game/resolve_coin', methods=['POST'])
def resolve_coin_toss_api():
    """解决抛硬币结果"""
    data = request.get_json() or {}
    room_id = data.get('room_id')
    
    if not room_id or room_id not in rooms:
        return jsonify({
            "success": False,
            "message": "房间不存在"
        }), 400
    
    room = rooms[room_id]
    if room['status'] != 'coin_toss':
        return jsonify({
            "success": False,
            "message": "不在抛硬币阶段"
        }), 400
    
    game = room['game']
    result = game.resolve_coin_toss()
    
    if isinstance(result, tuple):
        success, data = result
        if success and isinstance(data, dict):
            return jsonify({
                "success": True,
                **data
            })
        return jsonify({
            "success": False,
            "message": data
        })
    
    return jsonify({
        "success": False,
        "message": "处理结果时发生错误"
    })

@app.route('/api/game/choose_color', methods=['POST'])
def choose_color_api():
    """选择执子颜色"""
    data = request.get_json() or {}
    player_id = data.get('player_id')
    room_id = data.get('room_id')
    color_choice = data.get('color_choice')  # 1: 黑棋, 2: 白棋
    
    if not player_id or not room_id:
        return jsonify({
            "success": False,
            "message": "缺少必要参数"
        }), 400
    
    if room_id not in rooms:
        return jsonify({
            "success": False,
            "message": "房间不存在"
        }), 400
    
    room = rooms[room_id]
    game = room['game']
    
    success, message = game.player_choose_color(player_id, color_choice)
    
    if success:
        # 记录玩家颜色
        if color_choice == 1:
            room['player1'] = player_id
        else:
            room['player2'] = player_id
    
    return jsonify({
        "success": success,
        "message": message
    })

@app.route('/api/game/finalize_colors', methods=['POST'])
def finalize_colors_api():
    """确定第二个玩家颜色并开始游戏"""
    data = request.get_json() or {}
    room_id = data.get('room_id')
    player2_id = data.get('player2_id')
    
    if not room_id or not player2_id:
        return jsonify({
            "success": False,
            "message": "缺少必要参数"
        }), 400
    
    if room_id not in rooms:
        return jsonify({
            "success": False,
            "message": "房间不存在"
        }), 400
    
    room = rooms[room_id]
    game = room['game']
    
    result = game.finalize_player_colors(player2_id)
    
    if isinstance(result, tuple):
        success, data = result
        if success:
            # 更新房间状态
            room['status'] = 'playing'
            room['started_at'] = get_timestamp()
            # 确保两个玩家都已记录
            if isinstance(data, dict) and 'players' in data:
                room['player1'] = data['players'].get(1)
                room['player2'] = data['players'].get(2)
            
            return jsonify({
                "success": True,
                **(data if isinstance(data, dict) else {})
            })
        return jsonify({
            "success": False,
            "message": data
        })
    
    return jsonify({
        "success": False,
        "message": "处理结果时发生错误"
    })

@app.route('/api/game/place_piece', methods=['POST'])
def place_piece_api():
    """落子接口"""
    data = request.get_json() or {}
    player_id = data.get('player_id')
    room_id = data.get('room_id')
    row = data.get('row')
    col = data.get('col')
    
    if not player_id or not room_id:
        return jsonify({
            "success": False,
            "message": "缺少必要参数"
        }), 400
    
    if row is None or col is None:
        return jsonify({
            "success": False,
            "message": "缺少row或col参数"
        }), 400
    
    if room_id not in rooms:
        return jsonify({
            "success": False,
            "message": "房间不存在"
        }), 400
    
    room = rooms[room_id]
    if room['status'] != 'playing':
        return jsonify({
            "success": False,
            "message": "游戏未开始"
        }), 400
    
    game = room['game']
    
    # 获取玩家的颜色
    player_color = game.get_player_color(player_id)
    if player_color is None:
        return jsonify({
            "success": False,
            "message": "玩家未分配颜色"
        }), 400
    
    success, message = game.place_piece(row, col, player_color)
    
    # 检查游戏是否结束
    if success and game.is_game_over():
        room['status'] = 'finished'
        room['finished_at'] = get_timestamp()
        room['winner'] = game.get_winner()
        
        # 恢复玩家状态
        if room['player1'] in players:
            players[room['player1']]['status'] = 'idle'
            players[room['player1']]['current_room'] = None
        if room['player2'] in players:
            players[room['player2']]['status'] = 'idle'
            players[room['player2']]['current_room'] = None
    
    # 获取最新的游戏状态
    state = game.get_game_state(player_id)
    
    return jsonify({
        "success": success,
        "message": message,
        "game_state": state
    })

@app.route('/api/game/undo', methods=['POST'])
def undo_move_api():
    """悔棋接口"""
    data = request.get_json() or {}
    player_id = data.get('player_id')
    room_id = data.get('room_id')
    
    if not player_id or not room_id:
        return jsonify({
            "success": False,
            "message": "缺少必要参数"
        }), 400
    
    if room_id not in rooms:
        return jsonify({
            "success": False,
            "message": "房间不存在"
        }), 400
    
    room = rooms[room_id]
    if room['status'] != 'playing':
        return jsonify({
            "success": False,
            "message": "游戏未开始"
        }), 400
    
    game = room['game']
    
    # 如果游戏已结束，悔棋后恢复状态
    was_finished = game.is_game_over()
    
    success, message = game.undo_move()
    
    if success and was_finished:
        room['status'] = 'playing'
        room['finished_at'] = None
        room['winner'] = None
    
    # 获取最新的游戏状态
    state = game.get_game_state(player_id)
    
    return jsonify({
        "success": success,
        "message": message,
        "game_state": state
    })

@app.route('/api/game/reset', methods=['POST'])
def reset_game_api():
    """重置游戏接口"""
    data = request.get_json() or {}
    player_id = data.get('player_id')
    room_id = data.get('room_id')
    
    if not player_id or not room_id:
        return jsonify({
            "success": False,
            "message": "缺少必要参数"
        }), 400
    
    if room_id not in rooms:
        return jsonify({
            "success": False,
            "message": "房间不存在"
        }), 400
    
    room = rooms[room_id]
    
    # 重置游戏
    game = room['game']
    game.clear_board()
    
    # 重新开始抛硬币阶段
    game.start_coin_toss()
    room['status'] = 'coin_toss'
    room['started_at'] = None
    room['finished_at'] = None
    room['winner'] = None
    room['player1'] = None
    room['player2'] = None
    
    return jsonify({
        "success": True,
        "message": "游戏已重置",
        "game_state": game.get_game_state(player_id)
    })

@app.route('/api/game/quick_start', methods=['POST'])
def quick_start_api():
    """快速开始游戏（跳过抛硬币，直接分配颜色）"""
    data = request.get_json() or {}
    player1_id = data.get('player1_id')  # 黑棋
    player2_id = data.get('player2_id')  # 白棋
    
    if not player1_id or not player2_id:
        return jsonify({
            "success": False,
            "message": "缺少必要参数"
        }), 400
    
    if player1_id == player2_id:
        return jsonify({
            "success": False,
            "message": "两个玩家不能是同一个人"
        }), 400
    
    if player1_id not in players or player2_id not in players:
        return jsonify({
            "success": False,
            "message": "玩家不存在"
        }), 400
    
    # 检查玩家状态
    if players[player1_id]['status'] != 'idle' or players[player2_id]['status'] != 'idle':
        return jsonify({
            "success": False,
            "message": "玩家状态不允许开始游戏"
        }), 400
    
    # 创建房间
    room_id = generate_id()
    player1_name = players[player1_id]['name']
    player2_name = players[player2_id]['name']
    
    game = WuziqiGame()
    # 直接分配颜色并开始游戏
    game.players[1] = player1_id
    game.players[2] = player2_id
    game.start_game()
    
    rooms[room_id] = {
        'id': room_id,
        'name': f"{player1_name} vs {player2_name}",
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
    
    # 更新玩家状态
    players[player1_id]['status'] = 'in_game'
    players[player1_id]['current_room'] = room_id
    players[player2_id]['status'] = 'in_game'
    players[player2_id]['current_room'] = room_id
    
    return jsonify({
        "success": True,
        "room_id": room_id,
        "message": f"游戏开始！{player1_name}执黑棋，{player2_name}执白棋",
        "game_state": game.get_game_state()
    })

# ==================== 主函数 ====================

def main():
    print("=" * 60)
    print("五子棋游戏服务端 - 支持多玩家匹配对战")
    print("=" * 60)
    print("服务端将在 http://localhost:5001 运行")
    print("\nAPI接口说明：")
    print("=" * 60)
    print("\n【玩家相关】")
    print("  POST /api/player/register      玩家注册")
    print("  POST /api/player/heartbeat     玩家心跳")
    print("  POST /api/player/offline       玩家下线")
    print("  GET  /api/player/list          获取在线玩家列表")
    print("  GET  /api/player/info          获取玩家信息")
    print("\n【挑战相关】")
    print("  POST /api/challenge/send       发起挑战")
    print("  GET  /api/challenge/list       获取挑战列表")
    print("  POST /api/challenge/accept     接受挑战")
    print("  POST /api/challenge/decline    拒绝挑战")
    print("\n【房间/游戏相关】")
    print("  GET  /api/room/info            获取房间信息")
    print("  GET  /api/room/list            获取房间列表")
    print("  POST /api/game/coin_choice     抛硬币猜测")
    print("  POST /api/game/resolve_coin    解决抛硬币结果")
    print("  POST /api/game/choose_color    选择执子颜色")
    print("  POST /api/game/finalize_colors 确定颜色并开始")
    print("  POST /api/game/place_piece     落子")
    print("  POST /api/game/undo            悔棋")
    print("  POST /api/game/reset           重置游戏")
    print("  POST /api/game/quick_start     快速开始（跳过抛硬币）")
    print("\n【其他】")
    print("  GET  /api/health               健康检查")
    print("=" * 60)
    print("\n对战流程：")
    print("1. 两个玩家分别注册")
    print("2. 玩家A查看在线玩家列表")
    print("3. 玩家A向玩家B发起挑战")
    print("4. 玩家B接受或拒绝挑战")
    print("5. 接受挑战后，进入抛硬币阶段")
    print("6. 两个玩家分别猜测硬币结果")
    print("7. 猜对的玩家选择执黑或执白")
    print("8. 游戏开始，轮流落子")
    print("9. 连成5子获胜，或一方下线判负")
    print("=" * 60)
    
    # 启动Flask服务
    app.run(host='0.0.0.0', port=5001, debug=True, threaded=True)


if __name__ == '__main__':
    main()
