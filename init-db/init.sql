CREATE TABLE IF NOT EXISTS short_links (
    id SERIAL PRIMARY KEY,
    short_code VARCHAR(32) UNIQUE NOT NULL,
    original_url VARCHAR(2048) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_short_code ON short_links(short_code);
