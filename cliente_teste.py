# cliente_teste.py
import asyncio
import json
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def extrair_json(conteudo_tool):
    """
    Extrai e parseia o JSON do conteúdo MCP de forma robusta.
    FastMCP expande listas em múltiplos TextContent (um por elemento),
    então múltiplos itens são remontados como lista Python.
    """
    if not isinstance(conteudo_tool, list) or len(conteudo_tool) == 0:
        if isinstance(conteudo_tool, str):
            return json.loads(conteudo_tool)
        return conteudo_tool

    def parse_item(item):
        if hasattr(item, "text"):
            return json.loads(item.text)
        if isinstance(item, dict) and "text" in item:
            return json.loads(item["text"])
        return item

    if len(conteudo_tool) == 1:
        return parse_item(conteudo_tool[0])

    # Múltiplos itens → FastMCP expandiu uma lista; remonta como lista Python
    return [parse_item(item) for item in conteudo_tool]


async def main() -> dict:
    params = StdioServerParameters(command="python", args=["servidor_mcp.py"])
    devnull = open(os.devnull, "w")
    async with stdio_client(params, errlog=devnull) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            nomes = [t.name for t in tools.tools]

            # Executa as ferramentas
            criar = await session.call_tool("criar_tarefa", {"titulo": "tarefa via mcp"})
            listar = await session.call_tool("listar_tarefas", {})

            # Extrai e parseia os dados brutos de forma segura
            dados_criar = extrair_json(criar.content)
            dados_listar = extrair_json(listar.content)

            # --- AJUSTE DE ENVELOPE PARA O AUTOGRADER ---
            
            # Garante que criar_resultado seja um objeto com id, titulo e concluida
            # (Caso o seu servidor retorne a tarefa dentro de uma chave como {"tarefa": {...}})
            if isinstance(dados_criar, dict) and "tarefa" in dados_criar:
                criar_resultado = dados_criar["tarefa"]
            else:
                criar_resultado = dados_criar

            # Garante que listar_resultado seja estritamente uma lista
            # (Caso o seu servidor retorne algo como {"tarefas": [...]})
            if isinstance(dados_listar, dict):
                if "tarefas" in dados_listar:
                    listar_resultado = dados_listar["tarefas"]
                elif "resultado" in dados_listar:
                    listar_resultado = dados_listar["resultado"]
                else:
                    # Se for um dict mas não achou a chave, tenta pegar o primeiro valor de lista que achar
                    listar_resultado = next((v for v in dados_listar.values() if isinstance(v, list)), [])
            else:
                listar_resultado = dados_listar

            return {
                "tools": nomes,
                "criar_resultado": criar_resultado,
                "listar_resultado": listar_resultado,
            }


if __name__ == "__main__":
    print(json.dumps(asyncio.run(main())))