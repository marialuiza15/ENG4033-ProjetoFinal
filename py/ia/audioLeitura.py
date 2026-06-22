import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# Dados da LLM local
BASE_URL = "http://localhost:1234/v1"
MODEL = "google/genma-4-e4b"

# Prompt para a LLM gerar a nova sequencia musical
PROMPT_LLM = """
Crie uma nova sequencia musical baseada na sequencia de notas e duracoes
informada para melhorar a qualidade da sequencia original. Essa sequencia 
é a melodia de uma musica que deve ser seguida 
como base. Para a sequencia que deve ser gerada, siga também o estilo musical 
informado e o bpm em que essa sequencia deve ser tocada no instrumento informado.

A resposta deve ser somente um JSON valido, sem markdown, com o seguinte formato:
{
    "sequencia": [
        {"nota": "xx", "inicio": y, "duracao": z}
    ],
    "instrumento": "ii",
    "bpm": 120,
    "estilo": "ee"
}

onde "nota" é uma nota musical (ex: DO, RE, MI, FA, SOL, LA, SI), "inicio" é o
tempo de inicio da nota em milissegundos, "duracao" é a duracao da nota em milissegundos, 
"instrumento" é uma string com o instrumento utilizados na musica (ex: piano, baixo, bateria), 
"bpm" é o tempo da musica em batidas por minuto e "estilo" é o estilo musical da musica (ex: rock, pop, jazz).
Caso o estilo informado seja FALSE, a musica deve ser gerada sem seguir um estilo musical especifico.
"""

def gerar_sequencia_musical(json_entrada: dict[str, Any]) -> dict[str, Any]:
    url = f"{BASE_URL.rstrip('/')}/chat/completions"
    conteudo = (
        f"{PROMPT_LLM}\n\n"
        "JSON de entrada com a sequencia e parametros a serem usados como base:\n"
        f"{json.dumps(json_entrada, ensure_ascii=False)}"
    )
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": conteudo}],
    }

    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request) as response:
            dados = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        corpo = exc.read().decode("utf-8", errors="replace")
        raise Exception(f"Erro HTTP da LLM ({exc.code}): {corpo}") from exc
    except URLError as exc:
        raise Exception(f"Nao foi possivel conectar na LLM local: {exc}") from exc

    try:
        resposta = dados["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise Exception(f"Resposta inesperada da LLM: {dados}") from exc

    try:
        return json.loads(resposta)
    except json.JSONDecodeError as exc:
        raise Exception(f"Resposta da LLM nao e um JSON valido: {resposta}") from exc
