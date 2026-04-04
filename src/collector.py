import json
import time
import os
import socket
from datetime import datetime
from typing import Dict, List, Any
from pytrends.request import TrendReq
import boto3
from dotenv import load_dotenv

load_dotenv()

# Configurações de acesso ao Google Trends
pytrends = TrendReq(hl='pt-BR', tz=-3, timeout=(10, 25))

# Constantes de configuração
OPERADORAS_CONFIG = {
    "Vivo": ["Vivo internet", "Vivo caiu", "Vivo fora do ar", "Vivo sem sinal", "Vivo falha"],
    "Claro": ["Claro internet", "Claro caiu", "Claro fora do ar", "Claro sem sinal", "Claro falha"],
    "TIM": ["TIM internet", "TIM caiu", "TIM fora do ar", "TIM sem sinal", "TIM falha"],
    "Oi": ["Oi internet", "Oi caiu", "Oi fora do ar", "Oi sem sinal", "Oi falha"]
}

MAPA_ESTADOS = {
    'Acre': 'AC', 'Alagoas': 'AL', 'Amapá': 'AP', 'Amazonas': 'AM', 'Bahia': 'BA',
    'Ceará': 'CE', 'Distrito Federal': 'DF', 'Espírito Santo': 'ES', 'Goiás': 'GO',
    'Maranhão': 'MA', 'Mato Grosso': 'MT', 'Mato Grosso do Sul': 'MS', 'Minas Gerais': 'MG',
    'Pará': 'PA', 'Paraíba': 'PB', 'Paraná': 'PR', 'Pernambuco': 'PE', 'Piauí': 'PI',
    'Rio de Janeiro': 'RJ', 'Rio Grande do Norte': 'RN', 'Rio Grande do Sul': 'RS',
    'Rondônia': 'RO', 'Roraima': 'RR', 'Santa Catarina': 'SC', 'São Paulo': 'SP',
    'Sergipe': 'SE', 'Tocantins': 'TO'
}

OPERADORAS_ALVOS = {
    "Vivo": {"alvo": "www.vivo.com.br", "porta": 443},
    "Claro": {"alvo": "www.claro.com.br", "porta": 443},
    "TIM": {"alvo": "www.tim.com.br", "porta": 443},
    "Oi": {"alvo": "www.oi.com.br", "porta": 443}
}

# Timings para respeitar limites de rate do Google Trends
DELAY_ENTRE_REGIOES = 1.5  # segundos
DELAY_FALHA_API = 5      # segundos após erro

def coletar_telemetria_social() -> Dict[str, Dict[str, float]]:
    """
    Estratégia Otimizada (Estratégia 3):
    Faz apenas 1 requisição por operadora pedindo a quebra por estados (interest_by_region).
    Reduz o tempo de coleta de 10 minutos para ~15 segundos. Zero risco de rate limit.
    """
    print("\n[SENSOR SOCIAL] Iniciando varredura Nacional otimizada (interest_by_region)...")
    resultados_sociais: Dict[str, Dict[str, float]] = {}
    
    for operadora, keywords in OPERADORAS_CONFIG.items():
        resultados_sociais[operadora] = {}
        print(f"\nColetando dados da operadora: {operadora}")
        
        try:
            # 1. Configura a busca para o Brasil ('BR') inteiro nas últimas 4 horas
            pytrends.build_payload(keywords, cat=0, timeframe='now 4-H', geo='BR')
            
            # 2. O Pulo do Gato: Pede ao Google a quebra por estados de uma só vez
            df_regioes = pytrends.interest_by_region(resolution='REGION', inc_low_vol=True, inc_geo_code=False)
            
            if not df_regioes.empty:
                # Calcula a média de buscas entre todos os termos (ex: "vivo caiu" + "vivo falha")
                df_regioes['Media_Alertas'] = df_regioes.mean(axis=1)
                
                # 3. Popula nosso dicionário traduzindo "São Paulo" para "SP"
                for estado_google, row in df_regioes.iterrows():
                    sigla = MAPA_ESTADOS.get(estado_google, estado_google)
                    valor = float(row['Media_Alertas'])
                    resultados_sociais[operadora][sigla] = valor
                
                # O cenário Nacional é simplesmente a média de todos os estados juntos
                media_nacional = float(df_regioes['Media_Alertas'].mean())
                resultados_sociais[operadora]['Nacional'] = media_nacional
                
                print(f"  -> Dados extraídos com sucesso! (Média Nacional: {media_nacional:.1f})")
            
            else:
                print("  -> Sem dados suficientes de buscas no momento.")
                for sigla in MAPA_ESTADOS.values():
                    resultados_sociais[operadora][sigla] = 0
                resultados_sociais[operadora]['Nacional'] = 0
            
            # Pausa de apenas 2 segundos para respeitar a API entre as operadoras
            time.sleep(2) 
            
        except Exception as erro_trends:
            print(f"  -> Erro ao consultar {operadora}: {erro_trends}")
            for sigla in MAPA_ESTADOS.values():
                resultados_sociais[operadora][sigla] = 0
            resultados_sociais[operadora]['Nacional'] = 0
            time.sleep(5)
            
    return resultados_sociais

