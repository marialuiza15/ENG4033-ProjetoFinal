import streamlit as st

# ─────────────────────────────────────────────
# CONFIGURAÇÃO GERAL DA PÁGINA
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="SmartBeat Dashboard",
    page_icon="🎛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# ESTILOS CUSTOMIZADOS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Tema escuro musical */
    .stApp { background-color: #ffffff; color: #000000; }
    .block-container { padding-top: 1.5rem; }
    h1, h2, h3 { color: #c084fc; font-family: 'Courier New', monospace; }
    .section-card {
        background: #1a1a2e;
        border: 1px solid #4a3f6b;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
    }
    .param-tag {
        background: #2d1b69;
        color: #c084fc;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: bold;
        letter-spacing: 1px;
    }
    .badge-new {
        background: #16a34a;
        color: white;
        padding: 2px 8px;
        border-radius: 20px;
        font-size: 10px;
        margin-left: 6px;
    }
    .stSlider > div > div > div { background: #FFFFFF; }
    .stSelectbox label, .stSlider label, .stTextInput label,
    .stNumberInput label, .stCheckbox label, .stRadio label {
        color: #000000 !important;
        font-size: 13px;
        font-weight: 600;
    }
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed, #c084fc);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        padding: 0.5rem 1.5rem;
        width: 100%;
    }
    .stButton > button:hover { opacity: 0.88; }
    .status-indicator {
        display: inline-block;
        width: 10px; height: 10px;
        border-radius: 50%;
        background: #22c55e;
        margin-right: 6px;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
    }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR — STATUS E CONEXÃO
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## SmartBeat")
    st.markdown("**Mesa de som inteligente**")
    st.markdown("---")

    st.markdown("Preset")
    preset_name = st.text_input("Nome do preset atual", value="Meu Projeto")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.button("Salvar")
    with col_s2:
        st.button("Carregar")

# ─────────────────────────────────────────────
# CABEÇALHO PRINCIPAL
# ─────────────────────────────────────────────
st.markdown("<h1>SmartBeat — Dashboard de Configuração</h1>", unsafe_allow_html=True)
st.markdown("Configure os parâmetros detalhados da sua mesa de som inteligente.")
st.markdown("---")

# ─────────────────────────────────────────────
# LINHA 1 — PARÂMETROS FUNDAMENTAIS
# ─────────────────────────────────────────────
col1, col2, col3 = st.columns(3)

with col1:
    
    st.markdown('Sequência e Ritmo </br><span class="param-tag">A CONFIRMAR</span>', unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # PARÂMETRO: BPM
    # Range: 40–240. Altere min_value / max_value conforme necessário.
    # ══════════════════════════════════════════
    bpm = st.slider("BPM (Batidas por Minuto)", min_value=40, max_value=240, value=120, step=1)

    # ══════════════════════════════════════════
    # PARÂMETRO: Escala
    # Para adicionar escalas, insira novas opções na lista.
    # ══════════════════════════════════════════
    scale_type = st.selectbox("Escala", ["Maior", "Menor Natural", "Menor Harmônica", "Pentatônica", "Blues", "Dórica", "Frígia"])

    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    
    st.markdown('Estilo Musical </br><span class="param-tag">A CONFIRMAR</span>', unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # PARÂMETRO: Gênero musical principal
    # Para adicionar novos gêneros, inclua na lista abaixo.
    # ══════════════════════════════════════════
    genre = st.selectbox("Gênero principal", [
        "Pop", "Rock", "Jazz", "Blues", "Eletrônico", "Hip-Hop",
        "Samba", "Baião", "Funk", "Reggae", "Clássico", "Lo-Fi"
    ])

    # ══════════════════════════════════════════
    # PARÂMETRO: Subgênero / variante
    # Pode ser removido ou expandido conforme o projeto evolui.
    # ══════════════════════════════════════════
    subgenre = st.text_input("Subgênero / variante", placeholder="ex: Bossa Nova, Trap, Ambient…")

    # ══════════════════════════════════════════
    # PARÂMETRO: Energia/Intensidade da composição
    # ══════════════════════════════════════════
    energy = st.slider("Energia / Intensidade", 0, 100, 65, help="0 = suave e ambiente | 100 = intenso e acelerado")

    # ══════════════════════════════════════════
    # PARÂMETRO: Humor/Mood emocional
    # Pode ser usado como prompt auxiliar para a IA generativa.
    # ══════════════════════════════════════════
    mood = st.select_slider("Mood", options=["Melancólico", "Calmo", "Neutro", "Animado", "Eufórico"], value="Neutro")

    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    
    st.markdown('Parâmetros da IA </br><span class="param-tag">A CONFIRMAR</span>', unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # PARÂMETRO: Criatividade do modelo generativo
    # Equivale ao "temperature" da IA. 0 = conservador, 100 = experimental.
    # ══════════════════════════════════════════
    creativity = st.slider("Criatividade da IA (temperature)", 0, 100, 50,
                           help="Controla o quanto a IA se distancia da sequência original")

    # ══════════════════════════════════════════
    # PARÂMETRO: Densidade de notas geradas
    # ══════════════════════════════════════════
    note_density = st.slider("Densidade de notas", 1, 10, 5,
                             help="1 = esparso / minimalista | 10 = muito preenchido")

    # ══════════════════════════════════════════
    # PARÂMETRO: Duração da faixa gerada
    # ══════════════════════════════════════════
    duration = st.number_input("Duração da faixa (segundos)", min_value=10, max_value=300, value=60, step=10)

    # ══════════════════════════════════════════
    # PARÂMETRO: Fidelidade à sequência original inserida
    # 0 = IA ignora o input | 100 = replica fielmente
    # ══════════════════════════════════════════
    fidelity = st.slider("Fidelidade ao input original", 0, 100, 70)

    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# AÇÕES PRINCIPAIS
# ─────────────────────────────────────────────
st.markdown("---")
col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)

with col_btn1:
    if st.button("Gerar Composição"):
        with st.spinner("Gerando faixa com a IA…"):
            import time; time.sleep(2)
        st.success("Faixa gerada com sucesso! Pronta para reprodução.")
        st.audio("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3")  # placeholder

with col_btn2:
    if st.button("Pré-visualizar"):
        st.info("Reproduzindo pré-visualização do último preset…")

with col_btn3:
    if st.button("Exportar Faixa"):
        st.success(f"Exportando em MP3")

with col_btn4:
    if st.button("Resetar Padrões"):
        st.warning("Todos os parâmetros foram redefinidos para o padrão de fábrica.")

# ─────────────────────────────────────────────
# RODAPÉ COM RESUMO DOS PARÂMETROS ATIVOS
# ─────────────────────────────────────────────
st.markdown("---")
with st.expander(" Resumo da configuração atual", expanded=False):
    st.json({
        "bpm": bpm,
        "key": f"{scale_type}",
        "genre": genre,
        "subgenre": subgenre or None,
        "mood": mood,
        "energy": energy,
        "ai_creativity": creativity,
        "note_density": note_density,
        "duration_sec": duration,
        "fidelity_to_input": fidelity
    })

st.markdown(
    "<div style='text-align:center; color:#4a3f6b; font-size:12px; margin-top:20px;'>"
    "SmartBeat Dashboard v0.1 — Mesa de som inteligente para co-criação musical"
    "</div>",
    unsafe_allow_html=True
)