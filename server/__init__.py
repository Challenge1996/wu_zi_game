#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务端模块
"""

from server.app import app, main
from server.routes import register_routes
from server.utils import (
    get_player_info,
    get_room_info,
    cleanup_expired_challenges,
    cleanup_expired_undo_requests,
    get_room_undo_request,
    get_undo_request_info,
    get_room_status_name
)
from server.data_store import players, rooms, challenges, undo_requests

__all__ = [
    'app',
    'main',
    'register_routes',
    'get_player_info',
    'get_room_info',
    'cleanup_expired_challenges',
    'cleanup_expired_undo_requests',
    'get_room_undo_request',
    'get_undo_request_info',
    'get_room_status_name',
    'players',
    'rooms',
    'challenges',
    'undo_requests'
]
