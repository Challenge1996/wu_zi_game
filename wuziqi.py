import time
import random

class WuziqiGame:
    def __init__(self):
        self.board_size = 15
        self.board = None
        self.current_player = 1  # 1: 黑棋, 2: 白棋
        self.game_over = False
        self.winner = None
        self.move_history = []  # 悔棋历史
        self.start_time = None
        self.game_phase = "waiting"  # waiting, coin_toss, playing
        self.players = {1: None, 2: None}  # 玩家ID映射，1:黑棋，2:白棋
        self.player_choices = {}  # 存储玩家的硬币猜测
        self.coin_result = None
        self.initialize_board()

    def initialize_board(self):
        self.board = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.current_player = 1
        self.game_over = False
        self.winner = None
        self.move_history = []
        self.start_time = None
        self.game_phase = "waiting"
        self.players = {1: None, 2: None}
        self.player_choices = {}
        self.coin_result = None

    def check_win(self, row, col, player):
        """检查玩家是否获胜"""
        directions = [
            (0, 1),   # 水平方向
            (1, 0),   # 垂直方向
            (1, 1),   # 左斜方向（右下）
            (1, -1)   # 右斜方向（左下）
        ]
        
        for dr, dc in directions:
            count = 1
            # 检查正方向
            r, c = row + dr, col + dc
            while 0 <= r < self.board_size and 0 <= c < self.board_size and self.board[r][c] == player:
                count += 1
                r, c = r + dr, c + dc
            # 检查反方向
            r, c = row - dr, col - dc
            while 0 <= r < self.board_size and 0 <= c < self.board_size and self.board[r][c] == player:
                count += 1
                r, c = r - dr, c - dc
            # 如果连续5子，则获胜
            if count >= 5:
                return True
        return False

    def place_piece(self, row, col, player):
        # 先检查玩家编号有效性
        if player not in [1, 2]:
            return False, "无效的玩家编号"
        
        # 检查游戏是否结束
        if self.game_over:
            return False, "游戏已结束"
        
        # 检查游戏阶段
        if self.game_phase != "playing":
            return False, "游戏尚未开始"
        
        # 检查是否是当前玩家的回合
        if player != self.current_player:
            return False, "不是当前玩家的回合"
        
        # 检查边界
        if row < 0 or row >= self.board_size:
            return False, "行号超出范围"
        if col < 0 or col >= self.board_size:
            return False, "列号超出范围"
        if self.board[row][col] != 0:
            return False, "该位置已有棋子"
        
        # 记录历史
        self.move_history.append((row, col, player))
        
        # 落子
        self.board[row][col] = player
        
        # 检查是否获胜
        if self.check_win(row, col, player):
            self.game_over = True
            self.winner = player
            return True, f"恭喜！玩家{'黑棋' if player == 1 else '白棋'}获胜！"
        
        # 切换玩家
        self.current_player = 2 if self.current_player == 1 else 1
        return True, "落子成功"

    def clear_board(self):
        self.initialize_board()

    def undo_move(self):
        """悔棋功能"""
        if len(self.move_history) == 0:
            return False, "没有可悔的棋"
        
        # 获取最后一步
        row, col, player = self.move_history.pop()
        
        # 恢复棋盘
        self.board[row][col] = 0
        
        # 恢复玩家
        self.current_player = player
        
        # 恢复游戏状态
        if self.game_over:
            self.game_over = False
            self.winner = None
        
        return True, f"已悔棋：行={row}, 列={col}, 玩家={'黑棋' if player == 1 else '白棋'}"

    def start_game(self):
        """开始游戏"""
        if self.game_phase == "playing":
            return False, "游戏已经在进行中"
        
        self.start_time = time.time()
        self.game_phase = "playing"
        return True, "游戏开始！"

    def get_game_time(self):
        """获取游戏时间（秒）"""
        if self.start_time is None:
            return 0
        return int(time.time() - self.start_time)

    def is_game_over(self):
        """检查游戏是否结束"""
        return self.game_over

    def get_winner(self):
        """获取获胜者"""
        return self.winner

    def get_current_player(self):
        """获取当前玩家"""
        return self.current_player

    def get_game_phase(self):
        """获取游戏阶段"""
        return self.game_phase

    def start_coin_toss(self):
        """开始抛硬币阶段"""
        if self.game_phase != "waiting":
            return False, "游戏阶段不正确，无法开始抛硬币"
        
        self.game_phase = "coin_toss"
        self.coin_result = random.randint(0, 1)  # 0: 正面, 1: 反面
        return True, "抛硬币阶段开始，请玩家猜测硬币结果"

    def player_make_choice(self, player_id, choice):
        """玩家进行硬币猜测（0: 正面, 1: 反面）"""
        if self.game_phase != "coin_toss":
            return False, "不在抛硬币阶段"
        
        if choice not in [0, 1]:
            return False, "无效的猜测，只能选择0(正面)或1(反面)"
        
        if player_id in self.player_choices:
            return False, "您已经进行了猜测"
        
        self.player_choices[player_id] = choice
        return True, f"玩家 {player_id} 猜测：{'正面' if choice == 0 else '反面'}"

    def resolve_coin_toss(self):
        """解决抛硬币结果"""
        if self.game_phase != "coin_toss":
            return False, "不在抛硬币阶段"
        
        if len(self.player_choices) < 2:
            return False, "还有玩家未进行猜测"
        
        # 获取两个玩家ID
        player_ids = list(self.player_choices.keys())
        player1_id, player2_id = player_ids[0], player_ids[1]
        
        # 检查谁猜对了
        player1_choice = self.player_choices[player1_id]
        player2_choice = self.player_choices[player2_id]
        
        winner_id = None
        if player1_choice == self.coin_result and player2_choice != self.coin_result:
            winner_id = player1_id
        elif player2_choice == self.coin_result and player1_choice != self.coin_result:
            winner_id = player2_id
        else:
            # 如果都猜对或都猜错，重新抛硬币
            self.coin_result = random.randint(0, 1)
            self.player_choices = {}
            return False, "平局！重新抛硬币，请再次猜测"
        
        # 猜对的玩家可以选择执黑棋或白棋
        return True, {
            "winner_id": winner_id,
            "coin_result": "正面" if self.coin_result == 0 else "反面",
            "message": f"玩家 {winner_id} 猜对了！硬币结果是{'正面' if self.coin_result == 0 else '反面'}。请选择执黑棋或白棋。"
        }

    def player_choose_color(self, player_id, color_choice):
        """玩家选择执子颜色（1: 黑棋, 2: 白棋）"""
        if self.game_phase != "coin_toss":
            return False, "不在抛硬币阶段"
        
        if color_choice not in [1, 2]:
            return False, "无效的颜色选择，只能选择1(黑棋)或2(白棋)"
        
        # 记录玩家选择
        self.players[color_choice] = player_id
        self.players[3 - color_choice] = None  # 另一个颜色暂时设为None，等另一个玩家确认
        
        return True, f"玩家 {player_id} 选择了{'黑棋' if color_choice == 1 else '白棋'}"

    def finalize_player_colors(self, player2_id):
        """确定第二个玩家的颜色"""
        if self.game_phase != "coin_toss":
            return False, "不在抛硬币阶段"
        
        # 找到未分配的颜色
        unassigned_color = None
        for color, p_id in self.players.items():
            if p_id is None:
                unassigned_color = color
                break
        
        if unassigned_color is None:
            return False, "所有颜色已分配"
        
        # 分配给第二个玩家
        self.players[unassigned_color] = player2_id
        
        # 进入游戏阶段
        self.game_phase = "playing"
        self.start_time = time.time()
        
        return True, {
            "players": self.players.copy(),
            "message": f"玩家分配完成！黑棋: {self.players[1]}, 白棋: {self.players[2]}。游戏开始！"
        }

    def get_player_color(self, player_id):
        """获取玩家的颜色"""
        for color, p_id in self.players.items():
            if p_id == player_id:
                return color
        return None

    def get_board_state(self):
        return [row[:] for row in self.board]

    def get_game_state(self, player_id=None):
        """获取完整的游戏状态"""
        state = {
            "board": self.get_board_state(),
            "board_size": self.board_size,
            "current_player": self.current_player,
            "game_over": self.game_over,
            "winner": self.winner,
            "game_phase": self.game_phase,
            "game_time": self.get_game_time(),
            "move_count": len(self.move_history)
        }
        
        if player_id is not None:
            state["player_color"] = self.get_player_color(player_id)
            state["is_my_turn"] = (self.get_player_color(player_id) == self.current_player) if self.game_phase == "playing" else False
        
        return state

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
