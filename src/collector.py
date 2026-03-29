import time
import pandas as pd
import requests
import json
from datetime import datetime
from pytrends.request import TrendReq
import os

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
    
    # O nosso "disfarce" para passar pelo Firewall da Vivo
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    resultados = []
    
    for operadora, url in urls_operadoras.items():
        try:
            # Agora enviamos os headers junto com a requisição
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
# INTEGRAÇÃO E PERSISTÊNCIA (Salvando o JSON)
# ==========================================
def salvar_dados_json(dados_tecnicos, df_sociais):
    print("\n[PERSISTÊNCIA] Gerando arquivo JSON unificado...")
    
    # Cria a pasta 'dados' se ela não existir
    os.makedirs('dados', exist_ok=True)
    
    # Pega a última linha do Google Trends (o momento atual)
    ultima_linha_social = df_sociais.iloc[-1] if not df_sociais.empty else None
    
    # Monta o "Payload" final (O pacote de dados que vai pra AWS depois)
    payload = {
        "timestamp": datetime.now().isoformat(),
        "telemetria": []
    }
    
    for item in dados_tecnicos:
        op = item["Operadora"]
        # Pega o índice social da operadora correspondente (ou 0 se falhar)
        indice_social = int(ultima_linha_social[f'Indice_Falha_{op}']) if ultima_linha_social is not None else 0
        
        payload["telemetria"].append({
            "operadora": op,
            "status_http": item["Status_HTTP"],
            "latencia_ms": item["Latencia_ms"],
            "indice_social_falha": indice_social,
            "erro_tecnico": item["Erro"]
        })
        
    # Nome do arquivo baseado na data/hora
    nome_arquivo = f"dados/telemetria_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Salva o arquivo no disco do Linux
    with open(nome_arquivo, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=4)
        
    print(f"✅ Sucesso! Dados salvos em: {nome_arquivo}")

# ==========================================
# EXECUÇÃO PRINCIPAL
# ==========================================
if __name__ == "__main__":
    df_sociais = coletar_trends_nacional()
    dados_tecnicos = coletar_latencia_tecnica()
    salvar_dados_json(dados_tecnicos, df_sociais)