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

if platform.system() == "Windows":
    FLUIDSYNTH_BIN = (
        PASTA_ARQUIVOS
        / "fluidsynth-v2.5.5-win10-x64-cpp11"
        / "bin"
    )

    os.add_dll_directory(str(FLUIDSYNTH_BIN))
    os.environ["PATH"] = str(FLUIDSYNTH_BIN) + os.pathsep + os.environ["PATH"]


import fluidsynth


# =========================
# IMPORT DA IA
# =========================

sys.path.insert(0, str(PASTA_IA))

from audioLeitura import gerar_sequencia_musical


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

instrumentos_map = {
    "Piano": "piano",
    "Orgao": "orgao",
    "Órgão": "orgao",
    "Flauta": "flauta",
    "Guitarra": "guitarra",
    "Bateria": "bateria",
    "Baixo": "baixo",
    "Sintetizador": "sintetizador",
    "Strings": "strings",
}

estilo_map = {
    "Rock": "rock",
    "Jazz": "Jazz",
    "Samba": "Samba",
    "Escolha da IA": "completo",
}

INSTRUMENTOS = {
    "piano": {"canal": 0, "programa": 0},
    "baixo": {"canal": 1, "programa": 33},
    "guitarra": {"canal": 2, "programa": 27},
    "sintetizador": {"canal": 3, "programa": 89},
    "orgao": {"canal": 4, "programa": 19},
    "strings": {"canal": 5, "programa": 48},
    "flauta": {"canal": 6, "programa": 73},
    "bateria": {"canal": 9, "programa": 0},
}


# =========================
# ESTADO GLOBAL DO PROGRAMA
# =========================

estado_musica = {
    "instrumento": "orgao",
    "bpm": 100,
    "estilo": "rock",
}

instrumento_atual = "orgao"

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
            novo_evento["instrumento"] = "bateria"

        eventos.append(novo_evento)

    duracao_padrao = ajustar_tempo_batida(batida["duracao_padrao"], bpm)

    return eventos, duracao_padrao


def snapshot_estado_musica():
    with estado_lock:
        return estado_musica.copy()


# =========================
# THREAD DA BATIDA CONTÍNUA
# =========================

def loop_batida():
    print("[BATIDA] Thread da batida iniciada.")

    batidas = carregar_json(PASTA_ARQUIVOS / "batidas.json")

    while not batida_stop_event.is_set():
        estado = snapshot_estado_musica()

        estilo = estado["estilo"]
        bpm = estado["bpm"]

        if estilo not in batidas:
            print(f"[BATIDA] Estilo '{estilo}' não encontrado.")
            time.sleep(0.5)
            continue

        batida = batidas[estilo]
        eventos_batida, duracao_batida = preparar_batida(batida, bpm)
        global inicio_ciclo_loop, duracao_ciclo_atual

        with loop_lock:
            inicio_ciclo_loop = time.time()
            duracao_ciclo_atual = duracao_batida

        seq = fluidsynth.Sequencer(use_system_timer=False)
        synth_id = seq.register_fluidsynth(fs)

        for evento in eventos_batida:
            nota = evento["nota"]
            inicio = evento["inicio"]
            duracao = evento["duracao"]
            fim = inicio + duracao

            canal = INSTRUMENTOS["bateria"]["canal"]

            seq.note_on(inicio, canal, nota, 100, dest=synth_id)
            seq.note_off(fim, canal, nota, dest=synth_id)


        with loop_lock:
            notas_do_loop = loop_notas.copy()

        for evento in notas_do_loop:
            instrumento = evento["instrumento"]

            if instrumento not in INSTRUMENTOS:
                continue

            canal = INSTRUMENTOS[instrumento]["canal"]

            nota = evento["nota"]
            inicio = evento["inicio"]
            duracao = evento["duracao"]
            fim = inicio + duracao

            seq.note_on(inicio, canal, nota, 100, dest=synth_id)
            seq.note_off(fim, canal, nota, dest=synth_id)

        tempo = 0

        while tempo <= duracao_batida and not batida_stop_event.is_set():
            seq.process(tempo)
            time.sleep(0.01)
            tempo += 10

    print("[BATIDA] Thread da batida encerrada.")


