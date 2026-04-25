#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
五子棋游戏服务端
基于Flask的HTTP服务，支持多玩家匹配和对战
"""

from flask import Flask
from flask_cors import CORS
from constants import SERVER_PORT
from server.routes import register_routes

app = Flask(__name__)
CORS(app)

register_routes(app)


def main():
    print("=" * 60)
    print("五子棋游戏服务端 - 支持多玩家匹配对战")
    print("=" * 60)
    print(f"服务端将在 http://localhost:{SERVER_PORT} 运行")
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
    print("  POST /api/game/undo            直接悔棋（用于测试，不推荐生产使用）")
    print("  POST /api/game/undo/request    发起悔棋请求")
    print("  POST /api/game/undo/respond    响应悔棋请求（同意/拒绝）")
    print("  GET  /api/game/undo/status     获取悔棋请求状态")
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
    
    app.run(host='0.0.0.0', port=SERVER_PORT, debug=True, threaded=True)


if __name__ == '__main__':
    main()
