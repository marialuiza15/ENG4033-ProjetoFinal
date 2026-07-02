import os
import json
import platform
from pathlib import Path
import time
import sys
import serial
import serial.tools.list_ports
import fluidsynth


if platform.system() == "Windows":
    FLUIDSYNTH_BIN = r"C:\Users\micro1\Downloads\fluidsynth\fluidsynth-v2.5.5-win10-x64-cpp11\bin"
    os.add_dll_directory(FLUIDSYNTH_BIN)
    os.environ["PATH"] = FLUIDSYNTH_BIN + os.pathsep + os.environ["PATH"]


PASTA_ATUAL = Path(__file__).resolve().parent
PASTA_PY = PASTA_ATUAL.parent
PASTA_ARQUIVOS = PASTA_ATUAL / "arquivos_musicais"
SOUNDFONT = str(PASTA_ARQUIVOS / "FluidR3_GM.sf2")


sys.path.insert(0, str(PASTA_PY))
from ia.audioLeitura import gerar_sequencia_musical


notas_map = {
    "DO": 60,
    "RE": 62,
    "MI": 64,
    "FA": 65,
    "SOL": 67,
    "LA": 69,
    "SI": 71
}

instrumentos_map = {
    "Piano": "piano",
    "Orgao": "orgao",
    "Flauta": "flauta",
    "Guitarra": "guitarra",
    "Bateria": "bateria",
}

estilo_map = {
    "Rock": "rock",
    "Jazz": "hihat",
    "Samba": "simples",
    "Escolha da IA": "completo",
}

INSTRUMENTOS = {
    "piano": {"canal": 0, "programa": 0},
    "baixo": {"canal": 1, "programa": 33},
    "guitarra": {"canal": 2, "programa": 27},
    "sintetizador": {"canal": 3, "programa": 89},
    "orgao": {"canal": 4, "programa": 19},
    "strings": {"canal": 5, "programa": 48},
    "bateria": {"canal": 9, "programa": 0},
}


instrumento_atual = "orgao"  # atualizado quando o encoder muda

fs = fluidsynth.Synth()
if platform.system() == "Windows":
    fs.start(driver="wasapi", midi_driver="none")
else:
    fs.start(driver="coreaudio", midi_driver="coremidi")

sfid = fs.sfload(SOUNDFONT)
for instrumento in INSTRUMENTOS.values():
    fs.program_select(instrumento["canal"], sfid, 0, instrumento["programa"])

# FUNÇÕES AUXILIARES 

def carregar_json(caminho):
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)

def salvar_json(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, indent=4, ensure_ascii=False)

# FUNÇÕES MÚSICA

def preparar_sequencia(musica):
    sequencia_convertida = []
    for evento in musica["sequencia"]:
        novo_evento = evento.copy()
        novo_evento["instrumento"] = musica["instrumento"]
        sequencia_convertida.append(novo_evento)
    return sequencia_convertida

def ajustar_tempo_batida(valor_ms, bpm, bpm_base=120):
    return int(valor_ms * (bpm_base / bpm))

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
        novo_evento["inicio"]  = ajustar_tempo_batida(evento["inicio"],  bpm)
        novo_evento["duracao"] = ajustar_tempo_batida(evento["duracao"], bpm)
        eventos.append(novo_evento)
    duracao_padrao = ajustar_tempo_batida(batida["duracao_padrao"], bpm)
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

# TOCAR MÚSICA 