def iniciar_batida():
    global thread_batida

    batida_stop_event.clear()

    thread_batida = threading.Thread(
        target=loop_batida,
        daemon=True
    )

    thread_batida.start()


def parar_batida():
    batida_stop_event.set()


# =========================
# THREAD DA MÚSICA GERADA
# =========================

def tocar_melodia(musica_completa, stop_event):
    sequencia = preparar_sequencia(musica_completa)

    if not sequencia:
        print("[PLAY] Sequência vazia.")
        return

    seq = fluidsynth.Sequencer(use_system_timer=False)
    synth_id = seq.register_fluidsynth(fs)

    duracao_musica = calcular_duracao(sequencia)

    for evento in sequencia:
        instrumento = evento["instrumento"]

        if instrumento not in INSTRUMENTOS:
            print(f"[AVISO] Instrumento desconhecido: {instrumento}")
            continue

        canal = INSTRUMENTOS[instrumento]["canal"]

        nota = evento["nota"]
        inicio = evento["inicio"]
        duracao = evento["duracao"]
        fim = inicio + duracao

        seq.note_on(inicio, canal, nota, 100, dest=synth_id)
        seq.note_off(fim, canal, nota, dest=synth_id)

    tempo_atual = 0

    while tempo_atual <= duracao_musica and not stop_event.is_set():
        seq.process(tempo_atual)
        time.sleep(0.01)
        tempo_atual += 10

    print("[PLAY] Música finalizada.")


def tocar_musica_em_thread(musica_completa):
    global thread_musica

    if thread_musica is not None and thread_musica.is_alive():
        print("[PLAY] Parando música anterior...")
        musica_stop_event.set()
        thread_musica.join(timeout=1)

    musica_stop_event.clear()

    thread_musica = threading.Thread(
        target=tocar_melodia,
        args=(musica_completa, musica_stop_event),
        daemon=True
    )

    thread_musica.start()


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


def converter_notas_recebidas(notas_recebidas):
    sequencia = []

    for n in notas_recebidas:
        midi = notas_map.get(n["nota"])

        if midi is not None:
            sequencia.append({
                "nota": midi,
                "inicio": n["inicio"],
                "duracao": n["duracao"],
            })
        else:
            print(f"[AVISO] Nota desconhecida recebida: {n['nota']}")

    return sequencia


def montar_musica_completa(sequencia):
    estado = snapshot_estado_musica()

    musica_completa = {
        "instrumento": estado["instrumento"],
        "bpm": estado["bpm"],
        "estilo": estado["estilo"],
        "sequencia": sequencia,
    }

    return musica_completa


def gerar_musica_com_retry(musica_completa, tentativas=3):
    for tentativa in range(1, tentativas + 1):
        try:
            print(f"[IA] Tentativa {tentativa}/{tentativas}...")
            return gerar_sequencia_musical(musica_completa), True

        except Exception as erro:
            print(f"[IA] Falha na tentativa {tentativa}: {erro}")

            if tentativa < tentativas:
                time.sleep(2)

    print("[IA] Todas as tentativas falharam. Usando música original.")
    return musica_completa, False


def processar_sequencia(dados):
    sequencia = converter_notas_recebidas(dados["notas"])

    salvar_json(
        PASTA_ARQUIVOS / "notas.json",
        {"sequencia": sequencia}
    )

    print(f"[SEQUENCIA] {len(sequencia)} nota(s) salvas em notas.json")

    musica_completa = montar_musica_completa(sequencia)

    salvar_json(
        PASTA_ARQUIVOS / "musica_completa.json",
        musica_completa
    )

    print("[IA] Gerando música...")

    musica_gerada, usou_ia = gerar_musica_com_retry(musica_completa)

    salvar_json(
        PASTA_ARQUIVOS / "musica_gerada.json",
        musica_gerada
    )

    if usou_ia:
        print("[IA] Música gerada e salva em musica_gerada.json")
        print("[PLAY] Tocando música GERADA PELA IA...")
    else:
        print("[PLAY] Tocando música ORIGINAL, sem IA...")

    tocar_musica_em_thread(musica_gerada)


