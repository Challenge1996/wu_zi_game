# wu_zi_game
五子棋游戏

## 功能特性

### 核心功能
- 15x15标准棋盘
- 网络对战
- 抛硬币猜先
- 悔棋、重置
- 游戏计时
- 观战功能

### 新增功能：战绩统计与积分系统

#### 战绩统计
- **总对局数**：记录玩家的总游戏次数
- **胜场数**：记录玩家的获胜次数
- **负场数**：记录玩家的失败次数
- **平局数**：记录玩家的平局次数
- **胜率**：计算玩家的胜率百分比
- **当前连胜**：记录玩家当前的连胜次数
- **最高连胜**：记录玩家历史最高连胜次数

#### 积分系统
- **积分规则**：
  - 胜一局：+1 积分
  - 负一局：-1 积分
  - 平局：0 积分

#### 段位系统
| 段位 | 所需积分 |
|------|----------|
| 新手 | 0 及以下 |
| 黑铁 | 1-4 |
| 青铜 | 5-9 |
| 白银 | 10-19 |
| 黄金 | 20-34 |
| 铂金 | 35-54 |
| 钻石 | 55-79 |
| 星耀 | 80-109 |
| 王者 | 110 及以上 |

## 技术架构

### 服务端
- Python 3.13+
- Flask 框架
- 支持内存存储和 MySQL 数据库持久化

### 客户端
- Python 3.13+
- PyQt5 GUI
- 多线程网络通信

## 数据库配置（可选）

### 1. 数据库初始化

服务端支持 MySQL 数据库持久化存储。如需启用，请按以下步骤操作：

**创建数据库并导入表结构：**
```bash
# 方法一：使用 MySQL 命令行
mysql -u root -p < db/init.sql

# 方法二：在 MySQL 客户端中执行
source /path/to/db/init.sql
```

`db/init.sql` 包含以下 9 张表：
- `players` - 玩家基本信息
- `player_stats` - 玩家战绩统计
- `rooms` - 房间信息（区分 player1/player2 双方玩家）
- `challenges` - 挑战记录
- `undo_requests` - 悔棋请求
- `chat_messages` - 聊天消息
- `spectators` - 观战者记录
- `game_records` - 游戏历史记录（含完整落子历史）
- `player_game_relations` - 玩家与游戏记录的关联表

### 2. 环境变量配置

在启动服务端前，设置以下环境变量：

```bash
# 启用数据库模式（默认 false，使用内存模式）
export USE_DATABASE=true

# 数据库连接配置
export DB_HOST=localhost
export DB_PORT=3306
export DB_USER=root
export DB_PASSWORD=your_password
export DB_NAME=wuziqi_game
```

### 3. 启动服务端

```bash
# 内存模式（默认，无需数据库）
python server.py

# 数据库模式（需先配置环境变量和初始化数据库）
USE_DATABASE=true python server.py
```

### 4. 数据存储说明

#### 可持久化到数据库的数据

| 数据类型 | 落库时机 | 存储位置 |
|----------|----------|----------|
| 玩家信息 | 注册/登录/状态变更时 | `players` 表 |
| 玩家战绩 | 游戏结束后 | `player_stats` 表 |
| 房间信息 | 创建/状态变更时 | `rooms` 表 |
| 挑战记录 | 发起/响应时 | `challenges` 表 |
| 悔棋请求 | 发起/响应时 | `undo_requests` 表 |
| 聊天消息 | 发送时 | `chat_messages` 表 |
| 观战者 | 加入/离开时 | `spectators` 表 |
| 游戏记录 | 游戏结束后 | `game_records` 表 |
| 落子历史 | 游戏结束后 | `game_records.move_history` (JSON) |

#### 无法落库的数据说明

以下数据仅在内存中存储，**不持久化到数据库**：

**1. WuziqiGame 游戏实例对象**
- **原因**：包含复杂的游戏逻辑、状态机和回调函数，无法直接序列化到数据库
- **影响**：服务重启后，进行中的游戏会丢失
- **解决方案**：
  - 游戏结束后，完整落子历史会存储到 `game_records.move_history` 字段
  - 可以通过历史对局接口查询已结束的游戏进行复盘

**2. 房间中的实时游戏状态**
- **原因**：`rooms` 表存储的是房间元数据，不包含 `WuziqiGame` 对象
- **影响**：服务重启后，进行中的对局无法继续
- **当前实现**：
  - `room['game']` 字段存储的是 `WuziqiGame` 对象实例
  - 该对象包含棋盘状态、当前玩家、游戏阶段等运行时信息

**3. 运行时临时数据**
- **在线状态**：玩家的 `online` 字段虽然会同步到数据库，但服务重启后需要玩家重新心跳才能标记为在线
- **当前房间**：玩家的 `current_room` 字段会同步到数据库，但服务重启后实际连接状态丢失

### 5. 历史对局接口

以下接口在数据库模式下直接从数据库查询：

#### 获取玩家历史对局列表
```http
GET /api/player/game_records?player_id={player_id}
```

**响应示例：**
```json
{
  "success": true,
  "player_id": "player_123",
  "count": 10,
  "records": [
    {
      "id": "record_001",
      "room_name": "玩家A vs 玩家B",
      "opponent_name": "玩家B",
      "my_color": 1,
      "is_winner": true,
      "total_moves": 45,
      "resign_reason": null,
      "finished_at": 1714567890
    }
  ]
}
```

#### 获取单条游戏记录详情（含完整落子历史）
```http
GET /api/game/record?record_id={record_id}
```

