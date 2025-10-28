import pandas as pd
import smartsheet
import os
import traceback
import sys
from dotenv import load_dotenv
import re 

# ===============================================
# CONFIGURAÇÕES GLOBAIS
# ===============================================
# O NOME DO RELATÓRIO QUE VOCÊ QUER CARREGAR
SHEET_NAME = 'Relatório MF- Smart' 
FINAL_OUTPUT_CSV = "relatorio_macrofluxo_final.csv" 
TEMP_DOWNLOAD_DIR = "." 

def carregar_configuracao():
    """Carrega as configurações e verifica o ambiente"""
    try:
        if not os.path.exists('.env'):
            raise FileNotFoundError("Arquivo .env não encontrado")
        
        load_dotenv()
        token = os.getenv("SMARTSHEET_ACCESS_TOKEN")
        
        if not token:
            raise ValueError("Token não encontrado no arquivo .env")
        
        print("INFO: Arquivo .env carregado com sucesso.")
        return token
    
    except Exception as e:
        print(f"\nERRO DE CONFIGURAÇÃO: {str(e)}")
        return None

def setup_smartsheet_client(token):
    """Configura o cliente Smartsheet"""
    try:
        client = smartsheet.Smartsheet(token)
        client.errors_as_exceptions(True)
        return client
    except Exception as e:
        print(f"\nERRO: Falha ao configurar cliente Smartsheet - {str(e)}")
        return None

# ===================================================================
# FUNÇÕES DE COLETA DE DADOS (USANDO A ABORDAGEM DE RELATÓRIO/CSV)
# ===================================================================

def get_report_id(client, report_name):
    """Obtém o ID do Relatório"""
    try:
        print(f"\nBuscando RELATÓRIO '{report_name}'...")
        response = client.Reports.list_reports(include_all=True)
        
        for report in response.data:
            if report.name == report_name:
                print(f"INFO: Relatório encontrado (ID: {report.id})")
                return report.id
        
        print(f"\nERRO: Relatório '{report_name}' não encontrado")
        return None
        
    except Exception as e:
        print(f"\nErro inesperado ao buscar relatórios: {str(e)}")
        return None

def get_report_data(client, report_id):
    """Baixa o relatório diretamente como CSV e o converte para DataFrame."""
    
    downloaded_file_path = None 
    
    try:
        print("\nObtendo dados do Relatório (via CSV)...")
        print(f"INFO: Solicitando download para o diretório: '{TEMP_DOWNLOAD_DIR}'")
        
        result = client.Reports.get_report_as_csv(
            report_id,
            download_path=TEMP_DOWNLOAD_DIR
        )
        
        downloaded_file_path = result.filename
        print(f"INFO: Download concluído. Arquivo salvo como: '{downloaded_file_path}'")
        
        df = pd.read_csv(downloaded_file_path, sep=',')
        
        print(f"INFO: CSV lido para DataFrame. {len(df)} linhas encontradas.")

        if df.empty:
             print("AVISO: O DataFrame foi criado vazio (após ler o CSV).")
        
        return df
    
    except Exception as e:
        print(f"\nERRO: Falha ao obter dados do Relatório como CSV: {str(e)}")
        traceback.print_exc()
        return pd.DataFrame()

    finally:
        # Garante que o arquivo temporário seja limpo
        if downloaded_file_path and os.path.exists(downloaded_file_path):
            try:
                os.remove(downloaded_file_path)
                print(f"INFO: Arquivo temporário '{downloaded_file_path}' removido.")
            except Exception as e:
                print(f"AVISO: Não foi possível remover o arquivo temporário '{downloaded_file_path}'. {e}")


