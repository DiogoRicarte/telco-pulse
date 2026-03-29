import streamlit as st
import boto3
import json
import os
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time
import requests

load_dotenv()

st.set_page_config(page_title="Telco Pulse | Dashboard", layout="wide")

st.markdown("""
    <style>
    .titulo-dashboard { font-size: 32px !important; font-weight: 700 !important; color: #1E3A8A; margin-bottom: 0px; padding-bottom: 0px; }
    .subtitulo-dashboard { font-size: 16px !important; color: #6B7280; margin-top: 5px; margin-bottom: 30px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="titulo-dashboard">Painel de Telemetria: Telco Pulse</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitulo-dashboard">Monitoramento contínuo de latência e disponibilidade de redes nacionais.</p>', unsafe_allow_html=True)

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
            conteudo_json = json.loads(resposta['Body'].read().decode('utf-8'))
            return conteudo_json, ultimo_arquivo
        return None, None
    except Exception as e:
        return None, None

def disparar_robo_github():
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPO")
    url = f"https://api.github.com/repos/{repo}/actions/workflows/coleta_automatica.yml/dispatches"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    data = {"ref": "main"} 
    resposta = requests.post(url, headers=headers, json=data)
    return resposta.status_code == 204

dados, nome_arquivo = buscar_ultimo_dado_s3()

if dados:
    dt_utc = datetime.fromisoformat(dados['timestamp'])
    dt_brasilia = dt_utc - timedelta(hours=3)
    dt_formatada = dt_brasilia.strftime('%d/%m/%Y às %H:%M:%S')

    # Controles Superiores
    col_status, col_espaco, col_btn_s3, col_btn_github = st.columns([4, 1, 2, 2])
    with col_status:
        st.markdown(f"**Última leitura registrada:** {dt_formatada} (Horário de Brasília)")
    with col_btn_s3:
        if st.button("🔄 Atualizar Tela", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with col_btn_github:
        if st.button("🚀 Forçar Nova Coleta", use_container_width=True):
            with st.spinner("Acordando robô no GitHub..."):
                sucesso = disparar_robo_github()
                if sucesso:
                    st.success("✅ Ordem enviada! O robô leva cerca de 6 minutos para varrer o Brasil. Aguarde para atualizar.")
                else:
                    st.error("❌ Falha ao contatar o GitHub. Verifique o GITHUB_TOKEN no .env")

    st.markdown("---")
    
    # SELETOR DE ESTADO
    lista_regioes = ['Nacional', 'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']
    regiao_selecionada = st.selectbox("📍 Selecione a Região para Análise de Falhas (Google Trends):", lista_regioes, index=0)
    
    st.markdown("---")
    
    colunas = st.columns(4)
    
    # Preparando os dados para os cards e para a tabela de forma limpa
    df_view = []
    
    for index, item in enumerate(dados['telemetria']):
        operadora = item['operadora']
        latencia = item['latencia_ms']
        erro = item['erro_tecnico']
        
        # Pega o índice apenas do estado que o usuário escolheu na caixinha
        indice = item['indices_sociais'].get(regiao_selecionada, 0)
        
        # Salva na lista para mostrar na tabela lá embaixo
        df_view.append({
            "Operadora": operadora,
            "Latência (ms)": latencia,
            "Status HTTP": item["status_http"],
            f"Buscas ({regiao_selecionada})": indice,
            "Erro Técnico": erro
        })
        
        # Desenha os Cards
        with colunas[index]:
            if erro != "Nenhum" and erro != "HTTP 403" or latencia > 2000:
                status_cor = "🔴 FALHA"
            elif latencia > 500:
                status_cor = "🟡 INSTÁVEL"
            else:
                status_cor = "🟢 OPERACIONAL"

            st.markdown(f"### {operadora}")
            st.markdown(f"**Status:** {status_cor}")
            
            col_metrica1, col_metrica2 = st.columns(2)
            with col_metrica1:
                st.metric(label="Latência", value=f"{latencia} ms")
            with col_metrica2:
                # O label da métrica muda dinamicamente dependendo do estado escolhido!
                st.metric(label=f"Alertas ({regiao_selecionada})", value=indice)
            
            st.write("") 

    st.markdown("---")
    
    with st.expander("Visualizar Tabela de Dados Consolidados"):
        st.dataframe(pd.DataFrame(df_view), use_container_width=True)
        st.caption(f"Fonte de dados: s3://{os.getenv('S3_BUCKET_NAME')}/{nome_arquivo}")

else:
    st.error("Não foi possível carregar os dados. Verifique a conexão com a AWS.")