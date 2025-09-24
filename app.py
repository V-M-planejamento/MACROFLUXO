import streamlit as st
import pandas as pd
import numpy as np
import matplotlib as mpl
mpl.use('agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
from datetime import datetime
from dropdown_component import simple_multiselect_dropdown
from popup import show_welcome_screen
from calculate_business_days import calculate_business_days

# --- Bloco de Importação de Dados ---
try:
    from tratamento_dados_reais import processar_cronograma
    from tratamento_macrofluxo import tratar_macrofluxo
except ImportError:
    st.warning("Scripts de processamento não encontrados. O app usará dados de exemplo.")
    processar_cronograma = None
    tratar_macrofluxo = None

# --- Configurações de Estilo ---
class StyleConfig:
    LARGURA_GANTT = 10
    ALTURA_GANTT_POR_ITEM = 1.2
    ALTURA_BARRA_GANTT = 0.35
    LARGURA_TABELA = 5
    COR_PREVISTO = '#A8C5DA'
    COR_REAL = '#174c66'
    COR_HOJE = 'red'
    COR_CONCLUIDO = '#047031'
    COR_ATRASADO = '#a83232'
    COR_META_ASSINATURA = '#8e44ad'
    FONTE_TITULO = {'size': 10, 'weight': 'bold', 'color': 'black'}
    FONTE_ETAPA = {'size': 12, 'weight': 'bold', 'color': '#2c3e50'}
    FONTE_DATAS = {'family': 'monospace', 'size': 10, 'color': '#2c3e50'}
    FONTE_PORCENTAGEM = {'size': 12, 'weight': 'bold'}
    FONTE_VARIACAO = {"size": 8, "weight": "bold"}
    CABECALHO = {'facecolor': '#2c3e50', 'edgecolor': 'none', 'pad': 4.0, 'color': 'white'}
    CELULA_PAR = {'facecolor': 'white', 'edgecolor': '#d1d5db', 'lw': 0.8}
    CELULA_IMPAR = {'facecolor': '#f1f3f5', 'edgecolor': '#d1d5db', 'lw': 0.8}
    FUNDO_TABELA = '#f8f9fa'
    ESPACO_ENTRE_EMPREENDIMENTOS = 1.5
    OFFSET_VARIACAO_TERMINO = 0.31 # Posição vertical variação

    @classmethod
    def set_offset_variacao_termino(cls, novo_offset):
        """
        Método para alterar o offset vertical do texto da variação de término.
        
        Args:
            novo_offset (float): Novo offset vertical (valor float, e.g., 0.25)
        """
        cls.OFFSET_VARIACAO_TERMINO = novo_offset

# --- Funções Utilitárias ---
def abreviar_nome(nome):
    if pd.isna(nome):
        return nome
    
    nome = nome.replace('CONDOMINIO ', '')
    palavras = nome.split()
    
    if len(palavras) > 3:
        nome = ' '.join(palavras[:3])
    
    return nome

def converter_porcentagem(valor):
    if pd.isna(valor) or valor == '': return 0.0
    if isinstance(valor, str):
        valor = ''.join(c for c in valor if c.isdigit() or c in ['.', ',']).replace(',', '.').strip()
        if not valor: return 0.0
    try:
        return float(valor) * 100 if float(valor) <= 1 else float(valor)
    except (ValueError, TypeError):
        return 0.0

def formatar_data(data):
    return data.strftime("%d/%m/%y") if pd.notna(data) else "N/D"

def calcular_dias_uteis(inicio, fim):
    if pd.notna(inicio) and pd.notna(fim):
        data_inicio = np.datetime64(inicio.date())
        data_fim = np.datetime64(fim.date())
        return np.busday_count(data_inicio, data_fim) + 1
    return 0

def calcular_variacao_termino(termino_real, termino_previsto):
    """
    Calcula a variação entre o término real e o término previsto.
    Retorna uma tupla (texto_variacao, cor_variacao)
    """
    if pd.notna(termino_real) and pd.notna(termino_previsto):
        diferenca_dias = calculate_business_days(termino_previsto, termino_real)
        if pd.isna(diferenca_dias): diferenca_dias = 0 # Lidar com casos em que calculate_business_days retorna NA
        
        if diferenca_dias > 0:
            # Atrasado - vermelho
            return f"V: +{diferenca_dias}d", "#89281d"
        elif diferenca_dias < 0:
            # Adiantado - verde
            return f"V: {diferenca_dias}d", "#0b803c"
        else:
            # No prazo - cinza
            return "V: 0d", "#666666"
    else:
        # Sem dados suficientes - cinza
        return "V: -", "#666666"

def calcular_porcentagem_correta(grupo):
    if '% concluído' not in grupo.columns:
        return 0.0
    
    porcentagens = grupo['% concluído'].astype(str).apply(converter_porcentagem)
    porcentagens = porcentagens[(porcentagens >= 0) & (porcentagens <= 100)]
    
    if len(porcentagens) == 0:
        return 0.0
    
    porcentagens_validas = porcentagens[pd.notna(porcentagens)]
    if len(porcentagens_validas) == 0:
        return 0.0
    return porcentagens_validas.mean()

# --- Mapeamentos e Padronização ---
# Mapeamento fornecido pelo usuário
mapeamento_etapas_usuario = {
    'PROSPECÇÃO':             "PROSPEC",
    'LEGALIZAÇÃO PARA VENDA': "LEGVENDA",
    'PULMÃO VENDA':           "PULVENDA",
    'PL.LIMP':                "PL.LIMP",
    'LEG.LIMP':               "LEG.LIMP",
    'ENG. LIMP.':             "ENG.LIMP",
    'EXECUÇÃO LIMP.':         "EXECLIMP",
    'PL.TER.':                "PL.TER",
    'LEG.TER.':               "LEG.TER",
    'ENG. TER.':              "ENG.TER",
    'EXECUÇÃO TER.':          "EXECTER",
    'PL.INFRA':               "PL.INFRA",
    'LEG.INFRA':              "LEG.INFRA",
    'ENG. INFRA':             "ENG.INFRA",
    'EXECUÇÃO INFRA':         "EXECINFRA",
    'LEG.PAV':                "LEG.PAV",
    'ENG. PAV':               "ENG.PAV",
    'EXECUÇÃO PAV.':          "EXEC.PAV",
    'PULMÃO INFRA':           "PUL.INFRA",
    'PL.RADIER':              "PL.RAD",
    'LEG.RADIER':             "LEG.RAD",
    'RADIER':                 "RAD",
    'DEMANDA MÍNIMA':         "DEM.MIN",
}

# Mapeamento reverso para exibição
mapeamento_reverso = {v: k for k, v in mapeamento_etapas_usuario.items()}

# Siglas para nomes completos (mantendo compatibilidade com o código original)
sigla_para_nome_completo = {
    'PROSPEC': 'PROSPECÇÃO',
    'LEGVENDA': 'LEGALIZAÇÃO PARA VENDA',
    'PULVENDA': 'PULMÃO VENDA',
    'PL.LIMP': 'PL.LIMP',
    'LEG.LIMP': 'LEG.LIMP',
    'ENG.LIMP': 'ENG. LIMP.',
    'EXECLIMP': 'EXECUÇÃO LIMP.',
    'PL.TER': 'PL.TER.',
    'LEG.TER': 'LEG.TER.',
    'ENG.TER': 'ENG. TER.',
    'EXECTER': 'EXECUÇÃO TER.',
    'PL.INFRA': 'PL.INFRA',
    'LEG.INFRA': 'LEG.INFRA',
    'ENG.INFRA': 'ENG. INFRA',
    'EXECINFRA': 'EXECUÇÃO INFRA',
    'LEG.PAV': 'LEG.PAV',
    'ENG.PAV': 'ENG. PAV',
    'EXEC.PAV': 'EXECUÇÃO PAV.',
    'PUL.INFRA': 'PULMÃO INFRA',
    'PL.RAD': 'PL.RADIER',
    'LEG.RAD': 'LEG.RADIER',
    'RAD': 'RADIER',
    'DEM.MIN': 'DEMANDA MÍNIMA',
}

nome_completo_para_sigla = {v: k for k, v in sigla_para_nome_completo.items()}

def padronizar_etapa(etapa_str):
    if pd.isna(etapa_str): return 'UNKNOWN'
    etapa_limpa = str(etapa_str).strip().upper()
    
    # Primeiro, verifica se já está no formato de sigla
    if etapa_limpa in sigla_para_nome_completo:
        return etapa_limpa
    
    # Depois, verifica se está no mapeamento do usuário
    if etapa_limpa in mapeamento_etapas_usuario:
        return mapeamento_etapas_usuario[etapa_limpa]
    
    # Se não encontrou, retorna UNKNOWN
    return 'UNKNOWN'

# --- Funções de Filtragem e Ordenação ---
def filtrar_etapas_nao_concluidas(df):
    if df.empty or '% concluído' not in df.columns:
        return df
    
    df_copy = df.copy()
    df_copy['% concluído'] = df_copy['% concluído'].apply(converter_porcentagem)
    df_filtrado = df_copy[df_copy['% concluído'] < 100]
    return df_filtrado

def obter_data_meta_assinatura(df_original, empreendimento):
    df_meta = df_original[(df_original['Empreendimento'] == empreendimento) & (df_original['Etapa'] == 'DEM.MIN')]
    
    if df_meta.empty:
        return pd.Timestamp.max
    
    if pd.notna(df_meta['Termino_Prevista'].iloc[0]):
        return df_meta['Termino_Prevista'].iloc[0]
    elif pd.notna(df_meta['Inicio_Prevista'].iloc[0]):
        return df_meta['Inicio_Prevista'].iloc[0]
    elif pd.notna(df_meta['Termino_Real'].iloc[0]):
        return df_meta['Termino_Real'].iloc[0]
    elif pd.notna(df_meta['Inicio_Real'].iloc[0]):
        return df_meta['Inicio_Real'].iloc[0]
    else:
        return pd.Timestamp.max

def criar_ordenacao_empreendimentos(df_original):
    empreendimentos_meta = {}
    
    for empreendimento in df_original['Empreendimento'].unique():
        data_meta = obter_data_meta_assinatura(df_original, empreendimento)
        empreendimentos_meta[empreendimento] = data_meta
    
    empreendimentos_ordenados = sorted(
        empreendimentos_meta.keys(),
        key=lambda x: empreendimentos_meta[x]
    )
    
    return empreendimentos_ordenados

def aplicar_ordenacao_final(df, empreendimentos_ordenados):
    if df.empty:
        return df
    
    ordem_empreendimentos = {emp: idx for idx, emp in enumerate(empreendimentos_ordenados)}
    df['ordem_empreendimento'] = df['Empreendimento'].map(ordem_empreendimentos)
    
    ordem_etapas = {etapa: idx for idx, etapa in enumerate(sigla_para_nome_completo.keys())}
    df['ordem_etapa'] = df['Etapa'].map(ordem_etapas).fillna(len(ordem_etapas))
    
    df_ordenado = df.sort_values(['ordem_empreendimento', 'ordem_etapa']).drop(
        ['ordem_empreendimento', 'ordem_etapa'], axis=1
    )
    
    return df_ordenado.reset_index(drop=True)

# --- Funções de Geração do Gráfico ---

def gerar_gantt(df, tipo_visualizacao="Ambos", filtrar_nao_concluidas=False):
    if df.empty:
        st.warning("Sem dados disponíveis para exibir o Gantt.")
        return

    plt.rcParams['figure.dpi'] = 150
    plt.rcParams['savefig.dpi'] = 150

    df_original_completo = df.copy()

    if 'Empreendimento' in df.columns:
        df['Empreendimento'] = df['Empreendimento'].apply(abreviar_nome)
        df_original_completo['Empreendimento'] = df_original_completo['Empreendimento'].apply(abreviar_nome)

    if '% concluído' in df.columns:
        df_porcentagem = df.groupby(['Empreendimento', 'Etapa']).apply(calcular_porcentagem_correta).reset_index(name='%_corrigido')
        df = pd.merge(df, df_porcentagem, on=['Empreendimento', 'Etapa'], how='left')
        df['% concluído'] = df['%_corrigido'].fillna(0)
        df.drop('%_corrigido', axis=1, inplace=True)
    else:
        df['% concluído'] = 0.0

    for col in ['Inicio_Prevista', 'Termino_Prevista', 'Inicio_Real', 'Termino_Real']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            df_original_completo[col] = pd.to_datetime(df_original_completo[col], errors='coerce')

    empreendimentos_ordenados = criar_ordenacao_empreendimentos(df_original_completo)

    if filtrar_nao_concluidas:
        df = filtrar_etapas_nao_concluidas(df)
    
    df = aplicar_ordenacao_final(df, empreendimentos_ordenados)

    if df.empty:
        st.warning("Sem dados disponíveis para exibir o Gantt após a filtragem.")
        return

    num_empreendimentos = df['Empreendimento'].nunique()
    num_etapas = df['Etapa'].nunique()

    # REGRA ESPECÍFICA: Quando há múltiplos empreendimentos e apenas uma etapa
    if num_empreendimentos > 1 and num_etapas == 1:
        # Para este caso especial, geramos apenas UM gráfico comparativo
        gerar_gantt_comparativo(df, tipo_visualizacao, df_original_completo)
    elif num_empreendimentos > 1 and num_etapas > 1:
        # Caso tradicional: múltiplos empreendimentos com múltiplas etapas
        for empreendimento in empreendimentos_ordenados:
            if empreendimento in df['Empreendimento'].unique():
                # REMOVIDO: st.subheader(f"Empreendimento: {empreendimento.replace('CONDOMINIO ', '')}")
                df_filtrado = df[df['Empreendimento'] == empreendimento]
                df_original_filtrado = df_original_completo[df_original_completo['Empreendimento'] == empreendimento]
                
                gerar_gantt_individual(df_filtrado, tipo_visualizacao, df_original=df_original_filtrado)
                # REMOVIDO: st.markdown("---")
    else:
        # Caso único empreendimento (com uma ou múltiplas etapas)
        gerar_gantt_individual(df, tipo_visualizacao, df_original=df_original_completo)

def gerar_gantt_comparativo(df, tipo_visualizacao="Ambos", df_original=None):
    """
    Gera um gráfico Gantt comparativo para múltiplos empreendimentos com apenas uma etapa.
    Ordena os empreendimentos pela data de início e exibe em um único gráfico.
    """
    if df.empty:
        return

    if df_original is None:
        df_original = df.copy()
    
    hoje = pd.Timestamp.now()
    
    # Ordenação específica para o caso comparativo
    sort_col = 'Inicio_Real' if tipo_visualizacao == "Real" else 'Inicio_Prevista'
    df = df.sort_values(by=sort_col, ascending=True, na_position='last').reset_index(drop=True)
    
    # Configuração do mapeamento de posições
    rotulo_para_posicao = {}
    posicao = 0
    
    # Para o caso comparativo, uma linha por empreendimento
    for empreendimento in df['Empreendimento'].unique():
        rotulo_para_posicao[empreendimento] = posicao
        posicao += 1
    
    df['Posicao'] = df['Empreendimento'].map(rotulo_para_posicao)
    df.dropna(subset=['Posicao'], inplace=True)
    
    if df.empty:
        return

    # Configuração da figura
    num_linhas = len(rotulo_para_posicao)
    altura_total = max(10, num_linhas * StyleConfig.ALTURA_GANTT_POR_ITEM)
    figura = plt.figure(figsize=(StyleConfig.LARGURA_TABELA + StyleConfig.LARGURA_GANTT, altura_total))
    grade = gridspec.GridSpec(1, 2, width_ratios=[StyleConfig.LARGURA_TABELA, StyleConfig.LARGURA_GANTT], wspace=0.01)

    eixo_tabela = figura.add_subplot(grade[0], facecolor=StyleConfig.FUNDO_TABELA)
    eixo_gantt = figura.add_subplot(grade[1], sharey=eixo_tabela)
    eixo_tabela.axis('off')

    # Consolidação dos dados
    dados_consolidados = df.groupby('Posicao').agg({
        'Empreendimento': 'first', 'Etapa': 'first',
        'Inicio_Prevista': 'min', 'Termino_Prevista': 'max',
        'Inicio_Real': 'min', 'Termino_Real': 'max',
        '% concluído': 'max'
    }).reset_index()

    # Desenho da tabela
    for _, linha in dados_consolidados.iterrows():
        y_pos = linha['Posicao']
        
        estilo_celula = StyleConfig.CELULA_PAR if int(y_pos) % 2 == 0 else StyleConfig.CELULA_IMPAR
        eixo_tabela.add_patch(Rectangle((0.01, y_pos - 0.5), 0.98, 1.0,
                             facecolor=estilo_celula["facecolor"], edgecolor=estilo_celula["edgecolor"], lw=estilo_celula["lw"]))

        # Texto principal: nome do empreendimento
        eixo_tabela.text(0.04, y_pos - 0.2, linha['Empreendimento'], va="center", ha="left", **StyleConfig.FONTE_ETAPA)
        
        # Informações de datas e dias úteis
        dias_uteis_prev = calcular_dias_uteis(linha['Inicio_Prevista'], linha['Termino_Prevista'])
        dias_uteis_real = calcular_dias_uteis(linha['Inicio_Real'], linha['Termino_Real'])
        
        texto_prev = f"Prev: {formatar_data(linha['Inicio_Prevista'])} → {formatar_data(linha['Termino_Prevista'])}-({dias_uteis_prev}d)"
        texto_real = f"Real: {formatar_data(linha['Inicio_Real'])} → {formatar_data(linha['Termino_Real'])}-({dias_uteis_real}d)"
        
        eixo_tabela.text(0.04, y_pos + 0.05, f"{texto_prev:<32}", va="center", ha="left", **StyleConfig.FONTE_DATAS)
        eixo_tabela.text(0.04, y_pos + 0.28, f"{texto_real:<32}", va="center", ha="left", **StyleConfig.FONTE_DATAS)

        # Indicador de porcentagem com cores
        percentual = linha['% concluído']
        termino_real = linha['Termino_Real']
        termino_previsto = linha['Termino_Prevista']
        
        cor_texto = "#000000"
        cor_caixa = estilo_celula['facecolor']
        if percentual == 100:
            if pd.notna(termino_real) and pd.notna(termino_previsto):
                if termino_real < termino_previsto:
                    cor_texto, cor_caixa = "#2EAF5B", "#e6f5eb"
                elif termino_real > termino_previsto:
                    cor_texto, cor_caixa = "#C30202", "#fae6e6"
        elif percentual < 100:
            if pd.notna(termino_previsto) and (termino_previsto < hoje):
                cor_texto, cor_caixa = "#A38408", "#faf3d9"

        eixo_tabela.add_patch(Rectangle((0.78, y_pos - 0.2), 0.2, 0.4, facecolor=cor_caixa, edgecolor="#d1d5db", lw=0.8))
        percentual_texto = f"{percentual:.1f}%" if percentual % 1 != 0 else f"{int(percentual)}%"
        eixo_tabela.text(0.88, y_pos, percentual_texto, va="center", ha="center", color=cor_texto, **StyleConfig.FONTE_PORCENTAGEM)

        # NOVA FUNCIONALIDADE: Variação de término
        variacao_texto, variacao_cor = calcular_variacao_termino(termino_real, termino_previsto)
        eixo_tabela.text(0.88, y_pos + StyleConfig.OFFSET_VARIACAO_TERMINO, variacao_texto, va="center", ha="center",
                         color=variacao_cor, **StyleConfig.FONTE_VARIACAO)

    # Desenho das barras do Gantt
    datas_relevantes = []
    for _, linha in dados_consolidados.iterrows():
        y_pos = linha['Posicao']
        ALTURA_BARRA = StyleConfig.ALTURA_BARRA_GANTT
        ESPACAMENTO = 0 if tipo_visualizacao != "Ambos" else StyleConfig.ALTURA_BARRA_GANTT * 0.5

        # Barra prevista
        if tipo_visualizacao in ["Ambos", "Previsto"] and pd.notna(linha['Inicio_Prevista']) and pd.notna(linha['Termino_Prevista']):
            duracao = (linha['Termino_Prevista'] - linha['Inicio_Prevista']).days + 1
            eixo_gantt.barh(y=y_pos - ESPACAMENTO, width=duracao, left=linha['Inicio_Prevista'],
                            height=ALTURA_BARRA, color=StyleConfig.COR_PREVISTO, alpha=0.9,
                            antialiased=False)
            datas_relevantes.extend([linha['Inicio_Prevista'], linha['Termino_Prevista']])

        # Barra real
        if tipo_visualizacao in ["Ambos", "Real"] and pd.notna(linha['Inicio_Real']):
            termino_real = linha['Termino_Real'] if pd.notna(linha['Termino_Real']) else hoje
            duracao = (termino_real - linha['Inicio_Real']).days + 1
            eixo_gantt.barh(y=y_pos + ESPACAMENTO, width=duracao, left=linha['Inicio_Real'],
                            height=ALTURA_BARRA, color=StyleConfig.COR_REAL, alpha=0.9,
                            antialiased=False)
            datas_relevantes.extend([linha['Inicio_Real'], termino_real])

    if datas_relevantes:
        datas_validas = [pd.Timestamp(d) for d in datas_relevantes if pd.notna(d)]
        if datas_validas:
            # --- MODIFICAÇÃO: AJUSTE DO LIMITE DO EIXO X PARA INCLUIR "HOJE" ---
            data_min_do_grafico = min(datas_validas)
            data_max_do_grafico = max(datas_validas)
            
            data_min_final = min(hoje, data_min_do_grafico)
            limite_superior = max(hoje, data_max_do_grafico) + pd.Timedelta(days=90)
            
            eixo_gantt.set_xlim(left=data_min_final - pd.Timedelta(days=5), right=limite_superior)
            # --- FIM DA MODIFICAÇÃO ---
            
    if not rotulo_para_posicao:
        st.pyplot(figura)
        plt.close(figura)
        return

    max_pos = max(rotulo_para_posicao.values())
    eixo_gantt.set_ylim(max_pos + 1, -1)
    eixo_gantt.set_yticks([])
    
    for pos in rotulo_para_posicao.values():
        eixo_gantt.axhline(y=pos + 0.5, color='#dcdcdc', linestyle='-', alpha=0.7, linewidth=0.8)

    # --- MODIFICAÇÃO: LÓGICA CONDICIONAL PARA A LINHA E TEXTO "HOJE" ---
    limite_esquerdo, limite_direito = eixo_gantt.get_xlim()
    margem_fixa = pd.Timedelta(days=30)
    data_fim_projeto = max([d for d in [df['Termino_Real'].max(), df['Termino_Prevista'].max()] if pd.notna(d)], default=pd.Timestamp.min)
    
    if hoje <= data_fim_projeto + margem_fixa:
        eixo_gantt.axvline(hoje, color=StyleConfig.COR_HOJE, linestyle='--', linewidth=1.5)
        eixo_gantt.text(hoje, eixo_gantt.get_ylim()[0], 'Hoje', color=StyleConfig.COR_HOJE, fontsize=10, ha='center', va='bottom')
    else:
        eixo_gantt.axvline(limite_direito, color=StyleConfig.COR_HOJE, linestyle='--', linewidth=1.5)
        eixo_gantt.text(limite_direito, eixo_gantt.get_ylim()[1], 'Hoje >', color=StyleConfig.COR_HOJE, fontsize=10, ha='right', va='bottom')
    # --- FIM DA MODIFICAÇÃO ---

    eixo_gantt.grid(axis='x', linestyle='--', alpha=0.6)
    eixo_gantt.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    eixo_gantt.xaxis.set_major_formatter(mdates.DateFormatter('%m/%y'))
    plt.setp(eixo_gantt.get_xticklabels(), rotation=90, ha='center')

    handles_legenda = [Patch(color=StyleConfig.COR_PREVISTO, label='Previsto'), Patch(color=StyleConfig.COR_REAL, label='Real')]
    eixo_gantt.legend(handles=handles_legenda, loc='upper center', bbox_to_anchor=(1.1, 1), frameon=False, borderaxespad=0.1)

    plt.tight_layout(rect=[0, 0.03, 1, 1])
    st.pyplot(figura)
    plt.close(figura)

def gerar_gantt_individual(df, tipo_visualizacao="Ambos", df_original=None):
    """
    Gera um gráfico Gantt individual para um empreendimento ou conjunto de dados.
    """
    if df.empty:
        return

    if df_original is None:
        df_original = df.copy()
    
    hoje = pd.Timestamp.now()
    
    # Configuração do mapeamento de posições
    rotulo_para_posicao = {}
    posicao = 0
    
    num_empreendimentos = df['Empreendimento'].nunique()
    num_etapas = df['Etapa'].nunique()
    
    # Lógica de posicionamento baseada no número de empreendimentos e etapas
    if num_empreendimentos == 1 and num_etapas > 1:
        # Um empreendimento, múltiplas etapas
        for etapa in df['Etapa'].unique():
            rotulo_para_posicao[etapa] = posicao
            posicao += 1
    else:
        # Outros casos
        for _, linha in df.iterrows():
            chave = f"{linha['Empreendimento']} - {linha['Etapa']}"
            if chave not in rotulo_para_posicao:
                rotulo_para_posicao[chave] = posicao
                posicao += 1
    
    # Mapear posições no DataFrame
    if num_empreendimentos == 1 and num_etapas > 1:
        df['Posicao'] = df['Etapa'].map(rotulo_para_posicao)
    else:
        df['Posicao'] = df.apply(lambda row: rotulo_para_posicao.get(f"{row['Empreendimento']} - {row['Etapa']}", None), axis=1)
    
    df.dropna(subset=['Posicao'], inplace=True)
    
    if df.empty:
        return

    # Configuração da figura
    num_linhas = len(rotulo_para_posicao)
    altura_total = max(10, num_linhas * StyleConfig.ALTURA_GANTT_POR_ITEM)
    figura = plt.figure(figsize=(StyleConfig.LARGURA_TABELA + StyleConfig.LARGURA_GANTT, altura_total))
    grade = gridspec.GridSpec(1, 2, width_ratios=[StyleConfig.LARGURA_TABELA, StyleConfig.LARGURA_GANTT], wspace=0.01)

    eixo_tabela = figura.add_subplot(grade[0], facecolor=StyleConfig.FUNDO_TABELA)
    eixo_gantt = figura.add_subplot(grade[1], sharey=eixo_tabela)
    eixo_tabela.axis('off')

    # Consolidação dos dados
    dados_consolidados = df.groupby('Posicao').agg({
        'Empreendimento': 'first', 'Etapa': 'first',
        'Inicio_Prevista': 'min', 'Termino_Prevista': 'max',
        'Inicio_Real': 'min', 'Termino_Real': 'max',
        '% concluído': 'max'
    }).reset_index()

    # Desenho da tabela
    empreendimento_atual = None
    for _, linha in dados_consolidados.iterrows():
        y_pos = linha['Posicao']
        
        # Cabeçalho do empreendimento (se mudou)
        if linha['Empreendimento'] != empreendimento_atual and num_empreendimentos > 1:
            empreendimento_atual = linha['Empreendimento']
            nome_formatado = empreendimento_atual.replace('CONDOMINIO ', '')
            y_cabecalho = y_pos - (StyleConfig.ALTURA_GANTT_POR_ITEM / 2) - 0.2
            eixo_tabela.text(0.5, y_cabecalho, nome_formatado,
                             va="center", ha="center", bbox=StyleConfig.CABECALHO, **StyleConfig.FONTE_TITULO)

        estilo_celula = StyleConfig.CELULA_PAR if int(y_pos) % 2 == 0 else StyleConfig.CELULA_IMPAR
        eixo_tabela.add_patch(Rectangle((0.01, y_pos - 0.5), 0.98, 1.0,
                             facecolor=estilo_celula["facecolor"], edgecolor=estilo_celula["edgecolor"], lw=estilo_celula["lw"]))

        texto_principal = linha['Empreendimento'] if (num_empreendimentos > 1 and num_etapas == 1) else sigla_para_nome_completo.get(linha['Etapa'], linha['Etapa'])
        eixo_tabela.text(0.04, y_pos - 0.2, texto_principal, va="center", ha="left", **StyleConfig.FONTE_ETAPA)
        
        dias_uteis_prev = calcular_dias_uteis(linha['Inicio_Prevista'], linha['Termino_Prevista'])
        dias_uteis_real = calcular_dias_uteis(linha['Inicio_Real'], linha['Termino_Real'])
        
        texto_prev = f"Prev: {formatar_data(linha['Inicio_Prevista'])} → {formatar_data(linha['Termino_Prevista'])}-({dias_uteis_prev}d)"
        texto_real = f"Real: {formatar_data(linha['Inicio_Real'])} → {formatar_data(linha['Termino_Real'])}-({dias_uteis_real}d)"
        
        eixo_tabela.text(0.04, y_pos + 0.05, f"{texto_prev:<32}", va="center", ha="left", **StyleConfig.FONTE_DATAS)
        eixo_tabela.text(0.04, y_pos + 0.28, f"{texto_real:<32}", va="center", ha="left", **StyleConfig.FONTE_DATAS)

        percentual = linha['% concluído']
        termino_real = linha['Termino_Real']
        termino_previsto = linha['Termino_Prevista']
        
        cor_texto = "#000000"
        cor_caixa = estilo_celula['facecolor']
        if percentual == 100:
            if pd.notna(termino_real) and pd.notna(termino_previsto):
                if termino_real < termino_previsto:
                    cor_texto, cor_caixa = "#2EAF5B", "#e6f5eb"
                elif termino_real > termino_previsto:
                    cor_texto, cor_caixa = "#C30202", "#fae6e6"
        elif percentual < 100:
            if pd.notna(termino_real) and (termino_real < hoje):
                cor_texto, cor_caixa = "#A38408", "#faf3d9"

        eixo_tabela.add_patch(Rectangle((0.78, y_pos - 0.2), 0.2, 0.4, facecolor=cor_caixa, edgecolor="#d1d5db", lw=0.8))
        percentual_texto = f"{percentual:.1f}%" if percentual % 1 != 0 else f"{int(percentual)}%"
        eixo_tabela.text(0.88, y_pos, percentual_texto, va="center", ha="center", color=cor_texto, **StyleConfig.FONTE_PORCENTAGEM)

        # NOVA FUNCIONALIDADE: Variação de término
        variacao_texto, variacao_cor = calcular_variacao_termino(termino_real, termino_previsto)
        eixo_tabela.text(0.88, y_pos + StyleConfig.OFFSET_VARIACAO_TERMINO, variacao_texto, va="center", ha="center",
                         color=variacao_cor, **StyleConfig.FONTE_VARIACAO)

    datas_relevantes = []
    for _, linha in dados_consolidados.iterrows():
        y_pos = linha['Posicao']
        ALTURA_BARRA = StyleConfig.ALTURA_BARRA_GANTT
        ESPACAMENTO = 0 if tipo_visualizacao != "Ambos" else StyleConfig.ALTURA_BARRA_GANTT * 0.5

        if tipo_visualizacao in ["Ambos", "Previsto"] and pd.notna(linha['Inicio_Prevista']) and pd.notna(linha['Termino_Prevista']):
            duracao = (linha['Termino_Prevista'] - linha['Inicio_Prevista']).days + 1
            eixo_gantt.barh(y=y_pos - ESPACAMENTO, width=duracao, left=linha['Inicio_Prevista'],
                            height=ALTURA_BARRA, color=StyleConfig.COR_PREVISTO, alpha=0.9,
                            antialiased=False)
            datas_relevantes.extend([linha['Inicio_Prevista'], linha['Termino_Prevista']])

        if tipo_visualizacao in ["Ambos", "Real"] and pd.notna(linha['Inicio_Real']):
            termino_real = linha['Termino_Real'] if pd.notna(linha['Termino_Real']) else hoje
            duracao = (termino_real - linha['Inicio_Real']).days + 1
            eixo_gantt.barh(y=y_pos + ESPACAMENTO, width=duracao, left=linha['Inicio_Real'],
                            height=ALTURA_BARRA, color=StyleConfig.COR_REAL, alpha=0.9,
                            antialiased=False)
            datas_relevantes.extend([linha['Inicio_Real'], termino_real])

    if datas_relevantes:
        datas_validas = [pd.Timestamp(d) for d in datas_relevantes if pd.notna(d)]
        if datas_validas:
            # --- MODIFICAÇÃO: AJUSTE DO LIMITE DO EIXO X PARA INCLUIR "HOJE" ---
            data_min_do_grafico = min(datas_validas)
            data_max_do_grafico = max(datas_validas)
            
            data_min_final = min(hoje, data_min_do_grafico)
            limite_superior = max(hoje, data_max_do_grafico) + pd.Timedelta(days=90)
            
            eixo_gantt.set_xlim(left=data_min_final - pd.Timedelta(days=5), right=limite_superior)
            # --- FIM DA MODIFICAÇÃO ---
            
    if not rotulo_para_posicao:
        st.pyplot(figura)
        plt.close(figura)
        return

    max_pos = max(rotulo_para_posicao.values())
    eixo_gantt.set_ylim(max_pos + 1, -1)
    eixo_gantt.set_yticks([])
    
    for pos in rotulo_para_posicao.values():
        eixo_gantt.axhline(y=pos + 0.5, color='#dcdcdc', linestyle='-', alpha=0.7, linewidth=0.8)

    # --- MODIFICAÇÃO: LÓGICA CONDICIONAL PARA A LINHA E TEXTO "HOJE" ---
    limite_esquerdo, limite_direito = eixo_gantt.get_xlim()
    margem_fixa = pd.Timedelta(days=30)
    data_fim_projeto = max([d for d in [df['Termino_Real'].max(), df['Termino_Prevista'].max()] if pd.notna(d)], default=pd.Timestamp.min)
    
    if hoje <= data_fim_projeto + margem_fixa:
        eixo_gantt.axvline(hoje, color=StyleConfig.COR_HOJE, linestyle='--', linewidth=1.5)
        eixo_gantt.text(hoje, eixo_gantt.get_ylim()[0], 'Hoje', color=StyleConfig.COR_HOJE, fontsize=10, ha='center', va='bottom')
    else:
        eixo_gantt.axvline(limite_direito, color=StyleConfig.COR_HOJE, linestyle='--', linewidth=1.5)
        eixo_gantt.text(limite_direito, eixo_gantt.get_ylim()[1], 'Hoje >', color=StyleConfig.COR_HOJE, fontsize=10, ha='right', va='bottom')
    # --- FIM DA MODIFICAÇÃO ---

    if num_empreendimentos == 1 and num_etapas > 1:
        empreendimento = df["Empreendimento"].unique()[0]
        df_assinatura = df[(df["Empreendimento"] == empreendimento) & (df["Etapa"] == "DEM.MIN")]
        if not df_assinatura.empty:
            data_meta, tipo_meta = (None, "")
            if pd.notna(df_assinatura["Inicio_Prevista"].iloc[0]):
                data_meta, tipo_meta = df_assinatura["Inicio_Prevista"].iloc[0], "Prevista"
            elif pd.notna(df_assinatura["Inicio_Real"].iloc[0]):
                data_meta, tipo_meta = df_assinatura["Inicio_Real"].iloc[0], "Real"

            if data_meta is not None:
                eixo_gantt.axvline(data_meta, color=StyleConfig.COR_META_ASSINATURA, linestyle="--", linewidth=1.7, alpha=0.7)
                y_texto = eixo_gantt.get_ylim()[1] + 0.2
                eixo_gantt.text(data_meta, y_texto,
                               f"Meta Assinatura\n{tipo_meta}: {data_meta.strftime('%d/%m/%y')}",
                               color=StyleConfig.COR_META_ASSINATURA, fontsize=10, ha="center", va="top",
                               bbox=dict(facecolor="white", alpha=0.8, edgecolor=StyleConfig.COR_META_ASSINATURA, boxstyle="round,pad=0.5"))

    eixo_gantt.grid(axis='x', linestyle='--', alpha=0.6)
    eixo_gantt.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    eixo_gantt.xaxis.set_major_formatter(mdates.DateFormatter('%m/%y'))
    plt.setp(eixo_gantt.get_xticklabels(), rotation=90, ha='center')

    handles_legenda = [Patch(color=StyleConfig.COR_PREVISTO, label='Previsto'), Patch(color=StyleConfig.COR_REAL, label='Real')]
    eixo_gantt.legend(handles=handles_legenda, loc='upper center', bbox_to_anchor=(1.1, 1), frameon=False, borderaxespad=0.1)

    plt.tight_layout(rect=[0, 0.03, 1, 1])
    st.pyplot(figura)
    plt.close(figura)
    
#========================================================================================================

# --- Lógica Principal do App Streamlit ---
st.set_page_config(layout="wide", page_title="Dashboard de Gantt Comparativo")

@st.cache_data
def load_data():
    df_real = pd.DataFrame()
    df_previsto = pd.DataFrame()

    # Carregar dados reais
    if processar_cronograma:
        try:
            df_real_resultado = processar_cronograma('GRÁFICOMACROFLUXO.xlsx')
            if df_real_resultado is not None and not df_real_resultado.empty:
                df_real = df_real_resultado.copy()
                # Padronizar etapas usando o mapeamento do usuário
                df_real['Etapa'] = df_real['Etapa'].apply(padronizar_etapa)
                # Renomear colunas para compatibilidade
                df_real = df_real.rename(columns={
                    'EMP': 'Empreendimento',
                    '%_Concluido': '% concluído'
                })
                # Converter porcentagem
                if '% concluído' in df_real.columns:
                    df_real['% concluído'] = df_real['% concluído'].apply(converter_porcentagem)
                
                # Criar colunas de data baseadas no Tipo_Data e Inicio_Fim
                df_real_pivot = df_real.pivot_table(
                    index=['Empreendimento', 'Etapa', '% concluído'],
                    columns='Inicio_Fim',
                    values='Valor',
                    aggfunc='first'
                ).reset_index()
                
                # Renomear colunas
                df_real_pivot.columns.name = None
                if 'INICIO' in df_real_pivot.columns:
                    df_real_pivot = df_real_pivot.rename(columns={'INICIO': 'Inicio_Real'})
                if 'TERMINO' in df_real_pivot.columns:
                    df_real_pivot = df_real_pivot.rename(columns={'TERMINO': 'Termino_Real'})
                
                df_real = df_real_pivot
            else:
                df_real = pd.DataFrame()
                
        except Exception as e:
            st.warning(f"Erro ao carregar dados reais: {e}")
            df_real = pd.DataFrame()

    # Carregar dados previstos
    if tratar_macrofluxo:
        try:
            df_previsto_resultado = tratar_macrofluxo()
            if df_previsto_resultado is not None and not df_previsto_resultado.empty:
                df_previsto = df_previsto_resultado.copy()
                # Padronizar etapas usando o mapeamento do usuário
                df_previsto['Etapa'] = df_previsto['Etapa'].apply(padronizar_etapa)
                # Renomear colunas para compatibilidade
                df_previsto = df_previsto.rename(columns={
                    'EMP': 'Empreendimento',
                    'UGB': 'UGB'
                })
                
                # Criar pivot para separar INICIO e TERMINO
                df_previsto_pivot = df_previsto.pivot_table(
                    index=['UGB', 'Empreendimento', 'Etapa'],
                    columns='Inicio_Fim',
                    values='Valor',
                    aggfunc='first'
                ).reset_index()
                
                # Renomear colunas
                df_previsto_pivot.columns.name = None
                if 'INICIO' in df_previsto_pivot.columns:
                    df_previsto_pivot = df_previsto_pivot.rename(columns={'INICIO': 'Inicio_Prevista'})
                if 'TERMINO' in df_previsto_pivot.columns:
                    df_previsto_pivot = df_previsto_pivot.rename(columns={'TERMINO': 'Termino_Prevista'})
                
                df_previsto = df_previsto_pivot
            else:
                df_previsto = pd.DataFrame()
                
        except Exception as e:
            st.warning(f"Erro ao carregar dados previstos: {e}")
            df_previsto = pd.DataFrame()

    # Verificar se ambos os DataFrames estão vazios
    if df_real.empty and df_previsto.empty:
        st.warning("Nenhuma fonte de dados carregada. Usando dados de exemplo.")
        return criar_dados_exemplo()

    # Merge dos dados
    if not df_real.empty and not df_previsto.empty:
        # Merge baseado em UGB, Empreendimento e Etapa
        df_merged = pd.merge(
            df_previsto,
            df_real[['Empreendimento', 'Etapa', 'Inicio_Real', 'Termino_Real', '% concluído']],
            on=['Empreendimento', 'Etapa'],
            how='outer'
        )
    elif not df_previsto.empty:
        df_merged = df_previsto.copy()
        df_merged['% concluído'] = 0.0
    elif not df_real.empty:
        df_merged = df_real.copy()
        # Adicionar colunas de UGB se não existir
        if 'UGB' not in df_merged.columns:
            df_merged['UGB'] = 'UGB1'  # Valor padrão
    else:
        return criar_dados_exemplo()
    
    # Garantir que todas as colunas necessárias existam
    for col in ['UGB', 'Inicio_Prevista', 'Termino_Prevista', 'Inicio_Real', 'Termino_Real', '% concluído']:
        if col not in df_merged.columns:
            if col == 'UGB':
                df_merged[col] = 'UGB1'
            elif col == '% concluído':
                df_merged[col] = 0.0
            else:
                df_merged[col] = pd.NaT

    df_merged['% concluído'] = df_merged['% concluído'].fillna(0)
    df_merged.dropna(subset=['Empreendimento', 'Etapa'], inplace=True)
    
    return df_merged

def criar_dados_exemplo():
    dados = {
        'UGB': ['UGB1', 'UGB1', 'UGB1', 'UGB2', 'UGB2', 'UGB1'],
        'Empreendimento': ['Residencial Alfa', 'Residencial Alfa', 'Residencial Alfa', 'Condomínio Beta', 'Condomínio Beta', 'Projeto Gama'],
        'Etapa': ['PROSPEC', 'LEGVENDA', 'PULVENDA', 'PROSPEC', 'LEGVENDA', 'PROSPEC'],
        'Inicio_Prevista': pd.to_datetime(['2024-02-01', '2024-03-01', '2024-04-15', '2024-03-20', '2024-05-01', '2024-01-10']),
        'Termino_Prevista': pd.to_datetime(['2024-02-28', '2024-04-10', '2024-05-30', '2024-04-28', '2024-06-15', '2024-01-31']),
        'Inicio_Real': pd.to_datetime(['2024-02-05', '2024-03-03', pd.NaT, '2024-03-25', '2024-05-05', '2024-01-12']),
        'Termino_Real': pd.to_datetime(['2024-03-02', '2024-04-15', pd.NaT, '2024-05-05', pd.NaT, '2024-02-01']),
        '% concluído': [100, 100, 40, 100, 85, 100]
    }
    return pd.DataFrame(dados)

# --- Interface do Streamlit ---

# Verificar se o popup deve ser exibido
if show_welcome_screen():
    st.stop()  # Para a execução do resto do app enquanto o popup está ativo

# --- INÍCIO DA IMPLEMENTAÇÃO DO MENU FLUTUANTE ---
# CSS customizado
st.markdown("""
<style>
    /* Altera APENAS os checkboxes dos multiselects */
    div.stMultiSelect div[role="option"] input[type="checkbox"]:checked + div > div:first-child {
        background-color: #4a0101 !important;
        border-color: #4a0101 !important;
    }
    
    /* Cor de fundo dos itens selecionados */
    div.stMultiSelect [aria-selected="true"] {
        background-color: #f8d7da !important;
        color: #333 !important;
        border-radius: 4px;
    }
    
    /* Estilo do "×" de remoção */
    div.stMultiSelect [aria-selected="true"]::after {
        color: #4a0101 !important;
        font-weight: bold;
    }
    
    /* Espaçamento entre os filtros */
    .stSidebar .stMultiSelect, .stSidebar .stSelectbox, .stSidebar .stRadio {
        margin-bottom: 1rem;
    }
    
    /* Estilo para botões de navegação */
    .nav-button-container {
        position: fixed;
        right: 20px;
        top: 20%;
        transform: translateY(-20%);
        z-index: 80;
        background: white;
        padding: 5px;
        border-radius: 15px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
            
    /* Estilo padrão */
    .nav-link {
        display: block;
        background-color: #a6abb5;
        color: white !important;
        text-decoration: none !important;
        border-radius: 10px;
        padding: 5px 10px;
        margin: 5px 0;
        text-align: center;
        font-weight: bold;
        font-size: 14px;
        transition: all 0.3s ease;
    }
            
    /* Estilo para quando selecionado */
    .nav-link:hover {
        background-color: #ff4b4b; 
        transform: scale(1.05);
    }
</style>
""", unsafe_allow_html=True)
# --- FIM DA IMPLEMENTAÇÃO DO MENU FLUTUANTE ---

st.title("Módulo Vendas")

# Cache para melhorar performance
@st.cache_data
def get_unique_values(df, column):
    """Função para cachear valores únicos de uma coluna"""
    return sorted(df[column].dropna().unique().tolist())

@st.cache_data
def filter_dataframe(df, ugb_filter, emp_filter):
    """Função para cachear filtragem do DataFrame"""
    if not ugb_filter:
        return df.iloc[0:0]  # DataFrame vazio se nenhuma UGB selecionada
    
    df_filtered = df[df["UGB"].isin(ugb_filter)]
    
    if emp_filter:
        df_filtered = df_filtered[df_filtered["Empreendimento"].isin(emp_filter)]
    
    return df_filtered

with st.spinner('Carregando e processando dados...'):
    df_data = load_data()

if df_data is not None and not df_data.empty:
    # Logo no sidebar
    with st.sidebar:
        st.markdown("<br>", unsafe_allow_html=True)  # Espaço no topo
        
        # Centraliza a imagem
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            try:
                st.image("logoNova.png", width=200)
            except:
                st.write("Logo não encontrada")
            
        st.markdown("<br>", unsafe_allow_html=True)  # Espaço abaixo da imagem
        
        st.header("Filtros")

        # 1️⃣ Filtro UGB (Componente personalizado)
        ugb_options = get_unique_values(df_data, "UGB")
        try:
            selected_ugb = simple_multiselect_dropdown(
                label="Filtrar por UGB",
                options=ugb_options,
                key="ugb_filter",
                default_selected=ugb_options
            )
        except:
            selected_ugb = st.multiselect("Filtrar por UGB", ugb_options, default=ugb_options)
        
        # 2️⃣ Filtro Empreendimento (Componente personalizado)
        # Otimização: só calcular opções de empreendimento se UGB foi selecionada
        if selected_ugb:
            emp_options = get_unique_values(
                df_data[df_data["UGB"].isin(selected_ugb)],
                "Empreendimento"
            )
        else:
            emp_options = []
            
        try:
            selected_emp = simple_multiselect_dropdown(
                label="Filtrar por Empreendimento",
                options=emp_options,
                key="empreendimento_filter",
                default_selected=emp_options
            )
        except:
            selected_emp = st.multiselect("Filtrar por Empreendimento", emp_options, default=emp_options)
        
        # 3️⃣ Filtro Etapa
        # Usar função cacheada para filtragem
        df_filtered = filter_dataframe(df_data, selected_ugb, selected_emp)
        
        if not df_filtered.empty:
            etapas_disponiveis = get_unique_values(df_filtered, "Etapa")
            
            # Ordenar etapas se sigla_para_nome_completo estiver definido
            try:
                etapas_disponiveis = sorted(
                    etapas_disponiveis,
                    key=lambda x: list(sigla_para_nome_completo.keys()).index(x) if x in sigla_para_nome_completo else len(sigla_para_nome_completo)
                )
            except:
                pass
                
            try:
                selected_etapas = simple_multiselect_dropdown(
                    label="Filtrar por Etapa",
                    options=etapas_disponiveis,
                    key="etapa_filter",
                    default_selected=etapas_disponiveis
                )
            except:
                selected_etapas = st.multiselect("Filtrar por Etapa", etapas_disponiveis, default=etapas_disponiveis)
        else:
            selected_etapas = []

        # 4️⃣ Filtro de Visualização
        tipo_visualizacao = st.radio(
            "Tipo de Visualização:",
            ["Ambos", "Previsto", "Real"],
            index=0,
            key="tipo_visualizacao_radio"
        )

        # 5️⃣ Filtro de Etapas Não Concluídas
        filtrar_nao_concluidas = st.checkbox(
            "Mostrar apenas etapas não concluídas",
            value=False,
            key="filtrar_nao_concluidas_checkbox"
        )

    # Aplicar filtros
    if selected_ugb and selected_emp and selected_etapas:
        df_filtered = df_filtered[df_filtered["Etapa"].isin(selected_etapas)]
    else:
        df_filtered = pd.DataFrame()

    # Criar abas
    tab1, tab2 = st.tabs(["📊 Gráfico de Gantt", "📋 Tabela Detalhada"])

    with tab1:
        st.subheader("Gráfico de Gantt")
        
        if df_filtered.empty:
            st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
        else:
            gerar_gantt(df_filtered, tipo_visualizacao, filtrar_nao_concluidas)

    with tab2:
        st.subheader("Tabela Detalhada")

        if df_filtered.empty:
            st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
        else:
            # Exibir tabela simples
            df_display = df_filtered.copy()
            
            # Formatar datas
            for col in ['Inicio_Prevista', 'Termino_Prevista', 'Inicio_Real', 'Termino_Real']:
                if col in df_display.columns:
                    df_display[col] = df_display[col].dt.strftime('%d/%m/%Y').fillna('-')
            
            # Formatar porcentagem
            if '% concluído' in df_display.columns:
                df_display['% concluído'] = df_display['% concluído'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
            
            # Mapear etapas para nomes completos
            df_display['Etapa'] = df_display['Etapa'].map(sigla_para_nome_completo).fillna(df_display['Etapa'])
            
            st.dataframe(df_display, use_container_width=True)

else:
    st.error("Não foi possível carregar os dados. Verifique se os arquivos estão disponíveis.")

