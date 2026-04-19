# 📡 Telco Pulse: Monitoramento de Infraestrutura e Operabilidade
**Status:** Concluído / Em Otimização Contínua  
**Tecnologias:** Python, AWS (EC2, S3), Streamlit, GitHub Actions

## 📌 Apresentação
O **Telco Pulse** é uma solução robusta desenvolvida para monitorar a saúde e a operabilidade de infraestruturas de telecomunicações. O projeto integra métricas técnicas de rede com análise de sentimentos sociais para identificar quedas de serviço e instabilidades em tempo real, permitindo uma visão holística da experiência do cliente.

## 🚀 Destaques Técnicos e Engenharia de Dados
* **Otimização de Performance:** Implementação de processamento em lote (batch processing) que reduziu o tempo de execução do pipeline de dados de **10 minutos para apenas 18 segundos**.
* **Arquitetura em Nuvem:** Utilização de instâncias **AWS EC2** para processamento e **S3** para armazenamento escalável de dados.
* **CI/CD:** Automação de fluxos de trabalho e atualizações via **GitHub Actions**.
* **Visualização:** Dashboard interativo desenvolvido em **Streamlit** para acompanhamento de KPIs e alertas.

## 🛠️ Como Executar o Projeto
1. Clone o repositório: `git clone https://github.com/DiogoRicarte/telco_pulse.git`
2. Instale as dependências: `pip install -r requirements.txt`
3. Configure suas credenciais AWS no arquivo `.env`.
4. Execute a aplicação: `streamlit run app.py`

## 🌟 Funcionalidades Principais
* **Correlação de Dados:** Cruzamento automático entre falhas técnicas de rede e picos de reclamações em redes sociais.
* **Alertas Inteligentes:** Notificação de anomalias detectadas no tráfego de dados.
* **Pipeline Escalável:** Estrutura preparada para lidar com grandes volumes de logs de rede.
