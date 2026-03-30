import json
import time
import os
import requests
import socket
from datetime import datetime
from pytrends.request import TrendReq
import boto3
from dotenv import load_dotenv

load_dotenv()

pytrends = TrendReq(hl='pt-BR', tz=180, timeout=(10,25))

def coletar_telemetria_social():
    print("\n[SENSOR SOCIAL] Iniciando varredura Nacional e em 27 Estados...")
    print("Aviso: Esta etapa pode levar de 5 a 7 minutos para evitar bloqueios do Google.")
    
    # Máximo de 5 termos por consulta (limite estrito do Google Trends)
    termos = {
        "Vivo": ["Vivo internet", "Vivo caiu", "Vivo fora do ar", "Vivo sem sinal", "Vivo falha"],
        "Claro": ["Claro internet", "Claro caiu", "Claro fora do ar", "Claro sem sinal", "Claro falha"],
        "TIM": ["TIM internet", "TIM caiu", "TIM fora do ar", "TIM sem sinal", "TIM falha"],
        "Oi": ["Oi internet", "Oi caiu", "Oi fora do ar", "Oi sem sinal", "Oi falha"]
    }
    
    regioes = {
        'BR': 'Nacional', 
        'BR-AC': 'AC', 'BR-AL': 'AL', 'BR-AP': 'AP', 'BR-AM': 'AM', 'BR-BA': 'BA', 
        'BR-CE': 'CE', 'BR-DF': 'DF', 'BR-ES': 'ES', 'BR-GO': 'GO', 'BR-MA': 'MA', 
        'BR-MT': 'MT', 'BR-MS': 'MS', 'BR-MG': 'MG', 'BR-PA': 'PA', 'BR-PB': 'PB', 
        'BR-PR': 'PR', 'BR-PE': 'PE', 'BR-PI': 'PI', 'BR-RJ': 'RJ', 'BR-RN': 'RN', 
        'BR-RS': 'RS', 'BR-RO': 'RO', 'BR-RR': 'RR', 'BR-SC': 'SC', 'BR-SP': 'SP', 
        'BR-SE': 'SE', 'BR-TO': 'TO'
    }
    
    resultados_sociais = {}
    
    for operadora, keywords in termos.items():
        resultados_sociais[operadora] = {}
        print(f"\nColetando dados da operadora: {operadora}")
        
        for geo_code, nome_regiao in regioes.items():
            try:
                pytrends.build_payload(keywords, cat=0, timeframe='now 1-d', geo=geo_code)
                df = pytrends.interest_over_time()
                
                if not df.empty:
                    df = df.drop(columns=['isPartial'], errors='ignore')
                    valor = int(df.sum(axis=1).iloc[-1])
                    resultados_sociais[operadora][nome_regiao] = valor
                else:
                    resultados_sociais[operadora][nome_regiao] = 0
                
                print(f"  -> {nome_regiao}: {resultados_sociais[operadora][nome_regiao]}")
                time.sleep(3) 
                
            except Exception as e:
                print(f"  -> Erro ao consultar {nome_regiao}: Bloqueio de API ou Sem Dados")
                resultados_sociais[operadora][nome_regiao] = 0
                time.sleep(5)
                
    return resultados_sociais

def testar_ping_operadoras():
    print("\n[SENSOR TÉCNICO] Iniciando testes de rede (TCP Socket Ping na Porta 443)...")
    import socket 
    import time
    
    alvos = {
        "Vivo": {"alvo": "www.vivo.com.br", "porta": 443},
        "Claro": {"alvo": "www.claro.com.br", "porta": 443},
        "TIM": {"alvo": "www.tim.com.br", "porta": 443},
        "Oi": {"alvo": "www.oi.com.br", "porta": 443}
    }
    resultados = []
    
    for operadora, info in alvos.items():
        dominio = info["alvo"]     
        porta = info["porta"] 
        
        try:
            inicio = time.time()
            # Cria a conexão TCP
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            
            # Conecta na porta 443 e foge antes do HTTP agir!
            sock.connect((dominio, porta))
            sock.close()
            
            latencia = int((time.time() - inicio) * 1000)
            
            resultados.append({
                "operadora": operadora,
                "status_http": 200, 
                "latencia_ms": latencia,
                "erro_tecnico": "Nenhum"
            })
            print(f"  -> {operadora}: {latencia}ms (TCP Real Porta {porta})")
            
        except Exception as e:
            resultados.append({
                "operadora": operadora,
                "status_http": 0,
                "latencia_ms": 5000,
                "erro_tecnico": f"Falha TCP no IP {dominio}"
            })
            print(f"  -> {operadora}: FALHA CRÍTICA ({e})")
            
    return resultados

def salvar_e_enviar_dados(dados_tecnicos, dados_sociais):
    print("\n[PERSISTÊNCIA] Estruturando JSON com 27 estados e enviando para AWS...")
    os.makedirs('dados', exist_ok=True)
    
    payload = {
        "timestamp": datetime.now().isoformat(),
        "telemetria": []
    }
    
    for item in dados_tecnicos:
        op = item["operadora"]
        item["indices_sociais"] = dados_sociais[op]
        payload["telemetria"].append(item)
        
    nome_arquivo = f"telemetria_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    caminho_local = f"dados/{nome_arquivo}"
    
    with open(caminho_local, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=4)
    print(f" Salvo localmente em: {caminho_local}")
    
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION')
        )
        bucket_name = os.getenv('S3_BUCKET_NAME')
        caminho_s3 = f"raw/{nome_arquivo}"
        
        s3_client.upload_file(caminho_local, bucket_name, caminho_s3)
        print(f" SUCESSO! Arquivo S3: s3://{bucket_name}/{caminho_s3}")
    except Exception as e:
        print(f" Erro S3: {e}")

if __name__ == "__main__":
    dados_sociais = coletar_telemetria_social()
    dados_tecnicos = testar_ping_operadoras()
    salvar_e_enviar_dados(dados_tecnicos, dados_sociais)