import time
import pandas as pd
import requests
import json
from datetime import datetime
from pytrends.request import TrendReq
import os
import boto3
from dotenv import load_dotenv

# Carrega as chaves secretas do arquivo .env
load_dotenv()

# ==========================================
# SENSOR 1: SOCIAL (Google Trends)
# ==========================================
pytrends = TrendReq(hl='pt-BR', tz=180, retries=3, backoff_factor=0.5)

def coletar_trends_nacional():
    print("\n[SENSOR SOCIAL] Iniciando coleta Nacional...")
    termos_busca = {
        "Vivo": ["Vivo fora do ar", "Vivo caiu", "Vivo sem sinal", "Vivo internet ruim"],
        "Claro": ["Claro fora do ar", "Claro caiu", "Claro sem sinal", "Claro net caiu"],
        "TIM": ["TIM fora do ar", "TIM caiu", "TIM sem sinal", "TIM internet ruim"],
        "Oi": ["Oi fora do ar", "Oi caiu", "Oi sem sinal", "Oi fibra fora"]
    }
    
    df_final = pd.DataFrame()
    for operadora, keywords in termos_busca.items():
        try:
            pytrends.build_payload(keywords, cat=0, timeframe='now 4-H', geo='BR')
            df_temp = pytrends.interest_over_time()
            if not df_temp.empty:
                df_temp = df_temp.drop(columns=['isPartial'])
                df_final[f'Indice_Falha_{operadora}'] = df_temp.sum(axis=1)
            time.sleep(3)
        except Exception as e:
            print(f"Erro ao consultar {operadora}: {e}")
            
    return df_final

# ==========================================
# SENSOR 2: TÉCNICO (Latência e Status HTTP)
# ==========================================
def coletar_latencia_tecnica():
    print("\n[SENSOR TÉCNICO] Iniciando Teste de Latência (Ping)...")
    urls_operadoras = {
        "Vivo": "https://www.vivo.com.br",
        "Claro": "https://www.claro.com.br",
        "TIM": "https://www.tim.com.br",
        "Oi": "https://www.oi.com.br"
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    resultados = []
    for operadora, url in urls_operadoras.items():
        try:
            resposta = requests.get(url, headers=headers, timeout=5)
            tempo_ms = round(resposta.elapsed.total_seconds() * 1000)
            status = resposta.status_code
            resultados.append({
                "Operadora": operadora,
                "Status_HTTP": status,
                "Latencia_ms": tempo_ms,
                "Erro": "Nenhum" if status == 200 else f"HTTP {status}"
            })
        except requests.exceptions.RequestException as e:
            resultados.append({
                "Operadora": operadora,
                "Status_HTTP": 0,
                "Latencia_ms": 5000,
                "Erro": "Timeout/Inacessivel"
            })
    return resultados

# ==========================================
# INTEGRAÇÃO E PERSISTÊNCIA (Local e Nuvem)
# ==========================================
def salvar_e_enviar_dados(dados_tecnicos, df_sociais):
    print("\n[PERSISTÊNCIA] Gerando arquivo JSON unificado...")
    os.makedirs('dados', exist_ok=True)
    
    ultima_linha_social = df_sociais.iloc[-1] if not df_sociais.empty else None
    
    payload = {
        "timestamp": datetime.now().isoformat(),
        "telemetria": []
    }
    
    for item in dados_tecnicos:
        op = item["Operadora"]
        indice_social = int(ultima_linha_social[f'Indice_Falha_{op}']) if ultima_linha_social is not None else 0
        
        payload["telemetria"].append({
            "operadora": op,
            "status_http": item["Status_HTTP"],
            "latencia_ms": item["Latencia_ms"],
            "indice_social_falha": indice_social,
            "erro_tecnico": item["Erro"]
        })
        
    nome_arquivo = f"telemetria_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    caminho_local = f"dados/{nome_arquivo}"
    
    with open(caminho_local, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=4)
    print(f"✅ Salvo localmente em: {caminho_local}")
    
    # --- NOVO: ENVIO PARA O AWS S3 ---
    print("\n[CLOUD] Iniciando upload para o Amazon S3...")
    try:
        # Puxa as credenciais do .env invisível
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION')
        )
        
        bucket_name = os.getenv('S3_BUCKET_NAME')
        caminho_s3 = f"raw/{nome_arquivo}" # Vai criar uma pasta 'raw' dentro do bucket
        
        s3_client.upload_file(caminho_local, bucket_name, caminho_s3)
        print(f"🚀 SUCESSO! Arquivo enviado para s3://{bucket_name}/{caminho_s3}")
        
    except Exception as e:
        print(f"❌ Erro ao enviar para o S3: {e}")

# ==========================================
# EXECUÇÃO PRINCIPAL
# ==========================================
if __name__ == "__main__":
    df_sociais = coletar_trends_nacional()
    dados_tecnicos = coletar_latencia_tecnica()
    salvar_e_enviar_dados(dados_tecnicos, df_sociais)