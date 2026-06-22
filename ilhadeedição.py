import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
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
root.geometry("1400x850")

# ==========================================================
# ÁREA PRINCIPAL
# ==========================================================

main = tk.Frame(root, padx=10, pady=10)
main.pack(side="left", fill="both", expand=True)

tk.Label(
    main,
    text="SmartBeat — Dashboard de visualização",
    font=("Arial", 18, "bold"),
).pack(anchor="w")

tk.Label(
    main,
    text="Crie musicas com sua mesa de som inteligente.",
).pack(anchor="w", pady=(0, 10))

# ==========================================================
# BLOCO SUPERIOR: MENU PRINCIPAL + ÁREA DE ARQUIVOS
# ==========================================================

cols = tk.Frame(main)
cols.pack(fill="x")

# ---------- Menu principal (esquerda) ----------

col1 = tk.LabelFrame(cols, text="Menu principal")
col1.pack(side="left", fill="both", expand=True, padx=(0, 5))

bpm_var = tk.IntVar(value=120)
estilo_var = tk.StringVar()
instrumento_var = tk.StringVar()

params_frame = tk.Frame(col1)
params_frame.pack(fill="x", padx=5, pady=5)

for i in range(3):
    params_frame.columnconfigure(i, weight=1)

# BPM
tk.Label(params_frame, text="BPM").grid(row=0, column=0)
tk.Scale(
    params_frame,
    from_=40, to=240,
    orient="horizontal",
    variable=bpm_var,
).grid(row=1, column=0, sticky="ew", padx=5)

# INSTRUMENTO
tk.Label(params_frame, text="INSTRUMENTO").grid(row=0, column=1)
ttk.Combobox(
    params_frame,
    textvariable=estilo_var,
    values=["Orgao", "Flauta", "Guitarra", "Bateria", "Piano"],
).grid(row=1, column=1, sticky="ew", padx=5)

# RITMO
tk.Label(params_frame, text="RITMO").grid(row=0, column=2)
ttk.Combobox(
    params_frame,
    textvariable=instrumento_var,
    values=["Rock", "Jazz", "Samba", "Escolha da IA"],
).grid(row=1, column=2, sticky="ew", padx=5)

# ---------- Área de arquivos tratados (direita) ----------

col2 = tk.LabelFrame(cols, text="Arquivos de áudio tratados")
col2.pack(side="left", fill="both", expand=True, padx=(5, 0))

# Lista de arquivos recebidos
arquivos_list = tk.Listbox(col2, height=6, selectmode="extended")
arquivos_list.pack(fill="both", expand=True, padx=5, pady=(5, 0))

# Botões da área de arquivos
btns_arquivos = tk.Frame(col2)
btns_arquivos.pack(fill="x", padx=5, pady=5)


def simular_receber_arquivo():
    """Simula a chegada de um arquivo tratado pela IA."""
    count = arquivos_list.size() + 1
    instrumento = estilo_var.get() or "Audio"
    ritmo = instrumento_var.get() or "Base"
    nome = f"{instrumento}_{ritmo}_{bpm_var.get()}bpm_faixa{count}.wav"
    arquivos_list.insert(tk.END, nome)


def baixar_arquivo():
    """Simula o download do arquivo selecionado."""
    sel = arquivos_list.curselection()
    if not sel:
        messagebox.showwarning("Aviso", "Selecione um arquivo para baixar.")
        return
    nomes = [arquivos_list.get(i) for i in sel]
    pasta = filedialog.askdirectory(title="Escolha a pasta de destino")
    if pasta:
        messagebox.showinfo(
            "Download",
            f"Arquivo(s) salvo(s) em:\n{pasta}\n\n" + "\n".join(nomes),
        )


def inserir_na_timeline():
    """Move o(s) arquivo(s) selecionado(s) para a timeline de edição."""
    sel = arquivos_list.curselection()
    if not sel:
        messagebox.showwarning("Aviso", "Selecione um arquivo para inserir na timeline.")
        return
    for i in sel:
        nome = arquivos_list.get(i)
        adicionar_faixa(nome)


tk.Button(
    btns_arquivos, text="Receber arquivo", command=simular_receber_arquivo,
).pack(side="left", expand=True, fill="x", padx=2)

tk.Button(
    btns_arquivos, text="Baixar", command=baixar_arquivo,
).pack(side="left", expand=True, fill="x", padx=2)

tk.Button(
    btns_arquivos, text="Inserir na timeline", command=inserir_na_timeline,
).pack(side="left", expand=True, fill="x", padx=2)

# ==========================================================
# BOTÕES DE AÇÃO
# ==========================================================

acoes = tk.Frame(main)
acoes.pack(fill="x", pady=10)

tk.Button(acoes, text="ADICIONAR").pack(side="left", expand=True, fill="x")
tk.Button(acoes, text="REMOVER").pack(side="left", expand=True, fill="x")
tk.Button(acoes, text="PAUSAR MUSICA").pack(side="left", expand=True, fill="x")

# ==========================================================
# TIMELINE DE EDIÇÃO DE ÁUDIO (estilo DAW)
# ==========================================================

frame_timeline = tk.LabelFrame(main, text="Timeline de edição")
frame_timeline.pack(fill="both", expand=True, pady=(5, 0))

# Toolbar da timeline
toolbar_tl = tk.Frame(frame_timeline)
toolbar_tl.pack(fill="x", padx=5, pady=5)

tk.Button(toolbar_tl, text="Play").pack(side="left", padx=2)
tk.Button(toolbar_tl, text="Pause").pack(side="left", padx=2)
tk.Button(toolbar_tl, text="Stop").pack(side="left", padx=2)
tk.Label(toolbar_tl, text="   |   ").pack(side="left")
tk.Button(toolbar_tl, text="Mute selecionada").pack(side="left", padx=2)
tk.Button(toolbar_tl, text="Remover faixa").pack(side="left", padx=2)

