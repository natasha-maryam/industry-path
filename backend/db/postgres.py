import os
from contextlib import contextmanager
from dataclasses import dataclass

import psycopg2
from psycopg2.extras import RealDictCursor


@dataclass(frozen=True)
class PostgresConfig:
    host: str
    port: int
    database: str
    user: str
    password: str


class PostgresClient:
    def __init__(self) -> None:
        self.config = PostgresConfig(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "crosslayerx"),
            user=os.getenv("POSTGRES_USER", "crosslayer"),
            password=os.getenv("POSTGRES_PASSWORD", "crosslayer"),
        )

    @contextmanager
    def connection(self):
        conn = psycopg2.connect(
            host=self.config.host,
            port=self.config.port,
            dbname=self.config.database,
            user=self.config.user,
            password=self.config.password,
        )
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_schema(self) -> None:
        create_projects_sql = """
        CREATE TABLE IF NOT EXISTS projects (
          id UUID PRIMARY KEY,
          name VARCHAR NOT NULL,
          description TEXT NULL,
          status VARCHAR DEFAULT 'draft',
          created_at TIMESTAMP,
          updated_at TIMESTAMP
        );
        """

        create_files_sql = """
        CREATE TABLE IF NOT EXISTS project_files (
          id UUID PRIMARY KEY,
          project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
          original_name VARCHAR NOT NULL,
          stored_name VARCHAR NOT NULL,
          file_type VARCHAR NOT NULL,
          file_path TEXT NOT NULL,
          file_size BIGINT NULL,
          upload_status VARCHAR DEFAULT 'uploaded',
          uploaded_at TIMESTAMP,
          document_type VARCHAR DEFAULT 'unknown_document'
        );
        """

        create_parse_jobs_sql = """
        CREATE TABLE IF NOT EXISTS parse_jobs (
          id UUID PRIMARY KEY,
          project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
          parse_batch_id UUID NULL,
          status VARCHAR NOT NULL,
          current_stage VARCHAR NULL,
          stage_message TEXT NULL,
          progress_percent NUMERIC DEFAULT 0,
          nodes_count INTEGER DEFAULT 0,
          edges_count INTEGER DEFAULT 0,
          started_at TIMESTAMP,
          completed_at TIMESTAMP,
          error_message TEXT NULL
        );
        """

        alter_project_files_document_type_sql = """
        ALTER TABLE project_files
        ADD COLUMN IF NOT EXISTS document_type VARCHAR DEFAULT 'unknown_document';
        """

        alter_parse_jobs_parse_batch_sql = """
        ALTER TABLE parse_jobs
        ADD COLUMN IF NOT EXISTS parse_batch_id UUID NULL;
        """

        alter_parse_jobs_current_stage_sql = """
        ALTER TABLE parse_jobs
        ADD COLUMN IF NOT EXISTS current_stage VARCHAR NULL;
        """

        alter_parse_jobs_stage_message_sql = """
        ALTER TABLE parse_jobs
        ADD COLUMN IF NOT EXISTS stage_message TEXT NULL;
        """

        alter_parse_jobs_progress_percent_sql = """
        ALTER TABLE parse_jobs
        ADD COLUMN IF NOT EXISTS progress_percent NUMERIC DEFAULT 0;
        """

        create_parse_batches_sql = """
        CREATE TABLE IF NOT EXISTS parse_batches (
          id UUID PRIMARY KEY,
          project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
          batch_name VARCHAR NOT NULL,
          status VARCHAR NOT NULL,
          started_at TIMESTAMP,
          completed_at TIMESTAMP,
          summary JSONB DEFAULT '{}'::jsonb,
          warnings JSONB DEFAULT '[]'::jsonb
        );
        """

        create_parse_batch_files_sql = """
        CREATE TABLE IF NOT EXISTS parse_batch_files (
          id UUID PRIMARY KEY,
          parse_batch_id UUID REFERENCES parse_batches(id) ON DELETE CASCADE,
          file_id UUID REFERENCES project_files(id) ON DELETE CASCADE,
          document_type VARCHAR NOT NULL,
          created_at TIMESTAMP
        );
        """

        create_extracted_metadata_sql = """
        CREATE TABLE IF NOT EXISTS extracted_metadata (
          id UUID PRIMARY KEY,
          project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
          parse_batch_id UUID REFERENCES parse_batches(id) ON DELETE CASCADE,
          source_file_id UUID NULL REFERENCES project_files(id) ON DELETE SET NULL,
          category VARCHAR NOT NULL,
          tag VARCHAR NULL,
          payload JSONB NOT NULL,
          created_at TIMESTAMP
        );
        """

        create_narrative_rules_sql = """
        CREATE TABLE IF NOT EXISTS narrative_rules (
          id UUID PRIMARY KEY,
          project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
          parse_batch_id UUID REFERENCES parse_batches(id) ON DELETE CASCADE,
          rule_type VARCHAR NOT NULL,
          equipment_tag VARCHAR NULL,
          description TEXT NOT NULL,
          payload JSONB DEFAULT '{}'::jsonb,
          created_at TIMESTAMP
        );
        """

        create_parse_conflicts_sql = """
        CREATE TABLE IF NOT EXISTS parse_conflicts (
          id UUID PRIMARY KEY,
          project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
          parse_batch_id UUID REFERENCES parse_batches(id) ON DELETE CASCADE,
          conflict_type VARCHAR NOT NULL,
          tag VARCHAR NULL,
          details TEXT NOT NULL,
          created_at TIMESTAMP
        );
        """

        create_control_loop_definitions_sql = """
        CREATE TABLE IF NOT EXISTS control_loop_definitions (
          id UUID PRIMARY KEY,
          project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
          parse_batch_id UUID REFERENCES parse_batches(id) ON DELETE CASCADE,
          name TEXT NOT NULL,
          source_sentence TEXT NOT NULL,
          page_number INTEGER,
          related_tags JSONB DEFAULT '[]'::jsonb,
          confidence NUMERIC,
          created_at TIMESTAMP
        );
        """

        create_alarm_definitions_sql = """
        CREATE TABLE IF NOT EXISTS alarm_definitions (
          id UUID PRIMARY KEY,
          project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
          parse_batch_id UUID REFERENCES parse_batches(id) ON DELETE CASCADE,
          name TEXT NOT NULL,
          source_sentence TEXT NOT NULL,
          page_number INTEGER,
          related_tags JSONB DEFAULT '[]'::jsonb,
          confidence NUMERIC,
          created_at TIMESTAMP
        );
        """

        create_interlock_definitions_sql = """
        CREATE TABLE IF NOT EXISTS interlock_definitions (
          id UUID PRIMARY KEY,
          project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
          parse_batch_id UUID REFERENCES parse_batches(id) ON DELETE CASCADE,
          name TEXT NOT NULL,
          source_sentence TEXT NOT NULL,
          page_number INTEGER,
          related_tags JSONB DEFAULT '[]'::jsonb,
          confidence NUMERIC,
          created_at TIMESTAMP
        );
        """

        with self.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(create_projects_sql)
                cursor.execute(create_files_sql)
                cursor.execute(create_parse_jobs_sql)
                cursor.execute(alter_project_files_document_type_sql)
                cursor.execute(alter_parse_jobs_parse_batch_sql)
                cursor.execute(alter_parse_jobs_current_stage_sql)
                cursor.execute(alter_parse_jobs_stage_message_sql)
                cursor.execute(alter_parse_jobs_progress_percent_sql)
                cursor.execute(create_parse_batches_sql)
                cursor.execute(create_parse_batch_files_sql)
                cursor.execute(create_extracted_metadata_sql)
                cursor.execute(create_narrative_rules_sql)
                cursor.execute(create_parse_conflicts_sql)
                cursor.execute(create_control_loop_definitions_sql)
                cursor.execute(create_alarm_definitions_sql)
                cursor.execute(create_interlock_definitions_sql)

    def fetch_all(self, sql: str, params: tuple | None = None) -> list[dict]:
        with self.connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql, params)
                return list(cursor.fetchall())

    def fetch_one(self, sql: str, params: tuple | None = None) -> dict | None:
        with self.connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql, params)
                row = cursor.fetchone()
                return dict(row) if row else None

    def execute(self, sql: str, params: tuple | None = None) -> None:
        with self.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)

    def health(self) -> dict[str, str | int]:
        status = "connected"
        try:
            with self.connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
        except Exception as exc:
            status = f"error: {exc}"

        return {
            "backend": "postgres",
            "host": self.config.host,
            "port": self.config.port,
            "database": self.config.database,
            "status": status,
        }


postgres_client = PostgresClient()
