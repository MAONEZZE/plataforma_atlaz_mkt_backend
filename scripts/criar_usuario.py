"""CLI to create a user via Supabase Admin API.

Usage:
    python -m scripts.criar_usuario \\
      --nome "Maria Silva" \\
      --email "maria@example.com" \\
      --senha "Senha@123" \\
      --role "cliente"
"""

import re

import typer
from supabase import create_client

from app.api.config.settings import settings

app = typer.Typer()

_SENHA_PATTERN = re.compile(r"^(?=.*[A-Z])(?=.*\d).{8,}$")


def _validar_senha_forte(senha: str) -> bool:
    return bool(_SENHA_PATTERN.match(senha))


@app.command()
def main(
    nome: str = typer.Option(..., help="Nome completo"),
    email: str = typer.Option(..., help="Endereço de email"),
    senha: str = typer.Option(..., help="Senha inicial"),
    role: str = typer.Option("cliente", help="Role: cliente ou admin"),
    telefone: str | None = typer.Option(None, help="Telefone (opcional)"),
) -> None:
    if role not in ("cliente", "admin"):
        typer.echo("Erro: role deve ser 'cliente' ou 'admin'.", err=True)
        raise typer.Exit(1)

    if not _validar_senha_forte(senha):
        typer.echo(
            "Erro: senha deve ter ≥ 8 caracteres, ao menos 1 maiúscula e 1 número.",
            err=True,
        )
        raise typer.Exit(1)

    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

    try:
        response = supabase.auth.admin.create_user(
            {
                "email": email,
                "password": senha,
                "email_confirm": True,
                "user_metadata": {
                    "name": nome,
                    "role": role,
                },
            }
        )
        user = response.user
        if user is None:
            typer.echo("Erro: resposta inesperada da API do Supabase.", err=True)
            raise typer.Exit(1)

        typer.echo(f"✓ Usuário criado em auth.users com id={user.id}")
        typer.echo("  Trigger criou registro em public.usuario.")
        typer.echo(f"  Role: {role}")

        if telefone:
            from sqlalchemy import create_engine, text

            sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
            engine = create_engine(sync_url)
            with engine.connect() as conn:
                conn.execute(
                    text("UPDATE public.usuario SET telefone = :tel WHERE id = :uid"),
                    {"tel": telefone, "uid": str(user.id)},
                )
                conn.commit()
            typer.echo(f"  Telefone atualizado: {telefone}")

    except Exception as exc:
        typer.echo(f"Erro: {exc}", err=True)
        raise typer.Exit(1) from exc


if __name__ == "__main__":
    app()
