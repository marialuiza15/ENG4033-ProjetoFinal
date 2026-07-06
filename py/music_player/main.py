import os
import json
import platform
from pathlib import Path
import time
import sys
import threading

import serial
import serial.tools.list_ports


# =========================
# CAMINHOS DO PROJETO
# =========================

PASTA_ATUAL = Path(__file__).resolve().parent
PASTA_PY = PASTA_ATUAL.parent
PASTA_IA = PASTA_PY / "ia"
PASTA_ARQUIVOS = PASTA_ATUAL / "arquivos_musicais"

SOUNDFONT = PASTA_ARQUIVOS / "FluidR3_GM.sf2"


# =========================
# FLUIDSYNTH / DLLS
# =========================

def localizar_fluidsynth_bin():
    candidatos = [
        PASTA_ARQUIVOS / "fluidsynth-v2.5.6-win10-x64-cpp11" / "bin",
        PASTA_ARQUIVOS
        / "fluidsynth-v2.5.6-win10-x64-cpp11"
        / "fluidsynth-v2.5.6-win10-x64-cpp11"
        / "bin",
        PASTA_ARQUIVOS / "fluidsynth-v2.5.5-win10-x64-cpp11" / "bin",
        PASTA_ARQUIVOS
        / "fluidsynth-v2.5.5-win10-x64-cpp11"
        / "fluidsynth-v2.5.5-win10-x64-cpp11"
        / "bin",
    ]

    for candidato in candidatos:
        if candidato.exists():
            return candidato

    return None

if platform.system() == "Windows":
    FLUIDSYNTH_BIN = localizar_fluidsynth_bin()

    if FLUIDSYNTH_BIN is not None:
        os.add_dll_directory(str(FLUIDSYNTH_BIN))
        os.environ["PATH"] = str(FLUIDSYNTH_BIN) + os.pathsep + os.environ["PATH"]
    else:
        print(f"[AVISO] Pasta do Fluidsynth não encontrada em {PASTA_ARQUIVOS}")


import fluidsynth


# =========================
# IMPORT DA IA
# =========================

sys.path.insert(0, str(PASTA_PY))

from ia.audioLeitura import gerar_sequencia_musical


# =========================
# MAPAS
# =========================

notas_map = {
    "DO": 60,
    "RE": 62,
    "MI": 64,
    "FA": 65,
    "SOL": 67,
    "LA": 69,
    "SI": 71,
}


INSTRUMENTOS = {
    "Piano": {"canal": 0, "programa": 0},
    "Guitarra": {"canal": 2, "programa": 27},
    "Orgao": {"canal": 4, "programa": 19},
    "Flauta": {"canal": 6, "programa": 73},
    "Bateria": {"canal": 9, "programa": 0},
}


# =========================
# ESTADO GLOBAL DO PROGRAMA
# =========================

estado_musica = {
    "instrumento": "Orgao",
    "bpm": 100,
    "estilo": "Rock",
}

instrumento_atual = "Orgao"

estado_lock = threading.Lock()

batida_stop_event = threading.Event()
musica_stop_event = threading.Event()

thread_batida = None
thread_musica = None

loop_notas = []
notas_ativas_loop = {}

loop_lock = threading.Lock()

inicio_ciclo_loop = time.time()
duracao_ciclo_atual = 2000
gravando = False


# =========================
# JSON
# =========================

def carregar_json(caminho):
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def salvar_json(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, indent=4, ensure_ascii=False)


# =========================
# INICIALIZAÇÃO DO ÁUDIO
# =========================

fs = fluidsynth.Synth()

if platform.system() == "Windows":
    fs.start(driver="wasapi", midi_driver="none")
else:
    fs.start(driver="coreaudio", midi_driver="coremidi")

sfid = fs.sfload(str(SOUNDFONT))

for instrumento in INSTRUMENTOS.values():
    fs.program_select(
        instrumento["canal"],
        sfid,
        0,
        instrumento["programa"]
    )


# =========================
# FUNÇÕES DE MÚSICA
# =========================

def preparar_sequencia(musica):
    sequencia_convertida = []

    for evento in musica["sequencia"]:
        novo_evento = evento.copy()

        if "instrumento" not in novo_evento:
            novo_evento["instrumento"] = musica["instrumento"]

        sequencia_convertida.append(novo_evento)

    return sequencia_convertida

def obter_posicao_no_loop():
    global inicio_ciclo_loop, duracao_ciclo_atual

    agora = time.time()

    with loop_lock:
        tempo_decorrido_ms = int((agora - inicio_ciclo_loop) * 1000)
        posicao = tempo_decorrido_ms % duracao_ciclo_atual

    return posicao

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

        if "instrumento" not in novo_evento:
            novo_evento["instrumento"] = "Bateria"

        eventos.append(novo_evento)

    duracao_padrao = ajustar_tempo_batida(batida["duracao_padrao"], bpm)

    return eventos, duracao_padrao


