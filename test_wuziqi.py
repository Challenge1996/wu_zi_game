import unittest
import time
from wuziqi import WuziqiGame


class TestWuziqiGame(unittest.TestCase):
    def setUp(self):
        self.game = WuziqiGame()

    def test_initialize_board(self):
        self.game.initialize_board()
        board = self.game.get_board_state()
        self.assertEqual(len(board), 15)
        self.assertEqual(len(board[0]), 15)
        for row in board:
            for cell in row:
                self.assertEqual(cell, 0)

    def test_place_piece_success(self):
        # 先设置游戏状态为playing
        self.game.game_phase = "playing"
        success, message = self.game.place_piece(7, 7, 1)
        self.assertTrue(success)
        board = self.game.get_board_state()
        self.assertEqual(board[7][7], 1)

    def test_place_piece_out_of_range(self):
        self.game.game_phase = "playing"
        success, message = self.game.place_piece(-1, 7, 1)
        self.assertFalse(success)
        self.assertEqual(message, "行号超出范围")

        success, message = self.game.place_piece(15, 7, 1)
        self.assertFalse(success)
        self.assertEqual(message, "行号超出范围")

        success, message = self.game.place_piece(7, -1, 1)
        self.assertFalse(success)
        self.assertEqual(message, "列号超出范围")

        success, message = self.game.place_piece(7, 15, 1)
        self.assertFalse(success)
        self.assertEqual(message, "列号超出范围")

    def test_place_piece_invalid_player(self):
        self.game.game_phase = "playing"
        success, message = self.game.place_piece(7, 7, 0)
        self.assertFalse(success)
        self.assertEqual(message, "无效的玩家编号")

        success, message = self.game.place_piece(7, 7, 3)
        self.assertFalse(success)
        self.assertEqual(message, "无效的玩家编号")

    def test_place_piece_occupied(self):
        self.game.game_phase = "playing"
        self.game.place_piece(7, 7, 1)
        success, message = self.game.place_piece(7, 7, 2)
        self.assertFalse(success)
        self.assertEqual(message, "该位置已有棋子")

    def test_clear_board(self):
        self.game.game_phase = "playing"
        self.game.place_piece(7, 7, 1)
        self.game.place_piece(7, 8, 2)
        self.game.clear_board()
        board = self.game.get_board_state()
        for row in board:
            for cell in row:
                self.assertEqual(cell, 0)

    def test_get_board_state_is_copy(self):
        self.game.game_phase = "playing"
        self.game.place_piece(7, 7, 1)
        state = self.game.get_board_state()
        state[7][7] = 2
        board = self.game.get_board_state()
        self.assertEqual(board[7][7], 1)

    def test_print_board(self):
        import io
        import sys
        captured_output = io.StringIO()
        sys.stdout = captured_output
        self.game.print_board()
        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()
        self.assertIn("0", output)

    # 新增测试：胜负判断
    def test_check_win_horizontal(self):
        """测试水平方向连成5子获胜"""
        self.game.game_phase = "playing"
        # 放置水平5子
        for col in range(3, 8):
            self.game.place_piece(7, col, 1)
            self.game.current_player = 1  # 重置当前玩家，方便测试
        
        # 检查最后一步是否获胜
        self.assertTrue(self.game.check_win(7, 7, 1))

    def test_check_win_vertical(self):
        """测试垂直方向连成5子获胜"""
        self.game.game_phase = "playing"
        # 放置垂直5子
        for row in range(3, 8):
            self.game.place_piece(row, 7, 1)
            self.game.current_player = 1
        
        self.assertTrue(self.game.check_win(7, 7, 1))

    def test_check_win_diagonal_right(self):
        """测试右斜方向连成5子获胜（左上到右下）"""
        self.game.game_phase = "playing"
        # 放置右斜5子 (3,3), (4,4), (5,5), (6,6), (7,7)
        for i in range(3, 8):
            self.game.place_piece(i, i, 1)
            self.game.current_player = 1
        
        self.assertTrue(self.game.check_win(5, 5, 1))

    def test_check_win_diagonal_left(self):
        """测试左斜方向连成5子获胜（右上到左下）"""
        self.game.game_phase = "playing"
        # 放置左斜5子 (3,7), (4,6), (5,5), (6,4), (7,3)
        for i in range(3, 8):
            self.game.place_piece(i, 10 - i, 1)
            self.game.current_player = 1
        
        self.assertTrue(self.game.check_win(5, 5, 1))

    def test_check_win_boundary(self):
        """测试边界情况的胜负判断"""
        self.game.game_phase = "playing"
        # 在角落放置5子 (0,0)到(0,4)
        for col in range(5):
            self.game.place_piece(0, col, 1)
            self.game.current_player = 1
        
        self.assertTrue(self.game.check_win(0, 2, 1))

    # 新增测试：悔棋功能
    def test_undo_move(self):
        """测试悔棋功能"""
        self.game.game_phase = "playing"
        
        # 玩家1落子
        self.game.place_piece(7, 7, 1)
        board = self.game.get_board_state()
        self.assertEqual(board[7][7], 1)
        
        # 悔棋
        success, message = self.game.undo_move()
        self.assertTrue(success)
        board = self.game.get_board_state()
        self.assertEqual(board[7][7], 0)
        self.assertEqual(self.game.current_player, 1)  # 应该恢复到玩家1的回合

    def test_undo_move_empty(self):
        """测试没有棋可悔的情况"""
        success, message = self.game.undo_move()
        self.assertFalse(success)
        self.assertEqual(message, "没有可悔的棋")

    # 新增测试：游戏状态
    def test_game_over(self):
        """测试游戏结束状态"""
        self.assertFalse(self.game.is_game_over())
        self.assertIsNone(self.game.get_winner())

    def test_get_current_player(self):
        """测试获取当前玩家"""
        self.assertEqual(self.game.get_current_player(), 1)

    def test_game_time(self):
        """测试游戏时间"""
        self.assertEqual(self.game.get_game_time(), 0)
        
        self.game.start_game()
        time.sleep(1.1)  # 等待1秒多，确保时间变化
        self.assertGreater(self.game.get_game_time(), 0)

    # 新增测试：抛硬币功能
    def test_start_coin_toss(self):
        """测试开始抛硬币阶段"""
        self.assertEqual(self.game.get_game_phase(), "waiting")
        success, message = self.game.start_coin_toss()
        self.assertTrue(success)
        self.assertEqual(self.game.get_game_phase(), "coin_toss")

    def test_player_make_choice(self):
        """测试玩家进行硬币猜测"""
        self.game.start_coin_toss()
        
        success, message = self.game.player_make_choice("player1", 0)
        self.assertTrue(success)
        self.assertIn("player1", message)

    def test_player_make_choice_invalid(self):
        """测试无效的硬币猜测"""
        self.game.start_coin_toss()
        
        success, message = self.game.player_make_choice("player1", 2)
        self.assertFalse(success)
        self.assertEqual(message, "无效的猜测，只能选择0(正面)或1(反面)")

    # 新增测试：游戏阶段
    def test_game_phases(self):
        """测试游戏阶段切换"""
        self.assertEqual(self.game.get_game_phase(), "waiting")
        
        self.game.start_coin_toss()
        self.assertEqual(self.game.get_game_phase(), "coin_toss")
        
        self.game.start_game()
        self.assertEqual(self.game.get_game_phase(), "playing")

    # 新增测试：获取完整游戏状态
    def test_get_game_state(self):
        """测试获取完整游戏状态"""
        state = self.game.get_game_state()
        
        self.assertIn("board", state)
        self.assertIn("board_size", state)
        self.assertIn("current_player", state)
        self.assertIn("game_over", state)
        self.assertIn("winner", state)
        self.assertIn("game_phase", state)
        self.assertIn("game_time", state)
        self.assertIn("move_count", state)

    # 新增测试：落子后切换玩家
    def test_switch_player_after_place(self):
        """测试落子后切换玩家"""
        self.game.game_phase = "playing"
        
        # 玩家1落子
        self.assertEqual(self.game.current_player, 1)
        self.game.place_piece(7, 7, 1)
        
        # 应该切换到玩家2
        self.assertEqual(self.game.current_player, 2)

    # 新增测试：游戏结束后不能再落子
    def test_place_piece_after_game_over(self):
        """测试游戏结束后不能再落子"""
        self.game.game_phase = "playing"
        self.game.game_over = True
        
        success, message = self.game.place_piece(7, 7, 1)
        self.assertFalse(success)
        self.assertEqual(message, "游戏已结束")

    # 新增测试：悔棋后游戏结束状态恢复
    def test_undo_after_win(self):
        """测试获胜后悔棋恢复游戏状态"""
        self.game.game_phase = "playing"
        
        # 玩家1放置水平5子获胜
        for col in range(5):
            self.game.current_player = 1
            self.game.place_piece(0, col, 1)
        
        # 确认游戏结束
        self.assertTrue(self.game.game_over)
        self.assertEqual(self.game.winner, 1)
        
        # 悔棋
        self.game.undo_move()
        
        # 确认游戏状态恢复
        self.assertFalse(self.game.game_over)
        self.assertIsNone(self.game.winner)


if __name__ == "__main__":
    unittest.main()
