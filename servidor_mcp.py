import httpx
from mcp.server.fastmcp import FastMCP

API = "http://localhost:8000"
mcp = FastMCP("tarefas-mcp")


@mcp.tool()
def criar_tarefa(titulo: str) -> dict:
    """Cria uma tarefa na API e devolve o objeto criado."""
    resp = httpx.post(f"{API}/tarefas", json={"titulo": titulo}, timeout=10)
    resp.raise_for_status()
    return resp.json()


@mcp.tool()
def listar_tarefas() -> list:
    """Busca a lista de tarefas cadastradas na API REST e a retorna."""
    resp = httpx.get(f"{API}/tarefas", timeout=10)
    resp.raise_for_status()
    return resp.json()  # Deve retornar uma lista de dicionários


if __name__ == "__main__":
    mcp.run()  # Usa o transporte stdio por padrão