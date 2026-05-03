#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务端模块
使用模块代理确保 server.players 等变量始终指向 server.data_store 中的对应变量
"""

import sys

# 先保存当前模块对象
_original_module = sys.modules[__name__]

# 导入 data_store 模块
import server.data_store as _data_store

# 定义需要代理的数据变量
_DATA_STORE_VARS = ['players', 'rooms', 'challenges', 'undo_requests', 'chat_messages', 'game_records']


class _ModuleProxy:
    """模块代理类，用于拦截对数据变量的访问和赋值"""
    
    def __init__(self, original_module):
        # 使用 object.__setattr__ 避免触发自定义的 __setattr__
        object.__setattr__(self, '_original_module', original_module)
        object.__setattr__(self, '_data_store', _data_store)
    
    def __getattr__(self, name):
        """拦截属性读取"""
        # 对于数据存储变量，从 data_store 获取
        if name in _DATA_STORE_VARS:
            return getattr(self._data_store, name)
        # 对于其他属性，从原始模块获取
        try:
            return getattr(self._original_module, name)
        except AttributeError:
            raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    
    def __setattr__(self, name, value):
        """拦截属性赋值"""
        # 对于私有属性（以 _ 开头），直接设置
        if name.startswith('_'):
            object.__setattr__(self, name, value)
            return
        
        # 对于数据存储变量，拦截赋值操作
        if name in _DATA_STORE_VARS:
            target = getattr(self._data_store, name)
            # 清空原字典
            target.clear()
            # 如果新值是字典，更新内容
            if isinstance(value, dict):
                target.update(value)
            return
        
        # 对于其他属性，设置到原始模块
        setattr(self._original_module, name, value)
    
    def __delattr__(self, name):
        """拦截属性删除"""
        if name in _DATA_STORE_VARS:
            # 不允许删除数据变量
            raise AttributeError(f"cannot delete attribute '{name}'")
        delattr(self._original_module, name)


# 替换 sys.modules 中的模块对象
# 注意：这必须在导入其他依赖 server 模块的子模块之前完成
sys.modules[__name__] = _ModuleProxy(_original_module)

# 现在可以安全地导入其他子模块了
# 注意：这些子模块可能会导入 server 模块，此时 sys.modules['server'] 已经是代理对象

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
    'undo_requests',
    'chat_messages',
    'game_records'
]
