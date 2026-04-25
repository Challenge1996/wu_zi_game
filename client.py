#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
五子棋游戏命令行客户端入口
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from client import cli_main

if __name__ == '__main__':
    cli_main()
