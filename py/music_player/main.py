import os
import time

FLUIDSYNTH_BIN = r"C:\Users\micro1\Downloads\fluidsynth\fluidsynth-v2.5.5-win10-x64-cpp11\bin"

os.add_dll_directory(FLUIDSYNTH_BIN)
os.environ["PATH"] = FLUIDSYNTH_BIN + os.pathsep + os.environ["PATH"]

import fluidsynth

SOUNDFONT = r"C:\Users\micro1\Downloads\FluidR3_GM.sf2"

fs = fluidsynth.Synth()
fs.start(driver="wasapi", midi_driver="none")

sfid = fs.sfload(SOUNDFONT)
fs.program_select(0, sfid, 0, 0)
fs.program_select(0, sfid, 0, 0)

fs.noteon(0, 60, 100)
fs.noteon(0, 60, 100)
time.sleep(1)
fs.noteoff(0, 60)

time.sleep(0.2)
fs.delete()

print("Arquivo teste.wav criado!")