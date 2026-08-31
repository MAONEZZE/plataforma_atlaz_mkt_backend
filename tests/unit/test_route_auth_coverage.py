"""Trava a superficie publica da API.

Uma rota nova que esqueca Depends(get_current_user) quebra este teste em vez de
ir pra producao aberta. CORS nao protege nada disso (ver test_cors.py).
"""

from fastapi.routing import APIRoute

from app.api.config.dependencies.auth_deps import get_current_user, require_admin
from app.main import app

# Unicas rotas que podem ser acessadas sem token.
ROTAS_PUBLICAS = {
    ("GET", "/health"),
    ("POST", "/api/v1/auth/login"),
}

_AUTH_DEPS = {get_current_user, require_admin}


def _dependencias(route: APIRoute) -> set[object]:
    encontradas: set[object] = set()
    pilha = list(route.dependant.dependencies)
    while pilha:
        dep = pilha.pop()
        if dep.call is not None:
            encontradas.add(dep.call)
        pilha.extend(dep.dependencies)
    return encontradas


def _rotas() -> list[tuple[str, str, APIRoute]]:
    saida = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            for metodo in route.methods - {"HEAD", "OPTIONS"}:
                saida.append((metodo, route.path, route))
    return saida


def test_apenas_health_e_login_sao_publicas() -> None:
    publicas = {
        (metodo, caminho)
        for metodo, caminho, route in _rotas()
        if not (_dependencias(route) & _AUTH_DEPS)
    }
    assert publicas == ROTAS_PUBLICAS


def test_rotas_admin_exigem_require_admin() -> None:
    sem_admin = [
        f"{metodo} {caminho}"
        for metodo, caminho, route in _rotas()
        if "/admin/" in caminho and require_admin not in _dependencias(route)
    ]
    assert sem_admin == []


def test_existe_superficie_protegida() -> None:
    # Guarda contra o teste acima passar por vacuidade se o app nao carregar rotas.
    assert len(_rotas()) > 50
