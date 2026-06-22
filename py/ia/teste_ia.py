import json
import sys
from pathlib import Path

from audioLeitura import gerar_sequencia_musical


def main() -> None:
    caminho_entrada = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("entrada_teste.json")

    with caminho_entrada.open("r", encoding="utf-8") as arquivo:
        json_entrada = json.load(arquivo)

    json_retorno = gerar_sequencia_musical(json_entrada)
    print(json.dumps(json_retorno, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    main()
