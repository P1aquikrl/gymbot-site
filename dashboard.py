import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

st.set_page_config(page_title="GymBot System", page_icon="👾", layout="wide")

# CSS SOLO LEVELING
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    header[data-testid="stHeader"] { background-color: rgba(0,0,0,0); }
    .css-card {
        background-color: #1c1c2e;
        border-radius: 15px;
        padding: 20px;
        border: 1px solid #2d2d44;
        box-shadow: 0 0 10px rgba(138, 43, 226, 0.1);
        margin-bottom: 20px;
        transition: transform 0.3s;
    }
    .css-card:hover { transform: scale(1.02); border: 1px solid #8A2BE2; box-shadow: 0 0 20px rgba(138, 43, 226, 0.4); }
    h1, h2, h3 { color: #ffffff !important; font-family: 'Segoe UI', sans-serif; }
    .highlight-text { color: #8A2BE2; font-weight: bold; }
    .xp-bar-container { width: 100%; background-color: #2d2d44; border-radius: 10px; margin-top: 5px; margin-bottom: 20px; }
    .xp-bar-fill { height: 10px; background: linear-gradient(90deg, #4b0082, #8A2BE2, #00ffff); border-radius: 10px; width: 0%; transition: width 1s ease-in-out; }
    .metric-label { font-size: 0.9rem; color: #a0a0a0; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { font-size: 2rem; font-weight: bold; color: #fff; text-shadow: 0 0 10px rgba(138, 43, 226, 0.5); }
</style>
""", unsafe_allow_html=True)

# --- CONEXÃO INTELIGENTE (PC OU NUVEM) ---
def connect_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Tenta ler dos Segredos do Streamlit Cloud
    if "gcp_service_account" in st.secrets:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    # Se não achar, tenta ler do arquivo local (seu PC)
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
        
        # Vacina de Colunas
        mapa_colunas = {
            'Carga': 'Carga_Kg', 'carga': 'Carga_Kg', 'Carga (kg)': 'Carga_Kg',
            'Exercicio': 'Exercicio', 'Exercício': 'Exercicio',
            'Data': 'Data', 'data': 'Data',
            'Reps': 'Reps', 'reps': 'Reps',
            'Series': 'Series', 'Séries': 'Series', 'series': 'Series'
        }
        df = df.rename(columns=mapa_colunas)
        if 'Carga_Kg' not in df.columns: df['Carga_Kg'] = 0
        return df
    except: return None

def calcular_rank(total_carga):
    if total_carga < 2000: return "Rank E (Iniciante)", total_carga, 2000
    elif total_carga < 10000: return "Rank D (Aprendiz)", total_carga, 10000
    elif total_carga < 50000: return "Rank C (Veterano)", total_carga, 50000
    elif total_carga < 100000: return "Rank B (Elite)", total_carga, 100000
    elif total_carga < 500000: return "Rank A (Mestre)", total_carga, 500000
    else: return "👑 MONARCA", total_carga, 1000000

# LÓGICA DE LOGIN
query_params = st.query_params
usuario_url = query_params.get("id", None)
if usuario_url and 'telefone_usuario' not in st.session_state:
    df_check = get_data(usuario_url)
    if df_check is not None and not df_check.empty:
        st.session_state['telefone_usuario'] = usuario_url
        st.session_state['df_usuario'] = df_check
    else: st.error("❌ Player não encontrado.")

if 'telefone_usuario' not in st.session_state:
    st.markdown("<h1 style='text-align: center;'>👾 SYSTEM LOGIN</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        telefone_input = st.text_input("ID do Usuário")
        if st.button("ACESSAR", use_container_width=True):
            df = get_data(telefone_input)
            if df is not None and not df.empty:
                st.session_state['telefone_usuario'] = telefone_input
                st.session_state['df_usuario'] = df
                st.rerun()
            else: st.error("Usuário desconhecido.")
else:
    df = st.session_state['df_usuario']
    df['Carga_Kg'] = pd.to_numeric(df['Carga_Kg'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    carga_vida = df['Carga_Kg'].sum()
    rank_nome, xp_atual, xp_proximo = calcular_rank(carga_vida)
    pct = min(100, int((xp_atual / xp_proximo) * 100)) if xp_proximo > 0 else 100
    
    col_perf, col_out = st.columns([8,1])
    with col_perf:
        st.markdown(f"## Olá, <span class='highlight-text'>Caçador</span>.", unsafe_allow_html=True)
        st.markdown(f"**STATUS:** `{rank_nome}`")
        st.markdown(f"""
        <div class="xp-bar-container"><div class="xp-bar-fill" style="width: {pct}%;"></div></div>
        <div style="font-size: 0.8rem; color: #ccc;">XP: {xp_atual:,.0f} / {xp_proximo:,.0f}</div>
        """, unsafe_allow_html=True)
    with col_out:
        if st.button("SAIR"):
            st.session_state.clear(); st.query_params.clear(); st.rerun()

    st.divider()
    exercicios = df['Exercicio'].unique() if 'Exercicio' in df.columns else []
    escolha = st.sidebar.selectbox("Skill:", exercicios)
    
    if escolha:
        df_filt = df[df['Exercicio'] == escolha]
        ult_carga = df_filt['Carga_Kg'].iloc[-1]
        max_carga = df_filt['Carga_Kg'].max()
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='css-card'><div class='metric-label'>Atual</div><div class='metric-value'>{ult_carga} kg</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='css-card'><div class='metric-label'>Recorde</div><div class='metric-value' style='color:#00ffff'>{max_carga} kg</div></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='css-card'><div class='metric-label'>Treinos</div><div class='metric-value'>{len(df_filt)}</div></div>", unsafe_allow_html=True)
        st.markdown("### 📈 Evolução")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_filt['Data'], y=df_filt['Carga_Kg'], mode='lines+markers', fill='tozeroy', line=dict(color='#8A2BE2'), marker=dict(color='#00ffff')))
        fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)