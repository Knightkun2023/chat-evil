-- DDL for MySQL

CREATE TABLE IF NOT EXISTS chat_history (
    seq BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT, 
    chat_no INTEGER NOT NULL,
    role VARCHAR(10) NOT NULL,
    content TEXT NOT NULL,
    model_id INTEGER,
    name VARCHAR(50),
    chat_time VARCHAR(17) NOT NULL,
    moderation_color VARCHAR(1),
    moderation_result_original TEXT,
    moderation_sexual_flagged TINYINT,
    moderation_sexual_score FLOAT,
    moderation_sexual_minors_flagged TINYINT,
    moderation_sexual_minors_score FLOAT,
    is_updated TINYINT NOT NULL DEFAULT 0,
    is_deleted TINYINT NOT NULL DEFAULT 0
);
CREATE INDEX idx_chat_history_chat_no ON chat_history (chat_no);

CREATE TABLE IF NOT EXISTS chat_info (
    chat_no INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,
    chat_uuid VARCHAR(40) NOT NULL UNIQUE,
    chat_name VARCHAR(50) NOT NULL, 
    user_no INTEGER NOT NULL,
    assistant_pic_url TEXT,
    updated_time VARCHAR(17) NOT NULL,
    is_deleted TINYINT NOT NULL,
    deleted_time VARCHAR(17)
);
CREATE INDEX idx_chat_info_chat_uuid ON chat_info (chat_uuid);

CREATE TABLE IF NOT EXISTS login_users (
    user_no INTEGER NOT NULL,
    revision INTEGER NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    password_hash VARCHAR(200) NOT NULL,
    user_name VARCHAR(50) NOT NULL,
    roles INTEGER NOT NULL,
    updated_time VARCHAR(17) NOT NULL,
    PRIMARY KEY (user_no, revision)
);

CREATE TABLE IF NOT EXISTS registration_codes (
    registration_code VARCHAR(40) PRIMARY KEY,
    remarks TEXT NOT NULL,
    is_used TINYINT NOT NULL,
    issuing_user_no INTEGER NOT NULL,
    issuing_time VARCHAR(17) NOT NULL,
    expiration_time VARCHAR(17) NOT NULL,
    register_time VARCHAR(17),
    registered_user_no INTEGER,
    is_deleted TINYINT NOT NULL,
    deleted_time VARCHAR(17),
    roles INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS login_history (
    seq INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_no INTEGER,
    user_id VARCHAR(50) NOT NULL,
    login_time VARCHAR(17) NOT NULL,
    user_agent VARCHAR(512) NOT NULL,
    remote_ip VARCHAR(100) NOT NULL,
    is_success TINYINT NOT NULL
);

CREATE TABLE IF NOT EXISTS system_prompts (
    prompt_id INTEGER NOT NULL,
    revision INTEGER NOT NULL,
    prompt_name VARCHAR(50) NOT NULL,
    prompt_content TEXT NOT NULL,
    owner_user_no INTEGER NOT NULL,
    is_edit_locked TINYINT NOT NULL,
    is_viewable_by_everyone TINYINT NOT NULL,
    is_editable_by_everyone TINYINT NOT NULL,
    updated_user_no INTEGER NOT NULL,
    updated_time VARCHAR(17) NOT NULL,
    is_deleted TINYINT NOT NULL,
    PRIMARY KEY (prompt_id, revision)
);

CREATE TABLE IF NOT EXISTS roleplayers (
    roleplayer_no INTEGER NOT NULL,
    revision INTEGER NOT NULL,
    roleplayer_uuid VARCHAR(40) NOT NULL UNIQUE,
    roleplayer_name VARCHAR(50) NOT NULL,
    memo TEXT NOT NULL,
    assistant_first TINYINT NOT NULL,
    prompt_id INTEGER NOT NULL,
    prompt_revision INTEGER NOT NULL,
    owner_user_no INTEGER NOT NULL,
    is_edit_locked TINYINT NOT NULL,
    is_viewable_by_everyone TINYINT NOT NULL,
    is_editable_by_everyone TINYINT NOT NULL,
    updated_user_no INTEGER NOT NULL,
    updated_time VARCHAR(17) NOT NULL,
    is_deleted TINYINT NOT NULL,
    PRIMARY KEY (roleplayer_no, revision)
);

CREATE TABLE IF NOT EXISTS word_replacings (
    seq BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT, 
    chat_no INTEGER NOT NULL,
    is_assistant TINYINT NOT NULL,
    word_client VARCHAR(50) NOT NULL,
    word_server VARCHAR(50) NOT NULL, 
    user_no INTEGER NOT NULL,
    updated_time VARCHAR(17) NOT NULL,
    is_deleted TINYINT NOT NULL,
    deleted_time VARCHAR(17)
);
CREATE INDEX idx_word_replacings_chat_no ON word_replacings (chat_no);
