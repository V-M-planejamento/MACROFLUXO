import pandas as pd
import os
import traceback

def processar_cronograma(file_path):
    """
    Processa um cronograma com estrutura simples (cabeçalho na primeira linha),
    transformando as colunas de data de início e fim em um formato longo (unpivot).
    """
    try:
        # 1. CARREGAR O ARQUIVO USANDO O CABEÇALHO DA PRIMEIRA LINHA (header=0)
        # O padrão já é header=0, mas deixamos explícito para clareza.
        df = pd.read_excel(file_path, sheet_name='BD', header=0)
        print("INFO: Arquivo Excel carregado com sucesso, usando a primeira linha como cabeçalho.")

        # 2. RENOMEAR COLUNAS PARA OS NOMES DESEJADOS
        # Exatamente como você descreveu: 'Empreendimento' -> 'EMP' e 'Primário' -> 'Etapa'
        df = df.rename(columns={
            'Empreendimento': 'EMP',
            'Primário': 'Etapa'
        })
        print(f"INFO: Colunas renomeadas. Nomes atuais: {list(df.columns)}")

        # 3. REMOVER COLUNAS DESNECESSÁRIAS
        colunas_para_remover = ['Fase', 'Início LB', 'Término LB', 'Origem Planil', 'ID']
        # Remove apenas as colunas que realmente existem no DataFrame para evitar erros
        colunas_existentes_para_remover = [col for col in colunas_para_remover if col in df.columns]
        df = df.drop(columns=colunas_existentes_para_remover)
        print(f"INFO: Colunas desnecessárias removidas: {colunas_existentes_para_remover}")

        # 4. PRESERVAR ORDEM ORIGINAL DAS ETAPAS
        # Criamos uma coluna de ordem antes da transformação para garantir a ordenação correta no final.
        df['Ordem_Etapa'] = range(1, len(df) + 1)

        # 5. TRANSFORMAÇÃO (UNPIVOT / MELT)
        # Esta é a etapa principal: transformar as colunas de data em linhas.
        colunas_identificadoras = ['EMP', 'Serviço', '%', 'Etapa', 'Ordem_Etapa']
        colunas_de_data = ['Data de Início', 'Data de Fim']

        df_melted = pd.melt(
            df,
            id_vars=colunas_identificadoras,
            value_vars=colunas_de_data,
            var_name='Atributo',  # Coluna temporária com 'Data de Início' ou 'Data de Fim'
            value_name='Valor'      # Coluna com as datas
        )
        print("INFO: Transformação 'unpivot' (melt) concluída com sucesso.")
        
        # Remove linhas onde a data final é nula
        df_melted.dropna(subset=['Valor'], inplace=True)

        # 6. CRIAR NOVAS COLUNAS A PARTIR DO RESULTADO
        # Cria a coluna 'Inicio_Fim' com base no nome da coluna de data original
        df_melted['Inicio_Fim'] = df_melted['Atributo'].apply(lambda x: 'INICIO' if 'Início' in x else 'TERMINO')

        # Como as datas não especificam se são 'PREV' ou 'REAL', assumimos 'REAL'
        df_melted['Tipo_Data'] = 'REAL'

        # 7. LIMPEZA FINAL
        # Remove a coluna 'Atributo' que não é mais necessária
        df_final = df_melted.drop(columns=['Atributo'])
        
        # Converte a coluna de data/hora para apenas data
        df_final['Valor'] = pd.to_datetime(df_final['Valor']).dt.date
        
        # Renomeia a coluna '%' para um nome mais claro
        df_final = df_final.rename(columns={'%': '%_Concluido'})

        # 8. ORDENAR E ORGANIZAR O RESULTADO FINAL
        colunas_finais = [
            'EMP', 'Serviço', 'Etapa', 'Tipo_Data', 'Inicio_Fim', 
            'Valor', '%_Concluido', 'Ordem_Etapa'
        ]
        df_final = df_final[colunas_finais]
        df_final = df_final.sort_values(by=['EMP', 'Ordem_Etapa', 'Inicio_Fim'])

        return df_final

    except FileNotFoundError:
        print(f"ERRO: Arquivo não encontrado no caminho: {file_path}")
        return None
    except Exception as e:
        print(f"ERRO: Ocorreu um erro inesperado durante o processamento: {e}")
        print("\n--- DETALHES TÉCNICOS DO ERRO ---")
        traceback.print_exc()
        print("-----------------------------------\n")
        return None

# --- BLOCO DE EXECUÇÃO ---
if __name__ == '__main__':
    try:
        diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        diretorio_atual = os.getcwd()

    caminho_do_arquivo_excel = os.path.join(diretorio_atual, 'GRÁFICO MACROFLUXO.xlsx')
    caminho_saida_csv = os.path.join(diretorio_atual, 'dados_macrofluxo_processados.csv')

    print(f"Iniciando o processamento do arquivo: {caminho_do_arquivo_excel}...")
    
    df_processado = processar_cronograma(caminho_do_arquivo_excel)

    if df_processado is not None and not df_processado.empty:
        df_processado.to_csv(caminho_saida_csv, index=False, sep=';', decimal=',')
        print("-" * 50)
        print("Script concluído com sucesso!")
        print(f"Os dados processados foram salvos em: {caminho_saida_csv}")
        print("\nVisualização das primeiras 10 linhas do arquivo gerado:")
        print(df_processado.head(10))
        print("-" * 50)
    else:
        print("\nO processamento falhou ou não gerou dados. Verifique as mensagens de ERRO acima.")