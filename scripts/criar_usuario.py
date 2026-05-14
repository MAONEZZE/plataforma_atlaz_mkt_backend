"""CLI to create a user via Supabase Admin API.

Usage:
    python -m scripts.criar_usuario \\
      --nome "Maria Silva" \\
      --email "maria@example.com" \\
      --senha "Senha@123" \\
      --role "cliente"

Full implementation in backend/02-usuarios-context.
"""

import typer

app = typer.Typer()


@app.command()
def main(
    nome: str = typer.Option(..., help="Full name"),
    email: str = typer.Option(..., help="Email address"),
    senha: str = typer.Option(..., help="Initial password"),
    role: str = typer.Option("cliente", help="Role: cliente or admin"),
) -> None:
    raise NotImplementedError("Implement in backend/02-usuarios-context")


if __name__ == "__main__":
    app()
