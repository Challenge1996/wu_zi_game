#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI组件模块
"""

from ui.board_widget import BoardWidget
from ui.timer_widget import TimerWidget
from ui.signals import GameSignals
from ui.dialogs import (
    ChallengeDialog,
    CoinTossDialog,
    ColorChoiceDialog,
    PlayerListDialog,
    UndoRequestDialog,
    ChallengeListDialog
)

__all__ = [
    'BoardWidget',
    'TimerWidget',
    'GameSignals',
    'ChallengeDialog',
    'CoinTossDialog',
    'ColorChoiceDialog',
    'PlayerListDialog',
    'UndoRequestDialog',
    'ChallengeListDialog'
]
