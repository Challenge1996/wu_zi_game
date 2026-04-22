import unittest
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
        success, message = self.game.place_piece(7, 7, 1)
        self.assertTrue(success)
        self.assertEqual(message, "落子成功")
        board = self.game.get_board_state()
        self.assertEqual(board[7][7], 1)

        success, message = self.game.place_piece(7, 8, 2)
        self.assertTrue(success)
        self.assertEqual(message, "落子成功")
        board = self.game.get_board_state()
        self.assertEqual(board[7][8], 2)

    def test_place_piece_out_of_range(self):
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
        success, message = self.game.place_piece(7, 7, 0)
        self.assertFalse(success)
        self.assertEqual(message, "无效的玩家编号")

        success, message = self.game.place_piece(7, 7, 3)
        self.assertFalse(success)
        self.assertEqual(message, "无效的玩家编号")

    def test_place_piece_occupied(self):
        self.game.place_piece(7, 7, 1)
        success, message = self.game.place_piece(7, 7, 2)
        self.assertFalse(success)
        self.assertEqual(message, "该位置已有棋子")

    def test_clear_board(self):
        self.game.place_piece(7, 7, 1)
        self.game.place_piece(7, 8, 2)
        self.game.clear_board()
        board = self.game.get_board_state()
        for row in board:
            for cell in row:
                self.assertEqual(cell, 0)

    def test_get_board_state_is_copy(self):
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


if __name__ == "__main__":
    unittest.main()
