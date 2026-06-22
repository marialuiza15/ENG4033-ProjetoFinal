import json
import sys
from pathlib import Path

from audioLeitura import gerar_sequencia_musical


def main() -> None:
    caminho_entrada = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("entrada_teste.json")
    caminho_saida = Path("saida_teste.json")

    with caminho_entrada.open("r", encoding="utf-8") as arquivo:
        json_entrada = json.load(arquivo)

    json_retorno = gerar_sequencia_musical(json_entrada)

    with caminho_saida.open("w", encoding="utf-8") as arquivo:
        json.dump(json_retorno, arquivo, indent=4, ensure_ascii=False)

    print(json.dumps(json_retorno, indent=4, ensure_ascii=False))
    print(f"\nJSON retornado salvo em: {caminho_saida.resolve()}")


if __name__ == "__main__":
    main()
