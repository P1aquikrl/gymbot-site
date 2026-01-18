import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

# ==============================================================================
# 🎨 ESTILO "DARK HEALTH" (Igual sua referência de App)
# ==============================================================================
st.set_page_config(page_title="GymBot Pro", page_icon="🔥", layout="wide")

# Paleta de Cores (Inspirada no Apple Fitness / Nike Run Club)
BG_COLOR = "#000000"       # Preto Absoluto
CARD_BG = "#1c1c1e"        # Cinza Chumbo (Cards)
ACCENT_COLOR = "#CEFF00"   # Verde/Amarelo Marca-Texto (Destaque)
DIMMED_COLOR = "#2c2c2e"   # Cinza Apagado (Barras inativas)
TEXT_WHITE = "#ffffff"

st.markdown(f"""
<style>
    /* Fundo */
    .stApp {{ background-color: {BG_COLOR}; color: {TEXT_WHITE}; }}
    
    /* Remove barra superior */
    header[data-testid="stHeader"] {{ background-color: rgba(0,0,0,0); }}
    .block-container {{ padding-top: 1rem; padding-bottom: 5rem; }}
    
    /* Cards Arredondados (Estilo iOS) */
    .css-card {{
        background-color: {CARD_BG};
        border-radius: 22px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }}
    
    /* Tipografia */
    h1, h2, h3 {{ font-family: 'Inter', sans-serif; font-weight: 800; color: {TEXT_WHITE} !important; margin-bottom: 0px; }}
    p {{ color: #8e8e93; font-size: 0.9rem; }}
    
    /* Destaques */
    .highlight {{ color: {ACCENT_COLOR}; font-weight: bold; }}
    
    /* Botões customizados do Streamlit */
    div.stButton > button {{
        background-color: {ACCENT_COLOR};
        color: black;
        border-radius: 30px;
        border: none;
        font-weight: bold;
        padding: 10px 20px;
    }}
    div.stButton > button:hover {{ background-color: #b3dd00; color: black; }}

</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 🔗 CONEXÃO E DADOS
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
        # Pega Nome
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
        
        # Limpeza
        df.columns = df.columns.str.strip()
        mapa = {'Carga': 'Carga_Kg', 'carga': 'Carga_Kg', 'Data': 'Data', 'Exercicio': 'Exercicio'}
        cols_atuais = {c: c for c in df.columns}
        for k, v in mapa.items():
            if k in cols_atuais: cols_atuais[k] = v
        
        if 'Carga_Kg' in df.columns: df = df.rename(columns={'Carga_Kg': 'Carga'}) # Normaliza para 'Carga'
        if 'Carga' not in df.columns: df['Carga'] = 0
        if 'Data' not in df.columns: df['Data'] = datetime.today().strftime("%d/%m/%Y")
        
        # Converte Carga
        df['Carga'] = pd.to_numeric(df['Carga'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        
        # Converte Data
        df['Data_Dt'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        
        return df, nome_real
    except: return None, None

# ==============================================================================
# ⚡ LÓGICA DE CALORIAS (ESTIMATIVA)
# ==============================================================================
def estimar_calorias(row):
    # Lógica simples: 
    # Musculação: Volume * 0.02 (aprox)
    # Cardio: Minutos * 8 (aprox corrida leve)
    exercicio = str(row['Exercicio']).lower()
    eh_cardio = any(x in exercicio for x in ['esteira', 'bike', 'corrida', 'elíptico'])
    
    if eh_cardio:
        return row['Carga'] * 8 # Assumindo que Carga no cardio são minutos
    else:
        # Assumindo reps média de 10 se não tiver a coluna
        reps = float(row['Reps']) if 'Reps' in row and row['Reps'] != '' else 10
        series = float(row['Series']) if 'Series' in row and row['Series'] != '' else 3
        # Volume Load = Carga * Series * Reps. 
        # Caloria estimada ≈ Volume Load * 0.005 (Fator arbitrário para musculação)
        volume_load = row['Carga'] * reps * series
        return volume_load * 0.005

# ==============================================================================
# 🎨 GRÁFICO DE BARRAS "HIGHLIGHT" (O que você pediu)
# ==============================================================================
def plot_barras_destaque(df_semana):
    # Agrupa por dia da semana
    df_semana['Dia_Semana'] = df_semana['Data_Dt'].dt.strftime('%a') # Seg, Ter...
    # Cria ordem correta
    dias_ordem = [(datetime.today() - timedelta(days=i)).strftime('%a') for i in range(6, -1, -1)]
    
    # Agrupa dados reais
    dados_agrupados = df_semana.groupby('Dia_Semana')['Calorias'].sum().reindex(dias_ordem, fill_value=0).reset_index()
    
    # Lógica de Cores: O último dia (hoje) é ACESO, o resto é APAGADO
    cores = [DIMMED_COLOR] * 7
    cores[-1] = ACCENT_COLOR # O último dia da lista (Hoje) fica Neon
    
    fig = go.Figure(data=[go.Bar(
        x=dados_agrupados['Dia_Semana'],
        y=dados_agrupados['Calorias'],
        marker_color=cores,
        marker_line_width=0,
        width=0.5 # Largura da barra (fina e elegante)
    )])
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=10, b=0),
        height=150,
        showlegend=False,
        xaxis=dict(showgrid=False, tickfont=dict(color='#555')),
        yaxis=dict(showgrid=False, visible=False)
    )
    return fig

# ==============================================================================
# 🍩 GRÁFICO DE ANEL (DONUT)
# ==============================================================================
def plot_donut(atual, meta, cor, titulo):
    pct = min(1, atual / meta)
    restante = 1 - pct
    
    fig = go.Figure(data=[go.Pie(
        values=[pct, restante],
        hole=0.85, # Buraco grande (fino)
        marker_colors=[cor, "#2c2c2e"],
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
        # Texto no meio do buraco
        annotations=[dict(
            text=f"<span style='font-size:1.5rem; color:#fff; font-weight:bold'>{int(atual)}</span><br><span style='font-size:0.7rem; color:#666'>{titulo}</span>", 
            x=0.5, y=0.5, showarrow=False
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
        st.markdown("<br><h2 style='text-align:center'>Login GymBot</h2>", unsafe_allow_html=True)
        c1,c2,c3 = st.columns([1,2,1])
        with c2:
            t = st.text_input("ID", placeholder="55...")
            if st.button("ACESSAR", use_container_width=True):
                st.session_state['telefone'] = t
                st.rerun()
        st.stop()

# Carrega Dados
df, nome = get_data(st.session_state['telefone'])

if df is None:
    st.error("Erro no perfil.")
    st.stop()

# Processa Calorias
df['Calorias'] = df.apply(estimar_calorias, axis=1)
hoje = datetime.today()
df_hoje = df[df['Data_Dt'].dt.date == hoje.date()]

# Métricas de Hoje
cals_hoje = df_hoje['Calorias'].sum()
treinos_hoje = len(df_hoje)
# Meta Fake (pode virar real depois)
meta_cal = 600 

# --- HEADER (BOM DIA) ---
c1, c2 = st.columns([3,1])
with c1:
    saudacao = "Bom dia" if hoje.hour < 12 else "Boa tarde" if hoje.hour < 18 else "Boa noite"
    st.markdown(f"## {saudacao}, {nome.split()[0]}!")
    st.markdown("<p>Continue evoluindo hoje 🚀</p>", unsafe_allow_html=True)
with c2:
    if st.button("SAIR"): st.session_state.clear(); st.rerun()

# --- CARD PRINCIPAL: RESUMO DO DIA ---
# Layout em colunas dentro de um container visual
st.markdown(f"<div class='css-card'>", unsafe_allow_html=True)
st.markdown(f"<h3>🔥 Atividade Hoje</h3>", unsafe_allow_html=True)

col_a, col_b, col_c = st.columns(3)

with col_a:
    # Gráfico de Calorias
    fig_cal = plot_donut(cals_hoje, meta_cal, "#FF453A", "Kcal") # Vermelho Apple
    st.plotly_chart(fig_cal, use_container_width=True, config={'staticPlot': True})

with col_b:
    # Gráfico de Passos/Volume (Simulado)
    vol_hoje = df_hoje['Carga'].sum()
    fig_vol = plot_donut(vol_hoje, 10000, ACCENT_COLOR, "Vol") # Verde Neon
    st.plotly_chart(fig_vol, use_container_width=True, config={'staticPlot': True})

with col_c:
    # Gráfico de Foco (Treinos)
    fig_foco = plot_donut(treinos_hoje, 5, "#30D158", "Treinos") # Verde Claro
    st.plotly_chart(fig_foco, use_container_width=True, config={'staticPlot': True})

st.markdown("</div>", unsafe_allow_html=True)

# --- CARD 2: GRÁFICO DE BARRAS "APAGADO" ---
st.markdown(f"<div class='css-card'>", unsafe_allow_html=True)
st.markdown(f"<h3 style='margin-bottom:10px'>📊 Últimos 7 Dias</h3>", unsafe_allow_html=True)

# Filtra últimos 7 dias
data_inicio = hoje - timedelta(days=6)
df_7dias = df[(df['Data_Dt'] >= data_inicio) & (df['Data_Dt'] <= hoje)]

# Plota o gráfico com highlight
fig_barras = plot_barras_destaque(df_7dias)
st.plotly_chart(fig_barras, use_container_width=True, config={'staticPlot': True})

# Texto descritivo em baixo
st.markdown(f"""
<div style="display:flex; justify-content:space-between; margin-top:10px; color:#666; font-size:0.8rem;">
    <span>Média: {int(df_7dias['Calorias'].mean() if not df_7dias.empty else 0)} kcal</span>
    <span>Total: {int(df_7dias['Calorias'].sum())} kcal</span>
</div>
""", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# --- CARD 3: ÚLTIMO TREINO ---
if not df.empty:
    ult_treino = df.iloc[-1]
    st.markdown(f"<div class='css-card'>", unsafe_allow_html=True)
    st.markdown(f"<h3>💪 Último Registro</h3>", unsafe_allow_html=True)
    
    cc1, cc2 = st.columns(2)
    with cc1:
        st.markdown(f"<p style='margin:0'>Exercício</p><h2 style='color:{ACCENT_COLOR}'>{ult_treino['Exercicio']}</h2>", unsafe_allow_html=True)
    with cc2:
        st.markdown(f"<p style='margin:0'>Carga</p><h2>{ult_treino['Carga']} kg</h2>", unsafe_allow_html=True)
        
    st.markdown("</div>", unsafe_allow_html=True)
