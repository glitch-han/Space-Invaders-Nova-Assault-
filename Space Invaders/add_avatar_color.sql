SET @has_avatar_color = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'players'
      AND COLUMN_NAME = 'avatar_color'
);

SET @ddl = IF(
    @has_avatar_color = 0,
    'ALTER TABLE players ADD COLUMN avatar_color VARCHAR(20) NOT NULL DEFAULT ''white''',
    'SELECT ''avatar_color already exists - nothing to do'' AS info'
);

PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
