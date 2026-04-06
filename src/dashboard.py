import streamlit as st
import boto3
import json
import os
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
import requests
import time

load_dotenv()

st.set_page_config(page_title="Telco Pulse | Monitoramento NOC", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# DESIGN SYSTEM PROFISSIONAL
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        box-sizing: border-box;
    }
    
    /* Paleta de Cores */
    :root {
        --bg-primary: #0f172a;
        --bg-secondary: #1e293b;
        --bg-tertiary: #334155;
        --text-primary: #f8fafc;
        --text-secondary: #cbd5e1;
        --text-muted: #94a3b8;
        --border-color: #1e293b;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --info: #3b82f6;
    }
    
    /* Fundo e Estrutura Base */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif !important;
        background: linear-gradient(135deg, #0f172a 0%, #1a1f35 100%) !important;
        background-attachment: fixed !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #1e293b !important;
        border-right: 1px solid #334155 !important;
    }
    
    /* Header Premium */
    .header-container {
        background: linear-gradient(90deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.95));
        border-bottom: 1px solid rgba(51, 65, 85, 0.3);
        padding: 24px 32px;
        margin: -24px -24px 24px -24px;
        backdrop-filter: blur(10px);
        border-radius: 0 0 12px 12px;
    }
    
    .logo-section {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 8px;
    }
    
    .logo-icon {
        font-size: 28px;
        font-weight: 700;
        color: #60a5fa;
    }
    
    .titulo-dashboard {
        font-size: 28px !important;
        font-weight: 700 !important;
        color: #f8fafc !important;
        margin: 0 !important;
        padding: 0 !important;
        letter-spacing: -0.5px;
    }
    
    .subtitulo-dashboard {
        font-size: 13px !important;
        color: #94a3b8 !important;
        margin-top: 4px !important;
        margin-bottom: 0 !important;
        font-weight: 400 !important;
    }
    
    /* Status Badge Elegante (sem emojis) */
    .status-badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin: 8px 0;
    }
    
    .status-operational {
        background-color: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    .status-degraded {
        background-color: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    
    .status-unavailable {
        background-color: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    /* Cards Premium */
    .operative-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.6));
        border: 1px solid rgba(51, 65, 85, 0.5);
        border-radius: 12px;
        padding: 20px;
        backdrop-filter: blur(10px);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.05);
    }
    
    .operative-card:hover {
        border-color: rgba(96, 165, 250, 0.4);
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.05);
        transform: translateY(-2px);
    }
    
    /* KPI Cards */
    .kpi-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.9), rgba(20, 28, 45, 0.8));
        border: 1px solid rgba(51, 65, 85, 0.5);
        border-left: 3px solid #60a5fa;
        border-radius: 10px;
        padding: 16px;
        transition: all 0.3s ease;
    }
    
    .kpi-label {
        color: #94a3b8;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }
    
    .kpi-value {
        color: #f8fafc;
        font-size: 28px;
        font-weight: 700;
        line-height: 1;
    }
    
    .kpi-change {
        color: #94a3b8;
        font-size: 11px;
        margin-top: 8px;
        font-weight: 500;
    }
    
    /* Operadora Titles */
    .operadora-title {
        font-size: 18px !important;
        font-weight: 700 !important;
        margin-bottom: 4px !important;
        margin-top: 0 !important;
    }
    
    /* Métricas Refinadas */
    div[data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    
    div[data-testid="stMetricValue"] {
        color: #f8fafc !important;
        font-size: 26px !important;
        font-weight: 700 !important;
    }
    
    /* Botões Refined */
    .stButton > button {
        background: linear-gradient(135deg, #1e293b, #0f172a) !important;
        color: #e2e8f0 !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        padding: 10px 16px !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #334155, #1e293b) !important;
        border-color: #60a5fa !important;
        color: #60a5fa !important;
        box-shadow: 0 0 20px rgba(96, 165, 250, 0.2) !important;
    }
    
    /* Dividers Elegantes */
    .elegant-divider {
        margin: 24px 0 !important;
        border: 0 !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, rgba(51, 65, 85, 0.5), transparent) !important;
    }
    
    /* Section Titles */
    .section-title {
        color: #f8fafc !important;
        font-size: 20px !important;
        font-weight: 700 !important;
        margin-top: 32px !important;
        margin-bottom: 20px !important;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .section-icon {
        color: #60a5fa;
        font-size: 22px;
    }
    
    /* Selectbox Refined */
    [data-testid="stSelectbox"] div[data-baseweb="select"] {
        background-color: #1e293b !important;
        border-color: #334155 !important;
    }
    
    /* Expander Refined */
    [data-testid="stExpander"] button {
        background: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }
    
    [data-testid="stExpander"] summary {
        color: #e2e8f0 !important;
        font-weight: 600 !important;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    
    /* DataTable Styling */
    [data-testid="stDataFrame"] {
        background-color: transparent !important;
    }
    
    .dataframe-container {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.5), rgba(20, 28, 45, 0.4));
        border: 1px solid rgba(51, 65, 85, 0.3);
        border-radius: 8px;
        padding: 16px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# HEADER PREMIUM
# ==========================================
st.markdown('''<div class="header-container">
    <div class="logo-section">
        <span class="logo-icon">■</span>
        <div>
            <p class="titulo-dashboard">Telco Pulse</p>
            <p class="subtitulo-dashboard">NOC Dashboard • Monitoramento de Infraestrutura em Tempo Real</p>
        </div>
    </div>
</div>''', unsafe_allow_html=True)

@st.cache_data(ttl=60)
def buscar_ultimo_dado_s3():
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION')
        )
        bucket = os.getenv('S3_BUCKET_NAME')
        objetos = s3.list_objects_v2(Bucket=bucket, Prefix='raw/')
        
        if 'Contents' in objetos:
            arquivos_ordenados = sorted(objetos['Contents'], key=lambda x: x['LastModified'], reverse=True)
            ultimo_arquivo = arquivos_ordenados[0]['Key']
            resposta = s3.get_object(Bucket=bucket, Key=ultimo_arquivo)
            return json.loads(resposta['Body'].read().decode('utf-8')), ultimo_arquivo
        return None, None
    except Exception:
        return None, None

def disparar_robo_github():
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPO")
    url = f"https://api.github.com/repos/{repo}/actions/workflows/coleta_telco.yml/dispatches"
    headers = {"Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}", "X-GitHub-Api-Version": "2022-11-28"}
    resposta = requests.post(url, headers=headers, json={"ref": "main"})
    return resposta.status_code == 204

def gerar_status_badge(erro, latencia, maior_incidente):
    """Gera status badge sem emojis, baseado em métricas"""
    if erro != "Nenhum" or latencia > 1000 or maior_incidente > 70:
        return "INDISPONÍVEL", "status-unavailable"
    elif latencia > 350 or maior_incidente > 40:
        return "DEGRADADO", "status-degraded"
    else:
        return "OPERACIONAL", "status-operational"

# Carrega dados
dados, nome_arquivo = buscar_ultimo_dado_s3()

if dados:
    dt_utc = datetime.fromisoformat(dados['timestamp'])
    dt_formatada = (dt_utc - timedelta(hours=3)).strftime('%H:%M:%S')
    dt_data = (dt_utc - timedelta(hours=3)).strftime('%d de %B de %Y')
    
    # ==========================================
    # STATUS BAR SUPERIOR
    # ==========================================
    col_info, col_refresh, col_manual = st.columns([2, 1, 1])
    
    with col_info:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, rgba(30, 41, 59, 0.6), rgba(20, 28, 45, 0.5)); 
                    border: 1px solid rgba(51, 65, 85, 0.3); border-radius: 8px; padding: 12px 16px; margin-bottom: 16px;'>
            <span style='color: #94a3b8; font-size: 12px; font-weight: 600; text-transform: uppercase;'>Última Coleta Confirmada</span><br>
            <span style='color: #f8fafc; font-size: 14px; font-weight: 600;'>{dt_formatada} BRT</span><br>
            <span style='color: #60a5fa; font-size: 11px;'>Fonte: AWS S3 • {nome_arquivo[-12:]}</span>
        </div>
        """, unsafe_allow_html=True)
    
    # Inicializa o cronômetro zerado na memória do Streamlit
    if 'ultimo_clique' not in st.session_state:
        st.session_state.ultimo_clique = 0
        
    agora = time.time()
    tempo_restante = 60 - (agora - st.session_state.ultimo_clique)
    pode_clicar = tempo_restante <= 0

    with col_refresh:
        if st.button("Atualizar", use_container_width=True, key="btn_refresh"):
            st.cache_data.clear()
            st.rerun()
    
    with col_manual:
        # Se já passou 1 minuto, mostra o botão normal
        if pode_clicar:
            if st.button("Coleta Manual", use_container_width=True, key="btn_manual"):
                with st.spinner("Ativando sensor em São Paulo..."):
                    if disparar_robo_github():
                        # Registra o momento exato do clique
                        st.session_state.ultimo_clique = time.time() 
                        st.toast('Processo ativado no GitHub Actions!')
                        st.info(" Comando enviado! O robô leva cerca de 10 minutos para rodar. Volte e clique em 'Atualizar' em breve.")
                    else:
                        st.error('Falha na comunicação com a API do GitHub.')
        # Se não passou 1 minuto, mostra o botão bloqueado com a contagem regressiva
        else:
            st.button(f"Aguarde ({int(tempo_restante)}s)", use_container_width=True, key="btn_manual_disabled", disabled=True)
            
    st.markdown('<div class="elegant-divider"></div>', unsafe_allow_html=True)
    # ==========================================
    # SELETOR DE REGIÃO
    # ==========================================
    lista_regioes = ['Nacional', 'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']
    col_sel, col_empty = st.columns([2, 5])
    with col_sel:
        regiao_selecionada = st.selectbox("Análise por Região", lista_regioes, index=0, help="Selecione a região para filtrar alertas do Google Trends")
    
    # ==========================================
    # KPI CARDS (LINHA DE RESUMO)
    # ==========================================
    st.markdown('<div class="section-title"><span class="section-icon">─</span>Indicadores-Chave de Performance</div>', unsafe_allow_html=True)
    
    # Calcula KPIs
    total_operadoras_down = sum(1 for item in dados['telemetria'] if item['erro_tecnico'] != "Nenhum" or item['latencia_ms'] > 1000)
    media_latencia = sum(item['latencia_ms'] for item in dados['telemetria']) / len(dados['telemetria'])
    alertas_totais = sum(max(item['indices_sociais'].values()) for item in dados['telemetria'])
    
    kpi_cols = st.columns(4)
    
    with kpi_cols[0]:
        st.markdown(f'''
        <div class="kpi-card">
            <div class="kpi-label">Status Geral</div>
            <div class="kpi-value" style="color: #10b981;">{4 - total_operadoras_down}/4</div>
            <div class="kpi-change">Operadoras Operacionais</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with kpi_cols[1]:
        st.markdown(f'''
        <div class="kpi-card" style="border-left-color: #f59e0b;">
            <div class="kpi-label">Latência Média</div>
            <div class="kpi-value" style="color: #f59e0b;">{media_latencia:.0f}</div>
            <div class="kpi-change">Milissegundos · TCP 443</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with kpi_cols[2]:
        st.markdown(f'''
        <div class="kpi-card" style="border-left-color: #ef4444;">
            <div class="kpi-label">Alertas Críticos</div>
            <div class="kpi-value" style="color: #ef4444;">{alertas_totais:.0f}</div>
            <div class="kpi-change">Volume Google Trends</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with kpi_cols[3]:
        from datetime import timezone
        
        # 1. Pega a hora do arquivo
        dt_coleta = datetime.fromisoformat(dados['timestamp'])
        
        # Garante que a data do arquivo seja tratada como UTC (padrão da nuvem)
        if dt_coleta.tzinfo is None:
            dt_coleta = dt_coleta.replace(tzinfo=timezone.utc)
            
        # Pega a hora exata de agora também em UTC (funciona no Streamlit e no seu Linux)
        agora = datetime.now(timezone.utc)
        
        # Calcula a diferença absoluta
        tempo_atras = agora - dt_coleta
        minutos_totais = int(tempo_atras.total_seconds() / 60)
        
        # Prevenção contra bugs de fuso (evita números negativos)
        minutos_totais = max(0, minutos_totais)
        
        # 2. Formata para o visual humano (UX)
        horas, minutos = divmod(minutos_totais, 60)
        
        if horas > 0:
            tempo_texto = f"{horas}h {minutos}m"
            sub_texto = "Atrás · Coleta Automática"
        else:
            tempo_texto = f"{minutos}"
            sub_texto = "Minutos Atrás · Coleta Automática"

        st.markdown(f'''
        <div class="kpi-card" style="border-left-color: #3b82f6;">
            <div class="kpi-label">Tempo dos Dados</div>
            <div class="kpi-value" style="color: #3b82f6;">{tempo_texto}</div>
            <div class="kpi-change">{sub_texto}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown('<div class="elegant-divider"></div>', unsafe_allow_html=True)
    
    # ==========================================
    # CARDS DAS OPERADORAS (REDESENHADO)
    # ==========================================
    st.markdown('<div class="section-title"><span class="section-icon">◉</span>Status das Operadoras</div>', unsafe_allow_html=True)
    
    colunas = st.columns(4)
    df_view = []
    
    # Paleta de cores premium das marcas
    cores_marcas = {"Vivo": "#a855f7", "Claro": "#ef4444", "TIM": "#3b82f6", "Oi": "#eab308"}
    
    for index, item in enumerate(dados['telemetria']):
        operadora = item['operadora']
        latencia = item['latencia_ms']
        erro = item['erro_tecnico']
        status_http = item.get('status_http', 200)
        indice = item['indices_sociais'].get(regiao_selecionada, 0)
        cor_marca = cores_marcas.get(operadora, "#f8fafc")
        maior_incidente = max(item['indices_sociais'].values())
        
        df_view.append({
            "Operadora": operadora,
            "Ping (ms)": latencia,
            "Retorno": status_http,
            "Diagnóstico": erro,
            f"Alertas ({regiao_selecionada})": indice
        })
        
        with colunas[index]:
            status_text, status_class = gerar_status_badge(erro, latencia, maior_incidente)
            
            st.markdown(f'''
            <div class="operative-card">
                <h3 class="operadora-title" style="color: {cor_marca};">{operadora}</h3>
                <div class="status-badge {status_class}">{status_text}</div>
            </div>
            ''', unsafe_allow_html=True)
            
            # Métricas em colunas
            met_col1, met_col2 = st.columns(2)
            with met_col1:
                st.metric("Ping", f"{latencia}ms")
            with met_col2:
                st.metric("Alertas", f"{indice:.1f}")
            
            # Status HTTP
            if erro == "Nenhum":
                st.markdown(f'<p style="color: #10b981; font-family: monospace; font-size: 12px; margin: 8px 0;">HTTP {status_http} OK</p>', unsafe_allow_html=True)
            else:
                st.markdown(f'<p style="color: #ef4444; font-family: monospace; font-size: 12px; margin: 8px 0;">{erro}</p>', unsafe_allow_html=True)
    
    st.markdown('<div class="elegant-divider"></div>', unsafe_allow_html=True)
    
    # ==========================================
    # ANÁLISE ANALÍTICA - SEÇÃO GRÁFICOS
    # ==========================================
    st.markdown('<div class="section-title"><span class="section-icon">▦</span>Análise Analítica de Incidentes</div>', unsafe_allow_html=True)
    
    # Preparação de dados
    estado_totais = {}
    operadora_totais = {}
    
    for item in dados['telemetria']:
        op = item['operadora']
        sociais = item['indices_sociais']
        operadora_totais[op] = sociais.get(regiao_selecionada, 0)
        
        for estado, valor in sociais.items():
            if estado != 'Nacional':
                # CORREÇÃO: Pegamos o Maior Risco (max) em vez de somar.
                # Isso trava o gráfico na escala real do Google (0 a 100) e elimina distorções noturnas.
                atual = estado_totais.get(estado, 0)
                estado_totais[estado] = max(atual, valor)
    
    # Top 5 Estados
    top5_estados = sorted(estado_totais.items(), key=lambda x: x[1], reverse=True)[:5]
    df_top5 = pd.DataFrame(top5_estados, columns=['Estado', 'Volume'])
    df_top5['Volume'] = df_top5['Volume'].round(1)
    
    def definir_risco(volume):
        if volume > 60: return 'ALTO RISCO'
        elif volume > 40: return 'MÉDIO RISCO'
        else: return 'BAIXO RISCO'
    df_top5['Risco'] = df_top5['Volume'].apply(definir_risco)
    
    # Operadoras
    df_ops = pd.DataFrame(list(operadora_totais.items()), columns=['Operadora', 'Volume'])
    total_volume_regiao = df_ops['Volume'].sum()
    if total_volume_regiao > 0:
        df_ops['Percentual'] = (df_ops['Volume'] / total_volume_regiao * 100).round(1).astype(str) + '%'
    else:
        df_ops['Percentual'] = '0.0%'
    df_ops['VolumeLimp'] = df_ops['Volume'].round(0).astype(int)
    
    # Gráficos
    col_graf1, col_graf2 = st.columns(2)
    
    mapa_cores_risco = {'ALTO RISCO': '#ef4444', 'MÉDIO RISCO': '#f59e0b', 'BAIXO RISCO': '#10b981'}
    
    with col_graf1:
        max_valor = df_top5['Volume'].max() if not df_top5.empty else 0
        titulo_grafico = "Top 5 Estados Críticos" if max_valor >= 40 else "Nenhum Estado em Crise (Ruído Padrão)"

        fig_bar = px.bar(
            df_top5, x='Estado', y='Volume',
            text_auto=True,
            color='Risco',
            color_discrete_map=mapa_cores_risco,
            title=titulo_grafico
        )
        fig_bar.update_traces(textposition='outside', cliponaxis=False)
        fig_bar.update_layout(
            title=dict(text=titulo_grafico, font=dict(size=15, color='#e2e8f0'), x=0),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, title='', tickfont=dict(color='#94a3b8')),
            yaxis=dict(showgrid=True, gridcolor='rgba(51, 65, 85, 0.2)', title='', showticklabels=False, range=[0, 100]),
            margin=dict(l=0, r=0, t=40, b=0),
            hovermode=False,
            showlegend=False,
            font=dict(color='#e2e8f0', family='Inter')
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
    
    with col_graf2:
        fig_donut = px.pie(
            df_ops, values='Volume', names='Operadora',
            hole=0.6,
            color='Operadora', color_discrete_map=cores_marcas,
            custom_data=['Percentual']
        )
        fig_donut.update_traces(
            textposition='inside',
            textinfo='percent',
            hovertemplate="<b>%{label}</b><br>Participação: %{customdata[0]}<extra></extra>",
            marker=dict(line=dict(color='rgba(15, 23, 42, 0.95)', width=2))
        )
        fig_donut.update_layout(
            title=dict(text=f"Distribuição por Operadora ({regiao_selecionada})", font=dict(size=16, color='#e2e8f0'), x=0),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, font=dict(color='#e2e8f0')),
            margin=dict(l=0, r=0, t=40, b=50),
            font=dict(color='#e2e8f0', family='Inter')
        )
        st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})
    
    st.markdown('<div class="elegant-divider"></div>', unsafe_allow_html=True)
    
    # ==========================================
    # DETALHES E TABELA DE DADOS
    # ==========================================
    st.markdown('<div class="section-title"><span class="section-icon">◈</span>Dashboard de Dados</div>', unsafe_allow_html=True)
    
    with st.expander("Visualizar Matriz de Dados Brutos (S3)", expanded=False):
        st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
        df_view_limpo = pd.DataFrame(df_view).head(4)
        st.dataframe(
            df_view_limpo.style.format({
                "Ping (ms)": "{:.0f}",
                f"Alertas ({regiao_selecionada})": "{:.1f}"
            }),
            use_container_width=True,
            hide_index=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ==========================================
    # DOCUMENTAÇÃO
    # ==========================================
    with st.expander("Sobre as Métricas", expanded=False):
        st.markdown("""
        ### Componentes do Dashboard
        
        **Telemetria Técnica (TCP Ping)**
        - Testa conectividade direta com servidores centrais das operadoras (Porta 443)
        - Latência > 1000ms indica possível falha de backbone
        - Retorno HTTP confirma conclusão do handshake
        
        **Inteligência Social (Google Trends)**
        - Monitora volume de buscas por termos de falha (ex: "Vivo caiu", "Claro sem sinal")
        - Detecta problemas em 4G/5G mesmo quando backbone está OK
        - Valores elevados confirmam experiência negativa do usuário final
        
        **Categorias de Risco**
        - **ALTO RISCO** (>60): Apagão confirmado em múltiplas regiões
        - **MÉDIO RISCO** (40-60): Degradação de serviço detectada
        - **BAIXO RISCO** (<40): Operação normal ou problemas isolados
        """)
    
    st.markdown('<div class="elegant-divider"></div>', unsafe_allow_html=True)

else:
    st.error("⚠ Erro ao Carregar Dados")