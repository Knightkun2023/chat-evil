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
    LEFT(DATE_FORMAT(NOW(), '%Y%m%d%H%i%s%f'), 17),
    LEFT(DATE_FORMAT(NOW() + INTERVAL 1 hour, '%Y%m%d%H%i%s%f'), 17),
    0,
    0
);