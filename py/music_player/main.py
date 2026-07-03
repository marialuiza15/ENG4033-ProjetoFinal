import os
import json
from pathlib import Path
import time
import sys


# Caminhos base do projeto.
# A partir do local deste arquivo, o programa encontra a pasta da IA
# e a pasta onde ficam os JSONs, o FluidSynth e o SoundFont.
PASTA_ATUAL = Path(__file__).resolve().parent
PASTA_PY = PASTA_ATUAL.parent
PASTA_IA = PASTA_PY / "ia"

PASTA_ARQUIVOS = PASTA_ATUAL / "arquivos_musicais"

# Pasta com os binarios do FluidSynth usados para tocar audio no Windows.
FLUIDSYNTH_BIN = PASTA_ARQUIVOS / "fluidsynth-v2.5.5-win10-x64-cpp11" / "bin"

# Adiciona as DLLs do FluidSynth ao ambiente do Python.
# Sem isso, o import/uso do fluidsynth pode falhar por nao encontrar as DLLs.
DLL_DIRECTORY = os.add_dll_directory(str(FLUIDSYNTH_BIN))
os.environ["PATH"] = str(FLUIDSYNTH_BIN) + os.pathsep + os.environ["PATH"]


# Inclui a pasta py/ia no caminho de imports para acessar audioLeitura.py.
sys.path.insert(0, str(PASTA_IA))

# Importa a funcao responsavel por gerar uma sequencia musical com a IA.
from audioLeitura import gerar_sequencia_musical


# Carrega um arquivo JSON e transforma seu conteudo em objeto Python.
def carregar_json(caminho):
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


# Salva um objeto Python em formato JSON, mantendo acentos e indentacao.
def salvar_json(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, indent=4, ensure_ascii=False)


# Le os arquivos de configuracao da musica.
# batidas.json: padroes de bateria por estilo.
# notas.json: notas iniciais da melodia.
# parametros.json: instrumento, BPM e estilo escolhidos.
batidas = carregar_json(PASTA_ARQUIVOS / "batidas.json")
notas = carregar_json(PASTA_ARQUIVOS / "notas.json")
parametros = carregar_json(PASTA_ARQUIVOS / "parametros.json")


# Monta um JSON unico com todas as informacoes necessarias para a musica.
musica_completa = {
    "instrumento": parametros["instrumento"],
    "bpm": parametros["bpm"],
    "estilo": parametros["estilo"],
    "sequencia": notas["sequencia"]
}

# Salva a musica completa para registro e para servir de entrada para a IA.
salvar_json(PASTA_ARQUIVOS / "musica_completa.json", musica_completa)

# Recarrega o arquivo salvo e envia para a funcao de geracao musical.
json_entrada = carregar_json(PASTA_ARQUIVOS / "musica_completa.json")

# Recebe da IA uma nova estrutura musical gerada a partir da entrada.
json_recebido = gerar_sequencia_musical(json_entrada)

# Salva a resposta da IA em um arquivo separado.
salvar_json(PASTA_ARQUIVOS / "musica_gerada.json", json_recebido)

# A partir daqui, o programa toca a musica recebida da IA.
musica_para_tocar = json_recebido

# SoundFont com os timbres usados pelo sintetizador.
SOUNDFONT = PASTA_ARQUIVOS / "FluidR3_GM.sf2"

import fluidsynth

# Tabela que associa cada instrumento a um canal MIDI e a um programa/timbre.
# No padrao MIDI, o canal 9 e usado para bateria.
INSTRUMENTOS = {
    "piano": {"canal": 0, "programa": 0},
    "baixo": {"canal": 1, "programa": 33},
    "guitarra": {"canal": 2, "programa": 27},
    "sintetizador": {"canal": 3, "programa": 89},
    "orgao": {"canal": 4, "programa": 19},
    "strings": {"canal": 5, "programa": 48},
    "bateria": {"canal": 9, "programa": 0}
}

# Cria e inicia o sintetizador de audio usando o driver WASAPI do Windows.
fs = fluidsynth.Synth()
fs.start(driver="wasapi")

# Carrega o arquivo de timbres no FluidSynth.
sfid = fs.sfload(str(SOUNDFONT))

# Configura cada canal MIDI com o timbre definido na tabela de instrumentos.
for instrumento in INSTRUMENTOS.values():
    if instrumento["programa"] is not None:
        fs.program_select(instrumento["canal"], sfid, 0, instrumento["programa"])


# Adiciona o instrumento escolhido a cada evento da sequencia de notas.
# Cada evento passa a ter nota, inicio, duracao e instrumento.
def preparar_sequencia(musica):
    sequencia_convertida = []

    for evento in musica["sequencia"]:
        novo_evento = evento.copy()
        novo_evento["instrumento"] = musica["instrumento"]
        sequencia_convertida.append(novo_evento)

    return sequencia_convertida


sequencia = preparar_sequencia(musica_para_tocar)


# Converte tempos de uma batida criada para 120 BPM para o BPM da musica.
def ajustar_tempo_batida(valor_ms, bpm, bpm_base=120):
    fator = bpm_base / bpm
    return int(valor_ms * fator)


# Calcula a duracao da musica olhando qual evento termina mais tarde.
def calcular_duracao(sequencia):
    maior_fim = 0

    for evento in sequencia:
        fim = evento["inicio"] + evento["duracao"]
        if fim > maior_fim:
            maior_fim = fim

    return maior_fim


# Ajusta todos os eventos da batida para o BPM escolhido.
# Tambem ajusta a duracao do padrao para saber de quanto em quanto repetir.
def preparar_batida(batida, bpm):
    eventos = []

    for evento in batida["eventos"]:
        novo_evento = evento.copy()
        novo_evento["inicio"] = ajustar_tempo_batida(evento["inicio"], bpm)
        novo_evento["duracao"] = ajustar_tempo_batida(evento["duracao"], bpm)
        eventos.append(novo_evento)

    duracao_padrao = ajustar_tempo_batida(batida["duracao_padrao"], bpm)

    return eventos, duracao_padrao


# Repete o padrao de bateria ate preencher toda a duracao da musica.
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


# Loop principal de reproducao.
# A cada repeticao, a musica e agendada e tocada do inicio ao fim.
while True:
    # Cria um sequenciador manual para agendar os eventos MIDI.
    seq = fluidsynth.Sequencer(use_system_timer=False)
    synth_id = seq.register_fluidsynth(fs)

    # Calcula a duracao da melodia principal.
    duracao_musica = calcular_duracao(sequencia)

    # Seleciona o padrao de bateria de acordo com o estilo recebido da IA.
    batida = batidas[musica_para_tocar["estilo"]]

    # Prepara e repete a bateria conforme o BPM recebido da IA.
    eventos_batida, duracao_batida = preparar_batida(batida, musica_para_tocar["bpm"])

    batida_final = repetir_batida(eventos_batida, duracao_batida, duracao_musica)
    duracao_total = 0

    # Junta a melodia com a bateria em uma unica lista de eventos.
    sequencia_final = sequencia + batida_final

    # Agenda cada nota no sequenciador:
    # note_on liga a nota no tempo inicial;
    # note_off desliga a nota no tempo final.
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

    # Usa a duracao da melodia como limite de reproducao.
    duracao_total = duracao_musica

    # Avanca o sequenciador em passos de 10 ms.
    # O sleep sincroniza o tempo processado com a passagem real do tempo.
    for tempo in range(0, duracao_total + 10, 10):
        print(tempo)
        seq.process(tempo)
        time.sleep(0.01)