def tocar_musica():
    batidas = carregar_json(PASTA_ARQUIVOS / "batidas.json")

    json_entrada = carregar_json(PASTA_ARQUIVOS / "musica_completa.json")
    json_recebido = gerar_sequencia_musical(json_entrada)
    salvar_json(PASTA_ARQUIVOS / "musica_gerada.json", json_recebido)

    musica_completa = json_recebido
    sequencia = preparar_sequencia(musica_completa)

    seq = fluidsynth.Sequencer(use_system_timer=False)
    synth_id = seq.register_fluidsynth(fs)

    duracao_musica = calcular_duracao(sequencia)
    batida = batidas[musica_completa["estilo"]]
    eventos_batida, duracao_batida = preparar_batida(batida, musica_completa["bpm"])
    batida_final = repetir_batida(eventos_batida, duracao_batida, duracao_musica)

    for evento in sequencia + batida_final:
        canal = INSTRUMENTOS[evento["instrumento"]]["canal"]
        fim = evento["inicio"] + evento["duracao"]
        seq.note_on(evento["inicio"], canal, evento["nota"], 100, dest=synth_id)
        seq.note_off(fim, canal, evento["nota"], dest=synth_id)

    for tempo in range(0, duracao_musica + 10, 10):
        seq.process(tempo)
        time.sleep(0.01)

# SERIAL 

def listar_portas():
    portas = serial.tools.list_ports.comports()
    if not portas:
        print("Nenhuma porta serial encontrada.")
        return
    print("Portas disponíveis:")
    for p in portas:
        print(f"{p.device} — {p.description}")

def main():
    listar_portas()
    porta = input("\nDigite a porta do Arduino (ex: /dev/tty.usbmodem1101): ").strip()

    try:
        ser = serial.Serial(porta, 9600, timeout=2)
        print(f"\nConectado em {porta}. Aguardando dados...\n")
    except Exception as e:
        print(f"Erro ao abrir porta: {e}")
        return

    while True:
        try:
            linha = ser.readline().decode("utf-8").strip()
            if not linha:
                continue

            try:
                dados = json.loads(linha)

                if "notas" in dados:
                    sequencia = []
                    inicio_acumulado = 0
                    for n in dados["notas"]:
                        midi = notas_map.get(n["nota"])
                        if midi:
                            sequencia.append({"nota": midi, "inicio": inicio_acumulado, "duracao": n["duracao"]})
                            inicio_acumulado += n["inicio"] + n["duracao"]
                    salvar_json(PASTA_ARQUIVOS / "notas.json", {"sequencia": sequencia})
                    print(f"[SEQUENCIA] {len(sequencia)} nota(s) salvas em notas.json")

                    params = carregar_json(PASTA_ARQUIVOS / "parametros.json")
                    musica_completa = {
                        "instrumento": params["instrumento"],
                        "bpm": params["bpm"],
                        "estilo": params["estilo"],
                        "sequencia": sequencia,
                    }
                    salvar_json(PASTA_ARQUIVOS / "musica_completa.json", musica_completa)

                    tocar_musica()

                elif "instrumento" in dados and "bpm" in dados:
                    global instrumento_atual
                    params = {
                        "instrumento": instrumentos_map.get(dados["instrumento"], "piano"),
                        "bpm": dados["bpm"],
                        "estilo": estilo_map.get(dados["estilo"], "rock"),
                    }
                    instrumento_atual = params["instrumento"]
                    salvar_json(PASTA_ARQUIVOS / "parametros.json", params)
                    print(f"[CONFIG]    instrumento={params['instrumento']}  bpm={params['bpm']}  estilo={params['estilo']}")

                elif "nota" in dados and "ativa" in dados:
                    midi = notas_map.get(dados["nota"])
                    if midi:
                        canal = INSTRUMENTOS[instrumento_atual]["canal"]
                        if dados["ativa"]:
                            fs.noteon(canal, midi, 100)
                        else:
                            fs.noteoff(canal, midi)
                    print(f"[TECLA]     {'PRESS  ' if dados['ativa'] else 'release'}  {dados['nota']}")

                else:
                    print(f"[OUTRO]     {dados}")

            except json.JSONDecodeError:
                print(f"[RAW]       {linha}")

        except KeyboardInterrupt:
            print("\nEncerrando.")
            ser.close()
            fs.delete()
            break

main()