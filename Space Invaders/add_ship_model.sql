SET @has_ship_model = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'players'
      AND COLUMN_NAME = 'ship_model'
);

SET @ddl = IF(
    @has_ship_model = 0,
    'ALTER TABLE players ADD COLUMN ship_model VARCHAR(20) NOT NULL DEFAULT ''falcon''',
    'SELECT ''ship_model already exists - nothing to do'' AS info'
);

PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
