-- DDL for SQLite3

CREATE TABLE IF NOT EXISTS chat_history (
    seq INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
    chat_no INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    model_id INTEGER,
    name TEXT,
    chat_time TEXT NOT NULL,
    moderation_color TEXT,
    moderation_result_original TEXT,
    moderation_sexual_flagged INTEGER,
    moderation_sexual_score REAL,
    moderation_sexual_minors_flagged INTEGER,
    moderation_sexual_minors_score REAL,
    is_updated INTEGER NOT NULL DEFAULT 0,
    is_deleted INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_chat_history_chat_no ON chat_history (chat_no);

CREATE TABLE IF NOT EXISTS chat_info (
    chat_no INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    chat_uuid TEXT NOT NULL UNIQUE,
    chat_name TEXT NOT NULL, 
    user_no INTEGER NOT NULL,
    assistant_pic_url TEXT,
    updated_time TEXT NOT NULL,
    is_deleted INTEGER NOT NULL,
    deleted_time TEXT
);
CREATE INDEX idx_chat_info_chat_uuid ON chat_info (chat_uuid);

CREATE TABLE IF NOT EXISTS login_users (
    user_no INTEGER NOT NULL,
    revision INTEGER NOT NULL,
    user_id TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    user_name TEXT NOT NULL,
    roles INTEGER NOT NULL,
    updated_time TEXT NOT NULL,
    PRIMARY KEY (user_no, revision)
);

CREATE TABLE IF NOT EXISTS registration_codes (
    registration_code TEXT PRIMARY KEY,
    remarks TEXT NOT NULL,
    is_used INTEGER NOT NULL,
    issuing_user_no INTEGER NOT NULL,
    issuing_time TEXT NOT NULL,
    expiration_time TEXT NOT NULL,
    register_time TEXT,
    registered_user_no INTEGER,
    is_deleted INTEGER NOT NULL,
    deleted_time TEXT,
    roles INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS login_history (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    user_no INTEGER,
    user_id TEXT NOT NULL,
    login_time TEXT NOT NULL,
    user_agent TEXT NOT NULL,
    remote_ip TEXT NOT NULL,
    is_success INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS system_prompts (
    prompt_id INTEGER NOT NULL,
    revision INTEGER NOT NULL,
    prompt_name TEXT NOT NULL,
    prompt_content TEXT NOT NULL,
    owner_user_no INTEGER NOT NULL,
    is_edit_locked INTEGER NOT NULL,
    is_viewable_by_everyone INTEGER NOT NULL,
    is_editable_by_everyone INTEGER NOT NULL,
    updated_user_no INTEGER NOT NULL,
    updated_time TEXT NOT NULL,
    is_deleted INTEGER NOT NULL,
    PRIMARY KEY (prompt_id, revision)
);

CREATE TABLE IF NOT EXISTS roleplayers (
    roleplayer_no INTEGER NOT NULL,
    revision INTEGER NOT NULL,
    roleplayer_uuid TEXT NOT NULL UNIQUE,
    roleplayer_name TEXT NOT NULL,
    memo TEXT NOT NULL,
    assistant_first INTEGER NOT NULL,
    prompt_id INTEGER NOT NULL,
    prompt_revision INTEGER NOT NULL,
    owner_user_no INTEGER NOT NULL,
    is_edit_locked INTEGER NOT NULL,
    is_viewable_by_everyone INTEGER NOT NULL,
    is_editable_by_everyone INTEGER NOT NULL,
    updated_user_no INTEGER NOT NULL,
    updated_time TEXT NOT NULL,
    is_deleted INTEGER NOT NULL,
    PRIMARY KEY (roleplayer_no, revision)
);

CREATE TABLE IF NOT EXISTS word_replacings (
    seq INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
    chat_no INTEGER NOT NULL,
    is_assistant INTEGER NOT NULL,
    word_client TEXT NOT NULL,
    word_server TEXT NOT NULL, 
    user_no INTEGER NOT NULL,
    updated_time TEXT NOT NULL,
    is_deleted INTEGER NOT NULL,
    deleted_time TEXT
);
CREATE INDEX idx_word_replacings_chat_no ON word_replacings (chat_no);
