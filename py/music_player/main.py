import os
import json
from pathlib import Path
import time
import sys


FLUIDSYNTH_BIN = r"C:\Users\micro1\Downloads\fluidsynth\fluidsynth-v2.5.5-win10-x64-cpp11\bin"

os.add_dll_directory(FLUIDSYNTH_BIN)
os.environ["PATH"] = FLUIDSYNTH_BIN + os.pathsep + os.environ["PATH"]


PASTA_ATUAL = Path(__file__).resolve().parent
PASTA_PY = PASTA_ATUAL.parent
PASTA_IA = PASTA_PY / "ia"

sys.path.insert(0, str(PASTA_IA))

from audioLeitura import gerar_sequencia_musical


def carregar_json(caminho):
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)

def salvar_json(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, indent=4, ensure_ascii=False)

        
PASTA_ARQUIVOS = PASTA_ATUAL / "arquivos_musicais"

batidas = carregar_json(PASTA_ARQUIVOS / "batidas.json")
notas = carregar_json(PASTA_ARQUIVOS / "notas.json")
parametros = carregar_json(PASTA_ARQUIVOS / "parametros.json")


musica_completa = {
    "instrumento": parametros["instrumento"],
    "bpm": parametros["bpm"],
    "estilo": parametros["estilo"],
    "sequencia": notas["sequencia"]
}

salvar_json(PASTA_ARQUIVOS / "musica_completa.json", musica_completa)

json_entrada = carregar_json(PASTA_ARQUIVOS / "musica_completa.json")

json_recebido = gerar_sequencia_musical(json_entrada)

salvar_json(PASTA_ARQUIVOS / "musica_gerada.json", json_recebido)

SOUNDFONT = r"C:\Users\micro1\Downloads\FluidR3_GM.sf2"
import fluidsynth
INSTRUMENTOS = {
    "piano": {"canal": 0, "programa": 0},
    "baixo": {"canal": 1, "programa": 33},
    "guitarra": {"canal": 2, "programa": 27},
    "sintetizador": {"canal": 3, "programa": 89},
    "orgao": {"canal": 4, "programa": 19},
    "strings": {"canal": 5, "programa": 48},
    "bateria": {"canal": 9, "programa": 0}
}

fs = fluidsynth.Synth()
fs.start(driver="wasapi", midi_driver="none")

sfid = fs.sfload(SOUNDFONT)

for instrumento in INSTRUMENTOS.values():
    if instrumento["programa"] is not None:
        fs.program_select(instrumento["canal"],sfid,0,instrumento["programa"])

def preparar_sequencia(musica):
    sequencia_convertida = []

    for evento in musica["sequencia"]:
        novo_evento = evento.copy()
        novo_evento["instrumento"] = musica["instrumento"]
        sequencia_convertida.append(novo_evento)

    return sequencia_convertida

sequencia = preparar_sequencia(musica_completa)


def ajustar_tempo_batida(valor_ms, bpm, bpm_base=120):
    fator = bpm_base / bpm
    return int(valor_ms * fator)

def calcular_duracao(sequencia):
    maior_fim = 0

    for evento in sequencia:
        fim = evento["inicio"] + evento["duracao"]
        if fim > maior_fim:
            maior_fim = fim

    return maior_fim

def preparar_batida(batida, bpm):
    eventos = []

    for evento in batida["eventos"]:
        novo_evento = evento.copy()
        novo_evento["inicio"] = ajustar_tempo_batida(evento["inicio"], bpm)
        novo_evento["duracao"] = ajustar_tempo_batida(evento["duracao"], bpm)
        eventos.append(novo_evento)

    duracao_padrao = ajustar_tempo_batida(batida["duracao_padrao"],bpm)

    return eventos, duracao_padrao


def repetir_batida(batida, duracao_batida, duracao_musica):
    batida_final = []
    deslocamento = 0

    while deslocamento < duracao_musica:
        for evento in batida:
            novo_evento = evento.copy()
            novo_evento["inicio"] = evento["inicio"] + deslocamento
            batida_final.append(novo_evento)

        deslocamento += duracao_batida

    return batida_final


while True:
    seq = fluidsynth.Sequencer(use_system_timer=False)
    synth_id = seq.register_fluidsynth(fs)

    duracao_musica = calcular_duracao(sequencia)

    batida = batidas[musica_completa["estilo"]]

    eventos_batida, duracao_batida = preparar_batida(batida,musica_completa["bpm"])

    batida_final = repetir_batida(eventos_batida,duracao_batida,duracao_musica)
    duracao_total = 0

    sequencia_final = sequencia + batida_final

    for evento in sequencia_final:
        nota = evento["nota"]
        inicio = evento["inicio"]
        duracao = evento["duracao"]
        instrumento = evento["instrumento"]

        configuracao = INSTRUMENTOS[instrumento]
        canal = configuracao["canal"]

        fim = inicio + duracao

        seq.note_on(inicio, canal, nota, 100, dest=synth_id)
        seq.note_off(fim, canal, nota, dest=synth_id)

        if fim > duracao_total:
            duracao_total = fim
    duracao_total = duracao_musica

    for tempo in range(0, duracao_total+10, 10):
        print(tempo)
        seq.process(tempo)
        time.sleep(0.01)

fs.delete()