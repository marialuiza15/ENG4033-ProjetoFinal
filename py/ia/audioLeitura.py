import json
from typing import Any
from requests import post


# Dados da LLM local
BASE_URL = "http://localhost:1234/v1"
MODEL = "google/genma-4-e4b"

# Prompt para a LLM gerar a nova sequencia musical
PROMPT_LLM = """
Crie uma nova sequencia musical baseada na sequencia de notas e duracoes
informada para melhorar a qualidade da sequencia original de forma a deixa-la mais melodiosa. 
Essa sequencia e a melodia de uma musica que deve ser seguida como base para a sequencia que deve ser gerada.
Siga tambem o estilo musical informado e o bpm em que essa sequencia deve ser tocada no instrumento informado.

A resposta deve ser somente um JSON valido, sem markdown, com o seguinte formato:
{
    "sequencia": [
        {"nota": "xx", "inicio": y, "duracao": z}
    ],
    "instrumento": "ii",
    "bpm": 120,
    "estilo": "ee"
}

onde "nota" e uma nota musical (ex: DO, RE, MI, FA, SOL, LA, SI), "inicio" e o
tempo de inicio da nota em milissegundos, "duracao" e a duracao da nota em milissegundos, 
"instrumento" e uma string com o instrumento utilizados na musica (ex: piano, baixo, bateria), 
"bpm" e o tempo da musica em batidas por minuto e "estilo" e o estilo musical da musica (ex: rock, pop, jazz).
Caso o estilo informado seja FALSE, a musica deve ser gerada sem seguir um estilo musical especifico.
No json que vai ser retornado, a nota deve estar no formato de valor utilizado pelo Fluidsynth que vai tocar a musica (Ex: 64, 66, 67).
JSON de entrada com a sequencia e parametros a serem usados como base:
"""


def gerar_sequencia_musical(json_entrada: dict[str, Any]) -> dict[str, Any]:
    url = BASE_URL + "/chat/completions"
    conteudo = (
        f"{PROMPT_LLM}\n\n"
        f"{json.dumps(json_entrada, ensure_ascii=False)}"
    )
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": conteudo}],
    }

    resposta = post(url, json=payload)
    dados = resposta.json()

    try:
        resposta = dados["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise Exception(f"Resposta inesperada da LLM: {dados}") from exc

    try:
        return json.loads(resposta)
    except json.JSONDecodeError as exc:
        raise Exception(f"Resposta da LLM nao e um JSON valido: {resposta}") from exc