# Régua de tempo
regua_frame = tk.Frame(frame_timeline)
regua_frame.pack(fill="x", padx=5)

regua_label = tk.Frame(regua_frame, width=120)
regua_label.pack(side="left")
regua_label.pack_propagate(False)

regua_canvas = tk.Canvas(regua_frame, height=20, bg="#2a2a2a", highlightthickness=0)
regua_canvas.pack(side="left", fill="x", expand=True)


def desenhar_regua(event=None):
    regua_canvas.delete("all")
    largura = regua_canvas.winfo_width()
    for x in range(0, largura, 50):
        segundo = x // 50
        minuto = segundo // 60
        seg = segundo % 60
        regua_canvas.create_line(x, 0, x, 20, fill="#888")
        regua_canvas.create_text(
            x + 3, 10, text=f"{minuto}:{seg:02d}", anchor="w",
            fill="#ccc", font=("Courier", 7),
        )


regua_canvas.bind("<Configure>", desenhar_regua)

# Container scrollável para as faixas
canvas_container = tk.Frame(frame_timeline)
canvas_container.pack(fill="both", expand=True, padx=5, pady=(0, 5))

faixas_canvas = tk.Canvas(canvas_container, bg="#1e1e1e", highlightthickness=0)
scrollbar_v = ttk.Scrollbar(canvas_container, orient="vertical", command=faixas_canvas.yview)

faixas_inner = tk.Frame(faixas_canvas, bg="#1e1e1e")
faixas_inner.bind(
    "<Configure>",
    lambda e: faixas_canvas.configure(scrollregion=faixas_canvas.bbox("all")),
)

faixas_canvas.create_window((0, 0), window=faixas_inner, anchor="nw")
faixas_canvas.configure(yscrollcommand=scrollbar_v.set)

faixas_canvas.pack(side="left", fill="both", expand=True)
scrollbar_v.pack(side="right", fill="y")

# Cores das faixas
CORES_FAIXAS = ["#4a90d9", "#d94a4a", "#4ad97a", "#d9a84a", "#9b59b6", "#1abc9c"]
faixa_counter = [0]


def adicionar_faixa(nome_arquivo):
    """Cria uma faixa visual na timeline com o nome do arquivo."""
    idx = faixa_counter[0]
    cor = CORES_FAIXAS[idx % len(CORES_FAIXAS)]
    faixa_counter[0] += 1

    row = tk.Frame(faixas_inner, bg="#2a2a2a", pady=2)
    row.pack(fill="x", pady=1)

    # Cabeçalho da faixa (nome + controles)
    header = tk.Frame(row, bg="#333", width=120)
    header.pack(side="left", fill="y")
    header.pack_propagate(False)

    tk.Label(
        header, text=f"Faixa {idx + 1}", bg="#333", fg="white",
        font=("Arial", 8, "bold"),
    ).pack(anchor="w", padx=3, pady=(3, 0))

    tk.Label(
        header, text=nome_arquivo, bg="#333", fg="#aaa",
        font=("Arial", 7), wraplength=110, justify="left",
    ).pack(anchor="w", padx=3)

    vol_frame = tk.Frame(header, bg="#333")
    vol_frame.pack(fill="x", padx=3)
    tk.Label(vol_frame, text="Vol", bg="#333", fg="#aaa", font=("Arial", 7)).pack(side="left")
    vol_scale = tk.Scale(
        vol_frame, from_=0, to=100, orient="horizontal",
        length=70, bg="#333", fg="white", highlightthickness=0,
        troughcolor="#555", sliderrelief="flat",
    )
    vol_scale.set(80)
    vol_scale.pack(side="left")

    # Bloco visual representando o áudio na timeline
    wave_canvas = tk.Canvas(row, height=50, bg="#1e1e1e", highlightthickness=0)
    wave_canvas.pack(side="left", fill="x", expand=True)

    def desenhar_onda(event=None, canvas=wave_canvas, c=cor):
        canvas.delete("all")
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w < 10:
            return
        # Fundo do bloco de áudio
        canvas.create_rectangle(10, 2, w - 10, h - 2, fill=c, stipple="gray50", outline=cor)
        # Simulação de forma de onda
        import random
        random.seed(hash(nome_arquivo) + idx)
        pontos = []
        mid = h // 2
        for x in range(12, w - 10, 3):
            amp = random.randint(5, mid - 5)
            pontos.append((x, mid - amp))
            pontos.append((x, mid + amp))
        for px, py in pontos:
            canvas.create_line(px, mid, px, py, fill=cor, width=1)
        # Nome sobre o bloco
        canvas.create_text(20, 8, text=nome_arquivo, anchor="nw", fill="white", font=("Arial", 7))

    wave_canvas.bind("<Configure>", desenhar_onda)


# ==========================================================
# RESUMO DA CONFIGURAÇÃO
# ==========================================================

def atualizar_resumo():
    dados = {
        "bpm": bpm_var.get(),
        "estilo": estilo_var.get(),
        "instrumento": instrumento_var.get(),
    }
    resumo.delete("1.0", tk.END)
    resumo.insert(tk.END, json.dumps(dados, indent=4, ensure_ascii=False))


frame_resumo = tk.LabelFrame(main, text="Resumo da configuração atual")
frame_resumo.pack(fill="x", pady=(5, 0))

resumo = tk.Text(frame_resumo, height=4)
resumo.pack(fill="x", expand=False)

atualizar_resumo()

root.mainloop()