#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话框模块
"""

from ui.dialogs.challenge_dialog import ChallengeDialog
from ui.dialogs.coin_toss_dialog import CoinTossDialog
from ui.dialogs.color_choice_dialog import ColorChoiceDialog
from ui.dialogs.player_list_dialog import PlayerListDialog
from ui.dialogs.undo_request_dialog import UndoRequestDialog
from ui.dialogs.challenge_list_dialog import ChallengeListDialog
from ui.dialogs.public_rooms_dialog import PublicRoomsDialog

__all__ = [
    'ChallengeDialog',
    'CoinTossDialog',
    'ColorChoiceDialog',
    'PlayerListDialog',
    'UndoRequestDialog',
    'ChallengeListDialog',
    'PublicRoomsDialog'
]
