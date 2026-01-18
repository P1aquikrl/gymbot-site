import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ==============================================================================
# ⚙️ CONFIGURAÇÃO E ESTILO (MODERNO & PROFISSIONAL)
# ==============================================================================
st.set_page_config(page_title="GymBot Performance", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    /* Fundo Dark Moderno (Tipo Apple Watch / Strava Dark) */
    .stApp {
        background-color: #000000;
        color: #ffffff;
    }
    
    /* Remove barra superior */
    header[data-testid="stHeader"] { background-color: rgba(0,0,0,0); }
    
    /* Cards de Métricas (Estilo Glassmorphism) */
    .css-card {
        background: linear-gradient(145deg, #111111, #1a1a1a);
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #333;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
        text-align: center;
    }
    .css-card:hover {
        border-color: #00ff88; /* Verde Neon suave */
    }
    
    /* Tipografia */
    h1, h2, h3 { font-family: 'Helvetica Neue', sans-serif; font-weight: 600; }
    .highlight-text { color: #00ff88; font-weight: bold; } /* Verde Performance */
    
    /* Barra de Progresso */
    .progress-container {
        width: 100%;
        background-color: #222;
        border-radius: 20px;
        margin-top: 10px;
        margin-bottom: 5px;
        height: 8px;
    }
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #00b4db, #00ff88); /* Azul para Verde */
        border-radius: 20px;
        width: 0%;
        transition: width 1s ease-in-out;
    }

    /* Textos das Métricas */
    .metric-label { font-size: 0.8rem; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
    .metric-value { font-size: 1.8rem; font-weight: 700; color: #fff; }
    .metric-sub { font-size: 0.8rem; color: #666; margin-top: 5px; }
    
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
# 🏆 LÓGICA DE PERFORMANCE (NÍVEIS DE ACADEMIA)
# ==============================================================================
def calcular_nivel(total_carga):
    # Níveis baseados em consistência e volume
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
    # Tela de Login Limpa
    st.markdown("<br><br><h1 style='text-align: center;'>⚡ GYMBOT</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>Performance Tracking System</p>", unsafe_allow_html=True)
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
    
    # Converter Data para dia da semana
    try:
        df['Data_Dt'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        df['Dia_Semana'] = df['Data_Dt'].dt.day_name()
        # Tradução dos dias
        dias_pt = {'Monday': 'Seg', 'Tuesday': 'Ter', 'Wednesday': 'Qua', 'Thursday': 'Qui', 'Friday': 'Sex', 'Saturday': 'Sáb', 'Sunday': 'Dom'}
        df['Dia_Semana'] = df['Dia_Semana'].map(dias_pt)
    except:
        df['Dia_Semana'] = "N/A"

    # Cálculos de Nível
    carga_vida = df['Carga_Kg'].sum()
    nivel_nome, xp_atual, xp_prox = calcular_nivel(carga_vida)
    pct = min(100, int((xp_atual / xp_prox) * 100))
    
    # --- HEADER ---
    c_perfil, c_btn = st.columns([8,1])
    with c_perfil:
        st.markdown(f"### Olá, <span class='highlight-text'>Atleta</span>.", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <span style="font-size: 0.9rem; color: #888;">Nível: <b style="color:white">{nivel_nome}</b></span>
            <span style="font-size: 0.8rem; color: #666;">{xp_atual:,.0f} / {xp_prox:,.0f} pts</span>
        </div>
        <div class="progress-container"><div class="progress-fill" style="width: {pct}%;"></div></div>
        """, unsafe_allow_html=True)
    with c_btn:
        if st.button("SAIR"):
            st.session_state.clear(); st.query_params.clear(); st.rerun()

    st.markdown("---")

    # --- GRÁFICO DE CONSISTÊNCIA SEMANAL (NOVIDADE) ---
    st.markdown("##### 📅 Frequência Semanal")
    if 'Dia_Semana' in df.columns:
        ordem_dias = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
        contagem_dias = df['Dia_Semana'].value_counts().reindex(ordem_dias, fill_value=0).reset_index()
        contagem_dias.columns = ['Dia', 'Treinos']
        
        fig_week = px.bar(contagem_dias, x='Dia', y='Treinos', text_auto=True)
        fig_week.update_traces(marker_color='#00ff88', marker_line_width=0, opacity=0.8)
        fig_week.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#888"),
            margin=dict(l=0, r=0, t=0, b=0),
            height=200,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False, visible=False)
        )
        st.plotly_chart(fig_week, use_container_width=True)

    # --- SELEÇÃO DE EXERCÍCIOS ---
    st.markdown("##### 📈 Evolução por Exercício")
    exercicios = df['Exercicio'].unique()
    escolha = st.selectbox("", exercicios, label_visibility="collapsed")
    
    if escolha:
        df_filt = df[df['Exercicio'] == escolha]
        ult_carga = df_filt['Carga_Kg'].iloc[-1]
        max_carga = df_filt['Carga_Kg'].max()
        qtd_treinos = len(df_filt)

        # Cards Lado a Lado
        col1, col2, col3 = st.columns(3)
        
        # Identifica se é cardio (lógica simples)
        eh_cardio = any(x in escolha.lower() for x in ['esteira', 'corrida', 'bike', 'eliptico'])
        unidade = "km/min" if eh_cardio else "kg"
        
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
                <div class='metric-value' style='color: #00ff88'>{max_carga} <span style='font-size:1rem'>{unidade}</span></div>
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

        # Gráfico de Linha Clean
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_filt['Data'], 
            y=df_filt['Carga_Kg'],
            mode='lines+markers',
            line=dict(color='#00b4db', width=3, shape='spline'), # Linha curva suave (Spline)
            marker=dict(size=6, color='#fff', line=dict(color='#00b4db', width=2)),
            fill='tozeroy',
            fillcolor='rgba(0, 180, 219, 0.1)' # Azul transparente
        ))
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(showgrid=False, showline=True, linecolor='#333'),
            yaxis=dict(showgrid=True, gridcolor='#222', zeroline=False),
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- HISTÓRICO COMPACTO ---
    with st.expander("📜 Ver Histórico Completo"):
        st.dataframe(
            df_filt[['Data', 'Series', 'Reps', 'Carga_Kg', 'Notas']], 
            use_container_width=True,
            hide_index=True
        )
