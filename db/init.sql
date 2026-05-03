-- ============================================================
-- 五子棋游戏 MySQL 数据库初始化脚本
-- 数据库名: wuziqi_game
-- 字符集: utf8mb4
-- ============================================================

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS wuziqi_game DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE wuziqi_game;

-- ============================================================
-- 1. 玩家表 (players)
-- 存储玩家基本信息
-- ============================================================
CREATE TABLE IF NOT EXISTS players (
    id VARCHAR(64) PRIMARY KEY COMMENT '玩家ID',
    name VARCHAR(100) NOT NULL COMMENT '玩家昵称',
    online BOOLEAN DEFAULT FALSE COMMENT '是否在线',
    status VARCHAR(50) DEFAULT 'idle' COMMENT '玩家状态: idle/playing/spectating/challenging',
    current_room VARCHAR(64) NULL COMMENT '当前所在房间ID',
    last_heartbeat BIGINT DEFAULT 0 COMMENT '最后心跳时间戳',
    registered_at BIGINT DEFAULT 0 COMMENT '注册时间戳',
    INDEX idx_status (status),
    INDEX idx_online (online),
    INDEX idx_current_room (current_room)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='玩家表';

-- ============================================================
-- 2. 玩家战绩表 (player_stats)
-- 存储玩家战绩统计信息，与玩家表一对一关联
-- ============================================================
CREATE TABLE IF NOT EXISTS player_stats (
    player_id VARCHAR(64) PRIMARY KEY COMMENT '玩家ID',
    total_games INT DEFAULT 0 COMMENT '总对局数',
    wins INT DEFAULT 0 COMMENT '胜场数',
    losses INT DEFAULT 0 COMMENT '负场数',
    draws INT DEFAULT 0 COMMENT '平局数',
    win_rate DECIMAL(5,2) DEFAULT 0.00 COMMENT '胜率(%)',
    current_streak INT DEFAULT 0 COMMENT '当前连胜/连败',
    max_streak INT DEFAULT 0 COMMENT '最大连胜',
    score INT DEFAULT 0 COMMENT '积分',
    `rank` VARCHAR(50) DEFAULT '新手' COMMENT '段位: 新手/入门/初级/中级/高级/大师/宗师',
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
    INDEX idx_score (score),
    INDEX idx_rank (`rank`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='玩家战绩表';

-- ============================================================
-- 3. 房间表 (rooms)
-- 存储游戏房间信息
-- 注意: player1/player2 区分双方玩家，player1执黑棋，player2执白棋
-- ============================================================
CREATE TABLE IF NOT EXISTS rooms (
    id VARCHAR(64) PRIMARY KEY COMMENT '房间ID',
    name VARCHAR(200) NOT NULL COMMENT '房间名称',
    creator VARCHAR(64) NOT NULL COMMENT '房间创建者ID',
    challenger_id VARCHAR(64) NULL COMMENT '挑战者ID(发起挑战的玩家)',
    challenged_id VARCHAR(64) NULL COMMENT '被挑战者ID',
    player1 VARCHAR(64) NULL COMMENT '玩家1ID(黑棋)',
    player2 VARCHAR(64) NULL COMMENT '玩家2ID(白棋)',
    status VARCHAR(50) DEFAULT 'waiting' COMMENT '房间状态: waiting/coin_toss/playing/finished',
    visibility VARCHAR(50) DEFAULT 'public' COMMENT '房间可见性: public/private',
    spectator_count INT DEFAULT 0 COMMENT '观战人数',
    created_at BIGINT DEFAULT 0 COMMENT '创建时间戳',
    started_at BIGINT NULL COMMENT '游戏开始时间戳',
    finished_at BIGINT NULL COMMENT '游戏结束时间戳',
    winner INT NULL COMMENT '获胜方: 1=黑棋/2=白棋/NULL=平局',
    INDEX idx_status (status),
    INDEX idx_creator (creator),
    INDEX idx_player1 (player1),
    INDEX idx_player2 (player2),
    INDEX idx_visibility (visibility)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='房间表';

-- ============================================================
-- 4. 挑战表 (challenges)
-- 存储玩家之间的挑战记录
-- ============================================================
CREATE TABLE IF NOT EXISTS challenges (
    id VARCHAR(64) PRIMARY KEY COMMENT '挑战ID',
    challenger VARCHAR(64) NOT NULL COMMENT '挑战者ID',
    challenged VARCHAR(64) NOT NULL COMMENT '被挑战者ID',
    status VARCHAR(50) DEFAULT 'pending' COMMENT '挑战状态: pending/accepted/declined/expired',
    room_id VARCHAR(64) NULL COMMENT '关联的房间ID(接受挑战后创建)',
    created_at BIGINT DEFAULT 0 COMMENT '创建时间戳',
    expires_at BIGINT DEFAULT 0 COMMENT '过期时间戳',
    INDEX idx_challenger (challenger),
    INDEX idx_challenged (challenged),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='挑战表';

-- ============================================================
-- 5. 悔棋请求表 (undo_requests)
-- 存储游戏中的悔棋请求
-- ============================================================
CREATE TABLE IF NOT EXISTS undo_requests (
    id VARCHAR(64) PRIMARY KEY COMMENT '悔棋请求ID',
    room_id VARCHAR(64) NOT NULL COMMENT '房间ID',
    requester VARCHAR(64) NOT NULL COMMENT '请求悔棋的玩家ID',
    requested VARCHAR(64) NOT NULL COMMENT '被请求的玩家ID(对手)',
    status VARCHAR(50) DEFAULT 'pending' COMMENT '请求状态: pending/accepted/declined/expired',
    created_at BIGINT DEFAULT 0 COMMENT '创建时间戳',
    expires_at BIGINT DEFAULT 0 COMMENT '过期时间戳',
    INDEX idx_room_id (room_id),
    INDEX idx_status (status),
    INDEX idx_requester (requester)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='悔棋请求表';

-- ============================================================
-- 6. 聊天消息表 (chat_messages)
-- 存储房间内的聊天消息
-- ============================================================
CREATE TABLE IF NOT EXISTS chat_messages (
    id VARCHAR(64) PRIMARY KEY COMMENT '消息ID',
    room_id VARCHAR(64) NOT NULL COMMENT '房间ID',
    player_id VARCHAR(64) NULL COMMENT '发送者ID(系统消息为NULL)',
    player_name VARCHAR(100) NULL COMMENT '发送者名称',
    type VARCHAR(50) DEFAULT 'text' COMMENT '消息类型: text/system/move/undo/resign/spectator_join/spectator_leave',
    content TEXT COMMENT '消息内容',
    extra_data JSON NULL COMMENT '额外数据(JSON格式，如落子位置、悔棋结果等)',
    timestamp BIGINT DEFAULT 0 COMMENT '发送时间戳',
    INDEX idx_room_id (room_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_type (type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='聊天消息表';

-- ============================================================
-- 7. 观战者表 (spectators)
-- 存储房间的观战者信息
-- ============================================================
CREATE TABLE IF NOT EXISTS spectators (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    room_id VARCHAR(64) NOT NULL COMMENT '房间ID',
    player_id VARCHAR(64) NOT NULL COMMENT '观战者ID',
    joined_at BIGINT DEFAULT 0 COMMENT '加入观战时间戳',
    UNIQUE KEY uk_room_player (room_id, player_id),
    INDEX idx_room_id (room_id),
    INDEX idx_player_id (player_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='观战者表';

-- ============================================================
-- 8. 游戏记录表 (game_records)
-- 存储历史对局记录，用于复盘和历史查询
-- 注意: 完整的落子历史存储在 move_history 字段中(JSON格式)
-- ============================================================
CREATE TABLE IF NOT EXISTS game_records (
    id VARCHAR(64) PRIMARY KEY COMMENT '记录ID',
    room_id VARCHAR(64) NOT NULL COMMENT '房间ID',
    room_name VARCHAR(200) NULL COMMENT '房间名称',
    player1_id VARCHAR(64) NOT NULL COMMENT '玩家1ID(黑棋)',
    player1_name VARCHAR(100) NULL COMMENT '玩家1名称',
    player2_id VARCHAR(64) NOT NULL COMMENT '玩家2ID(白棋)',
    player2_name VARCHAR(100) NULL COMMENT '玩家2名称',
    player1_color INT DEFAULT 1 COMMENT '玩家1棋子颜色: 1=黑棋',
    player2_color INT DEFAULT 2 COMMENT '玩家2棋子颜色: 2=白棋',
    winner_color INT NULL COMMENT '获胜方棋子颜色: 1/2/NULL',
    winner_id VARCHAR(64) NULL COMMENT '获胜者玩家ID',
    created_at BIGINT DEFAULT 0 COMMENT '创建时间戳',
    started_at BIGINT NULL COMMENT '开始时间戳',
    finished_at BIGINT NULL COMMENT '结束时间戳',
    total_moves INT DEFAULT 0 COMMENT '总落子数',
    game_over BOOLEAN DEFAULT FALSE COMMENT '游戏是否结束',
    resign_reason VARCHAR(50) NULL COMMENT '认输原因: timeout/offline/user',
    move_history JSON NULL COMMENT '落子历史(JSON数组，每步包含row/col/color)',
    INDEX idx_player1_id (player1_id),
    INDEX idx_player2_id (player2_id),
    INDEX idx_winner_id (winner_id),
    INDEX idx_finished_at (finished_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='游戏记录表';

-- ============================================================
-- 9. 玩家游戏记录关联表 (player_game_relations)
-- 建立玩家与游戏记录的多对多关系，方便查询玩家历史对局
-- ============================================================
CREATE TABLE IF NOT EXISTS player_game_relations (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    player_id VARCHAR(64) NOT NULL COMMENT '玩家ID',
    game_record_id VARCHAR(64) NOT NULL COMMENT '游戏记录ID',
    player_color INT NOT NULL COMMENT '玩家在该局的棋子颜色: 1=黑/2=白',
    is_winner BOOLEAN DEFAULT FALSE COMMENT '是否获胜',
    UNIQUE KEY uk_player_record (player_id, game_record_id),
    INDEX idx_player_id (player_id),
    INDEX idx_game_record_id (game_record_id),
    FOREIGN KEY (game_record_id) REFERENCES game_records(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='玩家游戏记录关联表';

-- ============================================================
-- 初始化完成提示
-- ============================================================
SELECT '数据库初始化完成！' AS status;

-- 显示所有表
SHOW TABLES;
