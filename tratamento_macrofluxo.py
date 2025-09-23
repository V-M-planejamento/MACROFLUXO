import pandas as pd
import os

def tratar_macrofluxo():
    """Carrega e trata os dados do GRÁFICOMACROFLUXO.xlsx."""
    try:
        diretorio_atual = os.path.dirname(os.path.abspath(__file__))
        caminho_arquivo = os.path.join(diretorio_atual, "GRÁFICO MACROFLUXO.xlsx")
        
        if not os.path.exists(caminho_arquivo):
            print(f"Erro: Arquivo não encontrado no caminho: {caminho_arquivo}")
            return None

        # 1. CARREGAR OS DADOS, usando a linha 7 (índice 6) como cabeçalho
        df = pd.read_excel(caminho_arquivo, sheet_name="GERAL", header=6)

        # Renomear a coluna de índice 3 (coluna D) para 'TIPO_LOTES'
        # E as colunas 1 e 2 para UGB e EMP, conforme a inspeção
        df = df.rename(columns={
            df.columns[1]: 'UGB',
            df.columns[2]: 'EMP',
            df.columns[3]: 'TIPO_LOTES' # Coluna D, índice 3
        })

        # Remover colunas totalmente vazias
        df = df.dropna(axis=1, how='all')

        # Identificar as colunas de unpivot (datas)
        # As colunas de data agora têm o formato 'ETAPA.TIPO.INICIO_FIM'
        colunas_unpivot = [col for col in df.columns if 
                           (".PREV.INICIO" in str(col) or ".PREV.TERMINO" in str(col) or 
                            ".REAL.INICIO" in str(col) or ".REAL.TERMINO" in str(col)) and 
                           str(col) not in ['UGB', 'EMP', 'TIPO_LOTES']
                          ]
        
        colunas_fixas = [col for col in df.columns if col not in colunas_unpivot]

        # 2. UNPIVOT (transformar colunas de datas em linhas)
        df_unpivoted = pd.melt(
            df,
            id_vars=colunas_fixas,
            value_vars=colunas_unpivot,
            var_name="Atributo",
            value_name="Valor"
        )

        # 3. DIVIDIR COLUNA "Atributo" para extrair Etapa, Tipo (PREV/REAL) e Inicio_Fim
        # Ex: PROSPEC.PREV.INICIO -> Etapa='PROSPEC', Tipo_Data='PREV', Inicio_Fim='INICIO'
        split_data = df_unpivoted['Atributo'].str.extract(r'([A-ZÀ-ÚÀ-ÖØ-Þß-öø-þÿ -.]+)\.(REAL|PREV)\.(INICIO|TERMINO)', expand=True)
        split_data.columns = ['Etapa', 'Tipo_Data', 'Inicio_Fim']
        
        df_final = pd.concat([df_unpivoted, split_data], axis=1)
        df_final = df_final.drop(columns=['Atributo'])

        # 4. CONVERTER TIPOS DE COLUNAS
        df_final['UGB'] = df_final['UGB'].astype(str)
        df_final['EMP'] = df_final['EMP'].astype(str)
        df_final['TIPO_LOTES'] = df_final['TIPO_LOTES'].astype(str) # Alterado para string
        df_final['Valor'] = pd.to_datetime(df_final['Valor'], errors='coerce').dt.date

        # 5. FILTRAR APENAS "PREV"
        df_final = df_final[df_final['Tipo_Data'] == 'PREV'].copy()
        
        # 6. CRIAR ORDEM DAS ETAPAS E ORDENAR
        etapas_unicas = df_final['Etapa'].unique()
        mapa_ordem = {etapa: i+1 for i, etapa in enumerate(etapas_unicas)}
        
        df_final['Ordem_Etapa'] = df_final['Etapa'].map(mapa_ordem)
        
        df_final = df_final.sort_values(by=['UGB', 'EMP', 'Ordem_Etapa', 'Inicio_Fim']).reset_index(drop=True)

        return df_final

    except Exception as e:
        print(f"Erro durante o processamento: {str(e)}")
        return None

if __name__ == "__main__":
    dados_tratados = tratar_macrofluxo()
    if dados_tratados is not None:
        print("\nDados do Macrofluxo Tratados e Ordenados:")
        print(dados_tratados[[
            "UGB", "EMP", "TIPO_LOTES", "Etapa", "Tipo_Data", "Inicio_Fim", "Valor", "Ordem_Etapa"
        ]].head(20))
        
        dados_tratados.to_csv("dados_macrofluxo_tratados.csv", index=False)
        print("\nArquivo 'dados_macrofluxo_tratados.csv' salvo com sucesso!")
    else:
        print("\nNão foi possível obter os dados do macrofluxo.")


