#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
五子棋游戏服务端入口
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import main

if __name__ == '__main__':
    main()
