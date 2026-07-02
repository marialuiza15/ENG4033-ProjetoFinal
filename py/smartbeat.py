"""
SmartBeat — Simulador de terminal + Player FluidSynth

Modo simulador: substitui o Arduino com menus no terminal.
Modo serial   : trocar `rodar_simulador()` por `rodar_serial()` quando
                o Arduino estiver conectado.

Mensagens processadas (mesmo formato que o Arduino envia):
  {"nota": "DO", "ativa": true/false}          — tecla pressionada/solta
  {"instrumento": "Piano", "bpm": 120,
   "estilo": "Rock"}                            — configuração do encoder
  {"notas": [{"nota":"DO","inicio":0,
              "duracao":300}, ...]}             — sequência gravada
"""

import json
import time
import threading
from pathlib import Path

# ── Caminhos ────────────────────────────────────────────────────────────────
PASTA_ATUAL      = Path(__file__).resolve().parent
PASTA_ARQUIVOS   = PASTA_ATUAL / "music_player" / "arquivos_musicais"
SOUNDFONT        = str(PASTA_ARQUIVOS / "FluidR3_GM.sf2")

# ── Mapeamentos ──────────────────────────────────────────────────────────────
NOTA_PARA_MIDI = {
    "DO": 60, "RE": 62, "MI": 64, "FA": 65,
    "SOL": 67, "LA": 69, "SI": 71
}

# Converte nome do instrumento (Arduino) para chave interna
INSTRUMENTO_MAP = {
    "Piano":    "piano",
    "Orgao":    "orgao",
    "Flauta":   "flauta",
    "Guitarra": "guitarra",
    "Bateria":  "bateria",
}

# Converte estilo (Arduino) para chave do batidas.json
ESTILO_MAP = {
    "Rock":         "rock",
    "Jazz":         "hihat",
    "Samba":        "simples",
    "Escolha da IA":"completo",
}

INSTRUMENTOS = {
    "piano":       {"canal": 0, "programa": 0},
    "baixo":       {"canal": 1, "programa": 33},
    "guitarra":    {"canal": 2, "programa": 27},
    "sintetizador":{"canal": 3, "programa": 89},
    "orgao":       {"canal": 4, "programa": 19},
    "flauta":      {"canal": 6, "programa": 73},
    "strings":     {"canal": 5, "programa": 48},
    "bateria":     {"canal": 9, "programa": 0},
}

NOTAS_MENU   = ["DO", "RE", "MI", "FA", "SOL", "LA", "SI"]
ESTILOS      = ["Rock", "Jazz", "Samba", "Escolha da IA"]
INSTRUMENTOS_LISTA = ["Piano", "Orgao", "Flauta", "Guitarra", "Bateria"]

# ── Estado global ────────────────────────────────────────────────────────────
config = {"instrumento": "Piano", "bpm": 100, "estilo": "Rock"}

gravando          = False
notas_gravadas    = []          # [{"nota": "DO", "inicio": ms, "duracao": ms}]
tempo_ultima_nota = None        # timestamp do último noteoff

# ── FluidSynth ───────────────────────────────────────────────────────────────
fs             = None
sfid           = None
fs_disponivel  = False

def iniciar_fluidsynth():
    global fs, sfid, fs_disponivel
    try:
        import fluidsynth
        fs   = fluidsynth.Synth()
        fs.start(driver="coreaudio", midi_driver="coremidi")
        sfid = fs.sfload(SOUNDFONT)
        if sfid == -1:
            raise Exception("SoundFont inválido ou corrompido.")
        for inst in INSTRUMENTOS.values():
            fs.program_select(inst["canal"], sfid, 0, inst["programa"])
        fs_disponivel = True
        print("[FluidSynth] Iniciado com sucesso.")
    except Exception as e:
        print(f"[FluidSynth] Indisponível — rodando sem áudio. ({e})")

def canal_atual():
    nome = INSTRUMENTO_MAP.get(config["instrumento"], "piano")
    return INSTRUMENTOS[nome]["canal"]

def nota_on(nome_nota):
    midi = NOTA_PARA_MIDI.get(nome_nota)
    if midi and fs_disponivel:
        fs.noteon(canal_atual(), midi, 100)

def nota_off(nome_nota):
    midi = NOTA_PARA_MIDI.get(nome_nota)
    if midi and fs_disponivel:
        fs.noteoff(canal_atual(), midi)

# ── Gravação ─────────────────────────────────────────────────────────────────
def registrar_press(nome_nota):
    global tempo_ultima_nota
    agora = time.time() * 1000
    pausa = int(agora - tempo_ultima_nota) if tempo_ultima_nota else 0
    nota_on(nome_nota)
    return {"nota": nome_nota, "pausa": pausa, "_inicio_ms": agora}

