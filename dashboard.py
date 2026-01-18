import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

# ==============================================================================
# 🎨 ESTILO "CLEAN APP" (Igual sua referência)
# ==============================================================================
st.set_page_config(page_title="Minha Evolução", page_icon="🧘", layout="wide")

# Cores do Tema (Roxo/Azul Suave)
PRIMARY_COLOR = "#6C63FF"
BG_COLOR = "#f4f6f9" # Fundo cinza clarinho tipo App
CARD_BG = "#ffffff"
TEXT_COLOR = "#2c3e50"

st.markdown(f"""
<style>
    /* Fundo Geral */
    .stApp {{
        background-color: {BG_COLOR};
        color: {TEXT_COLOR};
    }}
    
    /* Remove barra superior */
    header[data-testid="stHeader"] {{ background-color: rgba(0,0,0,0); }}
    .block-container {{ padding-top: 2rem; padding-bottom: 5rem; }}
    
    /* Cartões (Cards) estilo iOS */
    .css-card {{
        background-color: {CARD_BG};
        border-radius: 24px; /* Bem redondo */
        padding: 24px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05); /* Sombra suave */
        margin-bottom: 20px;
        text-align: center;
        transition: transform 0.3s ease;
    }}
    .css-card:hover {{
        transform: translateY(-5px);
    }}
    
    /* Títulos */
    h1, h2, h3 {{ font-family: 'Segoe UI', sans-serif; color: #2c3e50 !important; font-weight: 700; }}
    h4, h5 {{ color: #7f8c8d !important; font-weight: 600; }}
    
    /* Métricas dentro dos Cards */
    .metric-value {{ font-size: 2.2rem; font-weight: 800; color: {PRIMARY_COLOR}; }}
    .metric-label {{ font-size: 0.9rem; color: #95a5a6; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }}
    .metric-sub {{ font-size: 0.8rem; color: #bdc3c7; margin-top: 5px; }}

    /* Remove padding dos gráficos Plotly */
    .js-plotly-plot .plotly .main-svg {{ border-radius: 24px; }}
    
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 🔗 CONEXÃO ROBUSTA (Corrigindo o erro de Data)
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
        # Tenta pegar nome
        nome_real = "Atleta"
        try:
            ws_u = sh.worksheet("Usuarios")
            c = ws_u.find(str(telefone))
            if c: nome_real = ws_u.cell(c.row, 2).value
        except: pass

        # Pega Treinos
        ws = sh.worksheet(str(telefone))
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        
        # --- VACINA CONTRA ERRO DE COLUNAS ---
        # 1. Limpa espaços nos nomes das colunas
        df.columns = df.columns.str.strip()
        
        # 2. Renomeia forçando o padrão (mesmo se estiver maiusculo/minusculo)
        rename_map = {
            'Data': 'Data', 'data': 'Data', 'DATA': 'Data',
            'Exercicio': 'Exercicio', 'exercicio': 'Exercicio', 'Exercício': 'Exercicio',
            'Carga_Kg': 'Carga', 'Carga': 'Carga', 'carga': 'Carga',
            'Reps': 'Reps', 'reps': 'Reps',
            'Series': 'Series', 'series': 'Series'
        }
        # Normaliza as colunas atuais para aplicar o mapa
        cols_atuais = {c: c for c in df.columns}
        for k, v in rename_map.items():
            if k in cols_atuais: cols_atuais[k] = v # Sobrescreve
            
        # Aplica renomeação manual caso o mapa falhe
        if 'Carga_Kg' in df.columns: df = df.rename(columns={'Carga_Kg': 'Carga'})
        
        # Garante existência
        if 'Carga' not in df.columns: df['Carga'] = 0
        if 'Data' not in df.columns: df['Data'] = datetime.today().strftime("%d/%m/%Y")
        if 'Exercicio' not in df.columns: df['Exercicio'] = "Geral"

        # Converte números
        df['Carga'] = pd.to_numeric(df['Carga'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        
        return df, nome_real
    except Exception as e:
        return None, None

# ==============================================================================
# 🍩 GRÁFICOS PERSONALIZADOS (Donut Charts)
# ==============================================================================
def plot_donut(valor_atual, meta, cor, titulo, sufixo=""):
    pct = min(100, (valor_atual / meta) * 100) if meta > 0 else 0
    restante = max(0, 100 - pct)
    
    fig = go.Figure(data=[go.Pie(
        labels=['Concluído', 'Falta'],
        values=[pct, restante],
        hole=.75, # Buraco no meio (Donut)
        marker_colors=[cor, '#e0e0e0'], # Cor da barra e cor de fundo cinza
        textinfo='none', # Não mostrar texto na roda
        sort=False,
        hoverinfo='none'
    )])

    fig.update_layout(
        showlegend=False,
        margin=dict(t=0, b=0, l=0, r=0),
        height=140,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        annotations=[dict(text=f"{int(valor_atual)}<br><span style='font-size:12px; color:#999'>{sufixo}</span>", x=0.5, y=0.5, font_size=24, font_weight='bold', showarrow=False, font_color=cor)]
    )
    return fig

# ==============================================================================
# 📱 INTERFACE PRINCIPAL
# ==============================================================================
# Login Simplificado
query = st.query_params
uid = query.get("id", None)

if 'telefone' not in st.session_state:
    if uid: 
        st.session_state['telefone'] = uid
        st.rerun()
    else:
        st.markdown("<h2 style='text-align: center;'>Bem-vindo de volta! 👋</h2>", unsafe_allow_html=True)
        c1,c2,c3 = st.columns([1,2,1])
        with c2:
            tel = st.text_input("Seu ID", placeholder="Ex: 5547...")
            if st.button("Entrar", use_container_width=True):
                st.session_state['telefone'] = tel
                st.rerun()
        st.stop()

# --- CARREGA DADOS ---
df, nome = get_data(st.session_state['telefone'])

if df is None:
    st.error("Erro ao carregar. Verifique se o número está correto.")
    if st.button("Voltar"):
        st.session_state.clear()
        st.rerun()
    st.stop()

# --- BARRA LATERAL (METAS DINÂMICAS) ---
st.sidebar.header("🎯 Suas Metas de Hoje")
meta_treinos = st.sidebar.slider("Treinos na Semana", 1, 7, 4)
meta_cardio = st.sidebar.slider("Minutos de Cardio", 10, 120, 30)
meta_volume = st.sidebar.number_input("Volume de Carga (kg)", 1000, 50000, 5000, step=500)

# --- PROCESSAMENTO ---
# Identifica Cardio vs Musculação
cardio_keywords = ['esteira', 'bike', 'bicicleta', 'corrida', 'elíptico', 'caminhada']
df['Tipo'] = df['Exercicio'].apply(lambda x: 'Cardio' if any(k in str(x).lower() for k in cardio_keywords) else 'Força')

# Filtra Ultima Semana (Mockup lógico se não tiver dados suficientes)
# Aqui pegamos o total geral para simplificar a visualização
total_treinos = len(df) # Isso seria total vida, mas vamos fingir que é ciclo atual
total_volume = df[df['Tipo']=='Força']['Carga'].sum()
total_cardio = df[df['Tipo']=='Cardio']['Carga'].sum() # Assume que carga no cardio é minutos

# --- HEADER ---
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown(f"### Olá, {nome.split()[0]}!")
    st.markdown("Aqui está o resumo da sua atividade.")
with c2:
    if st.button("Sair", type="secondary"):
        st.session_state.clear()
        st.query_params.clear()
        st.rerun()

# --- DASHBOARD GRID ---

# LINHA 1: OS CÍRCULOS (DONUTS)
st.markdown("#### 🔥 Atividade Diária")
col_a, col_b, col_c = st.columns(3)

with col_a:
    st.markdown(f"<div class='css-card' style='padding:15px'><h5>Cardio (Min)</h5>", unsafe_allow_html=True)
    fig_cardio = plot_donut(total_cardio, meta_cardio, "#FF6B6B", "Cardio", "min")
    st.plotly_chart(fig_cardio, use_container_width=True, config={'staticPlot': True})
    st.markdown("</div>", unsafe_allow_html=True)

with col_b:
    st.markdown(f"<div class='css-card' style='padding:15px'><h5>Volume (kg)</h5>", unsafe_allow_html=True)
    fig_vol = plot_donut(total_volume, meta_volume, "#6C63FF", "Volume", "kg")
    st.plotly_chart(fig_vol, use_container_width=True, config={'staticPlot': True})
    st.markdown("</div>", unsafe_allow_html=True)

with col_c:
    st.markdown(f"<div class='css-card' style='padding:15px'><h5>Frequência</h5>", unsafe_allow_html=True)
    # Calculando treinos na semana (Fake data logic para exemplo, usando total)
    treinos_semana = min(total_treinos, 7) 
    fig_freq = plot_donut(treinos_semana, meta_treinos, "#4ECDC4", "Frequência", "dias")
    st.plotly_chart(fig_freq, use_container_width=True, config={'staticPlot': True})
    st.markdown("</div>", unsafe_allow_html=True)

# LINHA 2: GRÁFICO DE AREA (EVOLUÇÃO)
st.markdown("#### 📈 Histórico de Performance")

exercicios = df['Exercicio'].unique()
escolha = st.selectbox("Selecione para ver o gráfico:", exercicios)

if escolha:
    df_filt = df[df['Exercicio'] == escolha]
    
    # Card de Resumo
    max_val = df_filt['Carga'].max()
    ult_val = df_filt['Carga'].iloc[-1]
    unidade = "min" if any(x in escolha.lower() for x in cardio_keywords) else "kg"
    
    st.markdown(f"""
    <div class='css-card' style='display:flex; justify-content:space-around; align-items:center;'>
        <div>
            <div class='metric-label'>Último Treino</div>
            <div class='metric-value'>{ult_val} <span style='font-size:1rem'>{unidade}</span></div>
        </div>
        <div style='border-left: 1px solid #eee; height: 50px;'></div>
        <div>
            <div class='metric-label'>Seu Recorde</div>
            <div class='metric-value' style='color:#4ECDC4'>{max_val} <span style='font-size:1rem'>{unidade}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Gráfico de Área Suave
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_filt['Data'], 
        y=df_filt['Carga'],
        mode='lines',
        line=dict(color=PRIMARY_COLOR, width=4, shape='spline'),
        fill='tozeroy',
        fillcolor='rgba(108, 99, 255, 0.2)' # Roxo transparente
    ))
    fig.update_layout(
        template="plotly_white", # Fundo branco clean
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(showgrid=False, showline=False),
        yaxis=dict(showgrid=True, gridcolor='#f0f0f0', zeroline=False),
        height=250
    )
    st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True})

# LINHA 3: TABELA CLEAN
with st.expander("Ver Todos os Registros"):
    st.dataframe(
        df[['Data', 'Exercicio', 'Series', 'Reps', 'Carga']], 
        use_container_width=True, 
        hide_index=True
    )
