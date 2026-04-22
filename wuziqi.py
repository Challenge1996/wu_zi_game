class WuziqiGame:
    def __init__(self):
        self.board_size = 15
        self.board = None
        self.initialize_board()

    def initialize_board(self):
        self.board = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]

    def place_piece(self, row, col, player):
        if row < 0 or row >= self.board_size:
            return False, "行号超出范围"
        if col < 0 or col >= self.board_size:
            return False, "列号超出范围"
        if player not in [1, 2]:
            return False, "无效的玩家编号"
        if self.board[row][col] != 0:
            return False, "该位置已有棋子"
        
        self.board[row][col] = player
        return True, "落子成功"

    def clear_board(self):
        self.initialize_board()

    def get_board_state(self):
        return [row[:] for row in self.board]

    def print_board(self):
        print("  " + " ".join([str(i % 10) for i in range(self.board_size)]))
        for i, row in enumerate(self.board):
            print(f"{i % 10} " + " ".join(["." if cell == 0 else "X" if cell == 1 else "O" for cell in row]))


def main():
    print("=== 五子棋游戏 ===")
    print("欢迎来到五子棋游戏！")
    print("游戏规则：")
    print("  - 黑方(1)先手，白方(2)后手")
    print("  - 输入格式：行 列 (例如：7 7)")
    print("  - 输入 'q' 或 'quit' 退出游戏")
    print("  - 输入 'c' 或 'clear' 清空棋盘")
    print("  - 输入 'h' 或 'help' 查看帮助\n")
    
    game = WuziqiGame()
    current_player = 1
    
    while True:
        game.print_board()
        print(f"\n当前玩家: {'黑方(1)' if current_player == 1 else '白方(2)'}")
        user_input = input("请输入落子位置: ").strip().lower()
        
        if user_input in ['q', 'quit']:
            print("游戏结束，再见！")
            break
        
        if user_input in ['c', 'clear']:
            game.clear_board()
            current_player = 1
            print("棋盘已清空，重新开始游戏。\n")
            continue
        
        if user_input in ['h', 'help']:
            print("\n帮助信息：")
            print("  - 输入格式：行 列 (例如：7 7)")
            print("  - 行和列的范围都是 0-14")
            print("  - 黑方(1)用 X 表示，白方(2)用 O 表示")
            print("  - 输入 'q' 或 'quit' 退出游戏")
            print("  - 输入 'c' 或 'clear' 清空棋盘")
            print("  - 输入 'h' 或 'help' 查看帮助\n")
            continue
        
        try:
            row, col = map(int, user_input.split())
        except ValueError:
            print("输入格式错误！请输入：行 列 (例如：7 7)，或输入 'h' 查看帮助\n")
            continue
        
        success, message = game.place_piece(row, col, current_player)
        if success:
            print(f"落子成功！\n")
            current_player = 2 if current_player == 1 else 1
        else:
            print(f"落子失败：{message}\n")


if __name__ == "__main__":
    main()
