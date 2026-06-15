import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import json

# ==========================================================
# JANELA PRINCIPAL
# ==========================================================

if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
    print(
        "Erro: nenhum display disponível. Execute este aplicativo em um ambiente gráfico ou defina a variável $DISPLAY.",
        file=sys.stderr,
    )
    sys.exit(1)

root = tk.Tk()
root.title("SmartBeat Dashboard")
root.geometry("1200x700")

# ==========================================================
# SIDEBAR
# ==========================================================

sidebar = tk.Frame(root, width=250, padx=10, pady=10)
sidebar.pack(side="left", fill="y")

tk.Label(sidebar, text="SmartBeat",
         font=("Arial", 16, "bold")).pack()

tk.Label(sidebar, text="Mesa de som inteligente").pack()

tk.Label(sidebar, text="\nPreset").pack()

preset_var = tk.StringVar(value="Meu Projeto")

preset_entry = tk.Entry(
    sidebar,
    textvariable=preset_var
)
preset_entry.pack(fill="x")

# ==========================================================
# FUNCIONALIDADE: SALVAR PRESET
# ==========================================================

def salvar_preset():
    messagebox.showinfo(
        "Salvar",
        f"Preset '{preset_var.get()}' salvo!"
    )

# ==========================================================
# FUNCIONALIDADE: CARREGAR PRESET
# ==========================================================

def carregar_preset():
    messagebox.showinfo(
        "Carregar",
        "Preset carregado!"
    )

btn_frame = tk.Frame(sidebar)
btn_frame.pack(fill="x", pady=5)

tk.Button(
    btn_frame,
    text="Salvar",
    command=salvar_preset
).pack(side="left", expand=True, fill="x")

tk.Button(
    btn_frame,
    text="Carregar",
    command=carregar_preset
).pack(side="left", expand=True, fill="x")

# ==========================================================
# ÁREA PRINCIPAL
# ==========================================================

main = tk.Frame(root, padx=10, pady=10)
main.pack(side="left", fill="both", expand=True)

tk.Label(
    main,
    text="SmartBeat — Dashboard de Configuração",
    font=("Arial", 18, "bold")
).pack(anchor="w")

tk.Label(
    main,
    text="Configure os parâmetros detalhados da sua mesa de som inteligente."
).pack(anchor="w", pady=(0, 10))

# ==========================================================
# TRÊS COLUNAS
# ==========================================================

cols = tk.Frame(main)
cols.pack(fill="x")

col1 = tk.LabelFrame(cols, text="Sequência e Ritmo")
col2 = tk.LabelFrame(cols, text="Estilo Musical")
col3 = tk.LabelFrame(cols, text="Parâmetros da IA")

col1.pack(side="left", fill="both", expand=True, padx=5)
col2.pack(side="left", fill="both", expand=True, padx=5)
col3.pack(side="left", fill="both", expand=True, padx=5)

# ==========================================================
# FUNCIONALIDADE: BPM
# ==========================================================

bpm_var = tk.IntVar(value=120)

tk.Label(col1, text="BPM").pack()
tk.Scale(
    col1,
    from_=40,
    to=240,
    orient="horizontal",
    variable=bpm_var
).pack(fill="x")

# ==========================================================
# FUNCIONALIDADE: ESCALA
# ==========================================================

scale_var = tk.StringVar()

tk.Label(col1, text="Escala").pack()

ttk.Combobox(
    col1,
    textvariable=scale_var,
    values=[
        "Maior",
        "Menor Natural",
        "Menor Harmônica",
        "Pentatônica",
        "Blues",
        "Dórica",
        "Frígia"
    ]
).pack(fill="x")

# ==========================================================
# FUNCIONALIDADE: GÊNERO
# ==========================================================

genre_var = tk.StringVar()

tk.Label(col2, text="Gênero Principal").pack()

ttk.Combobox(
    col2,
    textvariable=genre_var,
    values=[
        "Pop",
        "Rock",
        "Jazz",
        "Blues",
        "Eletrônico",
        "Hip-Hop",
        "Samba",
        "Baião",
        "Funk",
        "Reggae",
        "Clássico",
        "Lo-Fi"
    ]
).pack(fill="x")

# ==========================================================
# FUNCIONALIDADE: SUBGÊNERO
# ==========================================================

subgenre_var = tk.StringVar()

tk.Label(col2, text="Subgênero").pack()

tk.Entry(
    col2,
    textvariable=subgenre_var
).pack(fill="x")

# ==========================================================
# FUNCIONALIDADE: ENERGIA
# ==========================================================

energy_var = tk.IntVar(value=65)

tk.Label(col2, text="Energia").pack()

