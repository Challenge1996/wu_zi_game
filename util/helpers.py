#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用工具函数
"""

import time
import uuid
from datetime import datetime


def get_timestamp():
    """获取当前时间戳"""
    return int(time.time())


def generate_id():
    """生成唯一ID"""
    return str(uuid.uuid4())


def format_time(seconds):
    """将秒数格式化为 HH:MM:SS 格式"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def get_current_time_str():
    """获取当前时间字符串"""
    return datetime.now().strftime("%H:%M:%S")


def get_player_color_name(color):
    """获取玩家颜色名称"""
    if color == 1:
        return "黑棋"
    elif color == 2:
        return "白棋"
    return "未知"


def get_coin_result_name(result):
    """获取硬币结果名称"""
    if result == 0:
        return "正面"
    elif result == 1:
        return "反面"
    return "未知"
