"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-14
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE SCHEMA IF NOT EXISTS "ATZ_HUB"')

    # ── Extensions ───────────────────────────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")

    # ── usuario ──────────────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE "ATZ_HUB".usuario (
            id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
            nome text NOT NULL,
            email citext NOT NULL UNIQUE,
            telefone text,
            linkedin_url text,
            instagram_username text,
            foto_url text,
            role text NOT NULL DEFAULT 'cliente'
                CHECK (role IN ('cliente', 'admin')),
            inativo bool NOT NULL DEFAULT false,
            criado_em timestamp NOT NULL DEFAULT now(),
            atualizado_em timestamp NOT NULL DEFAULT now()
        )
        """)
    op.execute('CREATE INDEX usuario_role_idx ON "ATZ_HUB".usuario(role)')

    # ── Trigger: sync auth.users → "ATZ_HUB".usuario on insert ──────────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION "ATZ_HUB".handle_new_auth_user()
        RETURNS trigger AS $$
        BEGIN
            INSERT INTO "ATZ_HUB".usuario (id, email, nome, role)
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
    op.execute("""
        CREATE TRIGGER on_auth_user_created
        AFTER INSERT ON auth.users
        FOR EACH ROW EXECUTE FUNCTION "ATZ_HUB".handle_new_auth_user()
        """)

    # ── Trigger: sync email change ────────────────────────────────────────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION "ATZ_HUB".handle_auth_user_email_change()
        RETURNS trigger AS $$
        BEGIN
            IF NEW.email IS DISTINCT FROM OLD.email THEN
                UPDATE "ATZ_HUB".usuario
                SET email = NEW.email, atualizado_em = now()
                WHERE id = NEW.id;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER
        """)
    op.execute("""
        CREATE TRIGGER on_auth_user_email_changed
        AFTER UPDATE ON auth.users
        FOR EACH ROW EXECUTE FUNCTION "ATZ_HUB".handle_auth_user_email_change()
        """)

    # ── trilha ────────────────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE "ATZ_HUB".trilha (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            titulo text NOT NULL,
            descricao text,
            capa_url text,
            ordem int NOT NULL DEFAULT 0,
            criado_em timestamp NOT NULL DEFAULT now()
        )
        """)

    # ── modulo ────────────────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE "ATZ_HUB".modulo (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            trilha_id uuid NOT NULL REFERENCES "ATZ_HUB".trilha(id) ON DELETE CASCADE,
            titulo text NOT NULL,
            descricao text,
            ordem int NOT NULL DEFAULT 0
        )
        """)
    op.execute('CREATE INDEX modulo_trilha_idx ON "ATZ_HUB".modulo(trilha_id)')

    # ── aula ──────────────────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE "ATZ_HUB".aula (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            modulo_id uuid NOT NULL REFERENCES "ATZ_HUB".modulo(id) ON DELETE CASCADE,
            titulo text NOT NULL,
            descricao text,
            drive_file_id text NOT NULL,
            duracao_minutos int,
            ordem int NOT NULL DEFAULT 0,
            criado_em timestamp NOT NULL DEFAULT now()
        )
        """)
    op.execute('CREATE INDEX aula_modulo_idx ON "ATZ_HUB".aula(modulo_id)')

    # ── aluno_aula ────────────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE "ATZ_HUB".aluno_aula (
            usuario_id uuid REFERENCES "ATZ_HUB".usuario(id) ON DELETE CASCADE,
            aula_id uuid REFERENCES "ATZ_HUB".aula(id) ON DELETE CASCADE,
            concluida_em timestamp NOT NULL DEFAULT now(),
            PRIMARY KEY (usuario_id, aula_id)
        )
        """)

    # ── comentario ────────────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE "ATZ_HUB".comentario (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            aula_id uuid NOT NULL REFERENCES "ATZ_HUB".aula(id) ON DELETE CASCADE,
            usuario_id uuid NOT NULL REFERENCES "ATZ_HUB".usuario(id) ON DELETE CASCADE,
            texto text NOT NULL CHECK (length(texto) BETWEEN 1 AND 2000),
            criado_em timestamp NOT NULL DEFAULT now(),
            editado_em timestamp,
            apagado_em timestamp
        )
        """)
    op.execute('CREATE INDEX comentario_aula_idx ON "ATZ_HUB".comentario(aula_id, criado_em DESC)')

    # ── metrica_semanal ───────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE "ATZ_HUB".metrica_semanal (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            usuario_id uuid NOT NULL REFERENCES "ATZ_HUB".usuario(id) ON DELETE CASCADE,
            semana_inicio date NOT NULL,
            ligacoes_agendadas int NOT NULL DEFAULT 0 CHECK (ligacoes_agendadas >= 0),
            ligacoes_realizadas int NOT NULL DEFAULT 0 CHECK (ligacoes_realizadas >= 0),
            reunioes_agendadas int NOT NULL DEFAULT 0 CHECK (reunioes_agendadas >= 0),
            indicacoes int NOT NULL DEFAULT 0 CHECK (indicacoes >= 0),
            criado_em timestamp NOT NULL DEFAULT now(),
            atualizado_em timestamp NOT NULL DEFAULT now(),
            UNIQUE (usuario_id, semana_inicio),
            CHECK (EXTRACT(DOW FROM semana_inicio) = 1)
        )
        """)
    op.execute(
        'CREATE INDEX metrica_usuario_semana_idx ON "ATZ_HUB".metrica_semanal(usuario_id, semana_inicio DESC)'
    )

    # ── Row Level Security ────────────────────────────────────────────────────────
    for table in [
        '"ATZ_HUB".usuario',
        '"ATZ_HUB".trilha',
        '"ATZ_HUB".modulo',
        '"ATZ_HUB".aula',
        '"ATZ_HUB".aluno_aula',
        '"ATZ_HUB".comentario',
        '"ATZ_HUB".metrica_semanal',
    ]:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    for table in [
        '"ATZ_HUB".metrica_semanal',
        '"ATZ_HUB".comentario',
        '"ATZ_HUB".aluno_aula',
        '"ATZ_HUB".aula',
        '"ATZ_HUB".modulo',
        '"ATZ_HUB".trilha',
    ]:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")

    op.execute('DROP TABLE IF EXISTS "ATZ_HUB".usuario CASCADE')
    op.execute('DROP FUNCTION IF EXISTS "ATZ_HUB".handle_new_auth_user() CASCADE')
    op.execute('DROP FUNCTION IF EXISTS "ATZ_HUB".handle_auth_user_email_change() CASCADE')
