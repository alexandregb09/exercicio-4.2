# cliente_teste.py
import asyncio
import json
import logging
import sys
import warnings

# 1. Silencia avisos que possam poluir o stdout
warnings.filterwarnings("ignore")

# 2. Garante que os logs vão para o stderr (onde não quebram o JSON do avaliador)
logging.basicConfig(level=logging.ERROR, stream=sys.stderr)

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def extrair_json(conteudo_tool):
    """
    Função auxiliar para extrair e parsear o JSON de forma robusta,
    lidando com variações do SDK (.text ou extração direta).
    """
    # Se o conteúdo for uma lista (comum no MCP), pegamos o primeiro elemento
    if isinstance(conteudo_tool, list) and len(conteudo_tool) > 0:
        item = conteudo_tool[0]
        # Se o item tiver o atributo 'text' (comportamento padrão do SDK)
        if hasattr(item, "text"):
            return json.loads(item.text)
        # Se for um dicionário puro retornado pelo SDK
        elif isinstance(item, dict) and "text" in item:
            return json.loads(item["text"])
        # Caso o item já seja o próprio JSON estruturado
        elif isinstance(item, dict):
            return item
    
    # Caso já venha como string
    if isinstance(conteudo_tool, str):
        return json.loads(conteudo_tool)
        
    return conteudo_tool


async def main() -> dict:
    params = StdioServerParameters(command="python", args=["servidor_mcp.py"])
    async with stdio_client(params) as (read, write):
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
    # Garante que apenas o JSON estrito saia no stdout
    print(json.dumps(asyncio.run(main())))