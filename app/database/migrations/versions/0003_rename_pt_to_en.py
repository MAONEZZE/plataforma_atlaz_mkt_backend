"""rename tables and columns PT to EN

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-20
"""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Drop dependent FK indexes/constraints before renames ──────────────────
    # Rename tables
    op.rename_table("usuario", "users", schema="ATZ_HUB")
    op.rename_table("trilha", "tracks", schema="ATZ_HUB")
    op.rename_table("modulo", "modules", schema="ATZ_HUB")
    op.rename_table("aula", "lessons", schema="ATZ_HUB")
    op.rename_table("aluno_aula", "student_lessons", schema="ATZ_HUB")
    op.rename_table("comentario", "comments", schema="ATZ_HUB")
    op.rename_table("metrica_semanal", "weekly_metrics", schema="ATZ_HUB")

    # ── Rename columns in public.users ────────────────────────────────────────
    op.alter_column("users", "nome", new_column_name="name", schema="ATZ_HUB")
    op.alter_column("users", "descricao", new_column_name="description", schema="ATZ_HUB")
    op.alter_column("users", "foto_url", new_column_name="photo_url", schema="ATZ_HUB")
    op.alter_column("users", "inativo", new_column_name="inactive", schema="ATZ_HUB")
    op.alter_column("users", "criado_em", new_column_name="created_at", schema="ATZ_HUB")
    op.alter_column("users", "atualizado_em", new_column_name="updated_at", schema="ATZ_HUB")

    # ── Rename columns in public.tracks ───────────────────────────────────────
    op.alter_column("tracks", "criado_em", new_column_name="created_at", schema="ATZ_HUB")

    # ── Rename columns in public.lessons ──────────────────────────────────────
    op.alter_column("lessons", "modulo_id", new_column_name="module_id", schema="ATZ_HUB")
    op.alter_column("lessons", "criado_em", new_column_name="created_at", schema="ATZ_HUB")

    # ── Rename columns in public.modules ──────────────────────────────────────
    op.alter_column("modules", "trilha_id", new_column_name="track_id", schema="ATZ_HUB")

    # ── Rename columns in public.student_lessons ──────────────────────────────
    op.alter_column("student_lessons", "usuario_id", new_column_name="user_id", schema="ATZ_HUB")
    op.alter_column("student_lessons", "aula_id", new_column_name="lesson_id", schema="ATZ_HUB")
    op.alter_column(
        "student_lessons", "concluida_em", new_column_name="completed_at", schema="ATZ_HUB"
    )

    # ── Rename columns in public.comments ─────────────────────────────────────
    op.alter_column("comments", "aula_id", new_column_name="lesson_id", schema="ATZ_HUB")
    op.alter_column("comments", "usuario_id", new_column_name="user_id", schema="ATZ_HUB")
    op.alter_column("comments", "criado_em", new_column_name="created_at", schema="ATZ_HUB")
    op.alter_column("comments", "editado_em", new_column_name="edited_at", schema="ATZ_HUB")
    op.alter_column("comments", "apagado_em", new_column_name="deleted_at", schema="ATZ_HUB")

    # ── Rename columns in public.weekly_metrics ───────────────────────────────
    op.alter_column(
        "weekly_metrics", "usuario_id", new_column_name="user_id", schema="ATZ_HUB"
    )
    op.alter_column(
        "weekly_metrics", "semana_inicio", new_column_name="week_start", schema="ATZ_HUB"
    )
    op.alter_column(
        "weekly_metrics", "ligacoes_agendadas", new_column_name="calls_scheduled", schema="ATZ_HUB"
    )
    op.alter_column(
        "weekly_metrics", "ligacoes_realizadas", new_column_name="calls_made", schema="ATZ_HUB"
    )
    op.alter_column(
        "weekly_metrics", "reunioes_agendadas", new_column_name="meetings_scheduled", schema="ATZ_HUB"
    )
    op.alter_column(
        "weekly_metrics", "indicacoes", new_column_name="referrals", schema="ATZ_HUB"
    )
    op.alter_column(
        "weekly_metrics", "criado_em", new_column_name="created_at", schema="ATZ_HUB"
    )
    op.alter_column(
        "weekly_metrics", "atualizado_em", new_column_name="updated_at", schema="ATZ_HUB"
    )

    # ── Update database functions that reference old table/column names ────────
    # Update the trigger function that syncs auth.users → public.users
    op.execute("""
        CREATE OR REPLACE FUNCTION "ATZ_HUB".handle_new_auth_user()
        RETURNS trigger AS $$
        BEGIN
            INSERT INTO "ATZ_HUB".users (id, email, name, role)
            VALUES (
                NEW.id,
                NEW.email,
                COALESCE(NEW.raw_user_meta_data->>'nome', split_part(NEW.email, '@', 1)),
                COALESCE(NEW.raw_user_meta_data->>'role', 'cliente')
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER
    """)

    # Update email sync trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION "ATZ_HUB".handle_auth_user_email_change()
        RETURNS trigger AS $$
        BEGIN
            IF NEW.email IS DISTINCT FROM OLD.email THEN
                UPDATE "ATZ_HUB".users
                SET email = NEW.email, updated_at = now()
                WHERE id = NEW.id;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER
    """)


def downgrade() -> None:
    # ── Reverse column renames in public.weekly_metrics ───────────────────────
    op.alter_column(
        "weekly_metrics", "updated_at", new_column_name="atualizado_em", schema="ATZ_HUB"
    )
    op.alter_column(
        "weekly_metrics", "created_at", new_column_name="criado_em", schema="ATZ_HUB"
    )
    op.alter_column(
        "weekly_metrics", "referrals", new_column_name="indicacoes", schema="ATZ_HUB"
    )
    op.alter_column(
        "weekly_metrics",
        "meetings_scheduled",
        new_column_name="reunioes_agendadas",
        schema="ATZ_HUB",
    )
    op.alter_column(
        "weekly_metrics", "calls_made", new_column_name="ligacoes_realizadas", schema="ATZ_HUB"
    )
    op.alter_column(
        "weekly_metrics",
        "calls_scheduled",
        new_column_name="ligacoes_agendadas",
        schema="ATZ_HUB",
    )
    op.alter_column(
        "weekly_metrics", "week_start", new_column_name="semana_inicio", schema="ATZ_HUB"
    )
    op.alter_column(
        "weekly_metrics", "user_id", new_column_name="usuario_id", schema="ATZ_HUB"
    )

    # ── Reverse column renames in public.comments ─────────────────────────────
    op.alter_column("comments", "deleted_at", new_column_name="apagado_em", schema="ATZ_HUB")
    op.alter_column("comments", "edited_at", new_column_name="editado_em", schema="ATZ_HUB")
    op.alter_column("comments", "created_at", new_column_name="criado_em", schema="ATZ_HUB")
    op.alter_column("comments", "user_id", new_column_name="usuario_id", schema="ATZ_HUB")
    op.alter_column("comments", "lesson_id", new_column_name="aula_id", schema="ATZ_HUB")

    # ── Reverse column renames in public.student_lessons ──────────────────────
    op.alter_column(
        "student_lessons", "completed_at", new_column_name="concluida_em", schema="ATZ_HUB"
    )
    op.alter_column(
        "student_lessons", "lesson_id", new_column_name="aula_id", schema="ATZ_HUB"
    )
    op.alter_column(
        "student_lessons", "user_id", new_column_name="usuario_id", schema="ATZ_HUB"
    )

    # ── Reverse column renames in public.modules ──────────────────────────────
    op.alter_column("modules", "track_id", new_column_name="trilha_id", schema="ATZ_HUB")

    # ── Reverse column renames in public.lessons ──────────────────────────────
    op.alter_column("lessons", "created_at", new_column_name="criado_em", schema="ATZ_HUB")
    op.alter_column("lessons", "module_id", new_column_name="modulo_id", schema="ATZ_HUB")

    # ── Reverse column renames in public.tracks ───────────────────────────────
    op.alter_column("tracks", "created_at", new_column_name="criado_em", schema="ATZ_HUB")

    # ── Reverse column renames in public.users ────────────────────────────────
    op.alter_column("users", "updated_at", new_column_name="atualizado_em", schema="ATZ_HUB")
    op.alter_column("users", "created_at", new_column_name="criado_em", schema="ATZ_HUB")
    op.alter_column("users", "inactive", new_column_name="inativo", schema="ATZ_HUB")
    op.alter_column("users", "photo_url", new_column_name="foto_url", schema="ATZ_HUB")
    op.alter_column("users", "description", new_column_name="descricao", schema="ATZ_HUB")
    op.alter_column("users", "name", new_column_name="nome", schema="ATZ_HUB")

    # ── Reverse table renames ─────────────────────────────────────────────────
    op.rename_table("weekly_metrics", "metrica_semanal", schema="ATZ_HUB")
    op.rename_table("comments", "comentario", schema="ATZ_HUB")
    op.rename_table("student_lessons", "aluno_aula", schema="ATZ_HUB")
    op.rename_table("lessons", "aula", schema="ATZ_HUB")
    op.rename_table("modules", "modulo", schema="ATZ_HUB")
    op.rename_table("tracks", "trilha", schema="ATZ_HUB")
    op.rename_table("users", "usuario", schema="ATZ_HUB")