def registrar_release(evento_aberto):
    global tempo_ultima_nota
    agora = time.time() * 1000
    duracao = int(agora - evento_aberto["_inicio_ms"])
    nota_off(evento_aberto["nota"])
    tempo_ultima_nota = agora
    return {
        "nota":    evento_aberto["nota"],
        "inicio":  evento_aberto["pausa"],
        "duracao": duracao,
    }

# ── Playback de sequência ────────────────────────────────────────────────────
def carregar_json(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_json(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def ajustar_bpm(valor_ms, bpm, bpm_base=120):
    return int(valor_ms * (bpm_base / bpm))

def tocar_nota_thread(canal, midi, duracao_ms):
    if not fs_disponivel:
        return
    fs.noteon(canal, midi, 100)
    time.sleep(duracao_ms / 1000)
    fs.noteoff(canal, midi)

def tocar_sequencia(notas_list):
    """Recebe lista de {"nota":"DO","inicio":ms,"duracao":ms} e toca."""
    bpm   = config["bpm"]
    canal = canal_atual()
    batidas = carregar_json(PASTA_ARQUIVOS / "batidas.json")

    # Converte notas de string para MIDI e ajusta BPM
    eventos = []
    inicio_acumulado = 0
    for n in notas_list:
        midi = NOTA_PARA_MIDI.get(n["nota"])
        if not midi:
            continue
        inicio   = ajustar_bpm(inicio_acumulado, bpm)
        duracao  = ajustar_bpm(n["duracao"], bpm)
        eventos.append({"midi": midi, "canal": canal, "inicio": inicio, "duracao": duracao})
        inicio_acumulado += n["inicio"] + n["duracao"]

    # Adiciona batida do estilo selecionado
    chave_estilo = ESTILO_MAP.get(config["estilo"], "rock")
    if chave_estilo in batidas:
        batida = batidas[chave_estilo]
        duracao_musica = max((e["inicio"] + e["duracao"]) for e in eventos) if eventos else 0
        deslocamento   = 0
        while deslocamento < duracao_musica:
            for ev in batida["eventos"]:
                inst_bateria = INSTRUMENTOS["bateria"]
                eventos.append({
                    "midi":    ev["nota"],
                    "canal":   inst_bateria["canal"],
                    "inicio":  ev["inicio"] + deslocamento,
                    "duracao": ev["duracao"],
                })
            deslocamento += ajustar_bpm(batida["duracao_padrao"], bpm)

    if not eventos:
        print("[Player] Nenhuma nota para tocar.")
        return

    print(f"[Player] Tocando {len(notas_list)} nota(s) — instrumento={config['instrumento']} bpm={bpm} estilo={config['estilo']}")
    eventos.sort(key=lambda e: e["inicio"])

    # Salva para histórico
    salvar_json(PASTA_ARQUIVOS / "notas.json",      {"sequencia": [{"nota": e["midi"], "inicio": e["inicio"], "duracao": e["duracao"]} for e in eventos if e["canal"] == canal]})
    salvar_json(PASTA_ARQUIVOS / "parametros.json", {"instrumento": INSTRUMENTO_MAP.get(config["instrumento"], "piano"), "bpm": bpm, "estilo": chave_estilo})

    # Toca com threads para suportar notas simultâneas
    inicio_ref = time.time() * 1000
    threads    = []
    for e in eventos:
        agora  = time.time() * 1000 - inicio_ref
        espera = (e["inicio"] - agora) / 1000
        if espera > 0:
            time.sleep(espera)
        t = threading.Thread(target=tocar_nota_thread, args=(e["canal"], e["midi"], e["duracao"]))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()
    print("[Player] Fim.")

# ── Processador central de mensagens ────────────────────────────────────────
def processar_mensagem(dados: dict):
    """Ponto único de entrada — mesmo handler para serial e simulador."""
    global config, gravando, notas_gravadas, tempo_ultima_nota

    if "notas" in dados:
        # Sequência gravada recebida — toca
        tocar_sequencia(dados["notas"])

    elif "instrumento" in dados and "bpm" in dados:
        # Configuração do encoder
        config.update({
            "instrumento": dados["instrumento"],
            "bpm":         dados["bpm"],
            "estilo":      dados["estilo"],
        })
        print(f"[Config] instrumento={config['instrumento']}  bpm={config['bpm']}  estilo={config['estilo']}")

    elif "nota" in dados and "ativa" in dados:
        # Tecla pressionada / solta (tempo real)
        nome = dados["nota"]
        if dados["ativa"]:
            nota_on(nome)
            print(f"  ♪ {nome}")
        else:
            nota_off(nome)

# ── Menus do simulador ───────────────────────────────────────────────────────
def menu_configurar():
    while True:
        print(f"""
┌─ CONFIGURAR ──────────────────────────────┐
│  [1] BPM          atual: {config['bpm']}
│  [2] Estilo       atual: {config['estilo']}
│  [3] Instrumento  atual: {config['instrumento']}
│  [0] Voltar
└───────────────────────────────────────────┘""")
        op = input("> ").strip()

        if op == "1":
            val = input(f"BPM (20–300) [{config['bpm']}]: ").strip()
            if val.isdigit() and 20 <= int(val) <= 300:
                config["bpm"] = int(val)
                processar_mensagem({**config})

        elif op == "2":
            for i, e in enumerate(ESTILOS, 1):
                print(f"  [{i}] {e}")
            sel = input("> ").strip()
            if sel.isdigit() and 1 <= int(sel) <= len(ESTILOS):
                config["estilo"] = ESTILOS[int(sel) - 1]
                processar_mensagem({**config})

        elif op == "3":
            for i, inst in enumerate(INSTRUMENTOS_LISTA, 1):
                print(f"  [{i}] {inst}")
            sel = input("> ").strip()
            if sel.isdigit() and 1 <= int(sel) <= len(INSTRUMENTOS_LISTA):
                config["instrumento"] = INSTRUMENTOS_LISTA[int(sel) - 1]
                processar_mensagem({**config})

        elif op == "0":
            break

def menu_teclas():
    global gravando, notas_gravadas, tempo_ultima_nota

    while True:
        status_grav = "● GRAVANDO" if gravando else "○ parado"
        print(f"""
┌─ TECLAS ──────────────────────────────────┐
│  [1] DO   [2] RE   [3] MI   [4] FA        │
│  [5] SOL  [6] LA   [7] SI                 │
│  [G] Iniciar/Parar gravação  ({status_grav})
│  [P] Tocar sequência gravada               │
│  [0] Voltar                                │
└───────────────────────────────────────────┘""")
        op = input("> ").strip().upper()

        if op in [str(i) for i in range(1, 8)]:
            nome = NOTAS_MENU[int(op) - 1]
            if gravando:
                ev = registrar_press(nome)
                time.sleep(0.3)     # simula duração da tecla pressionada
                nota = registrar_release(ev)
                notas_gravadas.append(nota)
                print(f"  Gravado: {nota}")
            else:
                # Toca sem gravar
                processar_mensagem({"nota": nome, "ativa": True})
                time.sleep(0.3)
                processar_mensagem({"nota": nome, "ativa": False})

        elif op == "G":
            if not gravando:
                notas_gravadas    = []
                tempo_ultima_nota = time.time() * 1000
                gravando          = True
                print("  [REC] Gravação iniciada.")
            else:
                gravando = False
                print(f"  [REC] Gravação parada — {len(notas_gravadas)} nota(s) capturada(s).")

        elif op == "P":
            if not notas_gravadas:
                print("  Nenhuma nota gravada ainda.")
            else:
                # Simula o botão play do Arduino
                processar_mensagem({"notas": notas_gravadas})

        elif op == "0":
            break

def rodar_simulador():
    while True:
        print(f"""
╔══════════════════════════════════════════╗
║           S M A R T B E A T             ║
╠══════════════════════════════════════════╣
║  [1] Configurar (LCD / Encoder)          ║
║  [2] Teclas / Gravar                     ║
║  [0] Sair                                ║
╚══════════════════════════════════════════╝
  instrumento={config['instrumento']}  bpm={config['bpm']}  estilo={config['estilo']}""")
        op = input("> ").strip()
        if op == "1":
            menu_configurar()
        elif op == "2":
            menu_teclas()
        elif op == "0":
            print("Saindo.")
            if fs:
                fs.delete()
            break

# ── Modo serial (usar quando o Arduino estiver conectado) ────────────────────
def rodar_serial(porta="/dev/tty.usbmodem1101", baud=9600):
    import serial
    ser = serial.Serial(porta, baud, timeout=1)
    print(f"[Serial] Conectado em {porta}. Aguardando Arduino...")
    try:
        while True:
            linha = ser.readline().decode("utf-8").strip()
            if not linha:
                continue
            try:
                processar_mensagem(json.loads(linha))
            except json.JSONDecodeError:
                print(f"[Serial RAW] {linha}")
    except KeyboardInterrupt:
        print("\nEncerrando.")
        ser.close()
        if fs:
            fs.delete()

# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    iniciar_fluidsynth()
    rodar_simulador()
    # Para usar com o Arduino, substitua a linha acima por:
    # rodar_serial("/dev/tty.usbmodem1101")
