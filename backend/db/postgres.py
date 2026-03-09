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

        create_logic_runs_sql = """
        CREATE TABLE IF NOT EXISTS logic_runs (
          id UUID PRIMARY KEY,
          project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
          project_version INTEGER DEFAULT 1,
          rules_count INTEGER DEFAULT 0,
          warnings_count INTEGER DEFAULT 0,
          status VARCHAR NOT NULL,
          st_preview TEXT DEFAULT '',
          generator_version VARCHAR DEFAULT 'deterministic-v1',
          warnings JSONB DEFAULT '[]'::jsonb,
          created_at TIMESTAMP
        );
        """

        create_logic_warnings_sql = """
        CREATE TABLE IF NOT EXISTS logic_warnings (
          id UUID PRIMARY KEY,
          project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
          logic_run_id UUID REFERENCES logic_runs(id) ON DELETE CASCADE,
          warning_type VARCHAR NOT NULL,
          message TEXT NOT NULL,
          source_sentence TEXT NULL,
          created_at TIMESTAMP
        );
        """

        create_control_rules_sql = """
        CREATE TABLE IF NOT EXISTS control_rules (
          id UUID PRIMARY KEY,
          project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
          logic_run_id UUID NULL REFERENCES logic_runs(id) ON DELETE SET NULL,
          rule_group VARCHAR DEFAULT 'general',
          rule_type VARCHAR NOT NULL,
          source_tag VARCHAR NULL,
          source_type VARCHAR NULL,
          condition_kind VARCHAR NULL,
          operator VARCHAR NULL,
          threshold VARCHAR NULL,
          threshold_name VARCHAR NULL,
          action VARCHAR NOT NULL,
          target_tag VARCHAR NULL,
          target_type VARCHAR NULL,
          secondary_target_tag VARCHAR NULL,
          mode VARCHAR NULL,
          priority INTEGER DEFAULT 50,
          confidence NUMERIC,
          source_sentence TEXT NOT NULL,
          source_page INTEGER NULL,
          section_heading VARCHAR NULL,
          explanation TEXT NULL,
          resolution_strategy VARCHAR DEFAULT 'exact_tag',
          is_symbolic BOOLEAN DEFAULT FALSE,
          renderable BOOLEAN DEFAULT TRUE,
          unresolved_tokens JSONB DEFAULT '[]'::jsonb,
          comments JSONB DEFAULT '[]'::jsonb,
          display_text TEXT NOT NULL,
          st_preview TEXT NOT NULL,
          source_references JSONB DEFAULT '[]'::jsonb,
          created_at TIMESTAMP
        );
        """

        alter_control_rules_logic_run_id_sql = """
        ALTER TABLE control_rules
        ADD COLUMN IF NOT EXISTS logic_run_id UUID NULL REFERENCES logic_runs(id) ON DELETE SET NULL;
        """

        alter_control_rules_source_type_sql = """
        ALTER TABLE control_rules
        ADD COLUMN IF NOT EXISTS source_type VARCHAR NULL;
        """

        alter_control_rules_target_type_sql = """
        ALTER TABLE control_rules
        ADD COLUMN IF NOT EXISTS target_type VARCHAR NULL;
        """

        alter_control_rules_display_text_sql = """
        ALTER TABLE control_rules
        ADD COLUMN IF NOT EXISTS display_text TEXT;
        """

        alter_control_rules_st_preview_sql = """
        ALTER TABLE control_rules
        ADD COLUMN IF NOT EXISTS st_preview TEXT;
        """

        alter_control_rules_source_references_sql = """
        ALTER TABLE control_rules
        ADD COLUMN IF NOT EXISTS source_references JSONB DEFAULT '[]'::jsonb;
        """

        alter_control_rules_rule_group_sql = """
        ALTER TABLE control_rules
        ADD COLUMN IF NOT EXISTS rule_group VARCHAR DEFAULT 'general';
        """

        alter_control_rules_condition_kind_sql = """
        ALTER TABLE control_rules
        ADD COLUMN IF NOT EXISTS condition_kind VARCHAR NULL;
        """

        alter_control_rules_threshold_name_sql = """
        ALTER TABLE control_rules
        ADD COLUMN IF NOT EXISTS threshold_name VARCHAR NULL;
        """

        alter_control_rules_secondary_target_tag_sql = """
        ALTER TABLE control_rules
        ADD COLUMN IF NOT EXISTS secondary_target_tag VARCHAR NULL;
        """

        alter_control_rules_priority_sql = """
        ALTER TABLE control_rules
        ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 50;
        """

        alter_control_rules_renderable_sql = """
        ALTER TABLE control_rules
        ADD COLUMN IF NOT EXISTS renderable BOOLEAN DEFAULT TRUE;
        """

        alter_control_rules_unresolved_tokens_sql = """
        ALTER TABLE control_rules
        ADD COLUMN IF NOT EXISTS unresolved_tokens JSONB DEFAULT '[]'::jsonb;
        """

        alter_control_rules_comments_sql = """
        ALTER TABLE control_rules
        ADD COLUMN IF NOT EXISTS comments JSONB DEFAULT '[]'::jsonb;
        """

        alter_control_rules_is_symbolic_sql = """
        ALTER TABLE control_rules
        ADD COLUMN IF NOT EXISTS is_symbolic BOOLEAN DEFAULT FALSE;
        """

        alter_control_rules_resolution_strategy_sql = """
        ALTER TABLE control_rules
        ADD COLUMN IF NOT EXISTS resolution_strategy VARCHAR DEFAULT 'exact_tag';
        """

        alter_logic_runs_warnings_sql = """
        ALTER TABLE logic_runs
        ADD COLUMN IF NOT EXISTS warnings JSONB DEFAULT '[]'::jsonb;
        """

        alter_logic_runs_project_version_sql = """
        ALTER TABLE logic_runs
        ADD COLUMN IF NOT EXISTS project_version INTEGER DEFAULT 1;
        """

        alter_logic_runs_warnings_count_sql = """
        ALTER TABLE logic_runs
        ADD COLUMN IF NOT EXISTS warnings_count INTEGER DEFAULT 0;
        """

        alter_logic_runs_st_preview_sql = """
        ALTER TABLE logic_runs
        ADD COLUMN IF NOT EXISTS st_preview TEXT DEFAULT '';
        """

        alter_logic_runs_generator_version_sql = """
        ALTER TABLE logic_runs
        ADD COLUMN IF NOT EXISTS generator_version VARCHAR DEFAULT 'deterministic-v1';
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
                cursor.execute(create_logic_runs_sql)
                cursor.execute(create_logic_warnings_sql)
                cursor.execute(create_control_rules_sql)
                cursor.execute(alter_control_rules_logic_run_id_sql)
                cursor.execute(alter_control_rules_source_type_sql)
                cursor.execute(alter_control_rules_target_type_sql)
                cursor.execute(alter_control_rules_display_text_sql)
                cursor.execute(alter_control_rules_st_preview_sql)
                cursor.execute(alter_control_rules_source_references_sql)
                cursor.execute(alter_control_rules_rule_group_sql)
                cursor.execute(alter_control_rules_condition_kind_sql)
                cursor.execute(alter_control_rules_threshold_name_sql)
                cursor.execute(alter_control_rules_secondary_target_tag_sql)
                cursor.execute(alter_control_rules_priority_sql)
                cursor.execute(alter_control_rules_renderable_sql)
                cursor.execute(alter_control_rules_unresolved_tokens_sql)
                cursor.execute(alter_control_rules_comments_sql)
                cursor.execute(alter_control_rules_is_symbolic_sql)
                cursor.execute(alter_control_rules_resolution_strategy_sql)
                cursor.execute(alter_logic_runs_warnings_sql)
                cursor.execute(alter_logic_runs_project_version_sql)
                cursor.execute(alter_logic_runs_warnings_count_sql)
                cursor.execute(alter_logic_runs_st_preview_sql)
                cursor.execute(alter_logic_runs_generator_version_sql)

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
