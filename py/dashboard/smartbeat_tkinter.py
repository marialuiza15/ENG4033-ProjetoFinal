import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import json

# criando a janela 
root = tk.Tk()
root.title("SmartBeat Dashboard")
root.geometry("1000x700")

# criando o frame com 10 de espaçamento
main = tk.Frame(root, padx=10, pady=10)
main.pack(side="left", fill="both", expand=True)

# titulo
tk.Label(
    main,
    text="SmartBeat — Dashboard de visualização",
    font=("Arial", 18, "bold")
).pack(anchor="w")

# cria um frame dentro do frame para o bloco de menu
bloco = tk.Frame(main)
bloco.pack(fill="x")

bloco1 = tk.LabelFrame(bloco, text="Menu principal")
bloco1.pack(side="left", fill="both", expand=True, padx=5)

# valores vindo das entradas do tkinter
bpm_var = tk.IntVar(value=120)
estilo_var = tk.StringVar()
instrumento_var = tk.StringVar()

# separa os 3 controles igualmente (peso1)
params_frame = tk.Frame(bloco1)
params_frame.pack(fill="x", padx=5, pady=5)
for i in range(3):
    params_frame.columnconfigure(i, weight=1)

#controele BPM
tk.Label(params_frame, text="BPM").grid(row=0, column=0)
tk.Scale(
    params_frame,
    from_=40, to=240,
    orient="horizontal",
    variable=bpm_var
).grid(row=1, column=0, sticky="ew", padx=5)

#controle INSTRUMENTO
tk.Label(params_frame, text="INSTRUMENTO").grid(row=0, column=1)
ttk.Combobox(
    params_frame,
    textvariable=estilo_var,
    values=["Orgao", "Flauta", "Guitarra", "Bateria", "Piano"]
).grid(row=1, column=1, sticky="ew", padx=5)

#controle ESTILO
tk.Label(params_frame, text="ESTILO").grid(row=0, column=2)
ttk.Combobox(
    params_frame,
    textvariable=instrumento_var,
    values=["Rock", "Jazz", "Samba", "Escolha da IA"]
).grid(row=1, column=2, sticky="ew", padx=5)


#BOTÕES DE AÇÃO

acoes = tk.Frame(main)
acoes.pack(pady=15)

def oi():
    print('OI')

tk.Button(
    acoes,
    text="ADICIONAR",
    command=oi
).pack(side="left", expand=False, fill="x", padx=5)

tk.Button(
    acoes,
    text="REMOVER",
    #command=
).pack(side="left", expand=False, fill="x")

tk.Button(
    acoes,
    text="PAUSAR MUSICA",
    #command=
).pack(side="left", expand=False, fill="x")


#RESUMO DA CONFIGURAÇÃO

frame_resumo = tk.LabelFrame(
    main,
    text="Timeline de criação"
)
frame_resumo.pack(fill="both", expand=True)

resumo = tk.Text(frame_resumo, height=15)
resumo.pack(fill="both", expand=True)

root.mainloop()