def snapshot_estado_musica():
    with estado_lock:
        return estado_musica.copy()

def processar_configuracao(dados):
    global instrumento_atual
    with estado_lock:
        estado_musica["instrumento"] = dados["instrumento"]
        estado_musica["bpm"] = dados["bpm"]
        estado_musica["estilo"] = dados["estilo"]

    instrumento_atual = dados["instrumento"]

#o evento seriam as notas no formato de "nota": 64, "inicio": 500, "duracao": 500, "instrumento": "flauta"
def tocar_eventos(eventos, parar_evento, duracao_total):
    seq = fluidsynth.Sequencer(use_system_timer=False)
    synth_id = seq.register_fluidsynth(fs)

    for evento in eventos:
        inst = evento.get("instrumento", "piano") #tenta pegar o instrumento, se nao tem é piano
        canal = INSTRUMENTOS[inst]["canal"]
        fim = evento["inicio"] + evento["duracao"]
        seq.note_on(evento["inicio"], canal, evento["nota"], 100, dest=synth_id)
        seq.note_off(fim, canal, evento["nota"], dest=synth_id)

    tempo = 0
    while tempo <= duracao_total and not parar_evento.is_set():
        seq.process(tempo)
        time.sleep(0.01)
        tempo += 10


#funcao que prepara a musica para chamar o tocar eventos, transforma musica em sequencia e tb da a duracao
def tocar_melodia(musica, parar_evento):
    #adiciona o instrumento no final de cada nota
    sequencia=preparar_sequencia(musica)
    #calcula a duracai
    duracao=calcular_duracao(sequencia)
    #toca a sequencia efetivamente
    tocar_eventos(sequencia,parar_evento,duracao)


#faz rodar em thread
def tocar_musica_em_thread(musica):
    global thread_musica
    #verifica se a musica existe e se esta tocando
    if thread_musica is not None and thread_musica.is_alive():
        musica_stop_event.set()
        thread_musica.join(timeout=1)
    #limpa o evento de parar a musica para reiniciar a nova musica
    musica_stop_event.clear()

    #reiniciando a nova musica
    thread_musica=threading.Thread(target=tocar_melodia, args=(musica, musica_stop_event), daemon=True)
    thread_musica.start()

def loop_batida():
    batidas = carregar_json(PASTA_ARQUIVOS / "batidas.json")
    global inicio_ciclo_loop, duracao_ciclo_atual

    #enquanto a batida nao for parada, ele pega o estado atual das configuracoes e atribui ao estilo e bpm que vamos usar
    while not batida_stop_event.is_set():
        estado = snapshot_estado_musica()
        estilo = estado["estilo"]
        bpm = estado["bpm"]

        #chama a preparar batida para de fato preparar a batida
        eventos, duracao = preparar_batida(batidas[estilo], bpm)
        
        #
        with loop_lock:
            inicio_ciclo_loop = time.time()
            duracao_ciclo_atual = duracao
            eventos_completos = eventos + loop_notas.copy()
        #chama a tocar eventos com as configuracoes que criamos
        tocar_eventos(eventos_completos, batida_stop_event, duracao)


def iniciar_batida():
    global thread_batida
    batida_stop_event.clear()
    thread_batida=threading.Thread(target=loop_batida, daemon=True)
    thread_batida.start()

def parar_batida():
    batida_stop_event.set()
    thread_batida.join(timeout=1)

# =========================
# FUNÇÕES DA SERIAL
# =========================

def listar_portas():
    portas = serial.tools.list_ports.comports()

    if not portas:
        print("Nenhuma porta serial encontrada.")
        return

    print("Portas disponíveis:")

    for porta in portas:
        print(f"{porta.device} - {porta.description}")


#pega o estado atual da musica e salva em um json com as configuracoes corretas
def montar_musica_completa(sequencia):

    estado = snapshot_estado_musica()

    musica_completa = {
        "instrumento": estado["instrumento"],
        "bpm": estado["bpm"],
        "estilo": estado["estilo"],
        "sequencia": sequencia,
    }

    return musica_completa

