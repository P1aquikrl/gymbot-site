import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

# ==========================================================
# 🎨 CONFIGURAÇÃO DA PÁGINA E ESTILO VISUAL
# ==========================================================
st.set_page_config(page_title="GymBot Dashboard", layout="centered", page_icon="🦍")

# CSS para forçar o visual "App Dark Mode" parecido com sua imagem
st.markdown("""
    <style>
    /* Fundo geral */
    .stApp {
        background-color: #0e1117;
    }
    
    /* Cards (Caixinhas) */
    .css-card {
        background-color: #1c1c1e;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        border: 1px solid #2c2c2e;
    }
    
    /* Texto Destaque */
    .highlight-text {
        color: #B4F8C8; /* Verde Neon suave */
        font-weight: bold;
        font-size: 24px;
    }
    
    /* Calendário */
    .calendar-day {
        text-align: center;
        padding: 10px;
        border-radius: 10px;
        cursor: pointer;
        background-color: #1c1c1e;
        border: 1px solid #333;
    }
    .calendar-day:hover {
        border-color: #B4F8C8;
    }
    .calendar-selected {
        background-color: #B4F8C8;
        color: black !important;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================================
# 📂 DADOS MOCKADOS (SIMULAÇÃO DA SUA PLANILHA)
# ==========================================================
# No futuro, aqui entra o `connect_sheets()`
def carregar_dados_ficticios():
    # Simula dados do Google Sheets
    data = [
        {"Data": "20/01/2026", "Exercicio": "Supino Reto", "Series": 3, "Reps": 10, "Carga": 40},
        {"Data": "20/01/2026", "Exercicio": "Crucifixo", "Series": 3, "Reps": 12, "Carga": 14},
        {"Data": "20/01/2026", "Exercicio": "Esteira", "Series": 1, "Reps": 1, "Carga": "20min"},
        {"Data": "19/01/2026", "Exercicio": "Agachamento", "Series": 4, "Reps": 8, "Carga": 60},
    ]
    return pd.DataFrame(data)

df = carregar_dados_ficticios()

# ==========================================================
# 🧠 CÁLCULOS DE ATRIBUTOS (O HEXÁGONO)
# ==========================================================
def calcular_atributos():
    # Aqui você criará a lógica real baseada no histórico
    # Ex: Se treinou 5 dias seguidos -> Constância sobe
    # Ex: Se carga aumentou -> Força sobe
    return {
        "Força": 80,
        "Cardio": 45,
        "Resistência": 60,
        "Constância": 90,
        "Técnica": 75
    }

stats = calcular_atributos()

# ==========================================================
# 🗓️ TOPO: CALENDÁRIO VISUAL
# ==========================================================
st.title("Olá, João 👋")

# Lógica para selecionar dia
if 'data_selecionada' not in st.session_state:
    st.session_state.data_selecionada = datetime.today().strftime("%d/%m/%Y")

# Cria 7 colunas para os dias da semana
cols = st.columns(7)
hoje = datetime.today()
dias_semana = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

for i, col in enumerate(cols):
    data_loop = hoje - timedelta(days=hoje.weekday()) + timedelta(days=i)
    data_str = data_loop.strftime("%d/%m/%Y")
    dia_num = data_loop.strftime("%d")
    dia_nome = dias_semana[i]
    
    # Visual do botão de dia
    with col:
        if st.button(f"{dia_nome}\n{dia_num}", key=f"btn_{i}", use_container_width=True):
            st.session_state.data_selecionada = data_str

st.caption(f"Visualizando: {st.session_state.data_selecionada}")

# ==========================================================
# 📊 MEIO: DASHBOARD (HEXÁGONO + STREAK + PASSOS)
# ==========================================================
col_esq, col_dir = st.columns([1, 1.5])

with col_esq:
    # --- CARD DE STREAK (FOGO) ---
    st.markdown("""
    <div class="css-card">
        <span style='font-size:30px;'>🔥</span>
        <span style='font-size:14px; color:gray;'>Sequência</span><br>
        <span class='highlight-text'>12 Dias</span>
    </div>
    """, unsafe_allow_html=True)
    
    # --- CARD DE PASSOS ---
    passos = 6825 # Viria de uma integração futura ou input manual
    meta_passos = 10000
    progresso = min(passos / meta_passos, 1.0)
    
    st.markdown(f"""
    <div class="css-card">
        <span style='font-size:30px;'>👟</span>
        <span style='font-size:14px; color:gray;'>Passos</span><br>
        <span class='highlight-text'>{passos}</span> <span style='font-size:12px'>/ {meta_passos}</span>
    </div>
    """, unsafe_allow_html=True)
    st.progress(progresso)

with col_dir:
    # --- GRÁFICO DE RADAR (HEXÁGONO) ---
    valores = list(stats.values())
    categorias = list(stats.keys())
    
    # Fechar o ciclo do gráfico repetindo o primeiro item
    valores += [valores[0]]
    categorias += [categorias[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=valores,
        theta=categorias,
        fill='toself',
        name='Stats',
        line_color='#B4F8C8',
        fillcolor='rgba(180, 248, 200, 0.2)'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], showticklabels=False, linecolor='#333'),
            bgcolor='rgba(0,0,0,0)',
            gridshape='linear' # Deixa reto igual hexagono, não circular
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        margin=dict(l=20, r=20, t=20, b=20),
        font=dict(color='white', size=12)
    )
    
    # Envelope visual para o gráfico
    st.markdown('<div class="css-card" style="text-align:center;">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================================
# 📝 BAIXO: LISTA DE EXERCÍCIOS (TIMELINE)
# ==========================================================
st.subheader("Atividades do Dia")

# Filtra o DataFrame pela data selecionada
treinos_dia = df[df['Data'] == st.session_state.data_selecionada]

if not treinos_dia.empty:
    for index, row in treinos_dia.iterrows():
        # HTML Customizado para cada item da lista (Visual App)
        st.markdown(f"""
        <div class="css-card" style="display: flex; justify-content: space-between; align-items: center; padding: 15px;">
            <div style="display: flex; align-items: center; gap: 15px;">
                <div style="background-color: #333; width: 4px; height: 40px; border-radius: 2px;"></div> <div>
                    <div style="font-weight: bold; font-size: 18px; color: white;">{row['Exercicio']}</div>
                    <div style="font-size: 14px; color: #888;">{row['Series']} Séries • {row['Reps']} Reps</div>
                </div>
            </div>
            <div style="background-color: #2c2c2e; padding: 8px 15px; border-radius: 20px; font-weight: bold; color: #B4F8C8;">
                {row['Carga']} kg
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("😴 Nenhum treino registrado neste dia.")

# Botão Flutuante (Simulado)
st.markdown("""
<div style="position:fixed; bottom:30px; right:30px; background-color:#B4F8C8; width:60px; height:60px; border-radius:30px; display:flex; justify-content:center; align-items:center; box-shadow: 0 4px 10px rgba(0,0,0,0.5); font-size:30px; color:black; cursor:pointer;">
    +
</div>
""", unsafe_allow_html=True)
