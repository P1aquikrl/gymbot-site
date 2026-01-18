import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ==============================================================================
# ⚙️ CONFIGURAÇÃO E ESTILO (NEON ESTÁTICO)
# ==============================================================================
st.set_page_config(page_title="GymBot Performance", page_icon="⚡", layout="wide")

# Cor Principal (Verde Neon do exemplo)
NEON_GREEN = "#00ff88"
DARK_BG = "#0e0e0e"
CARD_BG = "#141414"

st.markdown(f"""
<style>
    /* Fundo Dark Profundo */
    .stApp {{
        background-color: {DARK_BG};
        color: #ffffff;
    }
    
    /* Remove barra superior */
    header[data-testid="stHeader"] {{ background-color: rgba(0,0,0,0); }}
    
    /* Cards de Métricas (Estilo Sólido e Arredondado) */
    .css-card {{
        background-color: {CARD_BG};
        border-radius: 16px;
        padding: 20px;
        border: 1px solid #222;
        /* Sombra suave verde para dar volume 3D */
        box-shadow: 0 4px 12px rgba(0, 255, 136, 0.1); 
        margin-bottom: 20px;
        text-align: center;
    }}
    
    /* Tipografia */
    h1, h2, h3, h4, h5 {{ font-family: 'Inter', 'Helvetica Neue', sans-serif; font-weight: 700; color: white !important; }}
    .highlight-text {{ color: {NEON_GREEN}; font-weight: bold; }}
    
    /* Barra de Progresso */
    .progress-container {{
        width: 100%;
        background-color: #222;
        border-radius: 30px; /* Bem redondo */
        margin-top: 10px;
        margin-bottom: 5px;
        height: 12px; /* Mais gordinha */
        overflow: hidden;
    }}
    .progress-fill {{
        height: 100%;
        /* Gradiente Verde */
        background: linear-gradient(90deg, #00b4db, {NEON_GREEN}); 
        border-radius: 30px;
        width: 0%;
        transition: width 1s ease-in-out;
    }}

    /* Textos das Métricas */
    .metric-label {{ font-size: 0.8rem; color: #999; text-transform: uppercase; font-weight: 600; letter-spacing: 1px; margin-bottom: 8px; }}
    .metric-value {{ font-size: 2rem; font-weight: 800; color: #fff; }}
    .metric-sub {{ font-size: 0.8rem; color: #666; margin-top: 5px; font-weight: 500; }}

    /* Forçar Plotly a não ter fundo */
    .js-plotly-plot .plotly .bg {{ fill: rgba(0,0,0,0) !important; }}
    
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 🔗 CONEXÃO GOOGLE SHEETS
# ==============================================================================
def connect_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    if "gcp_service_account" in st.secrets:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    return client.open("GymBot_Database")

def get_data(telefone):
    try:
        sh = connect_google()
        sheet = sh.worksheet(str(telefone))
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        # Padronização de Colunas
        mapa = {
            'Carga': 'Carga_Kg', 'carga': 'Carga_Kg', 'Carga (kg)': 'Carga_Kg',
            'Exercicio': 'Exercicio', 'Exercício': 'Exercicio',
            'Data': 'Data', 'data': 'Data',
            'Reps': 'Reps', 'reps': 'Reps',
            'Series': 'Series', 'series': 'Series'
        }
        df = df.rename(columns=mapa)
        if 'Carga_Kg' not in df.columns: df['Carga_Kg'] = 0
        return df
    except: return None

# ==============================================================================
# 🏆 LÓGICA DE PERFORMANCE
# ==============================================================================
def calcular_nivel(total_carga):
    if total_carga < 2000: return "Iniciante", total_carga, 2000
    elif total_carga < 10000: return "Em Evolução", total_carga, 10000
    elif total_carga < 50000: return "Intermediário", total_carga, 50000
    elif total_carga < 100000: return "Avançado", total_carga, 100000
    elif total_carga < 500000: return "Elite", total_carga, 500000
    else: return "LENDÁRIO", total_carga, 1000000

# ==============================================================================
# 🔐 LOGIN
# ==============================================================================
query_params = st.query_params
usuario_url = query_params.get("id", None)

if usuario_url and 'telefone_usuario' not in st.session_state:
    df_check = get_data(usuario_url)
    if df_check is not None and not df_check.empty:
        st.session_state['telefone_usuario'] = usuario_url
        st.session_state['df_usuario'] = df_check
    else: st.error("⚠️ Perfil não encontrado.")

if 'telefone_usuario' not in st.session_state:
    st.markdown("<br><br><h1 style='text-align: center;'>⚡ GYMBOT</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888; font-weight: 500;'>Performance Tracking System</p>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        telefone_input = st.text_input("ID de Acesso", placeholder="Seu número...")
        if st.button("ENTRAR", use_container_width=True):
            df = get_data(telefone_input)
            if df is not None and not df.empty:
                st.session_state['telefone_usuario'] = telefone_input
                st.session_state['df_usuario'] = df
                st.rerun()
            else: st.error("ID Inválido.")

# ==============================================================================
# 📊 DASHBOARD DO ATLETA
# ==============================================================================
else:
    df = st.session_state['df_usuario']
    
    # Tratamento de Dados
    df['Carga_Kg'] = pd.to_numeric(df['Carga_Kg'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    
    try:
        df['Data_Dt'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        df['Dia_Semana'] = df['Data_Dt'].dt.day_name()
        dias_pt = {'Monday': 'Seg', 'Tuesday': 'Ter', 'Wednesday': 'Qua', 'Thursday': 'Qui', 'Friday': 'Sex', 'Saturday': 'Sáb', 'Sunday': 'Dom'}
        df['Dia_Semana'] = df['Dia_Semana'].map(dias_pt)
    except:
        df['Dia_Semana'] = "N/A"

    carga_vida = df['Carga_Kg'].sum()
    nivel_nome, xp_atual, xp_prox = calcular_nivel(carga_vida)
    pct = min(100, int((xp_atual / xp_prox) * 100))
    
    # --- HEADER ---
    c_perfil, c_btn = st.columns([8,1])
    with c_perfil:
        st.markdown(f"### Olá, <span class='highlight-text'>Atleta</span>.", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 5px;">
            <span style="font-size: 0.9rem; color: #888; font-weight: 600;">Nível: <b style="color:white">{nivel_nome}</b></span>
            <span style="font-size: 0.8rem; color: #666; font-weight: 600;">{xp_atual:,.0f} / {xp_prox:,.0f} pts</span>
        </div>
        <div class="progress-container"><div class="progress-fill" style="width: {pct}%;"></div></div>
        """, unsafe_allow_html=True)
    with c_btn:
        if st.button("SAIR"):
            st.session_state.clear(); st.query_params.clear(); st.rerun()

    st.markdown("---")

    # --- GRÁFICO DE CONSISTÊNCIA SEMANAL (ESTÁTICO & GORDINHO) ---
    st.markdown("##### 📅 Frequência Semanal")
    if 'Dia_Semana' in df.columns:
        ordem_dias = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
        contagem_dias = df['Dia_Semana'].value_counts().reindex(ordem_dias, fill_value=0).reset_index()
        contagem_dias.columns = ['Dia', 'Treinos']
        
        # Usando go.Bar para mais controle visual
        fig_week = go.Figure(data=[go.Bar(
            x=contagem_dias['Dia'],
            y=contagem_dias['Treinos'],
            text=contagem_dias['Treinos'], # Mostra o número em cima da barra
            textposition='auto',
            marker_color=NEON_GREEN, # Cor Neon
            marker_line_color='#00cc6a', # Borda um pouco mais escura para dar "pop" 3D
            marker_line_width=1.5,
            opacity=1.0
        )])

        fig_week.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#888", family="Inter, sans-serif"),
            margin=dict(l=0, r=0, t=20, b=0), # Margem superior para o texto não cortar
            height=220,
            xaxis=dict(showgrid=False, tickfont=dict(weight='bold')),
            yaxis=dict(showgrid=False, visible=False),
            bargap=0.2 # <--- ISSO DEIXA AS BARRAS MAIS GORDINHAS (quanto menor, mais gorda)
        )
        
        # ⚠️ O SEGREDO DO SCROLL: config={'staticPlot': True} ⚠️
        st.plotly_chart(fig_week, use_container_width=True, config={'staticPlot': True, 'displayModeBar': False})

    # --- SELEÇÃO DE EXERCÍCIOS ---
    st.markdown("##### 📈 Evolução por Exercício")
    exercicios = df['Exercicio'].unique()
    escolha = st.selectbox("", exercicios, label_visibility="collapsed")
    
    if escolha:
        df_filt = df[df['Exercicio'] == escolha]
        ult_carga = df_filt['Carga_Kg'].iloc[-1]
        max_carga = df_filt['Carga_Kg'].max()
        qtd_treinos = len(df_filt)
        
        eh_cardio = any(x in escolha.lower() for x in ['esteira', 'corrida', 'bike', 'eliptico'])
        unidade = "km/min" if eh_cardio else "kg"
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class='css-card'>
                <div class='metric-label'>Último Treino</div>
                <div class='metric-value'>{ult_carga} <span style='font-size:1rem'>{unidade}</span></div>
                <div class='metric-sub'>Carga/Intensidade</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class='css-card'>
                <div class='metric-label'>Recorde (PR)</div>
                <div class='metric-value' style='color: {NEON_GREEN}'>{max_carga} <span style='font-size:1rem'>{unidade}</span></div>
                <div class='metric-sub'>Seu melhor</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class='css-card'>
                <div class='metric-label'>Volume</div>
                <div class='metric-value'>{qtd_treinos}</div>
                <div class='metric-sub'>Sessões totais</div>
            </div>
            """, unsafe_allow_html=True)

        # Gráfico de Linha (Também Estático)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_filt['Data'], 
            y=df_filt['Carga_Kg'],
            mode='lines+markers',
            # Usando a mesma cor verde neon
            line=dict(color=NEON_GREEN, width=4, shape='spline'), 
            marker=dict(size=8, color=CARD_BG, line=dict(color=NEON_GREEN, width=3)),
            fill='tozeroy',
            fillcolor='rgba(0, 255, 136, 0.1)' # Verde transparente
        ))
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(showgrid=False, showline=True, linecolor='#333', tickfont=dict(weight='bold')),
            yaxis=dict(showgrid=True, gridcolor='#222', zeroline=False, tickfont=dict(weight='bold')),
            hovermode="x unified"
        )
        # ⚠️ TAMBÉM ESTÁTICO PARA NÃO ATRAPALHAR O SCROLL ⚠️
        st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True, 'displayModeBar': False})

    # --- HISTÓRICO ---
    with st.expander("📜 Ver Histórico Completo"):
        st.dataframe(
            df_filt[['Data', 'Series', 'Reps', 'Carga_Kg', 'Notas']], 
            use_container_width=True,
            hide_index=True
        )