def processar_configuracao(dados):
    global instrumento_atual

    instrumento = instrumentos_map.get(dados["instrumento"], "piano")
    bpm = dados["bpm"]
    estilo = estilo_map.get(dados["estilo"], "rock")

    with estado_lock:
        estado_musica["instrumento"] = instrumento
        estado_musica["bpm"] = bpm
        estado_musica["estilo"] = estilo

    instrumento_atual = instrumento

    salvar_json(
        PASTA_ARQUIVOS / "parametros.json",
        snapshot_estado_musica()
    )

    print(
        "[CONFIG] "
        f"instrumento={instrumento} "
        f"bpm={bpm} "
        f"estilo={estilo}"
    )


def processar_tecla(dados):
    midi = notas_map.get(dados["nota"])

    if midi is None:
        print(f"[AVISO] Nota desconhecida: {dados['nota']}")
        return

    instrumento = instrumento_atual

    if instrumento not in INSTRUMENTOS:
        print(f"[AVISO] Instrumento atual inválido: {instrumento}")
        return

    canal = INSTRUMENTOS[instrumento]["canal"]

    nota_id = dados["nota"]

    if dados["ativa"]:
        fs.noteon(canal, midi, 100)

        inicio_loop = obter_posicao_no_loop()

        with loop_lock:
            notas_ativas_loop[nota_id] = {
                "nota": midi,
                "inicio": inicio_loop,
                "instrumento": instrumento,
            }

        print(f"[TECLA] PRESS {dados['nota']} | salvo início no loop em {inicio_loop} ms")

    else:
        fs.noteoff(canal, midi)

        fim_loop = obter_posicao_no_loop()

        with loop_lock:
            if nota_id in notas_ativas_loop:
                nota_salva = notas_ativas_loop.pop(nota_id)

                inicio = nota_salva["inicio"]

                if fim_loop >= inicio:
                    duracao = fim_loop - inicio
                else:
                    duracao = duracao_ciclo_atual - inicio + fim_loop

                if duracao < 50:
                    duracao = 100

                loop_notas.append({
                    "nota": nota_salva["nota"],
                    "inicio": inicio,
                    "duracao": duracao,
                    "instrumento": nota_salva["instrumento"],
                })

                print(
                    f"[LOOP] Nota salva: {dados['nota']} "
                    f"inicio={inicio} duracao={duracao}"
                )

        print(f"[TECLA] RELEASE {dados['nota']}")


def processar_dados(dados):
    if "notas" in dados:
        processar_sequencia(dados)

    elif "instrumento" in dados and "bpm" in dados:
        processar_configuracao(dados)

    elif "nota" in dados and "ativa" in dados:
        processar_tecla(dados)

    else:
        print(f"[OUTRO] {dados}")


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

    processar_sequencia(dados_notas)

    time.sleep(5)

    print("\n[TESTE] Finalizado.\n")


# =========================
# MAIN
# =========================

def main():
    iniciar_batida()

    listar_portas()

    porta = input(
        "\nDigite a porta do Arduino ou ENTER para modo teste: "
    ).strip()

    if porta == "":
        try:
            testar_sem_arduino()

        finally:
            parar_batida()
            musica_stop_event.set()
            fs.delete()

        return

    try:
        ser = serial.Serial(porta, 9600, timeout=2)
        print(f"\nConectado em {porta}. Aguardando dados...\n")

    except Exception as erro:
        print(f"Erro ao abrir porta: {erro}")
        parar_batida()
        fs.delete()
        return

    while True:
        try:
            linha = ser.readline().decode("utf-8").strip()

            if not linha:
                continue

            try:
                dados = json.loads(linha)
                processar_dados(dados)

            except json.JSONDecodeError:
                print(f"[RAW] {linha}")

        except KeyboardInterrupt:
            print("\nEncerrando.")

            ser.close()

            parar_batida()
            musica_stop_event.set()

            fs.delete()
            break


main()