# ===================================================================
# FUNÇÃO DE PROCESSAMENTO (Idêntica em ambos os scripts)
# ===================================================================
def processar_dados_macrofluxo(df):
    """
    Aplica a transformação 'unpivot' (melt)
    """
    print("\nIniciando processamento e transformação 'unpivot'...")
    
    if df.empty:
        print("AVISO: DataFrame de entrada está vazio. Pulando processamento.")
        return df
        
    try:
        # 1. RENOMEAR COLUNAS
        if 'Empreendimento' in df.columns and 'Primário' in df.columns:
            df = df.rename(columns={
                'Empreendimento': 'EMP',
                'Primário': 'Etapa'
            })
            print(f"INFO: Colunas 'Empreendimento' e 'Primário' renomeadas.")
        else:
            print("AVISO: Colunas 'Empreendimento' ou 'Primário' não encontradas. Verifique o relatório.")
            
        # 1.5. LIMPAR COLUNA 'EMP' (Remover "2.", "3.", etc.)
        if 'EMP' in df.columns:
            print("INFO: Limpando coluna 'EMP' (removendo prefixos 'N.')...")
            df['EMP'] = df['EMP'].astype(str).str.replace(r'^\d+\.', '', regex=True).str.strip()
            print("INFO: Coluna 'EMP' limpa.")

        # 2. FILTRAR ETAPAS
        if 'Etapa' in df.columns:
            valores_para_remover = ['PUL.RAD.:', 'LEG.PAV'] 
            linhas_antes = len(df)
            df = df[~df['Etapa'].isin(valores_para_remover)]
            linhas_depois = len(df)
            print(f"INFO: Linhas com 'Etapa' em {valores_para_remover} removidas. {linhas_antes - linhas_depois} linhas filtradas.")
        
        # 3. REMOVER COLUNAS DESNECESSÁRIAS
        colunas_para_remover = ['Fase', 'Início LB', 'Término LB', 'Origem Planil', 'ID']
        colunas_existentes_para_remover = [col for col in colunas_para_remover if col in df.columns]
        df = df.drop(columns=colunas_existentes_para_remover)
        print(f"INFO: Colunas desnecessárias removidas: {colunas_existentes_para_remover}")

        # 4. PRESERVAR ORDEM ORIGINAL
        df['Ordem_Etapa'] = range(1, len(df) + 1)

        # 5. TRANSFORMAÇÃO (UNPIVOT / MELT)
        colunas_identificadoras = ['EMP', 'Serviço', '%', 'Etapa', 'Ordem_Etapa']
        colunas_identificadoras_existentes = [col for col in colunas_identificadoras if col in df.columns]
        
        colunas_de_data = ['Data de Início', 'Data de Fim']
        colunas_de_data_existentes = [col for col in colunas_de_data if col in df.columns]
        
        if len(colunas_de_data_existentes) == 0:
            print(f"ERRO: Nenhuma coluna de data ({colunas_de_data}) encontrada para o 'melt'.")
            return pd.DataFrame()

        df_melted = pd.melt(
            df,
            id_vars=colunas_identificadoras_existentes,
            value_vars=colunas_de_data_existentes,
            var_name='Atributo',
            value_name='Valor'
        )
        print(f"INFO: Transformação 'unpivot' (melt) concluída. {len(df_melted)} linhas geradas.")
        
        df_melted.dropna(subset=['Valor'], inplace=True)
        print(f"INFO: Linhas com datas nulas removidas. {len(df_melted)} linhas restantes.")

        # 6. CRIAR NOVAS COLUNAS
        df_melted['Inicio_Fim'] = df_melted['Atributo'].apply(lambda x: 'INICIO' if 'Início' in x else 'TERMINO')
        df_melted['Tipo_Data'] = 'REAL' 

        # 7. LIMPEZA FINAL
        df_final = df_melted.drop(columns=['Atributo'])
        
        # O 'dayfirst=True' é importante para CSVs que podem ter formato DD/MM/AAAA
        df_final['Valor'] = pd.to_datetime(df_final['Valor'], dayfirst=True, errors='coerce').dt.date
        
        if '%' in df_final.columns:
             df_final = df_final.rename(columns={'%': '%_Concluido'})

        # 8. ORDENAR E ORGANIZAR
        colunas_finais = [
            'EMP', 'Serviço', 'Etapa', 'Tipo_Data', 'Inicio_Fim', 
            'Valor', '%_Concluido', 'Ordem_Etapa'
        ]
        
        colunas_finais_existentes = [col for col in colunas_finais if col in df_final.columns]
        df_final = df_final[colunas_finais_existentes]
        
        df_final = df_final.sort_values(by=['EMP', 'Ordem_Etapa', 'Inicio_Fim'])

        print("INFO: Processamento e transformação concluídos com sucesso.")
        return df_final

    except Exception as e:
        print(f"\nERRO: Falha during processamento/transformação dos dados: {str(e)}")
        traceback.print_exc()
        return pd.DataFrame() 

