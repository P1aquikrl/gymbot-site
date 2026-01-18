import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

# ==============================================================================
# ⚙️ CONFIGURAÇÃO E ESTILO
# ==============================================================================
st.set_page_config(page_title="GymBot Performance", page_icon="⚡", layout="wide")

NEON_GREEN = "#00ff88"
DARK_BG = "#000000"
CARD_BG = "#121212"

st.markdown(f"""
<style>
    .stApp {{ background-color: {DARK_BG}; color: #ffffff; }}
    header[data-testid="stHeader"] {{ background-color: rgba(0,0,0,0); }}
    .block-container {{ padding-top: 1rem; padding-bottom: 5rem; }}
    
    /* CARDS */
    .css-card {{
        background-color: {CARD_BG};
        border-radius: 16px;
        padding: 15px;
        border: 1px solid #222;
        box-shadow: 0 4px 15px rgba(0, 255, 136, 0.05); 
        margin-bottom: 15px;
        text-align: center;
    }}
    
    /* FONTE */
    h1, h2, h3, h4, h5 {{ font-family: 'Inter', sans-serif; font-weight: 700; color: white !important; }}
    
    .highlight-text {{ color: {NEON_GREEN}; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; }}
    .big-metric {{ font-family: 'Inter', sans-serif; font-size: 2.5rem; font-weight: 800; color: #fff; line-height: 1; }}
    .metric-label {{ font-size: 0.75rem; color: #888; text-transform: uppercase; font-weight: 600; letter-spacing: 1px; margin-bottom: 5px; }}

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
        nome_real = "Atleta"
        try:
            ws_users = sh.worksheet("Usuarios")
            cell = ws_users.find(str(telefone))
            if cell: nome_real = ws_users.cell(cell.row, 2).value
        except: pass

        ws_treino = sh.worksheet(str(telefone))
        data = ws_treino.get_all_records()
        df = pd.DataFrame(data)
        
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
        df = df.dropna(subset=['Data_Dt']).sort_values(by='Data_Dt')
        
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
# 📊 GRÁFICOS INTERATIVOS
# ==============================================================================
def plot_barras_interativo(df_semana, selecionado=None):
    df_semana = df_semana.sort_values(by='Data_Dt')
    df_semana['Dia_Str'] = df_semana['Data_Dt'].dt.strftime('%d/%m')
    
    dados = df_semana.groupby('Dia_Str', sort=False)['Calorias'].sum().reset_index()
    
    # --- LÓGICA DE SELEÇÃO ---
    # Se ninguém foi clicado, o último (hoje) fica aceso
    # Se alguém foi clicado, SÓ ele fica aceso
    
    cores = []
    for dia in dados['Dia_Str']:
        if selecionado:
            if dia == selecionado:
                cores.append(NEON_GREEN) # Aceso
            else:
                cores.append('rgba(0, 255, 136, 0.15)') # Apagado (Glass)
        else:
            # Comportamento padrão (Último aceso)
            if dia == dados['Dia_Str'].iloc[-1]:
                cores.append(NEON_GREEN)
            else:
                cores.append('rgba(0, 255, 136, 0.15)')

    fig = go.Figure(data=[go.Bar(
        x=dados['Dia_Str'],
        y=dados['Calorias'],
        marker=dict(
            color=cores,
            cornerradius=10 # <--- AQUI ESTÁ O ARREDONDAMENTO DAS BARRAS
        ),
        text=dados['Calorias'].astype(int),
        textposition='outside',
        textfont=dict(color='#ccc', family="Inter, sans-serif", size=12),
        hovertemplate='%{y} kcal<extra></extra>'
    )])
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=30, b=0),
        height=200,
        showlegend=False,
        xaxis=dict(showgrid=False, tickfont=dict(color='#888', family="Inter, sans-serif"), fixedrange=True),
        yaxis=dict(showgrid=False, visible=False, fixedrange=True),
        bargap=0.35,
        clickmode='event+select' # Habilita o clique
    )
    return fig

def plot_donut_neon(valor, meta, cor, label):
    pct = min(1, valor / meta) if meta > 0 else 0
    fig = go.Figure(data=[go.Pie(
        values=[pct, 1-pct],
        hole=0.85,
        marker_colors=[cor, "#1c1c1c"], 
        textinfo='none', 
        hoverinfo='none', 
        sort=False, 
        direction='clockwise'
    )])
    fig.update_layout(
        showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=120,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        annotations=[dict(text=f"<span style='font-family:Inter, sans-serif; font-size:1.4rem; color:#fff; font-weight:800'>{int(valor)}</span>", x=0.5, y=0.55, showarrow=False),
                     dict(text=f"<span style='font-family:Inter, sans-serif; font-size:0.7rem; color:#888; font-weight:700'>{label}</span>", x=0.5, y=0.35, showarrow=False)]
    )
    return fig

# ==============================================================================
# 📱 APP PRINCIPAL
# ==============================================================================
query_params = st.query_params
usuario_url = query_params.get("id", None)

if usuario_url and 'telefone' not in st.session_state:
    st.session_state['telefone'] = usuario_url

if 'telefone' not in st.session_state:
    st.markdown("<br><h1 style='text-align: center;'>⚡ GYMBOT</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        telefone_input = st.text_input("ID de Acesso", placeholder="Seu número...")
        if st.button("ACESSAR", use_container_width=True):
            st.session_state['telefone'] = telefone_input
            st.rerun()
    st.stop()

# Carregar Dados
df, nome = get_data(st.session_state['telefone'])

if df is None:
    st.error("⚠️ Perfil não encontrado.")
    st.stop()

# Cálculos
df['Calorias'] = df.apply(estimar_calorias, axis=1)
hoje = datetime.today()
df_hoje = df[df['Data_Dt'].dt.date == hoje.date()]

cals_hoje = df_hoje['Calorias'].sum()
treinos_hoje = len(df_hoje)
volume_hoje = df_hoje['Carga'].sum()

# HEADER
c_perfil, c_btn = st.columns([8,1])
with c_perfil:
    st.markdown(f"### Olá, <span class='highlight-text'>{nome.split()[0].upper()}</span>.", unsafe_allow_html=True)
with c_btn:
    if st.button("SAIR"):
        st.session_state.clear(); st.query_params.clear(); st.rerun()

st.markdown("---")

# 1. DONUTS
st.markdown(f"<div class='css-card'><h3>🔥 Hoje</h3>", unsafe_allow_html=True)
k1, k2, k3 = st.columns(3)
with k1: st.plotly_chart(plot_donut_neon(cals_hoje, 600, "#FF3B30", "KCAL"), use_container_width=True, config={'displayModeBar': False})
with k2: st.plotly_chart(plot_donut_neon(treinos_hoje, 5, NEON_GREEN, "TREINOS"), use_container_width=True, config={'displayModeBar': False})
with k3: st.plotly_chart(plot_donut_neon(volume_hoje, 10000, "#8A2BE2", "VOL KG"), use_container_width=True, config={'displayModeBar': False})
st.markdown("</div>", unsafe_allow_html=True)

# 2. BARRAS INTERATIVAS (CLIQUE PARA ACENDER)
st.markdown(f"<div class='css-card'><h3>📅 Gasto Calórico (7 Dias)</h3>", unsafe_allow_html=True)
datas_unicas = df['Data_Dt'].drop_duplicates().sort_values(ascending=False).head(7)

if not datas_unicas.empty:
    min_date = datas_unicas.min()
    df_sem = df[df['Data_Dt'] >= min_date]
    
    # Verifica se já tem algo selecionado na sessão
    selection = st.session_state.get("bar_selection", None)
    dia_selecionado = None
    
    # Se houver seleção, pega o X (Data)
    if selection and selection.get("selection") and selection["selection"]["points"]:
        dia_selecionado = selection["selection"]["points"][0]["x"]
        
        # Mostra detalhes do dia clicado
        cals_dia = df_sem[df_sem['Data_Dt'].dt.strftime('%d/%m') == dia_selecionado]['Calorias'].sum()
        st.caption(f"Selecionado: {dia_selecionado} — {int(cals_dia)} kcal")

    # Plota o gráfico com a lógica de seleção
    fig_barras = plot_barras_interativo(df_sem, selecionado=dia_selecionado)
    
    # on_select="rerun" faz o site recarregar quando você clica, atualizando as cores
    st.plotly_chart(fig_barras, use_container_width=True, on_select="rerun", key="bar_selection", config={'displayModeBar': False})
else:
    st.info("Sem dados recentes.")
st.markdown("</div>", unsafe_allow_html=True)

# 3. EVOLUÇÃO
st.markdown(f"<div class='css-card'><h3>📈 Evolução por Exercício</h3>", unsafe_allow_html=True)
exercicios = df['Exercicio'].unique()
escolha = st.selectbox("", exercicios, label_visibility="collapsed")

if escolha:
    df_filt = df[df['Exercicio'] == escolha].sort_values(by='Data_Dt')
    ult_carga = df_filt['Carga'].iloc[-1]
    max_carga = df_filt['Carga'].max()
    
    eh_cardio = any(x in escolha.lower() for x in ['esteira', 'corrida', 'bike', 'eliptico', 'cardio'])
    unidade = "min" if eh_cardio else "kg"
    
    m1, m2 = st.columns(2)
    m1.markdown(f"<div class='metric-label'>Último</div><div class='big-metric'>{int(ult_carga)}<span style='font-size:1rem'>{unidade}</span></div>", unsafe_allow_html=True)
    m2.markdown(f"<div class='metric-label'>Recorde</div><div class='big-metric' style='color:{NEON_GREEN}'>{int(max_carga)}<span style='font-size:1rem'>{unidade}</span></div>", unsafe_allow_html=True)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_filt['Data_Dt'], 
        y=df_filt['Carga'],
        mode='lines+markers',
        line=dict(color=NEON_GREEN, width=3, shape='spline'),
        marker=dict(size=6, color=CARD_BG, line=dict(color=NEON_GREEN, width=2)),
        hovertemplate=f'%{{y}} {unidade}<extra></extra>',
        fill='tozeroy',
        fillcolor='rgba(0, 255, 136, 0.05)'
    ))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(showgrid=False, showline=True, linecolor='#333', fixedrange=True, tickformat="%d/%m"),
        yaxis=dict(showgrid=True, gridcolor='#222', zeroline=False, fixedrange=True),
        height=220
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

st.markdown("</div>", unsafe_allow_html=True)
