#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务端API路由
"""

from flask import request, jsonify
from constants import (
    CHALLENGE_EXPIRE_SECONDS,
    UNDO_REQUEST_EXPIRE_SECONDS,
    PLAYER_BLACK,
    PLAYER_WHITE,
    PLAYER_STATUS_IDLE,
    PLAYER_STATUS_WAITING,
    PLAYER_STATUS_CHALLENGING,
    PLAYER_STATUS_IN_GAME,
    ROOM_STATUS_WAITING,
    ROOM_STATUS_COIN_TOSS,
    ROOM_STATUS_PLAYING,
    ROOM_STATUS_FINISHED,
    CHALLENGE_STATUS_PENDING,
    CHALLENGE_STATUS_ACCEPTED,
    CHALLENGE_STATUS_DECLINED,
    CHALLENGE_STATUS_EXPIRED,
    UNDO_REQUEST_STATUS_PENDING,
    UNDO_REQUEST_STATUS_ACCEPTED,
    UNDO_REQUEST_STATUS_DECLINED,
    UNDO_REQUEST_STATUS_EXPIRED,
    GAME_PHASE_PLAYING,
    GAME_PHASE_COIN_TOSS,
    GAME_PHASE_FINISHED
)
from util import get_timestamp, generate_id
from game import WuziqiGame
from server.data_store import players, rooms, challenges, undo_requests
from server.utils import (
    get_player_info,
    get_room_info,
    cleanup_expired_challenges,
    cleanup_expired_undo_requests,
    get_room_undo_request,
    get_undo_request_info
)


def register_routes(app):
    """注册所有API路由"""

    @app.route('/api/health', methods=['GET'])
    def health_check():
        """健康检查接口"""
        return jsonify({
            "status": "ok",
            "timestamp": get_timestamp(),
            "message": "服务端运行正常"
        })

    @app.route('/api/player/register', methods=['POST'])
    def register_player():
        """玩家注册接口"""
        data = request.get_json() or {}
        player_name = data.get('name', '').strip()
        
        if not player_name:
            player_name = f'玩家{len(players) + 1}'
        
        player_id = generate_id()
        now = get_timestamp()
        
        players[player_id] = {
            'id': player_id,
            'name': player_name,
            'online': True,
            'status': PLAYER_STATUS_IDLE,
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
        players[player_id]['status'] = PLAYER_STATUS_IDLE
        
        room_id = players[player_id]['current_room']
        if room_id and room_id in rooms:
            room = rooms[room_id]
            if room['status'] in [ROOM_STATUS_PLAYING, ROOM_STATUS_COIN_TOSS]:
                if room['player1'] == player_id:
                    room['winner'] = PLAYER_WHITE
                else:
                    room['winner'] = PLAYER_BLACK
                room['status'] = ROOM_STATUS_FINISHED
                room['finished_at'] = get_timestamp()
                
                other_player_id = room['player2'] if room['player1'] == player_id else room['player1']
                if other_player_id in players:
                    players[other_player_id]['status'] = PLAYER_STATUS_IDLE
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

    @app.route('/api/challenge/send', methods=['POST'])
    def send_challenge():
        """发起挑战"""
        data = request.get_json() or {}
        challenger_id = data.get('challenger_id')
        challenged_id = data.get('challenged_id')
        
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
        
        if challenger['status'] != PLAYER_STATUS_IDLE:
            return jsonify({
                "success": False,
                "message": "您当前状态无法发起挑战"
            }), 400
        
        if not challenged['online']:
            return jsonify({
                "success": False,
                "message": "对方不在线"
            }), 400
        
        if challenged['status'] != PLAYER_STATUS_IDLE:
            return jsonify({
                "success": False,
                "message": "对方正忙，无法接受挑战"
            }), 400
        
        for cid, challenge in challenges.items():
            if challenge['status'] == CHALLENGE_STATUS_PENDING:
                if (challenge['challenger'] == challenger_id and challenge['challenged'] == challenged_id) or \
                   (challenge['challenger'] == challenged_id and challenge['challenged'] == challenger_id):
                    return jsonify({
                        "success": False,
                        "message": "已有未处理的挑战"
                    }), 400
        
        now = get_timestamp()
        challenge_id = generate_id()
        challenges[challenge_id] = {
            'id': challenge_id,
            'challenger': challenger_id,
            'challenged': challenged_id,
            'status': CHALLENGE_STATUS_PENDING,
            'created_at': now,
            'expires_at': now + CHALLENGE_EXPIRE_SECONDS
        }
        
        players[challenger_id]['status'] = PLAYER_STATUS_CHALLENGING
        players[challenged_id]['status'] = PLAYER_STATUS_CHALLENGING
        
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
        
        cleanup_expired_challenges()
        
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
                    'room_id': challenge.get('room_id'),
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
        
        if challenge['status'] != CHALLENGE_STATUS_PENDING:
            return jsonify({
                "success": False,
                "message": "挑战已处理或已过期"
            }), 400
        
        if challenge['challenged'] != player_id:
            return jsonify({
                "success": False,
                "message": "您不是被挑战者"
            }), 400
        
        challenge['status'] = CHALLENGE_STATUS_ACCEPTED
        
        room_id = generate_id()
        challenger_name = players[challenge['challenger']]['name']
        challenged_name = players[player_id]['name']
        
        challenge['room_id'] = room_id
        
        rooms[room_id] = {
            'id': room_id,
            'name': f"{challenger_name} vs {challenged_name}",
            'creator': challenge['challenger'],
            'challenger_id': challenge['challenger'],
            'challenged_id': player_id,
            'player1': None,
            'player2': None,
            'status': ROOM_STATUS_COIN_TOSS,
            'game': WuziqiGame(),
            'created_at': get_timestamp(),
            'started_at': None,
            'finished_at': None,
            'winner': None
        }
        
        game = rooms[room_id]['game']
        
        game.players[PLAYER_BLACK] = challenge['challenger']
        game.players[PLAYER_WHITE] = player_id
        
        game.start_coin_toss()
        
        players[challenge['challenger']]['status'] = PLAYER_STATUS_IN_GAME
        players[challenge['challenger']]['current_room'] = room_id
        players[player_id]['status'] = PLAYER_STATUS_IN_GAME
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
        
        if challenge['status'] != CHALLENGE_STATUS_PENDING:
            return jsonify({
                "success": False,
                "message": "挑战已处理或已过期"
            }), 400
        
        if challenge['challenged'] != player_id:
            return jsonify({
                "success": False,
                "message": "您不是被挑战者"
            }), 400
        
        challenge['status'] = CHALLENGE_STATUS_DECLINED
        
        players[challenge['challenger']]['status'] = PLAYER_STATUS_IDLE
        players[player_id]['status'] = PLAYER_STATUS_IDLE
        
        return jsonify({
            "success": True,
            "message": "已拒绝挑战"
        })

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
        choice = data.get('choice')
        
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
        if room['status'] != ROOM_STATUS_COIN_TOSS:
            return jsonify({
                "success": False,
                "message": "不在抛硬币阶段"
            }), 400
        
        game = room['game']
        result = game.player_make_choice(player_id, choice)
        
        if isinstance(result, tuple):
            success, data = result
            if isinstance(data, dict):
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
        if room['status'] != ROOM_STATUS_COIN_TOSS:
            return jsonify({
                "success": False,
                "message": "不在抛硬币阶段"
            }), 400
        
        game = room['game']
        result = game.resolve_coin_toss()
        
        if isinstance(result, tuple):
            success, data = result
            if success and isinstance(data, dict):
                room['status'] = ROOM_STATUS_PLAYING
                room['started_at'] = get_timestamp()
                room['player1'] = data.get('winner_id')
                room['player2'] = data.get('loser_id')
                
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
        color_choice = data.get('color_choice')
        
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
            if color_choice == PLAYER_BLACK:
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
                room['status'] = ROOM_STATUS_PLAYING
                room['started_at'] = get_timestamp()
                if isinstance(data, dict) and 'players' in data:
                    room['player1'] = data['players'].get(PLAYER_BLACK)
                    room['player2'] = data['players'].get(PLAYER_WHITE)
                
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
        if room['status'] != ROOM_STATUS_PLAYING:
            return jsonify({
                "success": False,
                "message": "游戏未开始"
            }), 400
        
        game = room['game']
        
        player_color = game.get_player_color(player_id)
        if player_color is None:
            return jsonify({
                "success": False,
                "message": "玩家未分配颜色"
            }), 400
        
        success, message = game.place_piece(row, col, player_color)
        
        if success and game.is_game_over():
            room['status'] = ROOM_STATUS_FINISHED
            room['finished_at'] = get_timestamp()
            room['winner'] = game.get_winner()
            
            if room['player1'] in players:
                players[room['player1']]['status'] = PLAYER_STATUS_IDLE
                players[room['player1']]['current_room'] = None
            if room['player2'] in players:
                players[room['player2']]['status'] = PLAYER_STATUS_IDLE
                players[room['player2']]['current_room'] = None
        
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
        if room['status'] != ROOM_STATUS_PLAYING:
            return jsonify({
                "success": False,
                "message": "游戏未开始"
            }), 400
        
        game = room['game']
        
        was_finished = game.is_game_over()
        
        success, message = game.undo_move()
        
        if success and was_finished:
            room['status'] = ROOM_STATUS_PLAYING
            room['finished_at'] = None
            room['winner'] = None
        
        state = game.get_game_state(player_id)
        
        return jsonify({
            "success": success,
            "message": message,
            "game_state": state
        })

    @app.route('/api/game/undo/request', methods=['POST'])
    def request_undo_api():
        """发起悔棋请求"""
        cleanup_expired_undo_requests()
        
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
        if room['status'] != ROOM_STATUS_PLAYING:
            return jsonify({
                "success": False,
                "message": "游戏未开始"
            }), 400
        
        game = room['game']
        move_history = game.move_history
        
        if len(move_history) == 0:
            return jsonify({
                "success": False,
                "message": "没有可悔的棋"
            }), 400
        
        existing_request = get_room_undo_request(room_id)
        if existing_request:
            if existing_request['requester'] == player_id:
                return jsonify({
                    "success": False,
                    "message": "您已发起悔棋请求，请等待对手回应"
                }), 400
            else:
                return jsonify({
                    "success": False,
                    "message": "对手已发起悔棋请求，请先处理"
                }), 400
        
        player1 = room.get('player1')
        player2 = room.get('player2')
        
        if player_id not in [player1, player2]:
            return jsonify({
                "success": False,
                "message": "您不是该房间的玩家"
            }), 400
        
        opponent_id = player2 if player_id == player1 else player1
        
        now = get_timestamp()
        undo_request_id = generate_id()
        
        undo_requests[undo_request_id] = {
            'id': undo_request_id,
            'room_id': room_id,
            'requester': player_id,
            'requested': opponent_id,
            'status': UNDO_REQUEST_STATUS_PENDING,
            'created_at': now,
            'expires_at': now + UNDO_REQUEST_EXPIRE_SECONDS
        }
        
        requester_name = players[player_id]['name'] if player_id in players else '未知玩家'
        
        return jsonify({
            "success": True,
            "undo_request_id": undo_request_id,
            "opponent_id": opponent_id,
            "message": f"已向对手发起悔棋请求，等待 {requester_name} 同意"
        })

    @app.route('/api/game/undo/respond', methods=['POST'])
    def respond_undo_api():
        """响应悔棋请求（同意/拒绝）"""
        cleanup_expired_undo_requests()
        
        data = request.get_json() or {}
        player_id = data.get('player_id')
        room_id = data.get('room_id')
        accept = data.get('accept', False)
        
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
        
        undo_request = get_room_undo_request(room_id)
        
        if not undo_request:
            return jsonify({
                "success": False,
                "message": "没有待处理的悔棋请求"
            }), 400
        
        if undo_request['requested'] != player_id:
            return jsonify({
                "success": False,
                "message": "您不是被请求的玩家"
            }), 400
        
        if accept:
            undo_request['status'] = UNDO_REQUEST_STATUS_ACCEPTED
            
            game = room['game']
            was_finished = game.is_game_over()
            
            success, message = game.undo_move()
            
            if success and was_finished:
                room['status'] = ROOM_STATUS_PLAYING
                room['finished_at'] = None
                room['winner'] = None
            
            state = game.get_game_state(player_id)
            
            return jsonify({
                "success": success,
                "message": message if success else "悔棋失败",
                "undo_accepted": True,
                "game_state": state
            })
        else:
            undo_request['status'] = UNDO_REQUEST_STATUS_DECLINED
            
            game = room['game']
            state = game.get_game_state(player_id)
            
            return jsonify({
                "success": True,
                "message": "已拒绝悔棋请求",
                "undo_accepted": False,
                "game_state": state
            })

    @app.route('/api/game/undo/status', methods=['GET'])
    def get_undo_status_api():
        """获取悔棋请求状态"""
        cleanup_expired_undo_requests()
        
        room_id = request.args.get('room_id')
        player_id = request.args.get('player_id')
        
        if not room_id:
            return jsonify({
                "success": False,
                "message": "缺少必要参数"
            }), 400
        
        if room_id not in rooms:
            return jsonify({
                "success": False,
                "message": "房间不存在"
            }), 400
        
        undo_request = get_room_undo_request(room_id)
        
        if undo_request:
            return jsonify({
                "success": True,
                "has_pending_request": True,
                "undo_request": get_undo_request_info(undo_request, player_id)
            })
        else:
            return jsonify({
                "success": True,
                "has_pending_request": False,
                "undo_request": None
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
        
        game = room['game']
        game.clear_board()
        
        game.start_coin_toss()
        room['status'] = ROOM_STATUS_COIN_TOSS
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
        player1_id = data.get('player1_id')
        player2_id = data.get('player2_id')
        
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
        
        if players[player1_id]['status'] != PLAYER_STATUS_IDLE or players[player2_id]['status'] != PLAYER_STATUS_IDLE:
            return jsonify({
                "success": False,
                "message": "玩家状态不允许开始游戏"
            }), 400
        
        room_id = generate_id()
        player1_name = players[player1_id]['name']
        player2_name = players[player2_id]['name']
        
        game = WuziqiGame()
        game.players[PLAYER_BLACK] = player1_id
        game.players[PLAYER_WHITE] = player2_id
        game.start_game()
        
        rooms[room_id] = {
            'id': room_id,
            'name': f"{player1_name} vs {player2_name}",
            'creator': player1_id,
            'player1': player1_id,
            'player2': player2_id,
            'status': ROOM_STATUS_PLAYING,
            'game': game,
            'created_at': get_timestamp(),
            'started_at': get_timestamp(),
            'finished_at': None,
            'winner': None
        }
        
        players[player1_id]['status'] = PLAYER_STATUS_IN_GAME
        players[player1_id]['current_room'] = room_id
        players[player2_id]['status'] = PLAYER_STATUS_IN_GAME
        players[player2_id]['current_room'] = room_id
        
        return jsonify({
            "success": True,
            "room_id": room_id,
            "message": f"游戏开始！{player1_name}执黑棋，{player2_name}执白棋",
            "game_state": game.get_game_state()
        })
