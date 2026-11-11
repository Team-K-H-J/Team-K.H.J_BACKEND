CREATE TABLE `State` (
	`device_id`	VARCHAR(24)	NOT NULL,
	`updated_at`	DATETIME	NOT NULL	DEFAULT 현재 시각,
	`state`	VARCHAR(9)	NOT NULL	DEFAULT not_used	COMMENT '중복 불가, 허용값: used, not_used'
);

CREATE TABLE `State_log` (
	`state_log_id`	BIGINT	NOT NULL,
	`device_id`	VARCHAR(24)	NOT NULL	COMMENT 'UN',
	`state`	VARCHAR(15)	NOT NULL	DEFAULT not_subscribed,
	`created_at`	DATETIME	NOT NULL	DEFAULT 현재 시각
);

CREATE TABLE `Devices` (
	`device_id`	VARCHAR(24)	NOT NULL	COMMENT 'UN',
	`device_name`	VARCHAR(24)	NOT NULL	COMMENT '유니크'
);

CREATE TABLE `session` (
	`session`	VARCHAR(255)	NOT NULL,
	`user_id`	binary(16)	NOT NULL	COMMENT 'UN, UUID',
	`created_at`	DATETIME	NOT NULL,
	`expired_at`	DATETIME	NOT NULL
);

CREATE TABLE `Subscribe` (
	`device_id`	VARCHAR(24)	NOT NULL	COMMENT 'UN',
	`user_id`	binary(16)	NOT NULL	COMMENT 'UN, UUID'
);

CREATE TABLE `Users` (
	`user_id`	binary(16)	NOT NULL	COMMENT 'UN, UUID',
	`email`	VARCHAR(255)	NOT NULL	COMMENT 'UN',
	`password_hash`	VARCHAR(255)	NOT NULL	COMMENT 'UN',
	`name`	VARCHAR(24)	NOT NULL,
	`number`	VARCHAR(4)	NOT NULL	COMMENT 'UN'
);

CREATE TABLE `Favorite` (
	`device_id`	VARCHAR(24)	NOT NULL,
	`user_id`	binary(16)	NOT NULL	COMMENT 'UN, UUID'
);

CREATE TABLE `Subscribe_log` (
	`id`	binary(16)	NOT NULL,
	`created_at`	DATETIME	NOT NULL	DEFAULT CURRENT_TIMESTAMP,
	`state`	VARCHAR(15)	NOT NULL	DEFAULT not_subscribed,
	`user_id`	binary(16)	NOT NULL	COMMENT 'UN, UUID',
	`device_id`	VARCHAR(24)	NOT NULL	COMMENT 'UN'
);

ALTER TABLE `State` ADD CONSTRAINT `PK_STATE` PRIMARY KEY (
	`device_id`
);

ALTER TABLE `State_log` ADD CONSTRAINT `PK_STATE_LOG` PRIMARY KEY (
	`state_log_id`
);

ALTER TABLE `Devices` ADD CONSTRAINT `PK_DEVICES` PRIMARY KEY (
	`device_id`
);

ALTER TABLE `session` ADD CONSTRAINT `PK_SESSION` PRIMARY KEY (
	`session`
);

ALTER TABLE `Subscribe` ADD CONSTRAINT `PK_SUBSCRIBE` PRIMARY KEY (
	`device_id`,
	`user_id`
);

ALTER TABLE `Users` ADD CONSTRAINT `PK_USERS` PRIMARY KEY (
	`user_id`
);

ALTER TABLE `Favorite` ADD CONSTRAINT `PK_FAVORITE` PRIMARY KEY (
	`device_id`,
	`user_id`
);

ALTER TABLE `Subscribe_log` ADD CONSTRAINT `PK_SUBSCRIBE_LOG` PRIMARY KEY (
	`id`
);

ALTER TABLE `State` ADD CONSTRAINT `FK_Devices_TO_State_1` FOREIGN KEY (
	`device_id`
)
REFERENCES `Devices` (
	`device_id`
);

ALTER TABLE `State_log` ADD CONSTRAINT `FK_Devices_TO_State_log_1` FOREIGN KEY (
	`device_id`
)
REFERENCES `Devices` (
	`device_id`
);

ALTER TABLE `session` ADD CONSTRAINT `FK_Users_TO_session_1` FOREIGN KEY (
	`user_id`
)
REFERENCES `Users` (
	`user_id`
);

ALTER TABLE `Subscribe` ADD CONSTRAINT `FK_Devices_TO_Subscribe_1` FOREIGN KEY (
	`device_id`
)
REFERENCES `Devices` (
	`device_id`
);

ALTER TABLE `Subscribe` ADD CONSTRAINT `FK_Users_TO_Subscribe_1` FOREIGN KEY (
	`user_id`
)
REFERENCES `Users` (
	`user_id`
);

ALTER TABLE `Favorite` ADD CONSTRAINT `FK_Devices_TO_Favorite_1` FOREIGN KEY (
	`device_id`
)
REFERENCES `Devices` (
	`device_id`
);

ALTER TABLE `Favorite` ADD CONSTRAINT `FK_Users_TO_Favorite_1` FOREIGN KEY (
	`user_id`
)
REFERENCES `Users` (
	`user_id`
);

ALTER TABLE `Subscribe_log` ADD CONSTRAINT `FK_Users_TO_Subscribe_log_1` FOREIGN KEY (
	`user_id`
)
REFERENCES `Users` (
	`user_id`
);

ALTER TABLE `Subscribe_log` ADD CONSTRAINT `FK_Devices_TO_Subscribe_log_1` FOREIGN KEY (
	`device_id`
)
REFERENCES `Devices` (
	`device_id`
);

