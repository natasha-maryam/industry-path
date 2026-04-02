from __future__ import annotations

import logging
import os
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor


logger = logging.getLogger(__name__)


def _getenv_first(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value and value.strip():
            return value.strip()
    return None


def _get_database_url() -> str | None:
    return _getenv_first("DATABASE_URL")


def _get_postgres_connection_kwargs() -> dict[str, str | int]:
    host = _getenv_first("POSTGRES_HOST", "PGHOST") or "localhost"
    port = int(_getenv_first("POSTGRES_PORT", "PGPORT") or 5432)
    dbname = _getenv_first("POSTGRES_DB", "PGDATABASE")
    user = _getenv_first("POSTGRES_USER", "PGUSER")
    password = _getenv_first("POSTGRES_PASSWORD", "PGPASSWORD")

    if not all([dbname, user, password]):
        raise RuntimeError(
            "PostgreSQL configuration is missing. Set DATABASE_URL or provide "
            "POSTGRES_DB/PGDATABASE, POSTGRES_USER/PGUSER, and "
            "POSTGRES_PASSWORD/PGPASSWORD. POSTGRES_HOST/PGHOST and "
            "POSTGRES_PORT/PGPORT are optional and default to localhost:5432."
        )

    return {
        "host": host,
        "port": port,
        "dbname": dbname,
        "user": user,
        "password": password,
    }


class PostgresClient:
    def __init__(self) -> None:
        pass

    @contextmanager
    def connection(self):
        database_url = _get_database_url()
        if database_url:
            conn = psycopg2.connect(database_url)
        else:
            conn = psycopg2.connect(**_get_postgres_connection_kwargs())
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_schema(self) -> None:
        logger.info("initializing postgres schema")
        create_projects_sql = """
        CREATE TABLE IF NOT EXISTS projects (
          id UUID PRIMARY KEY,
          name VARCHAR NOT NULL,
          industry VARCHAR DEFAULT 'general',
          description TEXT NULL,
          plc_runtime VARCHAR DEFAULT 'beremiz',
          owner VARCHAR DEFAULT 'system',
          status VARCHAR DEFAULT 'draft',
          active_version INTEGER DEFAULT 1,
          created_at TIMESTAMP,
          updated_at TIMESTAMP
        );
        """

        alter_projects_plc_runtime_sql = """
        ALTER TABLE projects
        ADD COLUMN IF NOT EXISTS plc_runtime VARCHAR DEFAULT 'beremiz';
        """

        alter_projects_industry_sql = """
        ALTER TABLE projects
        ADD COLUMN IF NOT EXISTS industry VARCHAR DEFAULT 'general';
        """

        alter_projects_owner_sql = """
        ALTER TABLE projects
        ADD COLUMN IF NOT EXISTS owner VARCHAR DEFAULT 'system';
        """

        alter_projects_active_version_sql = """
        ALTER TABLE projects
        ADD COLUMN IF NOT EXISTS active_version INTEGER DEFAULT 1;
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

        create_io_mapping_versions_sql = """
        CREATE TABLE IF NOT EXISTS io_mapping_versions (
          id UUID PRIMARY KEY,
          project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
          version_number INTEGER NOT NULL,
          is_active BOOLEAN DEFAULT FALSE,
          status VARCHAR NOT NULL,
          summary JSONB DEFAULT '{}'::jsonb,
          artifact_path TEXT NULL,
          created_by VARCHAR DEFAULT 'system',
          generated_at TIMESTAMP,
          UNIQUE (project_id, version_number)
        );
        """

        create_io_mappings_sql = """
        CREATE TABLE IF NOT EXISTS io_mappings (
          id UUID PRIMARY KEY,
          project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
          version_id UUID REFERENCES io_mapping_versions(id) ON DELETE CASCADE,
          tag VARCHAR NOT NULL,
          device_type VARCHAR NOT NULL,
          signal_type VARCHAR NOT NULL,
          io_type VARCHAR NOT NULL,
          plc_id VARCHAR NOT NULL,
          slot INTEGER NOT NULL,
          channel INTEGER NOT NULL,
          description TEXT DEFAULT '',
          equipment VARCHAR NULL,
          created_at TIMESTAMP,
          UNIQUE (project_id, version_id, tag)
        );
        """

        create_io_mapping_issues_sql = """
        CREATE TABLE IF NOT EXISTS io_mapping_issues (
          id UUID PRIMARY KEY,
          project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
          version_id UUID REFERENCES io_mapping_versions(id) ON DELETE CASCADE,
          code VARCHAR NOT NULL,
          severity VARCHAR NOT NULL,
          message TEXT NOT NULL,
          tag VARCHAR NULL,
          created_at TIMESTAMP
        );
        """

        create_io_mapping_versions_project_idx_sql = """
        CREATE INDEX IF NOT EXISTS idx_io_mapping_versions_project
          ON io_mapping_versions(project_id, generated_at DESC);
        """

        create_io_mapping_versions_active_unique_sql = """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_io_mapping_versions_active_unique
          ON io_mapping_versions(project_id)
          WHERE is_active = TRUE;
        """

        create_io_mappings_project_version_idx_sql = """
        CREATE INDEX IF NOT EXISTS idx_io_mappings_project_version
          ON io_mappings(project_id, version_id);
        """

        create_io_mapping_issues_project_version_idx_sql = """
        CREATE INDEX IF NOT EXISTS idx_io_mapping_issues_project_version
          ON io_mapping_issues(project_id, version_id);
        """

        create_control_loops_sql = """
        CREATE TABLE IF NOT EXISTS control_loops (
          id UUID PRIMARY KEY,
          project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
          loop_tag VARCHAR NOT NULL,
          sensor_tag VARCHAR NOT NULL,
          actuator_tag VARCHAR NOT NULL,
          process_unit VARCHAR NULL,
          controller_tag VARCHAR NULL,
          loop_type VARCHAR NOT NULL,
          control_strategy VARCHAR NOT NULL,
          setpoint_tag VARCHAR NULL,
          output_tag VARCHAR NULL,
          status VARCHAR NOT NULL,
          confidence NUMERIC NOT NULL,
          created_at TIMESTAMP NOT NULL
        );
        """

        create_control_loops_project_idx_sql = """
        CREATE INDEX IF NOT EXISTS idx_control_loops_project_created
          ON control_loops(project_id, created_at DESC);
        """

        create_control_loops_tag_idx_sql = """
        CREATE INDEX IF NOT EXISTS idx_control_loops_tag
          ON control_loops(loop_tag);
        """

        create_control_loops_project_loop_unique_sql = """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_control_loops_project_loop_unique
          ON control_loops(project_id, loop_tag);
        """

        create_runtime_deployments_sql = """
        CREATE TABLE IF NOT EXISTS runtime_deployments (
          id UUID PRIMARY KEY,
          project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
          target_runtime VARCHAR NOT NULL,
          protocol VARCHAR NOT NULL,
          plc_address VARCHAR NULL,
          io_config_json JSONB DEFAULT '[]'::jsonb,
          deploy_status VARCHAR NOT NULL,
          validation_status VARCHAR NOT NULL,
          deployed_version VARCHAR NULL,
          artifact_path TEXT NULL,
          last_error TEXT NULL,
          started_at TIMESTAMP NOT NULL,
          updated_at TIMESTAMP NOT NULL
        );
        """

        create_runtime_deployments_project_idx_sql = """
        CREATE INDEX IF NOT EXISTS idx_runtime_deployments_project_updated
          ON runtime_deployments(project_id, updated_at DESC);
        """

        create_runtime_deployments_project_unique_sql = """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_runtime_deployments_project_unique
          ON runtime_deployments(project_id);
        """

        create_version_records_sql = """
        CREATE TABLE IF NOT EXISTS version_records (
          id UUID PRIMARY KEY,
          project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
          version_tag VARCHAR NOT NULL,
          commit_hash VARCHAR NOT NULL,
          trigger_source VARCHAR NOT NULL,
          summary TEXT DEFAULT '',
          plant_graph_path TEXT NULL,
          logic_path TEXT NULL,
          io_mapping_path TEXT NULL,
          simulation_results_path TEXT NULL,
          runtime_state_path TEXT NULL,
          created_at TIMESTAMP NOT NULL,
          created_by VARCHAR DEFAULT 'system',
          deployment_tag VARCHAR NULL,
          rollback_available BOOLEAN DEFAULT TRUE,
          UNIQUE (project_id, version_tag)
        );
        """

        create_version_records_project_idx_sql = """
        CREATE INDEX IF NOT EXISTS idx_version_records_project_created
          ON version_records(project_id, created_at DESC);
        """

        create_plant_genie_ai_connectors_sql = """
        CREATE TABLE IF NOT EXISTS plant_genie_ai_connectors (
          id UUID PRIMARY KEY,
          user_id VARCHAR NOT NULL,
          name VARCHAR NOT NULL,
          provider VARCHAR NOT NULL,
          api_key_encrypted TEXT NOT NULL,
          model VARCHAR NULL,
          provider_label VARCHAR NULL,
          notes TEXT NULL,
          is_active BOOLEAN DEFAULT FALSE,
          health_status VARCHAR DEFAULT 'unknown',
          health_message TEXT NULL,
          last_tested_at TIMESTAMP NULL,
          created_at TIMESTAMP NOT NULL,
          updated_at TIMESTAMP NOT NULL
        );
        """

        create_plant_genie_ai_connectors_user_idx_sql = """
        CREATE INDEX IF NOT EXISTS idx_plant_genie_ai_connectors_user_updated
          ON plant_genie_ai_connectors(user_id, updated_at DESC);
        """

        create_plant_genie_ai_connectors_active_unique_sql = """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_plant_genie_ai_connectors_active_unique
          ON plant_genie_ai_connectors(user_id)
          WHERE is_active = TRUE;
        """

        create_plant_genie_plant_data_connectors_sql = """
        CREATE TABLE IF NOT EXISTS plant_genie_plant_data_connectors (
          id UUID PRIMARY KEY,
          user_id VARCHAR NOT NULL,
          name VARCHAR NOT NULL,
          connector_type VARCHAR NOT NULL,
          poll_interval_ms INTEGER NOT NULL DEFAULT 5000,
          config_json TEXT NOT NULL,
          secrets_encrypted TEXT NULL,
          enabled BOOLEAN NOT NULL DEFAULT FALSE,
          running BOOLEAN NOT NULL DEFAULT FALSE,
          healthy BOOLEAN NOT NULL DEFAULT FALSE,
          last_update TIMESTAMP NULL,
          last_tested_at TIMESTAMP NULL,
          last_error TEXT NULL,
          created_at TIMESTAMP NOT NULL,
          updated_at TIMESTAMP NOT NULL
        );
        """

        create_plant_genie_plant_data_connectors_user_idx_sql = """
        CREATE INDEX IF NOT EXISTS idx_plant_genie_plant_data_connectors_user_updated
          ON plant_genie_plant_data_connectors(user_id, updated_at DESC);
        """

        create_plant_genie_plant_data_connectors_enabled_idx_sql = """
        CREATE INDEX IF NOT EXISTS idx_plant_genie_plant_data_connectors_enabled
          ON plant_genie_plant_data_connectors(enabled, updated_at DESC);
        """

        statements: list[tuple[str, str]] = [
            ("create projects table", create_projects_sql),
            ("alter projects industry column", alter_projects_industry_sql),
            ("alter projects plc_runtime column", alter_projects_plc_runtime_sql),
            ("alter projects owner column", alter_projects_owner_sql),
            ("alter projects active_version column", alter_projects_active_version_sql),
            ("create project_files table", create_files_sql),
            ("create parse_jobs table", create_parse_jobs_sql),
            ("alter project_files document_type column", alter_project_files_document_type_sql),
            ("alter parse_jobs parse_batch_id column", alter_parse_jobs_parse_batch_sql),
            ("alter parse_jobs current_stage column", alter_parse_jobs_current_stage_sql),
            ("alter parse_jobs stage_message column", alter_parse_jobs_stage_message_sql),
            ("alter parse_jobs progress_percent column", alter_parse_jobs_progress_percent_sql),
            ("create parse_batches table", create_parse_batches_sql),
            ("create parse_batch_files table", create_parse_batch_files_sql),
            ("create extracted_metadata table", create_extracted_metadata_sql),
            ("create narrative_rules table", create_narrative_rules_sql),
            ("create parse_conflicts table", create_parse_conflicts_sql),
            ("create control_loop_definitions table", create_control_loop_definitions_sql),
            ("create alarm_definitions table", create_alarm_definitions_sql),
            ("create interlock_definitions table", create_interlock_definitions_sql),
            ("create logic_runs table", create_logic_runs_sql),
            ("create logic_warnings table", create_logic_warnings_sql),
            ("create control_rules table", create_control_rules_sql),
            ("alter control_rules logic_run_id column", alter_control_rules_logic_run_id_sql),
            ("alter control_rules source_type column", alter_control_rules_source_type_sql),
            ("alter control_rules target_type column", alter_control_rules_target_type_sql),
            ("alter control_rules display_text column", alter_control_rules_display_text_sql),
            ("alter control_rules st_preview column", alter_control_rules_st_preview_sql),
            ("alter control_rules source_references column", alter_control_rules_source_references_sql),
            ("alter control_rules rule_group column", alter_control_rules_rule_group_sql),
            ("alter control_rules condition_kind column", alter_control_rules_condition_kind_sql),
            ("alter control_rules threshold_name column", alter_control_rules_threshold_name_sql),
            ("alter control_rules secondary_target_tag column", alter_control_rules_secondary_target_tag_sql),
            ("alter control_rules priority column", alter_control_rules_priority_sql),
            ("alter control_rules renderable column", alter_control_rules_renderable_sql),
            ("alter control_rules unresolved_tokens column", alter_control_rules_unresolved_tokens_sql),
            ("alter control_rules comments column", alter_control_rules_comments_sql),
            ("alter control_rules is_symbolic column", alter_control_rules_is_symbolic_sql),
            ("alter control_rules resolution_strategy column", alter_control_rules_resolution_strategy_sql),
            ("alter logic_runs warnings column", alter_logic_runs_warnings_sql),
            ("alter logic_runs project_version column", alter_logic_runs_project_version_sql),
            ("alter logic_runs warnings_count column", alter_logic_runs_warnings_count_sql),
            ("alter logic_runs st_preview column", alter_logic_runs_st_preview_sql),
            ("alter logic_runs generator_version column", alter_logic_runs_generator_version_sql),
            ("create io_mapping_versions table", create_io_mapping_versions_sql),
            ("create io_mappings table", create_io_mappings_sql),
            ("create io_mapping_issues table", create_io_mapping_issues_sql),
            ("create io_mapping_versions project index", create_io_mapping_versions_project_idx_sql),
            ("create io_mapping_versions active unique index", create_io_mapping_versions_active_unique_sql),
            ("create io_mappings project version index", create_io_mappings_project_version_idx_sql),
            ("create io_mapping_issues project version index", create_io_mapping_issues_project_version_idx_sql),
            ("create control_loops table", create_control_loops_sql),
            ("create control_loops project index", create_control_loops_project_idx_sql),
            ("create control_loops tag index", create_control_loops_tag_idx_sql),
            ("create control_loops project unique index", create_control_loops_project_loop_unique_sql),
            ("create runtime_deployments table", create_runtime_deployments_sql),
            ("create runtime_deployments project index", create_runtime_deployments_project_idx_sql),
            ("create runtime_deployments project unique index", create_runtime_deployments_project_unique_sql),
            ("create version_records table", create_version_records_sql),
            ("create version_records project index", create_version_records_project_idx_sql),
            ("create plant_genie_ai_connectors table", create_plant_genie_ai_connectors_sql),
            ("alter plant_genie_ai_connectors provider column", "ALTER TABLE plant_genie_ai_connectors ADD COLUMN IF NOT EXISTS provider VARCHAR"),
            (
                "backfill plant_genie_ai_connectors provider values",
                """
                DO $$
                BEGIN
                  IF EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = 'plant_genie_ai_connectors' AND column_name = 'endpoint_url'
                  ) THEN
                    UPDATE plant_genie_ai_connectors
                    SET provider = CASE
                      WHEN COALESCE(BTRIM(provider), '') <> '' THEN provider
                      WHEN endpoint_url ILIKE 'https://api.openai.com/%' THEN 'openai'
                      WHEN endpoint_url ILIKE 'https://api.anthropic.com/%' THEN 'anthropic'
                      WHEN endpoint_url ILIKE '%openai.azure.com/%' THEN 'azure_openai'
                      WHEN endpoint_url ILIKE 'https://openrouter.ai/api/%' THEN 'openrouter'
                      ELSE 'custom_openai_compatible'
                    END
                    WHERE COALESCE(BTRIM(provider), '') = '';
                  ELSE
                    UPDATE plant_genie_ai_connectors
                    SET provider = 'custom_openai_compatible'
                    WHERE COALESCE(BTRIM(provider), '') = '';
                  END IF;
                END $$;
                """
            ),
            ("enforce plant_genie_ai_connectors provider not null", "ALTER TABLE plant_genie_ai_connectors ALTER COLUMN provider SET NOT NULL"),
            ("drop plant_genie_ai_connectors endpoint_url column", "ALTER TABLE plant_genie_ai_connectors DROP COLUMN IF EXISTS endpoint_url"),
            ("alter plant_genie_ai_connectors model column", "ALTER TABLE plant_genie_ai_connectors ADD COLUMN IF NOT EXISTS model VARCHAR NULL"),
            ("create plant_genie_ai_connectors user index", create_plant_genie_ai_connectors_user_idx_sql),
            ("create plant_genie_ai_connectors active unique index", create_plant_genie_ai_connectors_active_unique_sql),
            ("create plant_genie_plant_data_connectors table", create_plant_genie_plant_data_connectors_sql),
            ("alter plant_genie_plant_data_connectors last_tested_at column", "ALTER TABLE plant_genie_plant_data_connectors ADD COLUMN IF NOT EXISTS last_tested_at TIMESTAMP NULL"),
            (
                "backfill plant_genie_plant_data_connectors enabled flag",
                """
                WITH single_connector_users AS (
                  SELECT user_id, id AS connector_id
                  FROM (
                    SELECT
                      user_id,
                      id,
                      COUNT(*) OVER (PARTITION BY user_id) AS connector_count,
                      BOOL_OR(enabled) OVER (PARTITION BY user_id) AS any_enabled
                    FROM plant_genie_plant_data_connectors
                  ) AS connector_stats
                  WHERE connector_count = 1 AND any_enabled = FALSE
                )
                UPDATE plant_genie_plant_data_connectors AS connectors
                SET enabled = TRUE
                FROM single_connector_users
                WHERE connectors.id = single_connector_users.connector_id;
                """
            ),
            ("create plant_genie_plant_data_connectors user index", create_plant_genie_plant_data_connectors_user_idx_sql),
            ("create plant_genie_plant_data_connectors enabled index", create_plant_genie_plant_data_connectors_enabled_idx_sql),
        ]

        try:
            with self.connection() as conn:
                with conn.cursor() as cursor:
                    for statement_name, statement_sql in statements:
                        cursor.execute(statement_sql)
        except Exception:
            logger.exception("postgres schema initialization failed")
            raise

        logger.info("postgres schema initialization complete")

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