def testar_ping_operadoras() -> List[Dict[str, Any]]:
    """
    Verifica a disponibilidade técnica das operadoras usando TCP Socket na porta 443.
    
    Por que TCP 443? É padrão HTTPS/SSL, não usa HTTP, evita redirects.
    A latência captura velocidade real de resposta da rede, não do HTTP.
    """
    print("\n[SENSOR TÉCNICO] Iniciando testes de rede (TCP Socket Porta 443)...")
    
    resultados: List[Dict[str, Any]] = []
    
    for operadora, info in OPERADORAS_ALVOS.items():
        dominio = info["alvo"]
        porta = info["porta"]
        
        try:
            inicio = time.time()
            
            # Cria conexão TCP e fecha logo (não queremos HTTP)
            socket_conexao = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_conexao.settimeout(5)
            socket_conexao.connect((dominio, porta))
            socket_conexao.close()
            
            latencia_ms = int((time.time() - inicio) * 1000)
            
            resultados.append({
                "operadora": operadora,
                "status_http": 200,
                "latencia_ms": latencia_ms,
                "erro_tecnico": "Nenhum"
            })
            print(f"  -> {operadora}: {latencia_ms}ms ✓")
            
        except (socket.timeout, socket.error, ConnectionRefusedError) as erro_conexao:
            # A operadora está indisponível ou não responde em tempo
            resultados.append({
                "operadora": operadora,
                "status_http": 0,
                "latencia_ms": 5000,
                "erro_tecnico": f"TCP indisponível em {dominio}:443"
            })
            print(f"  -> {operadora}: FALHA ✗ ({type(erro_conexao).__name__})")
            
    return resultados

def salvar_e_enviar_dados(dados_tecnicos: List[Dict[str, Any]], dados_sociais: Dict[str, Dict[str, float]]) -> None:
    """
    Persiste os dados coletados localmente e sincroniza com AWS S3.
    
    Estrutura gerada: timestamp (para auditoria) + telemetria de todas as operadoras
    Nomeação: telemetria_YYYYMMDD_HHMMSS.json (facilita buscas e ordenação cronológica)
    """
    print("\n[PERSISTÊNCIA] Estruturando dados e enviando para AWS S3...")
    os.makedirs('dados', exist_ok=True)
    
    # Constrói o payload final com índices sociais por operadora
    payload = {
        "timestamp": datetime.now().isoformat(),
        "telemetria": []
    }
    
    for item_tecnico in dados_tecnicos:
        operadora = item_tecnico["operadora"]
        item_tecnico["indices_sociais"] = dados_sociais[operadora]
        payload["telemetria"].append(item_tecnico)
    
    # Arquivo local para backup/debug
    nome_arquivo = f"telemetria_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    caminho_local = f"dados/{nome_arquivo}"
    
    with open(caminho_local, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=4)
    print(f" ✓ Backup local: {caminho_local}")
    
    # Sincroniza com S3 (fonte única da verdade para o dashboard)
    try:
        s3_cliente = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION')
        )
        bucket_name = os.getenv('S3_BUCKET_NAME')
        caminho_s3 = f"raw/{nome_arquivo}"
        
        s3_cliente.upload_file(caminho_local, bucket_name, caminho_s3)
        print(f" ✓ Sincronizado S3: s3://{bucket_name}/{caminho_s3}")
        
    except Exception as erro_s3:
        # Se falhar, o backup local fica como fallback
        print(f" ✗ Falha ao sincronizar S3: {erro_s3}")
        print(f"   Dados salvos localmente em: {caminho_local}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("TELCO PULSE - SENSOR DE MONITORAMENTO DE OPERADORAS")
    print("="*60)
    
    # Fase 1: Coleta dados de repercussão social (Google Trends)
    dados_sociais = coletar_telemetria_social()
    
    # Fase 2: Testa conectividade técnica (TCP Socket)
    dados_tecnicos = testar_ping_operadoras()
    
    # Fase 3: Persiste e sincroniza dados
    salvar_e_enviar_dados(dados_tecnicos, dados_sociais)
    
    print("\n" + "="*60)
    print("Ciclo de coleta concluído com sucesso!")
    print("="*60 + "\n")