**响应示例：**
```json
{
  "success": true,
  "record": {
    "id": "record_001",
    "room_id": "room_001",
    "room_name": "玩家A vs 玩家B",
    "player1_id": "player_a",
    "player1_name": "玩家A",
    "player2_id": "player_b",
    "player2_name": "玩家B",
    "player1_color": 1,
    "player2_color": 2,
    "winner_color": 1,
    "winner_id": "player_a",
    "finished_at": 1714567890,
    "total_moves": 45,
    "game_over": true,
    "resign_reason": null,
    "move_history": [
      {"row": 7, "col": 7, "color": 1},
      {"row": 7, "col": 8, "color": 2},
      {"row": 8, "col": 7, "color": 1},
      "..."
    ]
  }
}
```

### 6. 玩家区分设计

所有涉及玩家的表都明确区分双方玩家：

**rooms 表：**
- `player1` - 黑棋玩家 ID
- `player2` - 白棋玩家 ID
- `challenger_id` - 挑战者 ID
- `challenged_id` - 被挑战者 ID

**game_records 表：**
- `player1_id` / `player1_name` - 黑棋玩家信息
- `player2_id` / `player2_name` - 白棋玩家信息
- `player1_color` - 固定为 1（黑棋）
- `player2_color` - 固定为 2（白棋）
- `winner_color` - 获胜方棋子颜色
- `winner_id` - 获胜方玩家 ID

**player_game_relations 表：**
- `player_color` - 玩家在该局的棋子颜色
- `is_winner` - 是否获胜

## API接口

### 玩家相关
- `POST /api/player/register` - 注册玩家
- `POST /api/player/heartbeat` - 玩家心跳
- `POST /api/player/offline` - 玩家下线
- `GET /api/player/list` - 获取在线玩家列表
- `GET /api/player/stats` - 获取玩家战绩和积分（新增）
- `GET /api/player/game_records` - 获取玩家历史对局列表（数据库模式直接从数据库查询）

### 挑战相关
- `POST /api/challenge/send` - 发送挑战
- `POST /api/challenge/accept` - 接受挑战
- `POST /api/challenge/decline` - 拒绝挑战
- `GET /api/challenge/list` - 获取挑战列表

### 游戏相关
- `POST /api/game/coin_choice` - 抛硬币猜测
- `POST /api/game/resolve_coin` - 解决抛硬币结果
- `POST /api/game/choose_color` - 选择执子颜色
- `POST /api/game/finalize_colors` - 确定颜色并开始
- `POST /api/game/place_piece` - 落子（游戏结束后落子历史写入数据库）
- `POST /api/game/undo` - 直接悔棋
- `POST /api/game/undo/request` - 发起悔棋请求
- `POST /api/game/undo/respond` - 响应悔棋请求
- `GET /api/game/undo/status` - 获取悔棋请求状态
- `POST /api/game/reset` - 重置游戏
- `POST /api/game/quick_start` - 快速开始
- `POST /api/game/resign` - 认输
- `GET /api/game/record` - 获取游戏记录详情（数据库模式直接从数据库查询）

### 房间相关
- `GET /api/room/info` - 获取房间信息
- `GET /api/room/list` - 获取房间列表
- `GET /api/room/public_list` - 获取公开对局列表
- `POST /api/room/spectate` - 加入观战
- `POST /api/room/leave_spectate` - 离开观战

### 聊天相关
- `POST /api/chat/send` - 发送聊天消息（实时写入数据库）
- `GET /api/chat/history` - 获取聊天历史

### 其他
- `GET /api/health` - 健康检查

## 运行说明

### 启动服务端（内存模式，默认）
```bash
python server.py
```

### 启动服务端（数据库模式）
```bash
# 先配置环境变量
export USE_DATABASE=true
export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD=your_password
export DB_NAME=wuziqi_game

# 启动服务
python server.py
```

### 启动客户端
```bash
python gui_client.py
```

## 对战流程
1. 两个玩家分别注册
2. 玩家A查看在线玩家列表
3. 玩家A向玩家B发起挑战
4. 玩家B接受或拒绝挑战
5. 接受挑战后，进入抛硬币阶段
6. 两个玩家分别猜测硬币结果
7. 猜对的玩家选择执黑或执白
8. 游戏开始，轮流落子
9. 连成5子获胜，或一方下线判负
10. 游戏结束后，数据写入数据库（玩家战绩、游戏记录、落子历史）

## 观战流程
1. 其他玩家注册并登录
2. 查看公开对局列表（GET /api/room/public_list）
3. 选择感兴趣的对局加入观战（POST /api/room/spectate）
4. 观战者可以查看棋盘和聊天，但不能操作棋局
5. 观战人数大于1的对局会显示热门标识
6. 随时可以离开观战（POST /api/room/leave_spectate）

## 战绩统计流程
1. 玩家注册后，系统自动初始化战绩数据
2. 每局游戏结束后，系统自动更新双方战绩：
   - 获胜方：+1 积分，+1 胜场，当前连胜+1
   - 失败方：-1 积分，+1 负场，当前连胜重置为0
   - 平局：积分不变，+1 平局，当前连胜重置为0
3. 系统根据玩家积分自动计算段位
4. 玩家可以在个人信息面板查看详细战绩

## 版本信息
- 版本：1.1.0
- 开发日期：2026-05-03
- 支持系统：macOS, Windows, Linux

## 依赖包
- Flask==2.0.1
- PyQt5==5.15.4
- requests==2.26.0
- pymysql>=1.1.0（数据库模式必需）
