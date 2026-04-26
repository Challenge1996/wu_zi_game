#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络通信模块 - 客户端API
"""

import requests
from constants import SERVER_URL


class NetworkClient:
    """网络客户端类"""
    
    def __init__(self, server_url=None):
        self.server_url = server_url or SERVER_URL
        self.timeout = 10
    
    def _request(self, method, endpoint, data=None, params=None):
        """发送HTTP请求到服务端"""
        url = f"{self.server_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, params=params, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, timeout=self.timeout)
            else:
                return False, f"不支持的HTTP方法: {method}"
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"请求失败，状态码: {response.status_code}"
        except requests.exceptions.RequestException as e:
            return False, f"连接错误: {e}"
    
    def get(self, endpoint, params=None):
        """发送GET请求"""
        return self._request('GET', endpoint, params=params)
    
    def post(self, endpoint, data=None):
        """发送POST请求"""
        return self._request('POST', endpoint, data=data)
    
    def check_health(self):
        """检查服务端状态"""
        return self.get('/api/health')
