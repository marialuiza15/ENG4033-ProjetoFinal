import os
import time
import json


FLUIDSYNTH_BIN = r"C:\Users\micro1\Downloads\fluidsynth\fluidsynth-v2.5.5-win10-x64-cpp11\bin"

os.add_dll_directory(FLUIDSYNTH_BIN)
os.environ["PATH"] = FLUIDSYNTH_BIN + os.pathsep + os.environ["PATH"]

with open(
    r"C:\Users\micro1\Desktop\projeto final\ENG4033-ProjetoFinal\py\music_player\batidas.json",
    "r",
    encoding="utf-8"
) as arquivo:
    BATIDAS = json.load(arquivo)

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


sequencia = [
    {"nota": 60, "inicio": 0, "duracao": 1000, "instrumento": "orgao"},
    {"nota": 64, "inicio": 0, "duracao": 1000, "instrumento": "orgao"},
    {"nota": 67, "inicio": 4000, "duracao": 1000, "instrumento": "orgao"},
]


def calcular_duracao(sequencia):
    maior_fim = 0

    for evento in sequencia:
        fim = evento["inicio"] + evento["duracao"]
        if fim > maior_fim:
            maior_fim = fim

    return maior_fim

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
duracao_musica = calcular_duracao(sequencia)

batida = BATIDAS["simples"]

batida_final = repetir_batida(batida["eventos"],batida["duracao_padrao"],duracao_musica)
duracao_total = 0
while True:
    seq = fluidsynth.Sequencer(use_system_timer=False)
    synth_id = seq.register_fluidsynth(fs) 
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

    for tempo in range(0, duracao_total + 500, 10):
        seq.process(tempo)
        time.sleep(0.01)

fs.delete()