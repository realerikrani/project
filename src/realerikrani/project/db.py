CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS project (
    name TEXT NOT NULL CHECK(
        length("name") <= 100 AND
        length("name") >= 1
    ),
    id TEXT NOT NULL CHECK(
        length("id") = 36
    ),
    created_at_us INTEGER NOT NULL,
    PRIMARY KEY(id) ON CONFLICT FAIL
) WITHOUT ROWID;

CREATE INDEX IF NOT EXISTS project_page_idx
ON project(created_at_us DESC, id DESC);

CREATE TABLE IF NOT EXISTS public_key (
    pem TEXT NOT NULL UNIQUE CHECK(
        length("pem") <= 1000 AND
        length("pem") >= 1
    ),
    created_at INTEGER NOT NULL,
    project_id TEXT NOT NULL,
    id TEXT NOT NULL CHECK(
        length("id") = 36
    ),
    FOREIGN KEY(project_id) REFERENCES project(id) ON DELETE CASCADE,
    PRIMARY KEY (id) ON CONFLICT FAIL
) WITHOUT ROWID;

CREATE UNIQUE INDEX IF NOT EXISTS idx_public_key_project_id_created_at
ON public_key(project_id, created_at DESC);

CREATE TABLE group_project (
    group_id TEXT NOT NULL,
    project_id TEXT NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    PRIMARY KEY (group_id, project_id)
) WITHOUT ROWID;
"""