# ===================================================================
# FUNÇÃO PARA SALVAR
# ===================================================================
def salvar_resultados(df, filename):
    # Esta função só será usada se você rodar o script diretamente
    try:
        df.to_csv(filename, index=False, sep=';', decimal=',', encoding='utf-8-sig')
        print(f"\n💾 Arquivo final salvo com sucesso: {filename}")
        print("\n📋 Visualização dos dados PROCESSADOS:")
        
        if not df.empty:
            print(f"Colunas: {list(df.columns)}")
            print(df.head(10)) 
        else:
            print("O DataFrame salvo estava vazio.")
            
        return True
    except Exception as e:
        print(f"\nERRO AO SALVAR: {str(e)}")
        return False

# ===================================================================
# <<< FUNÇÃO (MASTER) PARA IMPORTAÇÃO PELO APP >>>
# ===================================================================
def buscar_e_processar_dados_completos():
    """
    Função 'master' que executa todo o pipeline:
    Configura -> Conecta -> Busca ID do Relatório -> Baixa Dados -> Processa.
    Retorna um DataFrame processado ou um DataFrame vazio em caso de falha.
    """
    print("\nINFO (MASTER): Iniciando pipeline completo de dados (Método: Relatório CSV)...")
    
    # 1. Configuração
    token = carregar_configuracao()
    if not token: 
        print("ERRO (MASTER): Falha ao carregar token.")
        return pd.DataFrame() # Retorna DF vazio

    client = setup_smartsheet_client(token)
    if not client: 
        print("ERRO (MASTER): Falha ao conectar ao Smartsheet.")
        return pd.DataFrame()

    # 2. Buscar ID do Relatório
    report_id = get_report_id(client, SHEET_NAME) # SHEET_NAME é global
    if not report_id: 
        print(f"ERRO (MASTER): Relatório '{SHEET_NAME}' não encontrado.")
        return pd.DataFrame()

    # 3. Obter dados brutos
    raw_data = get_report_data(client, report_id)
    if raw_data.empty:
        print("AVISO (MASTER): Nenhum dado foi baixado do Smartsheet.")
        return pd.DataFrame()
        
    # 4. Processar os dados
    processed_data = processar_dados_macrofluxo(raw_data)
    
    if processed_data.empty:
        print("AVISO (MASTER): Falha ao processar os dados (resultado vazio).")
        return pd.DataFrame()
    
    print("INFO (MASTER): Pipeline (Relatório CSV) concluído com sucesso.")
    return processed_data


# ===================================================================
# FUNÇÃO 'main' FINAL (Para execução direta do script)
# ===================================================================
def main():
    """
    Função principal para orquestrar o script (quando executado diretamente)
    """
    print("\n" + "="*50)
    print(" INÍCIO DO PROCESSAMENTO DO MACROFLUXO ".center(50, "="))
    print("="*50)

    # O main apenas chama a nova função master
    processed_data = buscar_e_processar_dados_completos()
    
    if processed_data.empty:
        print("\nAVISO: O processamento não gerou dados. Verifique os logs de erro.")
        sys.exit(1)

    # 5. Salvar resultados FINAIS
    if not salvar_resultados(processed_data, FINAL_OUTPUT_CSV):
        sys.exit(1)
        
    print("\n" + "="*50)
    print(" PROCESSAMENTO CONCLUÍDO ".center(50, "="))
    print("="*50)
    print(f"\nVerifique o arquivo final: '{FINAL_OUTPUT_CSV}'")

# --- BLOCO DE EXECUÇÃO ---
if __name__ == "__main__":
    main()
