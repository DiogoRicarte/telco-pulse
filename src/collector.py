import time
import pandas as pd
from pytrends.request import TrendReq

# Inicializa o pytrends
pytrends = TrendReq(hl='pt-BR', tz=180, retries=3, backoff_factor=0.5)

def coletar_trends_nacional():
    print("Iniciando coleta Nacional de estabilidade de operadoras...")
    
    # Dicionário de palavras-chave (Máx 5 por operadora para respeitar a API do Google)
    termos_busca = {
        "Vivo": ["Vivo fora do ar", "Vivo caiu", "Vivo sem sinal", "Vivo internet ruim"],
        "Claro": ["Claro fora do ar", "Claro caiu", "Claro sem sinal", "Claro internet ruim"],
        "TIM": ["TIM fora do ar", "TIM caiu", "TIM sem sinal", "TIM internet ruim"],
        "Oi": ["Oi fora do ar", "Oi caiu", "Oi sem sinal", "Oi internet ruim"]
    }
    
    # DataFrame vazio que vai receber todos os dados costurados
    df_final = pd.DataFrame()
    
    for operadora, keywords in termos_busca.items():
        print(f"Coletando dados da {operadora}...")
        try:
            # geo='BR' pega o Brasil inteiro. timeframe='now 4-H' pega as últimas 4 horas
            pytrends.build_payload(keywords, cat=0, timeframe='now 4-H', geo='BR')
            df_temp = pytrends.interest_over_time()
            
            if not df_temp.empty:
                # Remove a coluna inútil do Google
                df_temp = df_temp.drop(columns=['isPartial'])
                
                # SOMA o interesse de todas as palavras daquela operadora para criar um "Índice de Falha"
                df_final[f'Indice_Falha_{operadora}'] = df_temp.sum(axis=1)
            
            # Pausa de 3 segundos entre as requisições (Evita erro 429 - Too Many Requests)
            time.sleep(3)
            
        except Exception as e:
            print(f"Erro ao consultar {operadora}: {e}")
            
    if not df_final.empty:
        print("\n=== Dados Nacionais Coletados e Consolidados! ===")
        print("Últimos registros de Índice de Falha:")
        print(df_final.tail())
        return df_final
    else:
        print("Falha ao construir o DataFrame final.")
        return None

if __name__ == "__main__":
    dados = coletar_trends_nacional()