CREATE TABLE `devices` (
  `device_id` varchar(24) NOT NULL,
  `device_name` varchar(24) NOT NULL,
  PRIMARY KEY (`device_id`),
  UNIQUE KEY `device_name` (`device_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `email_verification` (
  `email` varchar(255) NOT NULL,
  `purpose` varchar(16) NOT NULL,
  `code_hash` varchar(64) NOT NULL,
  `expires_at` datetime(6) NOT NULL,
  `sent_at` datetime(6) NOT NULL,
  `attempts` int NOT NULL,
  `verified_at` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`email`,`purpose`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `login_attempt` (
  `email` varchar(255) NOT NULL,
  `failures` int NOT NULL,
  `locked_until` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `users` (
  `user_id` binary(16) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `name` varchar(24) NOT NULL,
  `number` varchar(4) NOT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `password_hash` (`password_hash`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `device_credential` (
  `device_id` varchar(24) NOT NULL,
  `key_hash` varchar(64) NOT NULL,
  PRIMARY KEY (`device_id`),
  CONSTRAINT `device_credential_ibfk_1` FOREIGN KEY (`device_id`) REFERENCES `devices` (`device_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `device_runtime` (
  `device_id` varchar(24) NOT NULL,
  `unavailable` tinyint(1) NOT NULL,
  `unavailable_reason` varchar(255) DEFAULT NULL,
  `sensor_error` varchar(255) DEFAULT NULL,
  `door_open` tinyint(1) DEFAULT NULL,
  `last_seen_at` datetime(6) DEFAULT NULL,
  `last_measured_at` datetime(6) DEFAULT NULL,
  `cycle_status` varchar(16) NOT NULL,
  `expected_seconds` int NOT NULL,
  `last_door_measured_at` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`device_id`),
  CONSTRAINT `device_runtime_ibfk_1` FOREIGN KEY (`device_id`) REFERENCES `devices` (`device_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `drying_cycle` (
  `id` binary(16) NOT NULL,
  `device_id` varchar(24) NOT NULL,
  `started_at` datetime(6) NOT NULL,
  `ended_at` datetime(6) DEFAULT NULL,
  `collected_at` datetime(6) DEFAULT NULL,
  `outcome` varchar(16) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_cycle_device_started` (`device_id`,`started_at`),
  CONSTRAINT `drying_cycle_ibfk_1` FOREIGN KEY (`device_id`) REFERENCES `devices` (`device_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `favorite` (
  `device_id` varchar(24) NOT NULL,
  `user_id` binary(16) NOT NULL,
  PRIMARY KEY (`device_id`,`user_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `favorite_ibfk_1` FOREIGN KEY (`device_id`) REFERENCES `devices` (`device_id`),
  CONSTRAINT `favorite_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `inquiry` (
  `id` binary(16) NOT NULL,
  `user_id` binary(16) NOT NULL,
  `device_id` varchar(24) DEFAULT NULL,
  `error_type` varchar(64) NOT NULL,
  `title` varchar(200) NOT NULL,
  `content` text NOT NULL,
  `status` varchar(16) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `device_id` (`device_id`),
  KEY `user_id` (`user_id`),
  KEY `ix_inquiry_status_created` (`status`,`created_at`),
  CONSTRAINT `inquiry_ibfk_1` FOREIGN KEY (`device_id`) REFERENCES `devices` (`device_id`),
  CONSTRAINT `inquiry_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `notice` (
  `id` binary(16) NOT NULL,
  `author_id` binary(16) DEFAULT NULL,
  `title` varchar(200) NOT NULL,
  `content` text NOT NULL,
  `pinned` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `author_id` (`author_id`),
  CONSTRAINT `notice_ibfk_1` FOREIGN KEY (`author_id`) REFERENCES `users` (`user_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `session` (
  `session_id` varchar(255) NOT NULL,
  `user_id` binary(16) NOT NULL,
  `created_at` datetime(6) NOT NULL DEFAULT (now()),
  `expired_at` datetime(6) NOT NULL,
  `purpose` varchar(16) NOT NULL DEFAULT 'login',
  `password_verified_at` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`session_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `session_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `state` (
  `device_id` varchar(24) NOT NULL,
  `state` varchar(9) NOT NULL DEFAULT 'not_used',
  `updated_at` datetime(6) NOT NULL DEFAULT (now()),
  PRIMARY KEY (`device_id`),
  CONSTRAINT `state_ibfk_1` FOREIGN KEY (`device_id`) REFERENCES `devices` (`device_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `state_log` (
  `state_log_id` bigint NOT NULL AUTO_INCREMENT,
  `device_id` varchar(24) NOT NULL,
  `state` varchar(15) NOT NULL DEFAULT 'not_used',
  `created_at` datetime(6) NOT NULL DEFAULT (now()),
  PRIMARY KEY (`state_log_id`),
  KEY `ix_state_log_device_time_state` (`device_id`,`created_at`,`state`),
  CONSTRAINT `state_log_ibfk_1` FOREIGN KEY (`device_id`) REFERENCES `devices` (`device_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `subscribe` (
  `device_id` varchar(24) NOT NULL,
  `user_id` binary(16) NOT NULL,
  PRIMARY KEY (`device_id`,`user_id`),
  KEY `ix_subscribe_user_device` (`user_id`,`device_id`),
  CONSTRAINT `subscribe_ibfk_1` FOREIGN KEY (`device_id`) REFERENCES `devices` (`device_id`),
  CONSTRAINT `subscribe_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `subscribe_log` (
  `id` binary(16) NOT NULL,
  `device_id` varchar(24) NOT NULL,
  `user_id` binary(16) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `state` varchar(15) NOT NULL DEFAULT 'not_subscribed',
  PRIMARY KEY (`id`),
  KEY `device_id` (`device_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `subscribe_log_ibfk_1` FOREIGN KEY (`device_id`) REFERENCES `devices` (`device_id`),
  CONSTRAINT `subscribe_log_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `telemetry_event` (
  `device_id` varchar(24) NOT NULL,
  `event_id` varchar(64) NOT NULL,
  `measured_at` datetime(6) NOT NULL,
  `received_at` datetime(6) NOT NULL,
  `payload_hash` varchar(64) NOT NULL,
  `payload` json NOT NULL,
  PRIMARY KEY (`device_id`,`event_id`),
  KEY `ix_telemetry_device_measured` (`device_id`,`measured_at`),
  CONSTRAINT `telemetry_event_ibfk_1` FOREIGN KEY (`device_id`) REFERENCES `devices` (`device_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `user_profile` (
  `user_id` binary(16) NOT NULL,
  `image_url` varchar(2048) DEFAULT NULL,
  PRIMARY KEY (`user_id`),
  CONSTRAINT `user_profile_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `user_settings` (
  `user_id` binary(16) NOT NULL,
  `notifications_enabled` tinyint(1) NOT NULL,
  `vibration_enabled` tinyint(1) NOT NULL,
  `theme` varchar(8) NOT NULL,
  `completed` tinyint(1) NOT NULL,
  `paused` tinyint(1) NOT NULL,
  `stopped` tinyint(1) NOT NULL,
  `uncollected` tinyint(1) NOT NULL,
  PRIMARY KEY (`user_id`),
  CONSTRAINT `user_settings_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `cycle_user` (
  `cycle_id` binary(16) NOT NULL,
  `user_id` binary(16) NOT NULL,
  `subscribed_at` datetime(6) NOT NULL,
  PRIMARY KEY (`cycle_id`,`user_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `cycle_user_ibfk_1` FOREIGN KEY (`cycle_id`) REFERENCES `drying_cycle` (`id`),
  CONSTRAINT `cycle_user_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `notification` (
  `id` binary(16) NOT NULL,
  `user_id` binary(16) NOT NULL,
  `device_id` varchar(24) NOT NULL,
  `cycle_id` binary(16) DEFAULT NULL,
  `event_key` varchar(128) NOT NULL,
  `kind` varchar(16) NOT NULL,
  `message` varchar(255) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `read_at` datetime(6) DEFAULT NULL,
  `delivered_at` datetime(6) DEFAULT NULL,
  `delivery_attempts` int NOT NULL,
  `next_attempt_at` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_notification_user_event` (`user_id`,`event_key`),
  KEY `cycle_id` (`cycle_id`),
  KEY `device_id` (`device_id`),
  KEY `ix_notification_user_id` (`user_id`),
  CONSTRAINT `notification_ibfk_1` FOREIGN KEY (`cycle_id`) REFERENCES `drying_cycle` (`id`),
  CONSTRAINT `notification_ibfk_2` FOREIGN KEY (`device_id`) REFERENCES `devices` (`device_id`),
  CONSTRAINT `notification_ibfk_3` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `push_token` (
  `token` varchar(512) NOT NULL,
  `user_id` binary(16) NOT NULL,
  `session_id` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`token`),
  KEY `ix_push_token_user_id` (`user_id`),
  KEY `session_id` (`session_id`),
  CONSTRAINT `push_token_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `push_token_ibfk_2` FOREIGN KEY (`session_id`) REFERENCES `session` (`session_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `push_delivery` (
  `notification_id` binary(16) NOT NULL,
  `token` varchar(512) NOT NULL,
  `delivered_at` datetime(6) NOT NULL,
  PRIMARY KEY (`notification_id`,`token`),
  KEY `token` (`token`),
  CONSTRAINT `push_delivery_ibfk_1` FOREIGN KEY (`notification_id`) REFERENCES `notification` (`id`) ON DELETE CASCADE,
  CONSTRAINT `push_delivery_ibfk_2` FOREIGN KEY (`token`) REFERENCES `push_token` (`token`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
