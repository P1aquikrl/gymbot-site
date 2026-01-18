import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

# ==============================================================================
# 🎨 ESTILO NEON PRO (Visual Mantido)
# ==============================================================================
st.set_page_config(page_title="GymBot Pro", page_icon="⚡", layout="wide")

NEON_GREEN = "#00ff88"
NEON_PURPLE = "#8A2BE2"
BG_COLOR = "#050505"
CARD_BG = "#101010"

st.markdown(f"""
<style>
    .stApp {{ background-color: {BG_COLOR}; color: #fff; }}
    header[data-testid="stHeader"] {{ background-color: rgba(0,0,0,0); }}
    .block-container {{ padding-top: 1rem; }}
    .css-card {{
        background-color: {CARD_BG};
        border-radius: 20px;
        padding: 20px;
        border: 1px solid #1a1a1a;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        margin-bottom: 15px;
    }}
    h1, h2, h3 {{ font-family: 'Inter', sans-serif; font-weight: 800; margin: 0; }}
    .highlight-text {{ color: {NEON_GREEN}; }}
    .big-metric {{ font-size: 2.5rem; font-weight: 900; color: #fff; line-height: 1; }}
    .metric-label {{ font-size: 0.8rem; color: #888; text-transform: uppercase; font-weight: 600; margin-bottom: 5px; }}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 🔗 CONEXÃO & TRATAMENTO DE DADOS (A CORREÇÃO ESTÁ AQUI)
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
        # Nome
        nome_real = "Atleta"
        try:
            ws_u = sh.worksheet("Usuarios")
            c = ws_u.find(str(telefone))
            if c: nome_real = ws_u.cell(c.row, 2).value
        except: pass

        # Treinos
        ws = sh.worksheet(str(telefone))
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        
        # Limpeza de Colunas
        df.columns = df.columns.str.strip()
        mapa = {'Carga': 'Carga_Kg', 'carga': 'Carga_Kg', 'Data': 'Data', 'Exercicio': 'Exercicio'}
        cols_atuais = {c: c for c in df.columns}
        for k, v in mapa.items():
            if k in cols_atuais: cols_atuais[k] = v
        
        if 'Carga_Kg' in df.columns: df = df.rename(columns={'Carga_Kg': 'Carga'})
        if 'Carga' not in df.columns: df['Carga'] = 0
        if 'Data' not in df.columns: df['Data'] = datetime.today().strftime("%d/%m/%Y")
        
        # Conversão Numérica
        df['Carga'] = pd.to_numeric(df['Carga'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        
        # 🚨 CORREÇÃO CRÍTICA DE DATA E ORDENAÇÃO 🚨
        # 1. Converte para objeto de Data Real (Dia/Mes/Ano)
        df['Data_Dt'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        
        # 2. Remove datas inválidas (NaT) que causam bugs
        df = df.dropna(subset=['Data_Dt'])
        
        # 3. ORDENA DO MAIS ANTIGO PARA O MAIS RECENTE (Isso conserta o gráfico embolado)
        df = df.sort_values(by='Data_Dt')
        
        return df, nome_real
    except: return None, None

def estimar_calorias(row):
    nome_ex = str(row['Exercicio']).lower()
    eh_cardio = any(x in nome_ex for x in ['esteira', 'bike', 'corrida', 'elíptico'])
    if eh_cardio: return row['Carga'] * 7
    reps = float(row['Reps']) if 'Reps' in row and row['Reps'] != '' else 10
    series = float(row['Series']) if 'Series' in row and row['Series'] != '' else 3
    return (row['Carga'] * reps * series) * 0.005

# ==============================================================================
# 📊 GRÁFICOS
# ==============================================================================
def plot_barras_neon(df_semana):
    # Garante ordenação
    df_semana = df_semana.sort_values(by='Data_Dt')
    
    df_semana['Dia_Str'] = df_semana['Data_Dt'].dt.strftime('%d/%m') # Mostra dia/mês (ex: 18/01)
    
    # Agrupa somando calorias por dia
    dados = df_semana.groupby('Dia_Str', sort=False)['Calorias'].sum().reset_index()
    
    # Lógica de Cores
    cores = ['#222222'] * len(dados)
    if len(cores) > 0: cores[-1] = NEON_GREEN # Último dia aceso
    
    fig = go.Figure(data=[go.Bar(
        x=dados['Dia_Str'],
        y=dados['Calorias'],
        marker_color=cores,
        marker_line_width=0,
        text=dados['Calorias'].astype(int),
        textposition='auto',
        textfont=dict(color='#fff')
    )])
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=10, b=0),
        height=180,
        showlegend=False,
        xaxis=dict(showgrid=False, tickfont=dict(color='#666')),
        yaxis=dict(showgrid=False, visible=False),
        bargap=0.3
    )
    return fig

def plot_donut_neon(valor, meta, cor, label):
    pct = min(1, valor / meta)
    fig = go.Figure(data=[go.Pie(
        values=[pct, 1-pct],
        hole=0.85,
        marker_colors=[cor, "#151515"],
        textinfo='none', hoverinfo='none', sort=False, direction='clockwise'
    )])
    fig.update_layout(
        showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=120,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        annotations=[dict(text=f"<span style='font-size:1.2rem; color:#fff; font-weight:900'>{int(valor)}</span>", x=0.5, y=0.55, showarrow=False),
                     dict(text=f"<span style='font-size:0.6rem; color:#666'>{label}</span>", x=0.5, y=0.35, showarrow=False)]
    )
    return fig

# ==============================================================================
# 📱 APP LÓGICA
# ==============================================================================
query = st.query_params
uid = query.get("id", None)

if 'telefone' not in st.session_state:
    if uid: 
        st.session_state['telefone'] = uid
        st.rerun()
    else:
        st.markdown("<br><h2 style='text-align:center'>LOGIN</h2>", unsafe_allow_html=True)
        c1,c2,c3 = st.columns([1,2,1])
        with c2:
            t = st.text_input("ID", placeholder="Seu número...")
            if st.button("ENTRAR", use_container_width=True):
                st.session_state['telefone'] = t
                st.rerun()
        st.stop()

df, nome = get_data(st.session_state['telefone'])
if df is None: st.error("Erro ao carregar."); st.stop()

df['Calorias'] = df.apply(estimar_calorias, axis=1)
hoje = datetime.today()
df_hoje = df[df['Data_Dt'].dt.date == hoje.date()]

# Métricas Hoje
cals_hoje = df_hoje['Calorias'].sum()
treinos_hoje = len(df_hoje)
volume_hoje = df_hoje['Carga'].sum()

# HEADER
c1, c2 = st.columns([4,1])
with c1: st.markdown(f"## Olá, <span class='highlight-text'>{nome.split()[0].upper()}</span>.", unsafe_allow_html=True)
with c2: 
    if st.button("SAIR"): st.session_state.clear(); st.rerun()

# 1. DONUTS (HOJE)
st.markdown(f"<div class='css-card'><h3>🔥 Hoje</h3>", unsafe_allow_html=True)
k1, k2, k3 = st.columns(3)
with k1: st.plotly_chart(plot_donut_neon(cals_hoje, 600, "#FF3B30", "KCAL"), use_container_width=True, config={'staticPlot':True})
with k2: st.plotly_chart(plot_donut_neon(treinos_hoje, 5, NEON_GREEN, "TREINOS"), use_container_width=True, config={'staticPlot':True})
with k3: st.plotly_chart(plot_donut_neon(volume_hoje, 10000, NEON_PURPLE, "VOL KG"), use_container_width=True, config={'staticPlot':True})
st.markdown("</div>", unsafe_allow_html=True)

# 2. BARRAS SEMANAIS
st.markdown(f"<div class='css-card'><h3>📅 Últimos 7 Dias de Treino</h3>", unsafe_allow_html=True)
# Pega os ultimos 7 registros de datas DISTINTAS presentes no banco
datas_unicas = df['Data_Dt'].drop_duplicates().sort_values(ascending=False).head(7)
if not datas_unicas.empty:
    min_date = datas_unicas.min()
    df_sem = df[df['Data_Dt'] >= min_date]
    st.plotly_chart(plot_barras_neon(df_sem), use_container_width=True, config={'staticPlot':True})
else:
    st.info("Ainda não há histórico suficiente.")
st.markdown("</div>", unsafe_allow_html=True)

# 3. EVOLUÇÃO (LINHA)
st.markdown(f"<div class='css-card'><h3>📈 Evolução</h3>", unsafe_allow_html=True)
exs = df['Exercicio'].unique()
escolha = st.selectbox("", exs, label_visibility="collapsed")

if escolha:
    df_f = df[df['Exercicio'] == escolha].sort_values(by='Data_Dt') # Ordena de novo pra garantir
    ult = df_f['Carga'].iloc[-1]
    rec = df_f['Carga'].max()
    
    m1, m2 = st.columns(2)
    m1.markdown(f"<div class='metric-label'>Último</div><div class='big-metric'>{int(ult)}<span style='font-size:1rem'>kg</span></div>", unsafe_allow_html=True)
    m2.markdown(f"<div class='metric-label'>Recorde</div><div class='big-metric' style='color:{NEON_GREEN}'>{int(rec)}<span style='font-size:1rem'>kg</span></div>", unsafe_allow_html=True)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_f['Data_Dt'], # USA A DATA REAL AGORA
        y=df_f['Carga'],
        mode='lines+markers',
        line=dict(color=NEON_GREEN, width=3, shape='spline'),
        marker=dict(size=6, color=BG_COLOR, line=dict(color=NEON_GREEN, width=2)),
        fill='tozeroy', fillcolor='rgba(0, 255, 136, 0.1)'
    ))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=20, b=0), height=200,
        xaxis=dict(showgrid=False, tickformat="%d/%m"), # Formata data bonita no eixo X
        yaxis=dict(showgrid=True, gridcolor='#222')
    )
    st.plotly_chart(fig, use_container_width=True, config={'staticPlot':True})
st.markdown("</div>", unsafe_allow_html=True)
