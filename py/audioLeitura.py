import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# Dados da LLM local
BASE_URL = "http://localhost:1234/v1"
MODEL = "google/genma-4-e4b",

# Prompt para a LLM gerar a nova sequencia musical
PROMPT_LLM = """
Crie uma nova sequencia musical baseada na sequencia de notas e duracoes
informada. Essa sequencia é a melodia de uma musica que deve ser seguida 
como base. Para a sequencia que deve ser gerada, siga também o estilo musical 
informado.
Retorne além dessa sequencia de melodia melhorada um sequencia de batida
que deve ser utilizada como acompanhamento da melodia. A sequencia de batida 
deve ser composta por notas e duracoes, assim como a sequencia de melodia. 

A repsosta deve ser um JSON com o seguinte formato:
{
    "melodia": [
        {"nota": "xx", "duracao": y},
    ],
    "batida": [
        {"nota": "xx", "duracao": y},
    ]
}

onde "xx" é a nota musical (ex: C4, D#5, etc) e y é a duracao da nota em segundos.
"""

def gerar_sequencia_musical() -> str:
    url = f"{BASE_URL.rstrip('/')}/chat/completions"
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": PROMPT_LLM}],
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
        return dados["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise Exception(f"Resposta inesperada da LLM: {dados}") from exc
