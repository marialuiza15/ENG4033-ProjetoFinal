import fluidsynth
import time

SOUNDFONT = "/usr/share/sounds/sf2/FluidR3_GM.sf2"

fs = fluidsynth.Synth()

fs.setting("audio.file.name", "teste.wav")
fs.setting("audio.file.type", "wav")
fs.setting("audio.file.format", "s16")
fs.start(driver="file")

sfid = fs.sfload(SOUNDFONT)
fs.program_select(0, sfid, 0, 0)

fs.noteon(0, 60, 100)
time.sleep(1)
fs.noteoff(0, 60)

time.sleep(0.5)
fs.delete()

print("Arquivo teste.wav criado!")