#toca em tempo real as teclas
def processar_tecla(dados):
    nota=notas_map[dados["nota"]]
    canal=INSTRUMENTOS[instrumento_atual]["canal"]
    nota_id = dados["nota"]  # ex: "DO"

    #toca e para de tocar de acordo com a ativa
    if dados["ativa"]:
        # toca ao vivo
        fs.noteon(canal, nota, 100)
        # grava início
        if gravando:
            inicio = obter_posicao_no_loop()
            with loop_lock:
                #dentro desse lock, criamos uma lista inicial para salvar as notas que foram clicadas (ainda nao sabemos quando vao ser soltas)
                notas_ativas_loop[nota_id] = {
                    "nota": nota,
                    "inicio": inicio,
                    "instrumento": instrumento_atual,
                }
    else:
        fs.noteoff(canal, nota)
        # grava fim
        if gravando:
            fim = obter_posicao_no_loop()
            with loop_lock:
                #verifica se a nota que soltamos esta de fato dentro da lista anterior que criamos
                if nota_id in notas_ativas_loop:
                    #se sim, salva a nota em especifico e retira ela da lista
                    salva = notas_ativas_loop.pop(nota_id)
                    inicio = salva["inicio"]
                    #calculo para saber onde encaixar a nota no loop da batida
                    if fim >= inicio:
                        duracao = fim - inicio
                    else:
                        duracao = duracao_ciclo_atual - inicio + fim
                    #adiciona no loop, toca junto e nao é um arquivo .json
                    loop_notas.append({
                        "nota": salva["nota"],
                        "inicio": inicio,
                        "duracao": duracao,
                        "instrumento": salva["instrumento"],
                    })

#converte a lista, de nota para numero identificador SOL-> 67
def converter_notas_recebidas(notas_recebidas):
    conversao=[]
    for notas in notas_recebidas:
        novo=notas.copy()
        novo["nota"]=notas_map[notas["nota"]]
        conversao.append(novo)
    return conversao

#recebe o json do arduino, modifica com a IA e toca
def processar_sequencia(sequencia_notas_recebidas):
    #converte as notas SOL-> 67
    convertidas=converter_notas_recebidas(sequencia_notas_recebidas["notas"])
    #monta a musica de acordo com as configuracoes recebidas
    musica_completa=montar_musica_completa(convertidas)
    #modifica a musica com a IA
    #se for teste nao roda esse trecho
    musica_ia=gerar_sequencia_musical(musica_completa)
    #toca a musica em thread
    tocar_musica_em_thread(musica_ia)

#recebe dados do arduino e verifica qual funcao usar
def processar_dados(dados):
    if "gravando" in dados:
        global gravando
        gravando = dados["gravando"]
        if gravando:
            with loop_lock:
                loop_notas.clear()
                notas_ativas_loop.clear()
                inicio_ciclo_loop = time.time() 
        return

    #se tem notas, significa que é a sequencia
    if "notas" in dados:
        processar_sequencia(dados)
    #se tem instrumento e bpm significa que é a configuracao
    elif "instrumento" in dados and "bpm" in dados:
        processar_configuracao(dados)
    #se tem nota (singular) e ativa significa que é a nota padrao
    elif "nota" in dados and "ativa" in dados:
        processar_tecla(dados)

# =========================
# TESTE SEM ARDUINO
# =========================

def testar_sem_arduino():
    print("\n[TESTE] Rodando sem Arduino...\n")

    dados_config = {
        "instrumento": "Orgao",
        "bpm": 120,
        "estilo": "Rock"
    }

    processar_configuracao(dados_config)

    print("[TESTE] A batida deve estar rodando em paralelo.")
    time.sleep(2)

    print("[TESTE] Tocando notas em tempo real...")

    processar_tecla({"nota": "DO", "ativa": True})
    time.sleep(0.4)
    processar_tecla({"nota": "DO", "ativa": False})

    processar_tecla({"nota": "MI", "ativa": True})
    time.sleep(0.4)
    processar_tecla({"nota": "MI", "ativa": False})

    processar_tecla({"nota": "SOL", "ativa": True})
    time.sleep(0.4)
    processar_tecla({"nota": "SOL", "ativa": False})

    dados_notas = {
        "notas": [
            {"nota": "DO", "inicio": 0, "duracao": 500},
            {"nota": "MI", "inicio": 500, "duracao": 500},
            {"nota": "SOL", "inicio": 1000, "duracao": 500},
            {"nota": "DO", "inicio": 1500, "duracao": 1000},
        ]
    }

    processar_dados(dados_notas)

    time.sleep(5)

    print("\n[TESTE] Finalizado.\n")


# =========================
# MAIN
# =========================

def main():
    iniciar_batida()
    listar_portas()
    
    porta = input("\nDigite a porta do Arduino ou ENTER para modo teste: ").strip()
    
    if porta == "":
        testar_sem_arduino()
        parar_batida()
        musica_stop_event.set()
        fs.delete()
        return
    
    ser = serial.Serial(porta, 9600, timeout=2)
    print(f"\nConectado em {porta}. Aguardando dados...\n")
    #momento em que esperamos a resposta do arduino nos mandando todo o conteudo, aqui significa que o programa do arduino ja fez sua parte e entregou o json 
    while True:
        linha = ser.readline().decode("utf-8").strip()
        if not linha:
            continue
        dados = json.loads(linha)
        processar_dados(dados)


main()