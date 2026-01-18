import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

# ==============================================================================
# 🎨 ESTILO NEON PRO (Híbrido: Visual Gamer + Funcionalidade Health)
# ==============================================================================
st.set_page_config(page_title="GymBot Pro", page_icon="⚡", layout="wide")

# Cores
NEON_GREEN = "#00ff88"   # Verde Razer
NEON_PURPLE = "#8A2BE2"  # Roxo Solo Leveling
BG_COLOR = "#050505"     # Preto Quase Absoluto
CARD_BG = "#101010"      # Cinza Chumbo
TEXT_DIM = "#555555"     # Texto apagado

st.markdown(f"""
<style>
    .stApp {{ background-color: {BG_COLOR}; color: #fff; }}
    header[data-testid="stHeader"] {{ background-color: rgba(0,0,0,0); }}
    .block-container {{ padding-top: 1rem; }}
    
    /* Cards Modernos */
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
    
    /* Métricas Grandes */
    .big-metric {{ font-size: 2.5rem; font-weight: 900; color: #fff; line-height: 1; }}
    .metric-label {{ font-size: 0.8rem; color: #888; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; margin-bottom: 5px; }}
    
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 🔗 CONEXÃO
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
        
        # Limpeza e Padronização
        df.columns = df.columns.str.strip()
        mapa = {'Carga': 'Carga_Kg', 'carga': 'Carga_Kg', 'Data': 'Data', 'Exercicio': 'Exercicio'}
        cols_atuais = {c: c for c in df.columns}
        for k, v in mapa.items():
            if k in cols_atuais: cols_atuais[k] = v
        
        if 'Carga_Kg' in df.columns: df = df.rename(columns={'Carga_Kg': 'Carga'})
        if 'Carga' not in df.columns: df['Carga'] = 0
        if 'Data' not in df.columns: df['Data'] = datetime.today().strftime("%d/%m/%Y")
        
        df['Carga'] = pd.to_numeric(df['Carga'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        df['Data_Dt'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        
        return df, nome_real
    except: return None, None

def estimar_calorias(row):
    # Algoritmo de Estimativa
    nome_ex = str(row['Exercicio']).lower()
    eh_cardio = any(x in nome_ex for x in ['esteira', 'bike', 'corrida', 'elíptico'])
    
    if eh_cardio:
        return row['Carga'] * 7 # 7 kcal por minuto (média corrida leve)
    else:
        # Musculação: Volume x Fator
        reps = float(row['Reps']) if 'Reps' in row and row['Reps'] != '' else 10
        series = float(row['Series']) if 'Series' in row and row['Series'] != '' else 3
        return (row['Carga'] * reps * series) * 0.005 # Fator estimado

# ==============================================================================
# 📊 GRÁFICO DE BARRAS INTELIGENTE (Highlight)
# ==============================================================================
def plot_barras_neon(df_semana):
    df_semana['Dia_Str'] = df_semana['Data_Dt'].dt.strftime('%a') # Seg, Ter...
    
    # Cria os últimos 7 dias na ordem certa
    dias_ordem = [(datetime.today() - timedelta(days=i)).strftime('%a') for i in range(6, -1, -1)]
    
    # Agrupa Kcal por dia
    dados = df_semana.groupby('Dia_Str')['Calorias'].sum().reindex(dias_ordem, fill_value=0).reset_index()
    
    # Lógica de Cores: Cinza para dias passados, Verde Neon para HOJE
    cores = ['#222222'] * 7
    cores[-1] = NEON_GREEN # Hoje brilha
    
    fig = go.Figure(data=[go.Bar(
        x=dados['Dia_Str'],
        y=dados['Calorias'],
        marker_color=cores,
        marker_line_width=0,
        text=dados['Calorias'].astype(int), # Valor em cima da barra
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
        bargap=0.3 # Barras mais finas e elegantes
    )
    return fig

# ==============================================================================
# 🍩 DONUTS NEON
# ==============================================================================
def plot_donut_neon(valor, meta, cor, label):
    pct = min(1, valor / meta)
    restante = 1 - pct
    
    fig = go.Figure(data=[go.Pie(
        values=[pct, restante],
        hole=0.85,
        marker_colors=[cor, "#151515"], # Cor Neon vs Fundo Escuro
        textinfo='none',
        hoverinfo='none',
        sort=False,
        direction='clockwise'
    )])
    
    fig.update_layout(
        showlegend=False,
        margin=dict(t=0, b=0, l=0, r=0),
        height=120,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        annotations=[dict(
            text=f"<span style='font-size:1.2rem; color:#fff; font-weight:900'>{int(valor)}</span>", 
            x=0.5, y=0.55, showarrow=False
        ), dict(
            text=f"<span style='font-size:0.6rem; color:#666'>{label}</span>", 
            x=0.5, y=0.35, showarrow=False
        )]
    )
    return fig

# ==============================================================================
# 📱 APP PRINCIPAL
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

# Dados
df, nome = get_data(st.session_state['telefone'])
if df is None: st.error("Erro ao carregar."); st.stop()

# Cálculos
df['Calorias'] = df.apply(estimar_calorias, axis=1)
hoje = datetime.today()
df_hoje = df[df['Data_Dt'].dt.date == hoje.date()]

cals_hoje = df_hoje['Calorias'].sum()
treinos_hoje = len(df_hoje)
volume_hoje = df_hoje['Carga'].sum()

# --- HEADER ---
c1, c2 = st.columns([4,1])
with c1:
    st.markdown(f"## Olá, <span class='highlight-text'>{nome.split()[0].upper()}</span>.", unsafe_allow_html=True)
with c2:
    if st.button("SAIR"): st.session_state.clear(); st.rerun()

# --- DASHBOARD ---

# 1. RESUMO DO DIA (DONUTS)
st.markdown(f"<div class='css-card'>", unsafe_allow_html=True)
st.markdown("### 🔥 Hoje", unsafe_allow_html=True)
k1, k2, k3 = st.columns(3)
with k1:
    st.plotly_chart(plot_donut_neon(cals_hoje, 600, "#FF3B30", "KCAL"), use_container_width=True, config={'staticPlot':True})
with k2:
    st.plotly_chart(plot_donut_neon(treinos_hoje, 5, NEON_GREEN, "TREINOS"), use_container_width=True, config={'staticPlot':True})
with k3:
    st.plotly_chart(plot_donut_neon(volume_hoje, 10000, NEON_PURPLE, "VOL KG"), use_container_width=True, config={'staticPlot':True})
st.markdown("</div>", unsafe_allow_html=True)

# 2. GRÁFICO DE BARRAS DESTAQUE (CALORIAS SEMANAIS)
st.markdown(f"<div class='css-card'>", unsafe_allow_html=True)
st.markdown("### 📅 Gasto Calórico (7 Dias)", unsafe_allow_html=True)
ini = hoje - timedelta(days=6)
df_sem = df[(df['Data_Dt'] >= ini) & (df['Data_Dt'] <= hoje)]
st.plotly_chart(plot_barras_neon(df_sem), use_container_width=True, config={'staticPlot':True})
st.markdown("</div>", unsafe_allow_html=True)

# 3. EVOLUÇÃO DE CARGA
st.markdown(f"<div class='css-card'>", unsafe_allow_html=True)
st.markdown("### 📈 Evolução", unsafe_allow_html=True)
exs = df['Exercicio'].unique()
escolha = st.selectbox("", exs, label_visibility="collapsed")

if escolha:
    df_f = df[df['Exercicio'] == escolha]
    ult = df_f['Carga'].iloc[-1]
    rec = df_f['Carga'].max()
    
    # Métricas lado a lado
    m1, m2 = st.columns(2)
    m1.markdown(f"<div class='metric-label'>Último</div><div class='big-metric'>{int(ult)}<span style='font-size:1rem'>kg</span></div>", unsafe_allow_html=True)
    m2.markdown(f"<div class='metric-label'>Recorde</div><div class='big-metric' style='color:{NEON_GREEN}'>{int(rec)}<span style='font-size:1rem'>kg</span></div>", unsafe_allow_html=True)
    
    # Gráfico Linha Neon
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_f['Data'], y=df_f['Carga'],
        mode='lines+markers',
        line=dict(color=NEON_GREEN, width=3, shape='spline'),
        marker=dict(size=6, color=BG_COLOR, line=dict(color=NEON_GREEN, width=2)),
        fill='tozeroy', fillcolor='rgba(0, 255, 136, 0.1)'
    ))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=20, b=0), height=200,
        xaxis=dict(showgrid=False, visible=False), yaxis=dict(showgrid=True, gridcolor='#222')
    )
    st.plotly_chart(fig, use_container_width=True, config={'staticPlot':True})
st.markdown("</div>", unsafe_allow_html=True)
