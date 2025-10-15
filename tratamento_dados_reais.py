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
        df = pd.read_excel(file_path, sheet_name='BD', header=0)
        print("INFO: Arquivo Excel carregado com sucesso, usando a primeira linha como cabeçalho.")

        # 2. RENOMEAR COLUNAS PARA OS NOMES DESEJADOS
        df = df.rename(columns={
            'Empreendimento': 'EMP',
            'Primário': 'Etapa'
        })
        print(f"INFO: Colunas renomeadas. Nomes atuais: {list(df.columns)}")

        # =================================================================
        # BLOCO MODIFICADO AQUI PARA FILTRAR MÚLTIPLOS VALORES
        # =================================================================
        linhas_antes = len(df)
        valores_para_remover = ['PUL.RAD.:', 'LEG.PAV'] # Lista de valores a serem excluídos
        df = df[~df['Etapa'].isin(valores_para_remover)]
        linhas_depois = len(df)
        print(f"INFO: Linhas com 'Etapa' em {valores_para_remover} foram removidas. {linhas_antes - linhas_depois} linhas filtradas.")
        # =================================================================

        # 3. REMOVER COLUNAS DESNECESSÁRIAS
        colunas_para_remover = ['Fase', 'Início LB', 'Término LB', 'Origem Planil', 'ID']
        colunas_existentes_para_remover = [col for col in colunas_para_remover if col in df.columns]
        df = df.drop(columns=colunas_existentes_para_remover)
        print(f"INFO: Colunas desnecessárias removidas: {colunas_existentes_para_remover}")

        # 4. PRESERVAR ORDEM ORIGINAL DAS ETAPAS
        df['Ordem_Etapa'] = range(1, len(df) + 1)

        # 5. TRANSFORMAÇÃO (UNPIVOT / MELT)
        colunas_identificadoras = ['EMP', 'Serviço', '%', 'Etapa', 'Ordem_Etapa']
        colunas_de_data = ['Data de Início', 'Data de Fim']

        df_melted = pd.melt(
            df,
            id_vars=colunas_identificadoras,
            value_vars=colunas_de_data,
            var_name='Atributo',
            value_name='Valor'
        )
        print("INFO: Transformação 'unpivot' (melt) concluída com sucesso.")
        
        df_melted.dropna(subset=['Valor'], inplace=True)

        # 6. CRIAR NOVAS COLUNAS A PARTIR DO RESULTADO
        df_melted['Inicio_Fim'] = df_melted['Atributo'].apply(lambda x: 'INICIO' if 'Início' in x else 'TERMINO')
        df_melted['Tipo_Data'] = 'REAL'

        # 7. LIMPEZA FINAL
        df_final = df_melted.drop(columns=['Atributo'])
        df_final['Valor'] = pd.to_datetime(df_final['Valor']).dt.date
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

# --- BLOCO DE EXECUÇÃO --- (permanece o mesmo)
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