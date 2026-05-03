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
- 内存数据存储

### 客户端
- Python 3.13+
- PyQt5 GUI
- 多线程网络通信

## API接口

### 玩家相关
- `POST /api/player/register` - 注册玩家
- `POST /api/player/heartbeat` - 玩家心跳
- `POST /api/player/offline` - 玩家下线
- `GET /api/player/list` - 获取在线玩家列表
- `GET /api/player/stats` - 获取玩家战绩和积分（新增）

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
- `POST /api/game/place_piece` - 落子
- `POST /api/game/undo` - 直接悔棋
- `POST /api/game/undo/request` - 发起悔棋请求
- `POST /api/game/undo/respond` - 响应悔棋请求
- `GET /api/game/undo/status` - 获取悔棋请求状态
- `POST /api/game/reset` - 重置游戏
- `POST /api/game/quick_start` - 快速开始
- `POST /api/game/resign` - 认输

### 房间相关
- `GET /api/room/info` - 获取房间信息
- `GET /api/room/list` - 获取房间列表
- `GET /api/room/public_list` - 获取公开对局列表
- `POST /api/room/spectate` - 加入观战
- `POST /api/room/leave_spectate` - 离开观战

### 聊天相关
- `POST /api/chat/send` - 发送聊天消息
- `GET /api/chat/history` - 获取聊天历史

### 其他
- `GET /api/health` - 健康检查

## 运行说明

### 启动服务端
```bash
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
- 版本：1.0.0
- 开发日期：2026-04-30
- 支持系统：macOS, Windows, Linux

## 依赖包
- Flask==2.0.1
- PyQt5==5.15.4
- requests==2.26.0