tk.Scale(
    col2,
    from_=0,
    to=100,
    orient="horizontal",
    variable=energy_var
).pack(fill="x")

# ==========================================================
# FUNCIONALIDADE: MOOD
# ==========================================================

mood_var = tk.StringVar(value="Neutro")

tk.Label(col2, text="Mood").pack()

ttk.Combobox(
    col2,
    textvariable=mood_var,
    values=[
        "Melancólico",
        "Calmo",
        "Neutro",
        "Animado",
        "Eufórico"
    ]
).pack(fill="x")

# ==========================================================
# FUNCIONALIDADE: CRIATIVIDADE IA
# ==========================================================

creativity_var = tk.IntVar(value=50)

tk.Label(col3, text="Criatividade IA").pack()

tk.Scale(
    col3,
    from_=0,
    to=100,
    orient="horizontal",
    variable=creativity_var
).pack(fill="x")

# ==========================================================
# FUNCIONALIDADE: DENSIDADE DE NOTAS
# ==========================================================

density_var = tk.IntVar(value=5)

tk.Label(col3, text="Densidade de Notas").pack()

tk.Scale(
    col3,
    from_=1,
    to=10,
    orient="horizontal",
    variable=density_var
).pack(fill="x")

# ==========================================================
# FUNCIONALIDADE: DURAÇÃO
# ==========================================================

duration_var = tk.IntVar(value=60)

tk.Label(col3, text="Duração (segundos)").pack()

tk.Spinbox(
    col3,
    from_=10,
    to=300,
    textvariable=duration_var
).pack(fill="x")

# ==========================================================
# FUNCIONALIDADE: FIDELIDADE
# ==========================================================

fidelity_var = tk.IntVar(value=70)

tk.Label(col3, text="Fidelidade").pack()

tk.Scale(
    col3,
    from_=0,
    to=100,
    orient="horizontal",
    variable=fidelity_var
).pack(fill="x")

# ==========================================================
# RESUMO DOS PARÂMETROS
# ==========================================================

def atualizar_resumo():

    dados = {
        "bpm": bpm_var.get(),
        "key": scale_var.get(),
        "genre": genre_var.get(),
        "subgenre": subgenre_var.get(),
        "mood": mood_var.get(),
        "energy": energy_var.get(),
        "ai_creativity": creativity_var.get(),
        "note_density": density_var.get(),
        "duration_sec": duration_var.get(),
        "fidelity_to_input": fidelity_var.get()
    }

    resumo.delete("1.0", tk.END)
    resumo.insert(
        tk.END,
        json.dumps(dados, indent=4, ensure_ascii=False)
    )

# ==========================================================
# FUNCIONALIDADE: GERAR COMPOSIÇÃO
# ==========================================================

def gerar_composicao():
    atualizar_resumo()

    messagebox.showinfo(
        "SmartBeat",
        "Faixa gerada com sucesso!"
    )

# ==========================================================
# FUNCIONALIDADE: PRÉ-VISUALIZAR
# ==========================================================

def preview():
    messagebox.showinfo(
        "Preview",
        "Reproduzindo pré-visualização..."
    )

# ==========================================================
# FUNCIONALIDADE: EXPORTAR
# ==========================================================

def exportar():
    messagebox.showinfo(
        "Exportar",
        "Exportando MP3..."
    )

# ==========================================================
# FUNCIONALIDADE: RESETAR PADRÕES
# ==========================================================

def resetar():

    bpm_var.set(120)
    energy_var.set(65)
    creativity_var.set(50)
    density_var.set(5)
    duration_var.set(60)
    fidelity_var.set(70)

    atualizar_resumo()

# ==========================================================
# BOTÕES DE AÇÃO
# ==========================================================

acoes = tk.Frame(main)
acoes.pack(fill="x", pady=15)

tk.Button(
    acoes,
    text="Gerar Composição",
    command=gerar_composicao
).pack(side="left", expand=True, fill="x")

tk.Button(
    acoes,
    text="Pré-visualizar",
    command=preview
).pack(side="left", expand=True, fill="x")

tk.Button(
    acoes,
    text="Exportar Faixa",
    command=exportar
).pack(side="left", expand=True, fill="x")

tk.Button(
    acoes,
    text="Resetar Padrões",
    command=resetar
).pack(side="left", expand=True, fill="x")

# ==========================================================
# RESUMO DA CONFIGURAÇÃO
# ==========================================================

frame_resumo = tk.LabelFrame(
    main,
    text="Resumo da Configuração Atual"
)

frame_resumo.pack(fill="both", expand=True)

resumo = tk.Text(frame_resumo, height=15)
resumo.pack(fill="both", expand=True)

atualizar_resumo()

root.mainloop()