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

# Paleta de Cores
NEON_GREEN = "#00ff88"
DARK_BG = "#000000"
CARD_BG = "#121212"

st.markdown(f"""
<style>
    .stApp {{ background-color: {DARK_BG}; color: #ffffff; }}
    header[data-testid="stHeader"] {{ background-color: rgba(0,0,0,0); }}
    .block-container {{ padding-top: 1rem; padding-bottom: 5rem; }}
    
    .css-card {{
        background-color: {CARD_BG};
        border-radius: 16px;
        padding: 15px;
        border: 1px solid #222;
        box-shadow: 0 4px 15px rgba(0, 255, 136, 0.05); 
        margin-bottom: 15px;
        text-align: center;
    }}
    
    h1, h2, h3, h4, h5 {{ font-family: 'Inter', sans-serif; font-weight: 700; color: white !important; }}
    .highlight-text {{ color: {NEON_GREEN}; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; }}
    
    .progress-container {{
        width: 100%; background-color: #222; border-radius: 50px;
        margin-top: 8px; margin-bottom: 5px; height: 14px; border: 1px solid #333;
    }}
    .progress-fill {{
        height: 100%; background: {NEON_GREEN}; border-radius: 50px; width: 0%;
        box-shadow: 0 0 10px {NEON_GREEN};
    }}

    .metric-label {{ font-size: 0.75rem; color: #888; text-transform: uppercase; font-weight: 600; letter-spacing: 1px; margin-bottom: 5px; }}
    .metric-value {{ font-size: 1.6rem; font-weight: 800; color: #fff; }}
    .metric-sub {{ font-size: 0.75rem; color: #555; font-weight: 500; }}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 🔗 CONEXÃO E LEITURA DE DADOS
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

def get_user_data_completo(telefone):
    try:
        sh = connect_google()
        
        # 1. Pega Nome
        nome_real = "Atleta"
        try:
            ws_users = sh.worksheet("Usuarios")
            cell = ws_users.find(str(telefone))
            if cell: nome_real = ws_users.cell(cell.row, 2).value
        except: pass

        # 2. Pega Treinos
        ws_treino = sh.worksheet(str(telefone))
        data = ws_treino.get_all_records()
        df = pd.DataFrame(data)
        
        # --- VACINA CONTRA ERROS DE COLUNA ---
        # Remove espaços extras dos nomes das colunas (Ex: "Data " vira "Data")
        df.columns = df.columns.str.strip()
        
        # Mapa de renomeação
        mapa = {
            'Carga': 'Carga_Kg', 'carga': 'Carga_Kg', 'Carga (kg)': 'Carga_Kg',
            'Exercicio': 'Exercicio', 'Exercício': 'Exercicio', 'exercicio': 'Exercicio',
            'Data': 'Data', 'data': 'Data', 'Dia': 'Data',
            'Reps': 'Reps', 'reps': 'Reps',
            'Series': 'Series', 'series': 'Series'
        }
        df = df.rename(columns=mapa)
        
        # Garante colunas essenciais mesmo se vazias
        if 'Carga_Kg' not in df.columns: df['Carga_Kg'] = 0
        if 'Data' not in df.columns: df['Data'] = datetime.today().strftime("%d/%m/%Y")
        if 'Exercicio' not in df.columns: df['Exercicio'] = "Treino Geral"
        
        return df, nome_real
    except: return None, None

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
    df_check, nome_check = get_user_data_completo(usuario_url)
    if df_check is not None and not df_check.empty:
        st.session_state['telefone_usuario'] = usuario_url
        st.session_state['df_usuario'] = df_check
        st.session_state['nome_usuario'] = nome_check
    else: st.error("⚠️ Perfil não encontrado.")

if 'telefone_usuario' not in st.session_state:
    st.markdown("<br><h1 style='text-align: center;'>⚡ GYMBOT</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        telefone_input = st.text_input("ID de Acesso", placeholder="Seu número...")
        if st.button("ACESSAR", use_container_width=True):
            df, nome = get_user_data_completo(telefone_input)
            if df is not None and not df.empty:
                st.session_state['telefone_usuario'] = telefone_input
                st.session_state['df_usuario'] = df
                st.session_state['nome_usuario'] = nome
                st.rerun()
            else: st.error("ID Inválido.")

# ==============================================================================
# 📊 DASHBOARD
# ==============================================================================
else:
    df = st.session_state['df_usuario']
    nome_exibicao = st.session_state.get('nome_usuario', 'Atleta').split()[0].upper()
    
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
    
    # Header
    c_perfil, c_btn = st.columns([8,1])
    with c_perfil:
        st.markdown(f"### Olá, <span class='highlight-text'>{nome_exibicao}</span>.", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 5px;">
            <span style="font-size: 0.8rem; color: #888; font-weight: 600;">NÍVEL: <b style="color:white">{nivel_nome}</b></span>
            <span style="font-size: 0.8rem; color: #666; font-weight: 600;">{xp_atual:,.0f} / {xp_prox:,.0f} pts</span>
        </div>
        <div class="progress-container"><div class="progress-fill" style="width: {pct}%;"></div></div>
        """, unsafe_allow_html=True)
    with c_btn:
        if st.button("SAIR"):
            st.session_state.clear(); st.query_params.clear(); st.rerun()

    st.markdown("---")

    # Gráfico 1: Frequência
    st.markdown("##### 📅 Frequência Semanal")
    if 'Dia_Semana' in df.columns:
        ordem_dias = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
        contagem_dias = df['Dia_Semana'].value_counts().reindex(ordem_dias, fill_value=0).reset_index()
        contagem_dias.columns = ['Dia', 'Treinos']
        
        fig_week = go.Figure(data=[go.Bar(
            x=contagem_dias['Dia'],
            y=contagem_dias['Treinos'],
            text=contagem_dias['Treinos'],
            textposition='auto',
            marker_color=NEON_GREEN,
            marker_line_color='#004d29',
            marker_line_width=1,
        )])

        fig_week.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#666", family="Inter, sans-serif"),
            margin=dict(l=0, r=0, t=20, b=0),
            height=180,
            xaxis=dict(showgrid=False, fixedrange=True),
            yaxis=dict(showgrid=False, visible=False, fixedrange=True),
            bargap=0.25
        )
        st.plotly_chart(fig_week, use_container_width=True, config={'staticPlot': True})

    # Seleção
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
        
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='css-card'><div class='metric-label'>Último</div><div class='metric-value'>{ult_carga} <span style='font-size:0.8rem'>{unidade}</span></div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='css-card'><div class='metric-label'>Recorde</div><div class='metric-value' style='color:{NEON_GREEN}'>{max_carga} <span style='font-size:0.8rem'>{unidade}</span></div></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='css-card'><div class='metric-label'>Treinos</div><div class='metric-value'>{qtd_treinos}</div></div>", unsafe_allow_html=True)

        # Gráfico 2: Linha
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_filt['Data'], 
            y=df_filt['Carga_Kg'],
            mode='lines+markers',
            line=dict(color=NEON_GREEN, width=3, shape='spline'),
            marker=dict(size=6, color=CARD_BG, line=dict(color=NEON_GREEN, width=2)),
            fill='tozeroy',
            fillcolor='rgba(0, 255, 136, 0.05)'
        ))
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(showgrid=False, showline=True, linecolor='#333', fixedrange=True),
            yaxis=dict(showgrid=True, gridcolor='#222', zeroline=False, fixedrange=True),
            height=220
        )
        st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True})

    with st.expander("📜 Histórico Completo"):
        st.dataframe(df_filt[['Data', 'Series', 'Reps', 'Carga_Kg', 'Notas']], use_container_width=True, hide_index=True)
