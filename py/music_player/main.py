import fluidsynth
import time

SOUNDFONT = "soundfonts/FluidR3_GM.sf2"

fs = fluidsynth.Synth()
fs.start(driver="pulseaudio")

sfid = fs.sfload(SOUNDFONT)
fs.program_select(0, sfid, 0, 0)  # piano

fs.noteon(0, 60, 100)  # Dó
time.sleep(1)
fs.noteoff(0, 60)

fs.delete()