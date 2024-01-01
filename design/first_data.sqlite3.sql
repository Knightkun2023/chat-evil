INSERT INTO registration_codes (
    registration_code,
    remarks,
    is_used,
    issuing_user_no,
    issuing_time,
    expiration_time,
    is_deleted,
    roles
)
VALUES (
    'registration_code',
    '初回登録用',
    0,
    0,
    strftime('%Y%m%d%H%M%S', 'now', '+9 hours') || '000',
    strftime('%Y%m%d%H%M%S', 'now', '+10 hours') || '000',
    0,
    0
);