import streamlit as st
import pandas as pd
import numpy as np
import matplotlib as mpl
mpl.use("agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle
from matplotlib.legend_handler import HandlerTuple
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
from datetime import datetime
from dropdown_component import simple_multiselect_dropdown
from popup import show_welcome_screen
from calculate_business_days import calculate_business_days    
import traceback

# --- Bloco de Importação de Dados ---
try:
    from tratamento_dados_reais import processar_cronograma
    from tratamento_macrofluxo import tratar_macrofluxo
except ImportError:
    st.warning("Scripts de processamento não encontrados. O app usará dados de exemplo.")
    processar_cronograma = None
    tratar_macrofluxo = None

# --- Definição dos Grupos ---
GRUPOS = {
    "PLANEJAMENTO MACROFLUXO": [
        "PROSPECÇÃO",
        "LEGALIZAÇÃO PARA VENDA",
        "PULMÃO VENDA",
    ],
    "LIMPEZA 'SUPRESSÃO'": [
        "PL.LIMP",
        "LEG.LIMP",
        "ENG. LIMP.",
        "EXECUÇÃO LIMP.",
    ],
    "TERRAPLANAGEM": [
        "PL.TER.",
        "LEG.TER.",
        "ENG. TER.",
        "EXECUÇÃO TER.",
    ],
    "INFRA INCIDENTE (SAA E SES)": [
        "PL.INFRA",
        "LEG.INFRA",
        "ENG. INFRA",
        "EXECUÇÃO INFRA",
        "ENG. PAV",
        "EXECUÇÃO PAV.",
    ],
    "PULMÃO": ["PULMÃO INFRA"],
    "RADIER": ["PL.RADIER", "LEG.RADIER", "PULMÃO RADIER", "RADIER"],
    "DEMANDA MÍNIMA": ["DEMANDA MÍNIMA"],
}

SETOR = {
    "PROSPECÇÃO": [
        "PROSPECÇÃO",
    ],
    "LEGALIZAÇÃO": [
        "LEGALIZAÇÃO PARA VENDA",
        "LEG.LIMP",
        "LEG.TER.",
        "LEG.INFRA"
    ],
    "PULMÃO": [
        "PULMÃO VENDA",
        "PULMÃO INFRA",
        "PULMÃO RADIER",
    ],
    "ENGENHARIA": [
        "PL.LIMP",
        "ENG.LIMP.",
        "PL.TER.",
        "ENG. TER.",
        "PL.INFRA",
        "ENG. INFRA",
        "ENG. PAV",
    ],
    "INFRA": [
        "EXECUÇÃO LIMP.",
        "EXECUÇÃO TER.",
        "EXECUÇÃO INFRA",
        "EXECUÇÃO PAV.",
        "PL.RADIER",
    ],
    "PRODUÇÃO": [
        "RADIER",
    ],
    "NOVOS PRODUTOS": [
        "LEG.RADIER",
    ],
    "VENDA": [
        "DEMANDA MÍNIMA",
    ],
}

# --- Mapeamentos e Padronização (MOVIDO PARA CIMA) ---
# Mapeamento fornecido pelo usuário
mapeamento_etapas_usuario = {
    "PROSPECÇÃO": "PROSPEC",
    "LEGALIZAÇÃO PARA VENDA": "LEGVENDA",
    "PULMÃO VENDA": "PULVENDA",
    "PL.LIMP": "PL.LIMP",
    "LEG.LIMP": "LEG.LIMP",
    "ENG. LIMP.": "ENG.LIMP",
    "EXECUÇÃO LIMP.": "EXECLIMP",
    "PL.TER.": "PL.TER",
    "LEG.TER.": "LEG.TER",
    "ENG. TER.": "ENG.TER",
    "EXECUÇÃO TER.": "EXECTER",
    "PL.INFRA": "PL.INFRA",
    "LEG.INFRA": "LEG.INFRA",
    "ENG. INFRA": "ENG.INFRA",
    "EXECUÇÃO INFRA": "EXECINFRA",
    "LEG.PAV": "LEG.PAV",
    "ENG. PAV": "ENG.PAV",
    "EXECUÇÃO PAV.": "EXEC.PAV",
    "PULMÃO INFRA": "PUL.INFRA",
    "PL.RADIER": "PL.RAD",
    "LEG.RADIER": "LEG.RAD",
    "RADIER": "RAD",
    "DEMANDA MÍNIMA": "DEM.MIN",
}

# Mapeamento reverso para exibição
mapeamento_reverso = {v: k for k, v in mapeamento_etapas_usuario.items()}

# Siglas para nomes completos (mantendo compatibilidade com o código original)
sigla_para_nome_completo = {
    "PROSPEC": "PROSPECÇÃO",
    "LEGVENDA": "LEGALIZAÇÃO PARA VENDA",
    "PULVENDA": "PULMÃO VENDA",
    "PL.LIMP": "PL.LIMP",
    "LEG.LIMP": "LEG.LIMP",
    "ENG.LIMP": "ENG. LIMP.",
    "EXECLIMP": "EXECUÇÃO LIMP.",
    "PL.TER": "PL.TER.",
    "LEG.TER": "LEG.TER.",
    "ENG.TER": "ENG. TER.",
    "EXECTER": "EXECUÇÃO TER.",
    "PL.INFRA": "PL.INFRA",
    "LEG.INFRA": "LEG.INFRA",
    "ENG.INFRA": "ENG. INFRA",
    "EXECINFRA": "EXECUÇÃO INFRA",
    "LEG.PAV": "LEG.PAV",
    "ENG.PAV": "ENG. PAV",
    "EXEC.PAV": "EXECUÇÃO PAV.",
    "PUL.INFRA": "PULMÃO INFRA",
    "PL.RAD": "PL.RADIER",
    "LEG.RAD": "LEG.RADIER",
    "RAD": "RADIER",
    "DEM.MIN": "DEMANDA MÍNIMA",
}

nome_completo_para_sigla = {v: k for k, v in sigla_para_nome_completo.items()}

# --- Mapa de Grupo por Etapa (similar ao FASE_POR_ETAPA) ---
GRUPO_POR_ETAPA = {}
for grupo, etapas in GRUPOS.items():
    for etapa in etapas:
        # Converter para sigla se necessário
        if etapa in mapeamento_etapas_usuario:
            sigla = mapeamento_etapas_usuario[etapa]
            GRUPO_POR_ETAPA[sigla] = grupo
        else:
            GRUPO_POR_ETAPA[etapa] = grupo

# --- Mapa de Setor por Etapa ---
SETOR_POR_ETAPA = {}
for setor, etapas in SETOR.items():
    for etapa in etapas:
        if etapa in mapeamento_etapas_usuario:
            sigla = mapeamento_etapas_usuario[etapa] #eixo_tabela
            SETOR_POR_ETAPA[sigla] = setor
        else:
            SETOR_POR_ETAPA[etapa] = setor

# --- Configurações de Estilo ---
class StyleConfig:
    LARGURA_GANTT = 10
    ALTURA_GANTT_POR_ITEM = 1
    ALTURA_BARRA_GANTT = 0.20
    LARGURA_TABELA = 5
    COR_PREVISTO = "#A8C5DA"
    COR_REAL = "#174c66"
    COR_HOJE = "red"
    COR_CONCLUIDO = "#047031"
    COR_ATRASADO = "#a83232"
    COR_META_ASSINATURA = "#8e44ad"
    FONTE_TITULO = {"size": 10, "weight": "bold", "color": "black"}
    FONTE_ETAPA = {"size": 12, "weight": "bold", "color": "#2c3e50"}
    FONTE_DATAS = {"family": "monospace", "size": 10, "color": "#2c3e50"}
    FONTE_PORCENTAGEM = {"size": 12, "weight": "bold"}
    FONTE_VARIACAO = {"size": 8, "weight": "bold"}
    CABECALHO = {"facecolor": "#2c3e50", "edgecolor": "none", "pad": 4.0, "color": "white"}
    CELULA_PAR = {"facecolor": "white", "edgecolor": "#d1d5db", "lw": 0.8}
    CELULA_IMPAR = {"facecolor": "#f1f3f5", "edgecolor": "#d1d5db", "lw": 0.8}
    FUNDO_TABELA = "#f8f9fa"
    ESPACO_ENTRE_EMPREENDIMENTOS = 1.5
    OFFSET_VARIACAO_TERMINO = 0.31  # Posição vertical variação

    CORES_POR_SETOR = {
        "PLANEJAMENTO MACROFLUXO": {"previsto": "#ffe1af", "real": "#be5900"},
        "LIMPEZA 'SUPRESSÃO'": {"previsto": "#b9ddfc", "real": "#003C6C"},
        "TERRAPLANAGEM": {"previsto": "#ebc7ef", "real": "#63006E"},
        "INFRA INCIDENTE (SAA E SES)": {"previsto": "#f8cd7c", "real": "#6C3F00"},
        "PULMÃO": {"previsto": "#bdbdbd", "real": "#3a3a3a"},
        "RADIER": {"previsto": "#c6e7c8", "real": "#014606"},
        "DEMANDA MÍNIMA": {"previsto": "#c6e7c8", "real": "#014606"}
    }

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

    nome = nome.replace("CONDOMINIO ", "")
    palavras = nome.split()

    if len(palavras) > 3:
        nome = " ".join(palavras[:3])

    return nome


def converter_porcentagem(valor):
    if pd.isna(valor) or valor == "":
        return 0.0
    if isinstance(valor, str):
        valor = (
            "".join(c for c in valor if c.isdigit() or c in [".", ","])
            .replace(",", ".")
            .strip()
        )
        if not valor:
            return 0.0
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
        if pd.isna(diferenca_dias):
            diferenca_dias = 0  # Lidar com casos em que calculate_business_days retorna NA

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
    if "% concluído" not in grupo.columns:
        return 0.0

    porcentagens = grupo["% concluído"].astype(str).apply(converter_porcentagem)
    porcentagens = porcentagens[(porcentagens >= 0) & (porcentagens <= 100)]

    if len(porcentagens) == 0:
        return 0.0

    porcentagens_validas = porcentagens[pd.notna(porcentagens)]
    if len(porcentagens_validas) == 0:
        return 0.0
    return porcentagens_validas.mean()


def padronizar_etapa(etapa_str):
    if pd.isna(etapa_str):
        return "UNKNOWN"
    etapa_limpa = str(etapa_str).strip().upper()

    # Primeiro, verifica se já está no formato de sigla
    if etapa_limpa in sigla_para_nome_completo:
        return etapa_limpa

    # Depois, verifica se está no mapeamento do usuário
    if etapa_limpa in mapeamento_etapas_usuario:
        return mapeamento_etapas_usuario[etapa_limpa]

    # Se não encontrou, retorna UNKNOWN
    return "UNKNOWN"


# --- Funções de Filtragem e Ordenação ---
def filtrar_etapas_nao_concluidas(df):
    if df.empty or "% concluído" not in df.columns:
        return df

    df_copy = df.copy()
    df_copy["% concluído"] = df_copy["% concluído"].apply(converter_porcentagem)
    df_filtrado = df_copy[df_copy["% concluído"] < 100]
    return df_filtrado


def obter_data_meta_assinatura(df_original, empreendimento):
    df_meta = df_original[
        (df_original["Empreendimento"] == empreendimento)
        & (df_original["Etapa"] == "DEM.MIN")
    ]

    if df_meta.empty:
        return pd.Timestamp.max

    if pd.notna(df_meta["Termino_Prevista"].iloc[0]):
        return df_meta["Termino_Prevista"].iloc[0]
    elif pd.notna(df_meta["Inicio_Prevista"].iloc[0]):
        return df_meta["Inicio_Prevista"].iloc[0]
    elif pd.notna(df_meta["Termino_Real"].iloc[0]):
        return df_meta["Termino_Real"].iloc[0]
    elif pd.notna(df_meta["Inicio_Real"].iloc[0]):
        return df_meta["Inicio_Real"].iloc[0]
    else:
        return pd.Timestamp.max


def criar_ordenacao_empreendimentos(df_original):
    empreendimentos_meta = {}

    for empreendimento in df_original["Empreendimento"].unique():
        data_meta = obter_data_meta_assinatura(df_original, empreendimento)
        empreendimentos_meta[empreendimento] = data_meta

    empreendimentos_ordenados = sorted(
        empreendimentos_meta.keys(), key=lambda x: empreendimentos_meta[x]
    )

    return empreendimentos_ordenados


def aplicar_ordenacao_final(df, empreendimentos_ordenados):
    if df.empty:
        return df

    ordem_empreendimentos = {emp: idx for idx, emp in enumerate(empreendimentos_ordenados)}
    df["ordem_empreendimento"] = df["Empreendimento"].map(ordem_empreendimentos)

    ordem_etapas = {etapa: idx for idx, etapa in enumerate(sigla_para_nome_completo.keys())}
    df["ordem_etapa"] = df["Etapa"].map(ordem_etapas).fillna(len(ordem_etapas))

    df_ordenado = df.sort_values(["ordem_empreendimento", "ordem_etapa"]).drop(
        ["ordem_empreendimento", "ordem_etapa"], axis=1
    )

    return df_ordenado.reset_index(drop=True)


# --- Funções de Geração do Gráfico ---
def gerar_gantt(df, tipo_visualizacao="Ambos", filtrar_nao_concluidas=False):
    if df.empty:
        st.warning("Sem dados disponíveis para exibir o Gantt.")
        return

    plt.rcParams["figure.dpi"] = 150
    plt.rcParams["savefig.dpi"] = 150

    df_original_completo = df.copy()

    if "Empreendimento" in df.columns:
        df["Empreendimento"] = df["Empreendimento"].apply(abreviar_nome)
        df_original_completo["Empreendimento"] = df_original_completo[
            "Empreendimento"
        ].apply(abreviar_nome)

    if "% concluído" in df.columns:
        df_porcentagem = (
            df.groupby(["Empreendimento", "Etapa"])
            .apply(calcular_porcentagem_correta)
            .reset_index(name="%_corrigido")
        )
        df = pd.merge(df, df_porcentagem, on=["Empreendimento", "Etapa"], how="left")
        df["% concluído"] = df["%_corrigido"].fillna(0)
        df.drop("%_corrigido", axis=1, inplace=True)
    else:
        df["% concluído"] = 0.0

    for col in ["Inicio_Prevista", "Termino_Prevista", "Inicio_Real", "Termino_Real"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            df_original_completo[col] = pd.to_datetime(df_original_completo[col], errors="coerce")

    empreendimentos_ordenados = criar_ordenacao_empreendimentos(df_original_completo)

    if filtrar_nao_concluidas:
        df = filtrar_etapas_nao_concluidas(df)

    df = aplicar_ordenacao_final(df, empreendimentos_ordenados)

    if df.empty:
        st.warning("Sem dados disponíveis para exibir o Gantt após a filtragem.")
        return

    num_empreendimentos = df["Empreendimento"].nunique()
    num_etapas = df["Etapa"].nunique()

    # REGRA ESPECÍFICA: Quando há múltiplos empreendimentos e apenas uma etapa
    if num_empreendimentos > 1 and num_etapas == 1:
        # Para este caso especial, geramos apenas UM gráfico comparativo
        gerar_gantt_comparativo(df, tipo_visualizacao, df_original_completo)
    elif num_empreendimentos > 1 and num_etapas > 1:
        # Caso tradicional: múltiplos empreendimentos com múltiplas etapas
        for empreendimento in empreendimentos_ordenados:
            if empreendimento in df["Empreendimento"].unique():
                df_filtrado = df[df["Empreendimento"] == empreendimento]
                df_original_filtrado = df_original_completo[
                    df_original_completo["Empreendimento"] == empreendimento
                ]

                gerar_gantt_individual(df_filtrado, tipo_visualizacao, df_original=df_original_filtrado)
    else:
        # Caso único empreendimento (com uma ou múltiplas etapas)
        gerar_gantt_individual(df, tipo_visualizacao, df_original=df_original_completo)

# SUBSTITUA NOVAMENTE A FUNÇÃO 'gerar_gantt_comparativo' POR ESTA VERSÃO COMPLETA
# SUBSTITUA NOVAMENTE A FUNÇÃO 'gerar_gantt_comparativo' POR ESTA
def gerar_gantt_comparativo(df, tipo_visualizacao="Ambos", df_original=None):
    """
    Gera um gráfico Gantt comparativo para múltiplos empreendimentos com apenas uma etapa.
    """
    if df.empty:
        return

    if df_original is None:
        df_original = df.copy()

    hoje = pd.Timestamp.now().normalize()

    # Ordenação específica para o caso comparativo
    sort_col = "Inicio_Real" if tipo_visualizacao == "Real" else "Inicio_Prevista"
    df = df.sort_values(by=sort_col, ascending=True, na_position="last").reset_index(drop=True)

    # Configuração do mapeamento de posições
    rotulo_para_posicao = {
        empreendimento: i
        for i, empreendimento in enumerate(df["Empreendimento"].unique())
    }
    df["Posicao"] = df["Empreendimento"].map(rotulo_para_posicao)
    df.dropna(subset=["Posicao"], inplace=True)

    if df.empty:
        return

    # Configuração da figura
    num_linhas = len(rotulo_para_posicao)
    altura_total = max(10, num_linhas * StyleConfig.ALTURA_GANTT_POR_ITEM)
    figura = plt.figure(figsize=(StyleConfig.LARGURA_TABELA + StyleConfig.LARGURA_GANTT, altura_total))
    grade = gridspec.GridSpec(1, 2, width_ratios=[StyleConfig.LARGURA_TABELA, StyleConfig.LARGURA_GANTT], wspace=0.01)

    eixo_tabela = figura.add_subplot(grade[0], facecolor=StyleConfig.FUNDO_TABELA)
    eixo_gantt = figura.add_subplot(grade[1], sharey=eixo_tabela)
    eixo_tabela.axis("off")

    # Consolidação dos dados (já remove duplicatas por natureza)
    dados_consolidados = (
        df.groupby("Posicao")
        .agg(
            Empreendimento=("Empreendimento", "first"),
            Etapa=("Etapa", "first"),
            Inicio_Prevista=("Inicio_Prevista", "min"),
            Termino_Prevista=("Termino_Prevista", "max"),
            Inicio_Real=("Inicio_Real", "min"),
            Termino_Real=("Termino_Real", "max"),
            Percentual_Concluido=("% concluído", "max"),
        )
        .reset_index()
    )
    
    # Inicializar variáveis fora do laço
    datas_relevantes = []
    ALTURA_BARRA = StyleConfig.ALTURA_BARRA_GANTT
    ESPACAMENTO = 0 if tipo_visualizacao != "Ambos" else StyleConfig.ALTURA_BARRA_GANTT * 0.5
    
    # Laço ÚNICO para desenhar TUDO (tabela e gantt)
    for _, linha in dados_consolidados.iterrows():
        y_pos = linha["Posicao"]
        
        # --- 1. Desenho da Tabela ---
        estilo_celula = StyleConfig.CELULA_PAR if int(y_pos) % 2 == 0 else StyleConfig.CELULA_IMPAR
        eixo_tabela.add_patch(
            Rectangle((0.01, y_pos - 0.5), 0.98, 1.0, **estilo_celula)
        )

        # Textos da tabela
        eixo_tabela.text(0.04, y_pos - 0.2, linha["Empreendimento"], va="center", ha="left", **StyleConfig.FONTE_ETAPA)
        
        dias_uteis_prev = calcular_dias_uteis(linha["Inicio_Prevista"], linha["Termino_Prevista"])
        dias_uteis_real = calcular_dias_uteis(linha["Inicio_Real"], linha["Termino_Real"])
        texto_prev = f"Prev: {formatar_data(linha['Inicio_Prevista'])} → {formatar_data(linha['Termino_Prevista'])}-({dias_uteis_prev}d)"
        texto_real = f"Real: {formatar_data(linha['Inicio_Real'])} → {formatar_data(linha['Termino_Real'])}-({dias_uteis_real}d)"
        eixo_tabela.text(0.04, y_pos + 0.05, f"{texto_prev:<32}", va="center", ha="left", **StyleConfig.FONTE_DATAS)
        eixo_tabela.text(0.04, y_pos + 0.28, f"{texto_real:<32}", va="center", ha="left", **StyleConfig.FONTE_DATAS)

        # Indicador de porcentagem
        percentual = linha["Percentual_Concluido"]
        termino_real_pct = linha["Termino_Real"]
        termino_previsto_pct = linha["Termino_Prevista"]
        cor_texto, cor_caixa = "#000000", estilo_celula["facecolor"]
        if percentual == 100:
            if pd.notna(termino_real_pct) and pd.notna(termino_previsto_pct):
                if termino_real_pct < termino_previsto_pct: cor_texto, cor_caixa = "#2EAF5B", "#e6f5eb"
                elif termino_real_pct > termino_previsto_pct: cor_texto, cor_caixa = "#C30202", "#fae6e6"
        elif percentual < 100:
            if pd.notna(termino_previsto_pct) and (termino_previsto_pct < hoje):
                cor_texto, cor_caixa = "#A38408", "#faf3d9"
        
        eixo_tabela.add_patch(Rectangle((0.78, y_pos - 0.2), 0.2, 0.4, facecolor=cor_caixa, edgecolor="#d1d5db", lw=0.8))
        percentual_texto = f"{percentual:.1f}%" if percentual % 1 != 0 else f"{int(percentual)}%"
        eixo_tabela.text(0.88, y_pos, percentual_texto, va="center", ha="center", color=cor_texto, **StyleConfig.FONTE_PORCENTAGEM)

        # Variação de término
        variacao_texto, variacao_cor = calcular_variacao_termino(linha["Termino_Real"], linha["Termino_Prevista"])
        propriedades_bbox = dict(
            boxstyle='square,pad=0.2',
            facecolor=estilo_celula["facecolor"],
            edgecolor='none',
            alpha=1
        )
        eixo_tabela.text(
            0.88, y_pos + StyleConfig.OFFSET_VARIACAO_TERMINO, variacao_texto,
            va="center", ha="center", color=variacao_cor,
            bbox=propriedades_bbox, zorder=10, **StyleConfig.FONTE_VARIACAO
        )

        # --- 2. Desenho do Gantt ---
        fase = GRUPO_POR_ETAPA.get(linha['Etapa'], "OUTROS")
        cor_previsto = StyleConfig.CORES_POR_SETOR.get(fase, {}).get("previsto", StyleConfig.COR_PREVISTO)
        cor_real = StyleConfig.CORES_POR_SETOR.get(fase, {}).get("real", StyleConfig.COR_REAL)
        
        if tipo_visualizacao in ["Ambos", "Previsto"] and pd.notna(linha['Inicio_Prevista']) and pd.notna(linha['Termino_Prevista']):
            duracao = (linha['Termino_Prevista'] - linha['Inicio_Prevista']).days + 1
            eixo_gantt.barh(y=y_pos - ESPACAMENTO, width=duracao, left=linha['Inicio_Prevista'], height=ALTURA_BARRA, color=cor_previsto, alpha=0.9, antialiased=False)
            datas_relevantes.extend([linha['Inicio_Prevista'], linha['Termino_Prevista']])

        if tipo_visualizacao in ["Ambos", "Real"] and pd.notna(linha['Inicio_Real']):
            termino_real_gantt = linha['Termino_Real'] if pd.notna(linha['Termino_Real']) else hoje
            duracao = (termino_real_gantt - linha['Inicio_Real']).days + 1
            eixo_gantt.barh(y=y_pos + ESPACAMENTO, width=duracao, left=linha['Inicio_Real'], height=ALTURA_BARRA, color=cor_real, alpha=0.9, antialiased=False)
            datas_relevantes.extend([linha['Inicio_Real'], termino_real_gantt])
    
    # Configuração dos eixos e finalização
    if datas_relevantes:
        datas_validas = [pd.Timestamp(d) for d in datas_relevantes if pd.notna(d)]
        if datas_validas:
            data_min_do_grafico = min(datas_validas)
            data_max_do_grafico = max(datas_validas)
            data_min_final = min(hoje, data_min_do_grafico)
            limite_superior = max(hoje, data_max_do_grafico) + pd.Timedelta(days=90)
            eixo_gantt.set_xlim(left=data_min_final - pd.Timedelta(days=5), right=limite_superior)
    
    max_pos = max(rotulo_para_posicao.values())
    eixo_gantt.set_ylim(max_pos + 0.5, -0.5)
    eixo_gantt.set_yticks([])

    for pos in rotulo_para_posicao.values():
        eixo_gantt.axhline(y=pos + 0.5, color="#dcdcdc", linestyle="-", alpha=0.7, linewidth=0.8)

    eixo_gantt.axvline(hoje, color=StyleConfig.COR_HOJE, linestyle="--", linewidth=1.5)
    eixo_gantt.text(hoje, eixo_gantt.get_ylim()[0], "Hoje", color=StyleConfig.COR_HOJE, fontsize=10, ha="center", va="bottom")
    
    eixo_gantt.grid(axis="x", linestyle="--", alpha=0.6)
    eixo_gantt.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    
    # <-- CORREÇÃO: Formato da data alterado de volta para %m/%y
    eixo_gantt.xaxis.set_major_formatter(mdates.DateFormatter("%m/%y"))
    
    plt.setp(eixo_gantt.get_xticklabels(), rotation=90, ha="right")

    # Cria os handles em pares para cada fase
    handles_legenda = []
    labels_legenda = []

    for fase in StyleConfig.CORES_POR_SETOR:
        if fase in StyleConfig.CORES_POR_SETOR:
            prev_patch = Patch(color=StyleConfig.CORES_POR_SETOR[fase]["previsto"])
            real_patch = Patch(color=StyleConfig.CORES_POR_SETOR[fase]["real"])
            handles_legenda.append((prev_patch, real_patch))
            labels_legenda.append(fase)

    # Adiciona a legenda com pares de cores (mantendo posição original)
    eixo_gantt.legend(
        handles=handles_legenda,
        labels=labels_legenda,
        handler_map={tuple: HandlerTuple(ndivide=None)},
        loc='upper center',
        bbox_to_anchor=(1.2, 1),  # Posição original ao lado do gráfico
        frameon=False,
        borderaxespad=0.1,
        fontsize=8,
        title=" Previsto | Real"
    )

    plt.tight_layout(rect=[0, 0, 1, 0.98])
    figura.suptitle(
    f"Comparativo da Etapa: {sigla_para_nome_completo.get(df['Etapa'].iloc[0], '')}", 
    fontsize=14, 
    weight='bold',
    ha='left',      # <-- Alinha o texto à esquerda
    x=0.12,         # <-- Posição horizontal (mais para a esquerda)
    y=0.90          # <-- Posição vertical (mais para baixo, perto do gráfico)
)
    st.pyplot(figura)
    plt.close(figura)

# gantts individuais 
def gerar_gantt_individual(df, tipo_visualizacao="Ambos", df_original=None):
    if df.empty:
        return

    if df_original is None:
        df_original = df.copy()

    hoje = pd.Timestamp.now().normalize()
    
    # Lógica de posicionamento
    rotulo_para_posicao = {}
    posicao = 0
    empreendimentos_unicos = df["Empreendimento"].unique()
    for emp_idx, empreendimento in enumerate(empreendimentos_unicos):
        etapas_do_empreendimento = df[df["Empreendimento"] == empreendimento]["Etapa"].unique()
        for etapa in etapas_do_empreendimento:
            rotulo = f"{empreendimento}||{etapa}"
            rotulo_para_posicao[rotulo] = posicao
            posicao += 1
        if len(empreendimentos_unicos) > 1 and emp_idx < len(empreendimentos_unicos) - 1:
            posicao += StyleConfig.ESPACO_ENTRE_EMPREENDIMENTOS / 2
    
    df["Posicao"] = (df["Empreendimento"] + "||" + df["Etapa"]).map(rotulo_para_posicao)
    df.dropna(subset=["Posicao"], inplace=True)
    if df.empty:
        return

    # Configuração da Figura
    num_linhas_reais = df["Posicao"].nunique()
    altura_total = max(10, num_linhas_reais * StyleConfig.ALTURA_GANTT_POR_ITEM)
    figura = plt.figure(figsize=(StyleConfig.LARGURA_TABELA + StyleConfig.LARGURA_GANTT, altura_total))
    grade = gridspec.GridSpec(1, 2, width_ratios=[StyleConfig.LARGURA_TABELA, StyleConfig.LARGURA_GANTT], wspace=0.01)

    eixo_tabela = figura.add_subplot(grade[0], facecolor=StyleConfig.FUNDO_TABELA)
    eixo_gantt = figura.add_subplot(grade[1], sharey=eixo_tabela)
    eixo_tabela.axis("off")

    # Consolidação dos dados
    dados_consolidados = (
        df.groupby("Posicao")
        .agg(
            Empreendimento=("Empreendimento", "first"),
            Etapa=("Etapa", "first"),
            Inicio_Prevista=("Inicio_Prevista", "min"),
            Termino_Prevista=("Termino_Prevista", "max"),
            Inicio_Real=("Inicio_Real", "min"),
            Termino_Real=("Termino_Real", "max"),
            Percentual_Concluido=("% concluído", "max"),
        )
        .reset_index()
    )

    # Inicializar variáveis fora do laço
    datas_relevantes = []
    ALTURA_BARRA = StyleConfig.ALTURA_BARRA_GANTT
    ESPACAMENTO = 0 if tipo_visualizacao != "Ambos" else StyleConfig.ALTURA_BARRA_GANTT * 0.5
    empreendimento_atual = None
    
    # Laço ÚNICO para desenhar TUDO
    for i, linha in dados_consolidados.iterrows():
        y_pos = linha["Posicao"]

        # --- 1. Desenho da Tabela e Cabeçalhos ---
        if linha["Empreendimento"] != empreendimento_atual:
            empreendimento_atual = linha["Empreendimento"]
            nome_formatado = empreendimento_atual.replace("CONDOMINIO ", "")
            y_cabecalho = y_pos - (StyleConfig.ALTURA_GANTT_POR_ITEM / 2) - 0.2
            eixo_tabela.text(0.5, y_cabecalho, nome_formatado, va="center", ha="center", bbox=StyleConfig.CABECALHO, **StyleConfig.FONTE_TITULO)
        
        estilo_celula = StyleConfig.CELULA_PAR if i % 2 == 0 else StyleConfig.CELULA_IMPAR
        eixo_tabela.add_patch(
            Rectangle((0.01, y_pos - 0.5), 0.98, 1.0, **estilo_celula)
        )
        
        texto_principal = sigla_para_nome_completo.get(linha["Etapa"], linha["Etapa"])
        eixo_tabela.text(0.04, y_pos - 0.2, texto_principal, va="center", ha="left", **StyleConfig.FONTE_ETAPA)

        dias_uteis_prev = calcular_dias_uteis(linha["Inicio_Prevista"], linha["Termino_Prevista"])
        dias_uteis_real = calcular_dias_uteis(linha["Inicio_Real"], linha["Termino_Real"])
        texto_prev = f"Prev: {formatar_data(linha['Inicio_Prevista'])} → {formatar_data(linha['Termino_Prevista'])}-({dias_uteis_prev}d)"
        texto_real = f"Real: {formatar_data(linha['Inicio_Real'])} → {formatar_data(linha['Termino_Real'])}-({dias_uteis_real}d)"
        eixo_tabela.text(0.04, y_pos + 0.05, f"{texto_prev:<32}", va="center", ha="left", **StyleConfig.FONTE_DATAS)
        eixo_tabela.text(0.04, y_pos + 0.28, f"{texto_real:<32}", va="center", ha="left", **StyleConfig.FONTE_DATAS)

        percentual = linha["Percentual_Concluido"]
        termino_real_pct = linha["Termino_Real"]
        termino_previsto_pct = linha["Termino_Prevista"]
        cor_texto, cor_caixa = "#000000", estilo_celula["facecolor"]
        if percentual == 100:
            if pd.notna(termino_real_pct) and pd.notna(termino_previsto_pct):
                if termino_real_pct < termino_previsto_pct: cor_texto, cor_caixa = "#2EAF5B", "#e6f5eb"
                elif termino_real_pct > termino_previsto_pct: cor_texto, cor_caixa = "#C30202", "#fae6e6"
        elif percentual < 100:
            if pd.notna(termino_previsto_pct) and (termino_previsto_pct < hoje):
                cor_texto, cor_caixa = "#A38408", "#faf3d9"

        eixo_tabela.add_patch(Rectangle((0.78, y_pos - 0.2), 0.2, 0.4, facecolor=cor_caixa, edgecolor="#d1d5db", lw=0.8))
        percentual_texto = f"{percentual:.1f}%" if percentual % 1 != 0 else f"{int(percentual)}%"
        eixo_tabela.text(0.88, y_pos, percentual_texto, va="center", ha="center", color=cor_texto, **StyleConfig.FONTE_PORCENTAGEM)

        variacao_texto, variacao_cor = calcular_variacao_termino(linha["Termino_Real"], linha["Termino_Prevista"])
        propriedades_bbox = dict(
            boxstyle='square,pad=0.2',
            facecolor=estilo_celula["facecolor"],
            edgecolor='none',
            alpha=1
        )
        eixo_tabela.text(
            0.88, y_pos + StyleConfig.OFFSET_VARIACAO_TERMINO, variacao_texto,
            va="center", ha="center", color=variacao_cor,
            bbox=propriedades_bbox, zorder=10, **StyleConfig.FONTE_VARIACAO
        )

        # --- 2. Desenho do Gantt ---
        fase = GRUPO_POR_ETAPA.get(linha['Etapa'], "OUTROS")
        cor_previsto = StyleConfig.CORES_POR_SETOR.get(fase, {}).get("previsto", StyleConfig.COR_PREVISTO)
        cor_real = StyleConfig.CORES_POR_SETOR.get(fase, {}).get("real", StyleConfig.COR_REAL)

        if tipo_visualizacao in ["Ambos", "Previsto"] and pd.notna(linha['Inicio_Prevista']) and pd.notna(linha['Termino_Prevista']):
            duracao = (linha['Termino_Prevista'] - linha['Inicio_Prevista']).days + 1
            eixo_gantt.barh(y=y_pos - ESPACAMENTO, width=duracao, left=linha['Inicio_Prevista'], height=ALTURA_BARRA, color=cor_previsto, alpha=0.9, antialiased=False)
            datas_relevantes.extend([linha['Inicio_Prevista'], linha['Termino_Prevista']])

        if tipo_visualizacao in ["Ambos", "Real"] and pd.notna(linha['Inicio_Real']):
            termino_real_gantt = linha['Termino_Real'] if pd.notna(linha['Termino_Real']) else hoje
            duracao = (termino_real_gantt - linha['Inicio_Real']).days + 1
            eixo_gantt.barh(y=y_pos + ESPACAMENTO, width=duracao, left=linha['Inicio_Real'], height=ALTURA_BARRA, color=cor_real, alpha=0.9, antialiased=False)
            datas_relevantes.extend([linha['Inicio_Real'], termino_real_gantt])
    
    # Configuração dos eixos e finalização
    if datas_relevantes:
        datas_validas = [pd.Timestamp(d) for d in datas_relevantes if pd.notna(d)]
        if datas_validas:
            data_min_do_grafico = min(datas_validas)
            data_max_do_grafico = max(datas_validas)
            data_min_final = min(hoje, data_min_do_grafico)
            limite_superior = max(hoje, data_max_do_grafico) + pd.Timedelta(days=90)
            eixo_gantt.set_xlim(left=data_min_final - pd.Timedelta(days=5), right=limite_superior)
    
    max_pos = max(rotulo_para_posicao.values())
    eixo_gantt.set_ylim(max_pos + 1, -1)
    eixo_gantt.set_yticks([])

    for pos in rotulo_para_posicao.values():
        eixo_gantt.axhline(y=pos + 0.5, color="#dcdcdc", linestyle="-", alpha=0.7, linewidth=0.8)

    eixo_gantt.axvline(hoje, color=StyleConfig.COR_HOJE, linestyle="--", linewidth=1.5)
    eixo_gantt.text(hoje, eixo_gantt.get_ylim()[0], "Hoje", color=StyleConfig.COR_HOJE, fontsize=10, ha="center", va="bottom")
    
    empreendimento_principal = df["Empreendimento"].unique()[0]
    data_meta = obter_data_meta_assinatura(df_original, empreendimento_principal)
    if data_meta != pd.Timestamp.max:
        eixo_gantt.axvline(data_meta, color=StyleConfig.COR_META_ASSINATURA, linestyle="--", linewidth=1.7, alpha=0.7)
        eixo_gantt.text(
            data_meta, eixo_gantt.get_ylim()[1] + 0.2, f"Meta Assinatura\n{data_meta.strftime('%d/%m/%y')}",
            color=StyleConfig.COR_META_ASSINATURA, fontsize=10, ha="center", va="top",
            bbox=dict(facecolor="white", alpha=0.8, edgecolor=StyleConfig.COR_META_ASSINATURA, boxstyle="round,pad=0.3")
        )
        
    eixo_gantt.grid(axis="x", linestyle="--", alpha=0.6)
    eixo_gantt.xaxis.set_major_locator(mdates.MonthLocator(interval=1))

    # <-- CORREÇÃO: Formato da data alterado de volta para %m/%y
    eixo_gantt.xaxis.set_major_formatter(mdates.DateFormatter("%m/%y"))

    plt.setp(eixo_gantt.get_xticklabels(), rotation=90, ha="right")

    # Cria os handles em pares para cada fase
    handles_legenda = []
    labels_legenda = []

    for fase in StyleConfig.CORES_POR_SETOR:
        if fase in StyleConfig.CORES_POR_SETOR:
            prev_patch = Patch(color=StyleConfig.CORES_POR_SETOR[fase]["previsto"])
            real_patch = Patch(color=StyleConfig.CORES_POR_SETOR[fase]["real"])
            handles_legenda.append((prev_patch, real_patch))
            labels_legenda.append(fase)

    # Adiciona a legenda com pares de cores (mantendo posição original)
    eixo_gantt.legend(
        handles=handles_legenda,
        labels=labels_legenda,
        handler_map={tuple: HandlerTuple(ndivide=None)},
        loc='upper center',
        bbox_to_anchor=(1.2, 1),  # Posição original ao lado do gráfico
        frameon=False,
        borderaxespad=0.1,
        fontsize=8,
        title=" (Previsto | Real)"
    )

    plt.tight_layout(rect=[0, 0, 1, 1])
    st.pyplot(figura)
    plt.close(figura)
# ========================================================================================================
# O RESTANTE DO CÓDIGO (LÓGICA DO STREAMLIT)
# ========================================================================================================

st.set_page_config(layout="wide", page_title="Dashboard de Gantt Comparativo")
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

@st.cache_data
def load_data():
    df_real = pd.DataFrame()
    df_previsto = pd.DataFrame()

    if processar_cronograma:
        try:
            df_real_resultado = processar_cronograma("GRÁFICO MACROFLUXO.xlsx")
            if df_real_resultado is not None and not df_real_resultado.empty:
                df_real = df_real_resultado.copy()
                df_real["Etapa"] = df_real["Etapa"].apply(padronizar_etapa)
                df_real = df_real.rename(
                    columns={"EMP": "Empreendimento", "%_Concluido": "% concluído"}
                )
                if "% concluído" in df_real.columns:
                    df_real["% concluído"] = df_real["% concluído"].apply(
                        converter_porcentagem
                    )
                df_real_pivot = (
                    df_real.pivot_table(
                        index=["Empreendimento", "Etapa", "% concluído"],
                        columns="Inicio_Fim",
                        values="Valor",
                        aggfunc="first",
                    )
                    .reset_index()
                )
                df_real_pivot.columns.name = None
                if "INICIO" in df_real_pivot.columns:
                    df_real_pivot = df_real_pivot.rename(
                        columns={"INICIO": "Inicio_Real"}
                    )
                if "TERMINO" in df_real_pivot.columns:
                    df_real_pivot = df_real_pivot.rename(
                        columns={"TERMINO": "Termino_Real"}
                    )
                df_real = df_real_pivot
            else:
                df_real = pd.DataFrame()
        except Exception as e:
            st.warning(f"Erro ao carregar dados reais: {e}")
            df_real = pd.DataFrame()

    if tratar_macrofluxo:
        try:
            df_previsto_resultado = tratar_macrofluxo()
            if df_previsto_resultado is not None and not df_previsto_resultado.empty:
                df_previsto = df_previsto_resultado.copy()
                df_previsto["Etapa"] = df_previsto["Etapa"].apply(padronizar_etapa)
                df_previsto = df_previsto.rename(
                    columns={"EMP": "Empreendimento", "UGB": "UGB"}
                )
                df_previsto_pivot = (
                    df_previsto.pivot_table(
                        index=["UGB", "Empreendimento", "Etapa"],
                        columns="Inicio_Fim",
                        values="Valor",
                        aggfunc="first",
                    )
                    .reset_index()
                )
                df_previsto_pivot.columns.name = None
                if "INICIO" in df_previsto_pivot.columns:
                    df_previsto_pivot = df_previsto_pivot.rename(
                        columns={"INICIO": "Inicio_Prevista"}
                    )
                if "TERMINO" in df_previsto_pivot.columns:
                    df_previsto_pivot = df_previsto_pivot.rename(
                        columns={"TERMINO": "Termino_Prevista"}
                    )
                df_previsto = df_previsto_pivot
            else:
                df_previsto = pd.DataFrame()
        except Exception as e:
            st.warning(f"Erro ao carregar dados previstos: {e}")
            df_previsto = pd.DataFrame()

    if df_real.empty and df_previsto.empty:
        st.warning("Nenhuma fonte de dados carregada. Usando dados de exemplo.")
        return criar_dados_exemplo()

    if not df_real.empty and not df_previsto.empty:
        df_merged = pd.merge(
            df_previsto,
            df_real[["Empreendimento", "Etapa", "Inicio_Real", "Termino_Real", "% concluído"]],
            on=["Empreendimento", "Etapa"],
            how="outer",
        )
    elif not df_previsto.empty:
        df_merged = df_previsto.copy()
        df_merged["% concluído"] = 0.0
    elif not df_real.empty:
        df_merged = df_real.copy()
        if "UGB" not in df_merged.columns:
            df_merged["UGB"] = "UGB1"
    else:
        return criar_dados_exemplo()

    for col in [
        "UGB",
        "Inicio_Prevista",
        "Termino_Prevista",
        "Inicio_Real",
        "Termino_Real",
        "% concluído",
    ]:
        if col not in df_merged.columns:
            if col == "UGB":
                df_merged[col] = "UGB1"
            elif col == "% concluído":
                df_merged[col] = 0.0
            else:
                df_merged[col] = pd.NaT

    df_merged["% concluído"] = df_merged["% concluído"].fillna(0)
    df_merged.dropna(subset=["Empreendimento", "Etapa"], inplace=True)

    # Adicionar coluna GRUPO baseada na etapa
    df_merged["GRUPO"] = df_merged["Etapa"].map(GRUPO_POR_ETAPA).fillna("Não especificado")

    # Adicionar coluna SETOR baseada na etapa
    df_merged["SETOR"] = df_merged["Etapa"].map(SETOR_POR_ETAPA).fillna("Não especificado")

    return df_merged


def criar_dados_exemplo():
    dados = {
        "UGB": ["UGB1", "UGB1", "UGB1", "UGB2", "UGB2", "UGB1"],
        "Empreendimento": [
            "Residencial Alfa",
            "Residencial Alfa",
            "Residencial Alfa",
            "Condomínio Beta",
            "Condomínio Beta",
            "Projeto Gama",
        ],
    }
    df_exemplo = pd.DataFrame(dados)
    # Adicionar coluna GRUPO
    df_exemplo["GRUPO"] = df_exemplo["Etapa"].map(GRUPO_POR_ETAPA).fillna("PLANEJAMENTO MACROFLUXO")
    return df_exemplo


# --- Funções de Cache para Performance ---
@st.cache_data
def get_unique_values(df, column):
    """Função para cachear valores únicos de uma coluna"""
    return sorted(df[column].dropna().unique().tolist())


@st.cache_data
def filter_dataframe(df, ugb_filter, emp_filter, grupo_filter, setor_filter):
    """
    Função para cachear filtragem do DataFrame (adaptada para grupos)
    """
    if not ugb_filter:
        return df.iloc[0:0]  # DataFrame vazio se nenhuma UGB selecionada

    df_filtered = df[df["UGB"].isin(ugb_filter)]

    if emp_filter:
        df_filtered = df_filtered[df_filtered["Empreendimento"].isin(emp_filter)]

    if grupo_filter:
        df_filtered = df_filtered[df_filtered["GRUPO"].isin(grupo_filter)]

    if setor_filter:
        df_filtered = df_filtered[df_filtered["SETOR"].isin(setor_filter)]

    return df_filtered


if show_welcome_screen():
    st.stop()

st.markdown(
    """
<style>
    div.stMultiSelect div[role="option"] input[type="checkbox"]:checked + div > div:first-child { background-color: #4a0101 !important; border-color: #4a0101 !important; }
    div.stMultiSelect [aria-selected="true"] { background-color: #f8d7da !important; color: #333 !important; border-radius: 4px; }
    div.stMultiSelect [aria-selected="true"]::after { color: #4a0101 !important; font-weight: bold; }
    .stSidebar .stMultiSelect, .stSidebar .stSelectbox, .stSidebar .stRadio { margin-bottom: 1rem; }
</style>
""",
    unsafe_allow_html=True,
)

# Carregamento dos dados
with st.spinner("Carregando e processando dados..."):
    df_data = load_data()

if df_data is not None and not df_data.empty:
     # Logo no sidebar
    with st.sidebar:
        st.markdown("<br>", unsafe_allow_html=True)  # Espaço no topo

        # Centraliza a imagem
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            try:
                st.image("logoNova.png", width=200)
            except FileNotFoundError:
                st.warning(
                    "Logo não encontrada. Verifique se o arquivo 'logoNova.png' está no diretório correto.")

        # 1️⃣ Filtro UGB
        ugb_options = get_unique_values(df_data, "UGB")
        selected_ugb = simple_multiselect_dropdown(
            label="Filtrar por UGB",
            options=ugb_options,
            key="ugb_filter",
            default_selected=ugb_options,
        )

        # 2️⃣ Filtro Empreendimento
        if selected_ugb:
            emp_options = get_unique_values(
                df_data[df_data["UGB"].isin(selected_ugb)], "Empreendimento"
            )
        else:
            emp_options = []

        selected_emp = simple_multiselect_dropdown(
            label="Filtrar por Empreendimento",
            options=emp_options,
            key="empreendimento_filter",
            default_selected=emp_options,
        )

        # 3️⃣ Filtro GRUPO (NOVO - igual ao filtro de FASE)
        if selected_ugb:
            # Primeiro filtra por UGB
            df_temp = df_data[df_data["UGB"].isin(selected_ugb)]

            # Depois filtra por Empreendimento se houver seleção
            if selected_emp:
                df_temp = df_temp[df_temp["Empreendimento"].isin(selected_emp)]

            grupo_options = get_unique_values(df_temp, "GRUPO")
        else:
            grupo_options = []

        selected_grupo = simple_multiselect_dropdown(
            label="Filtrar por GRUPO",
            options=grupo_options,
            key="grupo_filter",
            default_selected=grupo_options,
        )

        # 4️⃣ Filtro SETOR (NOVO - similar ao filtro de GRUPO)
        if selected_ugb:
            df_temp_setor = df_data[df_data["UGB"].isin(selected_ugb)]
            if selected_emp:
                df_temp_setor = df_temp_setor[df_temp_setor["Empreendimento"].isin(selected_emp)]
            if selected_grupo:
                df_temp_setor = df_temp_setor[df_temp_setor["GRUPO"].isin(selected_grupo)]
            setor_options = list(SETOR.keys())
        else:
            setor_options = []

        selected_setor = simple_multiselect_dropdown(
            label="Filtrar por SETOR",
            options=setor_options,
            key="setor_filter",
            default_selected=setor_options,
        )


        # 4️⃣ Filtro Etapa (agora depende também do filtro de GRUPO)
        # Aplicar todos os filtros antes de mostrar etapas
        df_temp_filtered = filter_dataframe(
            df_data, selected_ugb, selected_emp, selected_grupo, selected_setor
        )


        if not df_temp_filtered.empty:
            etapas_disponiveis = get_unique_values(df_temp_filtered, "Etapa")

            # Ordenar etapas se sigla_para_nome_completo estiver definido
            try:
                etapas_disponiveis = sorted(
                    etapas_disponiveis,
                    key=lambda x:
                        list(sigla_para_nome_completo.keys()).index(x)
                        if x in sigla_para_nome_completo
                        else 99,
                )
                etapas_para_exibir = ["Todos"] + [
                    sigla_para_nome_completo.get(e, e) for e in etapas_disponiveis
                ]
            except NameError:
                # Se sigla_para_nome_completo não estiver definido, usar as etapas como estão
                etapas_para_exibir = ["Todos"] + etapas_disponiveis
        else:
            etapas_para_exibir = ["Todos"]

        selected_etapa_nome = st.selectbox(
            "Filtrar por Etapa", options=etapas_para_exibir
        )

        # 5️⃣ Filtro de etapas não concluídas
        st.markdown("---")
        filtrar_nao_concluidas = st.checkbox(
            "Etapas não concluídas",
            value=False,
            help="Quando marcado, mostra apenas etapas com menos de 100% de conclusão",
        )

        # 6️⃣ Opção de visualização
        st.markdown("---")
        tipo_visualizacao = st.radio("Mostrar dados:", ("Ambos", "Previsto", "Real"))

    # Aplica todos os filtros finais
    df_filtered = filter_dataframe(df_data, selected_ugb, selected_emp, selected_grupo, selected_setor)


    # Aplica o filtro de etapa final
    if selected_etapa_nome != "Todos" and not df_filtered.empty:
        try:
            sigla_selecionada = nome_completo_para_sigla.get(
                selected_etapa_nome, selected_etapa_nome
            )
            df_filtered = df_filtered[df_filtered["Etapa"] == sigla_selecionada]
        except NameError:
            # Se nome_completo_para_sigla não estiver definido, usar o nome como está
            df_filtered = df_filtered[df_filtered["Etapa"] == selected_etapa_nome]

    # APLICAR NOVO FILTRO: Etapas não concluídas
    if filtrar_nao_concluidas and not df_filtered.empty:
        df_filtered = filtrar_etapas_nao_concluidas(df_filtered)

        # Mostrar informação sobre o filtro aplicado
        if not df_filtered.empty:
            total_etapas_nao_concluidas = len(df_filtered)
            st.sidebar.success(f"✅ Mostrando {total_etapas_nao_concluidas} etapas não concluídas")
        else:
            st.sidebar.info("ℹ️ Todas as etapas estão 100% concluídas")

    # Interface principal
    st.title("Macrofluxo")

    # Navegação por abas
    tab1, tab2 = st.tabs(["Gráfico de Gantt", "Tabelão Horizontal"])

#=============================================================================================================

    # --- Início do Bloco de Código Fornecido ---
    with tab1:
        # --- INÍCIO DA IMPLEMENTAÇÃO DO MENU FLUTUANTE ---
        # Botões de navegação simples usando HTML com âncoras
        st.markdown("""
        <div class="nav-button-container">
            <a href="#inicio" class="nav-link">↑</a>
            <a href="#visao-detalhada" class="nav-link">↓</a>
        </div>
        """, unsafe_allow_html=True)
        
        # Âncora para o início
        st.markdown('<div id="inicio"></div>', unsafe_allow_html=True)
        # --- FIM DA IMPLEMENTAÇÃO DO MENU FLUTUANTE ---

        st.subheader("Gantt Comparativo")
        if df_filtered.empty:
            st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
        else:
            # Passa o parâmetro filtrar_nao_concluidas para a função de Gantt
            gerar_gantt(df_filtered.copy(), tipo_visualizacao, filtrar_nao_concluidas)

        # --- INÍCIO DA IMPLEMENTAÇÃO DO MENU FLUTUANTE ---
        # Âncora para a tabela
        st.markdown('<div id="visao-detalhada"></div>', unsafe_allow_html=True)
        # --- FIM DA IMPLEMENTAÇÃO DO MENU FLUTUANTE ---
        
        st.subheader("Visão Detalhada por Empreendimento")
        if df_filtered.empty:
            st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
        else:
            # --- INÍCIO DA LÓGICA CORRIGIDA ---
            df_detalhes = df_filtered.copy()
            
            # 1. Obter a ordem correta dos empreendimentos ANTES de qualquer filtro.
            # A ordenação é baseada na data da meta de assinatura (etapa 'M').
            empreendimentos_ordenados_por_meta = criar_ordenacao_empreendimentos(df_data)
            
            # 2. Aplicar o filtro de "não concluídas" se estiver ativo.
            if filtrar_nao_concluidas:
                df_detalhes = filtrar_etapas_nao_concluidas(df_detalhes)

            # Se após o filtro o dataframe ficar vazio, exibe um aviso.
            if df_detalhes.empty:
                st.info("ℹ️ Nenhuma etapa não concluída encontrada para os filtros selecionados.")
            else:
                hoje = pd.Timestamp.now().normalize()

                # Conversão de colunas de data
                for col in ['Inicio_Prevista', 'Termino_Prevista', 'Inicio_Real', 'Termino_Real']:
                    df_detalhes[col] = pd.to_datetime(df_detalhes[col], errors='coerce')

                # Agregação de dados por empreendimento e etapa
                df_agregado = df_detalhes.groupby(['Empreendimento', 'Etapa']).agg(
                    Inicio_Prevista=('Inicio_Prevista', 'min'),
                    Termino_Prevista=('Termino_Prevista', 'max'),
                    Inicio_Real=('Inicio_Real', 'min'),
                    Termino_Real=('Termino_Real', 'max'),
                    Percentual_Concluido=('% concluído', 'max') if '% concluído' in df_detalhes.columns else ('% concluído', lambda x: 0)
                ).reset_index()

                # Converte percentual para o formato 0-100, se necessário
                if '% concluído' in df_detalhes.columns and not df_agregado.empty and df_agregado['Percentual_Concluido'].max() <= 1:
                    df_agregado['Percentual_Concluido'] *= 100

                # Cálculo da variação de término
                df_agregado['Var. Term'] = df_agregado.apply(
                    lambda row: calculate_business_days(row['Termino_Prevista'], row['Termino_Real']), axis=1
                )
                
                # 3. Aplicar a ordenação dos empreendimentos baseada na meta
                # Isso garante que a ordem dos blocos de empreendimento seja consistente.
                df_agregado['ordem_empreendimento'] = pd.Categorical(
                    df_agregado['Empreendimento'],
                    categories=empreendimentos_ordenados_por_meta,
                    ordered=True
                )
                
                # 4. Ordenar o dataframe final, respeitando a ordem dos empreendimentos e, em seguida, a ordem das etapas.
                ordem_etapas = list(sigla_para_nome_completo.keys())
                df_agregado['Etapa_Ordem'] = df_agregado['Etapa'].apply(lambda x: ordem_etapas.index(x) if x in ordem_etapas else len(ordem_etapas))
                
                df_ordenado = df_agregado.sort_values(by=['ordem_empreendimento', 'Etapa_Ordem'])

                st.write("---")

                # A lógica de exibição da tabela (hierárquica ou horizontal) permanece a mesma
                etapas_unicas = df_ordenado['Etapa'].unique()
                usar_layout_horizontal = len(etapas_unicas) == 1

                tabela_final_lista = []
                
                if usar_layout_horizontal:
                    tabela_para_processar = df_ordenado.copy()
                    tabela_para_processar['Etapa'] = tabela_para_processar['Etapa'].map(sigla_para_nome_completo)
                    tabela_final_lista.append(tabela_para_processar)
                else:
                    # Agrupa por 'ordem_empreendimento' para manter a ordem correta
                    for _, grupo in df_ordenado.groupby('ordem_empreendimento', sort=False):
                        if grupo.empty:
                            continue # Pula para o próximo grupo se estiver vazio

                        empreendimento = grupo['Empreendimento'].iloc[0]
                        
                        percentual_medio = grupo['Percentual_Concluido'].mean()
                        
                        cabecalho = pd.DataFrame([{
                            'Hierarquia': f'📂 {empreendimento}',
                            'Inicio_Prevista': grupo['Inicio_Prevista'].min(),
                            'Termino_Prevista': grupo['Termino_Prevista'].max(),
                            'Inicio_Real': grupo['Inicio_Real'].min(),
                            'Termino_Real': grupo['Termino_Real'].max(),
                            'Var. Term': grupo['Var. Term'].mean(),
                            'Percentual_Concluido': percentual_medio
                        }])
                        tabela_final_lista.append(cabecalho)

                        grupo_formatado = grupo.copy()
                        grupo_formatado['Hierarquia'] = ' &nbsp; &nbsp; ' + grupo_formatado['Etapa'].map(sigla_para_nome_completo)
                        tabela_final_lista.append(grupo_formatado)

                if not tabela_final_lista:
                    st.info("ℹ️ Nenhum dado para exibir na tabela detalhada com os filtros atuais.")
                else:
                    tabela_final = pd.concat(tabela_final_lista, ignore_index=True)

                    # A função de estilo e a exibição final permanecem as mesmas
                    def aplicar_estilo(df_para_estilo, layout_horizontal):
                        if df_para_estilo.empty:
                            return df_para_estilo.style

                        def estilo_linha(row):
                            style = [''] * len(row)
                            
                            if not layout_horizontal and 'Empreendimento / Etapa' in row and str(row['Empreendimento / Etapa']).startswith('📂'):
                                style = ['font-weight: 500; color: #000000; background-color: #F0F2F6; border-left: 4px solid #000000; padding-left: 10px;'] * len(row)
                                for i in range(1, len(style)):
                                    style[i] = "background-color: #F0F2F6;"
                                return style
                            
                            percentual = row.get('% Concluído', 0)
                            if isinstance(percentual, str) and '%' in percentual:
                                try: percentual = int(percentual.replace('%', ''))
                                except: percentual = 0

                            termino_real, termino_previsto = pd.to_datetime(row.get("Término Real"), errors='coerce'), pd.to_datetime(row.get("Término Prev."), errors='coerce')
                            cor = "#000000"
                            if percentual == 100:
                                if pd.notna(termino_real) and pd.notna(termino_previsto):
                                    if termino_real < termino_previsto: cor = "#2EAF5B"
                                    elif termino_real > termino_previsto: cor = "#C30202"
                            elif pd.notna(termino_previsto) and (termino_previsto < pd.Timestamp.now()):
                                cor = "#A38408"

                            for i, col in enumerate(df_para_estilo.columns):
                                if col in ['Início Real', 'Término Real']:
                                    style[i] = f"color: {cor};"

                            if pd.notna(row.get("Var. Term", None)):
                                val = row["Var. Term"]
                                if isinstance(val, str):
                                    try: val = int(val.split()[1]) * (-1 if '▲' in val else 1)
                                    except: val = 0
                                cor_texto = "#e74c3c" if val < 0 else "#2ecc71"
                                style[df_para_estilo.columns.get_loc("Var. Term")] = f"color: {cor_texto}; font-weight: 600; font-size: 12px; text-align: center;"
                            return style

                        styler = df_para_estilo.style.format({
                            "Início Prev.": lambda x: x.strftime("%d/%m/%Y") if pd.notna(x) else "-",
                            "Término Prev.": lambda x: x.strftime("%d/%m/%Y") if pd.notna(x) else "-",
                            "Início Real": lambda x: x.strftime("%d/%m/%Y") if pd.notna(x) else "-",
                            "Término Real": lambda x: x.strftime("%d/%m/%Y") if pd.notna(x) else "-",
                            "Var. Term": lambda x: f"{'▼' if isinstance(x, (int, float)) and x > 0 else '▲'} {abs(int(x))} dias" if pd.notna(x) else "-",
                            "% Concluído": lambda x: f"{int(x)}%" if pd.notna(x) and str(x) != 'nan' else "-"
                        }, na_rep="-")
                        
                        styler = styler.set_properties(**{'white-space': 'nowrap', 'text-overflow': 'ellipsis', 'overflow': 'hidden', 'max-width': '380px'})
                        styler = styler.apply(estilo_linha, axis=1).hide(axis="index")
                        return styler

                    st.markdown("""
                    <style>
                        .stDataFrame { width: 100%; }
                        .stDataFrame td, .stDataFrame th { white-space: nowrap !important; text-overflow: ellipsis !important; overflow: hidden !important; max-width: 380px !important; }
                    </style>
                    """, unsafe_allow_html=True)

                    colunas_rename = {
                        'Inicio_Prevista': 'Início Prev.', 'Termino_Prevista': 'Término Prev.',
                        'Inicio_Real': 'Início Real', 'Termino_Real': 'Término Real',
                        'Percentual_Concluido': '% Concluído'
                    }
                    
                    if usar_layout_horizontal:
                        colunas_rename['Empreendimento'] = 'Empreendimento'
                        colunas_rename['Etapa'] = 'Etapa'
                        colunas_para_exibir = ['Empreendimento', 'Etapa', '% Concluído', 'Início Prev.', 'Término Prev.', 'Início Real', 'Término Real', 'Var. Term']
                    else:
                        colunas_rename['Hierarquia'] = 'Empreendimento / Etapa'
                        colunas_para_exibir = ['Empreendimento / Etapa', '% Concluído', 'Início Prev.', 'Término Prev.', 'Início Real', 'Término Real', 'Var. Term']

                    tabela_para_exibir = tabela_final.rename(columns=colunas_rename)
                    
                    tabela_estilizada = aplicar_estilo(tabela_para_exibir[colunas_para_exibir], layout_horizontal=usar_layout_horizontal)
                    
                    st.markdown(tabela_estilizada.to_html(), unsafe_allow_html=True)

#========================================================================================================

    with tab2:
        st.subheader("Tabelão Horizontal")

        if df_filtered.empty:
            st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
        else:
            # --- DATA PREPARATION ---
            df_detalhes = df_filtered.copy()
            
            # CORREÇÃO: Aplicar filtragem de etapas não concluídas se necessário
            if filtrar_nao_concluidas:
                df_detalhes = filtrar_etapas_nao_concluidas(df_detalhes)
            
            hoje = pd.Timestamp.now().normalize()

            # Column renaming and cleaning
            df_detalhes = df_detalhes.rename(columns={
                'Termino_prevista': 'Termino_Prevista',
                'Termino_real': 'Termino_Real'
            })
            
            # Date conversion
            for col in ['Inicio_Prevista', 'Termino_Prevista', 'Inicio_Real', 'Termino_Real']:
                if col in df_detalhes.columns:
                    df_detalhes[col] = df_detalhes[col].replace('-', pd.NA)
                    df_detalhes[col] = pd.to_datetime(df_detalhes[col], errors='coerce')

            # Completion validation
            df_detalhes['Conclusao_Valida'] = False
            if '% concluído' in df_detalhes.columns:
                mask = (
                    (df_detalhes['% concluído'] == 100) &
                    (df_detalhes['Termino_Real'].notna()) &
                    ((df_detalhes['Termino_Prevista'].isna()) |
                    (df_detalhes['Termino_Real'] <= df_detalhes['Termino_Prevista']))
                )
                df_detalhes.loc[mask, 'Conclusao_Valida'] = True

            # --- SORTING OPTIONS ---
            st.write("---")
            col1, col2 = st.columns(2)
            
            opcoes_classificacao = {
                'Padrão (UGB, Empreendimento e Etapa)': ['UGB', 'Empreendimento', 'Etapa_Ordem'],
                'UGB (A-Z)': ['UGB'],
                'Empreendimento (A-Z)': ['Empreendimento'],
                'Data de Início Previsto (Mais antiga)': ['Inicio_Prevista'],
                'Data de Término Previsto (Mais recente)': ['Termino_Prevista'],
            }
            
            with col1:
                classificar_por = st.selectbox(
                    "Ordenar tabela por:",
                    options=list(opcoes_classificacao.keys()),
                    key="classificar_por_selectbox"
                )
                
            with col2:
                ordem = st.radio(
                    "Ordem:",
                    options=['Crescente', 'Decrescente'],
                    horizontal=True,
                    key="ordem_radio"
                )

            # NOVA ABORDAGEM: Ordenar ANTES da agregação para preservar ordem cronológica
            ordem_etapas_completas = list(sigla_para_nome_completo.keys())
            df_detalhes['Etapa_Ordem'] = df_detalhes['Etapa'].apply(
                lambda x: ordem_etapas_completas.index(x) if x in ordem_etapas_completas else len(ordem_etapas_completas)
            )
            
            # Para ordenações por data, ordenar os dados originais primeiro
            if classificar_por in ['Data de Início Previsto (Mais antiga)', 'Data de Término Previsto (Mais recente)']:
                coluna_data = 'Inicio_Prevista' if 'Início' in classificar_por else 'Termino_Prevista'
                
                # Ordenar os dados originais pela data escolhida
                df_detalhes_ordenado = df_detalhes.sort_values(
                    by=[coluna_data, 'UGB', 'Empreendimento', 'Etapa'],
                    ascending=[ordem == 'Crescente', True, True, True],
                    na_position='last'
                )
                
                # Criar um mapeamento de ordem para UGB/Empreendimento baseado na primeira ocorrência
                ordem_ugb_emp = df_detalhes_ordenado.groupby(['UGB', 'Empreendimento']).first().reset_index()
                ordem_ugb_emp = ordem_ugb_emp.sort_values(
                    by=coluna_data,
                    ascending=(ordem == 'Crescente'),
                    na_position='last'
                )
                ordem_ugb_emp['ordem_index'] = range(len(ordem_ugb_emp))
                
                # Mapear a ordem de volta para os dados originais
                df_detalhes = df_detalhes.merge(
                    ordem_ugb_emp[['UGB', 'Empreendimento', 'ordem_index']],
                    on=['UGB', 'Empreendimento'],
                    how='left'
                )
                
            # --- DATA AGGREGATION ---
            agg_dict = {
                'Inicio_Prevista': ('Inicio_Prevista', 'min'),
                'Termino_Prevista': ('Termino_Prevista', 'max'),
                'Inicio_Real': ('Inicio_Real', 'min'),
                'Termino_Real': ('Termino_Real', 'max'),
                'Concluido_Valido': ('Conclusao_Valida', 'any')
            }
            
            if '% concluído' in df_detalhes.columns:
                agg_dict['Percentual_Concluido'] = ('% concluído', 'max')
                if not df_detalhes.empty and df_detalhes['% concluído'].max() <= 1:
                    df_detalhes['% concluído'] *= 100

            # Adicionar ordem_index à agregação se existir
            if 'ordem_index' in df_detalhes.columns:
                agg_dict['ordem_index'] = ('ordem_index', 'first')

            # Aggregate data
            df_agregado = df_detalhes.groupby(['UGB', 'Empreendimento', 'Etapa']).agg(**agg_dict).reset_index()
            
            # Calculate variation
            df_agregado['Var. Term'] = df_agregado.apply(lambda row: calculate_business_days(row['Termino_Prevista'], row['Termino_Real']), axis=1)

            # Adicionar Etapa_Ordem
            df_agregado['Etapa_Ordem'] = df_agregado['Etapa'].apply(
                lambda x: ordem_etapas_completas.index(x) if x in ordem_etapas_completas else len(ordem_etapas_completas)
            )

            # Aplicar ordenação baseada na escolha do usuário
            if classificar_por in ['Data de Início Previsto (Mais antiga)', 'Data de Término Previsto (Mais recente)']:
                # Para ordenações por data, usar a ordem_index criada anteriormente
                df_ordenado = df_agregado.sort_values(
                    by=['ordem_index', 'UGB', 'Empreendimento', 'Etapa_Ordem'],
                    ascending=[True, True, True, True]
                )
            else:
                # Para outras ordenações, usar o método original
                df_ordenado = df_agregado.sort_values(
                    by=opcoes_classificacao[classificar_por],
                    ascending=(ordem == 'Crescente')
                )
            
            st.write("---")

            # --- PIVOT TABLE CREATION ---
            df_pivot = df_ordenado.pivot_table(
                index=['UGB', 'Empreendimento'],
                columns='Etapa',
                values=['Inicio_Prevista', 'Termino_Prevista', 'Inicio_Real', 'Termino_Real', 'Var. Term'],
                aggfunc='first'
            )

            # Column ordering for pivot table
            etapas_existentes_no_pivot = df_pivot.columns.get_level_values(1).unique()
            colunas_ordenadas = []
            
            for etapa in ordem_etapas_completas:
                if etapa in etapas_existentes_no_pivot:
                    for tipo in ['Inicio_Prevista', 'Termino_Prevista', 'Inicio_Real', 'Termino_Real', 'Var. Term']:
                        if (tipo, etapa) in df_pivot.columns:
                            colunas_ordenadas.append((tipo, etapa))
            
            df_final = df_pivot[colunas_ordenadas].reset_index()

            # Para ordenações por data, reordenar o df_final baseado na ordem correta
            if classificar_por in ['Data de Início Previsto (Mais antiga)', 'Data de Término Previsto (Mais recente)']:
                # Obter ordem única de UGB/Empreendimento do df_ordenado
                ordem_linhas_final = df_ordenado[['UGB', 'Empreendimento']].drop_duplicates().reset_index(drop=True)
                
                # Reordenar df_final
                df_final = df_final.set_index(['UGB', 'Empreendimento'])
                df_final = df_final.reindex(pd.MultiIndex.from_frame(ordem_linhas_final))
                df_final = df_final.reset_index()

            # --- COLUMN RENAMING FOR MULTIINDEX ---
            novos_nomes = []
            for col in df_final.columns:
                if col[0] in ['UGB', 'Empreendimento']:
                    novos_nomes.append((col[0], ''))  # Segundo nível vazio para colunas simples
                else:
                    tipo, etapa = col[0], col[1]
                    nome_etapa = sigla_para_nome_completo.get(etapa, etapa)
                    nome_tipo = {
                        'Inicio_Prevista': 'Início Prev.',
                        'Termino_Prevista': 'Término Prev.',
                        'Inicio_Real': 'Início Real',
                        'Termino_Real': 'Término Real',
                        'Var. Term': 'VarTerm'
                    }[tipo]
                    novos_nomes.append((nome_etapa, nome_tipo))
            
            df_final.columns = pd.MultiIndex.from_tuples(novos_nomes)

            # --- FORMATTING FUNCTIONS ---
            def formatar_valor(valor, tipo):
                if pd.isna(valor):
                    return "-"
                if tipo == 'data':
                    return valor.strftime("%d/%m/%Y")
                if tipo == 'variacao':
                    return f"{'▼' if valor > 0 else '▲'} {abs(int(valor))} dias"
                return str(valor)

            def determinar_cor(row, col_tuple):
                """Determina a cor baseada no status da etapa"""
                if len(col_tuple) == 2 and (col_tuple[1] in ['Início Real', 'Término Real']):
                    etapa_nome_completo = col_tuple[0]
                    etapa_sigla = nome_completo_para_sigla.get(etapa_nome_completo)
                    
                    if etapa_sigla:
                        # Busca os dados da etapa específica no df_agregado
                        etapa_data = df_agregado[
                            (df_agregado['UGB'] == row[('UGB', '')]) &
                            (df_agregado['Empreendimento'] == row[('Empreendimento', '')]) &
                            (df_agregado['Etapa'] == etapa_sigla)
                        ]
                        
                        if not etapa_data.empty:
                            etapa_data = etapa_data.iloc[0]
                            percentual = etapa_data.get('Percentual_Concluido', 0)
                            termino_real = etapa_data['Termino_Real']
                            termino_previsto = etapa_data['Termino_Prevista']
                            
                            # Verifica se está 100% concluído
                            if percentual == 100:
                                if pd.notna(termino_real) and pd.notna(termino_previsto):
                                    if termino_real < termino_previsto:
                                        return "color: #2EAF5B; font-weight: bold;"  # Concluído antes
                                    elif termino_real > termino_previsto:
                                        return "color: #C30202; font-weight: bold;"  # Concluído com atraso
                            # Verifica se está atrasado (data passou mas não está 100%)
                            elif pd.notna(termino_real) and (termino_real < hoje):
                                return "color: #A38408; font-weight: bold;"  # Aguardando atualização
                
                # Padrão para outras colunas ou casos não especificados
                return ""

            # --- DATA FORMATTING (APLICAR APENAS APÓS ORDENAÇÃO) ---
            df_formatado = df_final.copy()
            for col_tuple in df_formatado.columns:
                if len(col_tuple) == 2 and col_tuple[1] != '':  # Ignorar colunas sem segundo nível
                    if any(x in col_tuple[1] for x in ["Início Prev.", "Término Prev.", "Início Real", "Término Real"]):
                        df_formatado[col_tuple] = df_formatado[col_tuple].apply(lambda x: formatar_valor(x, "data"))
                    elif "VarTerm" in col_tuple[1]:
                        df_formatado[col_tuple] = df_formatado[col_tuple].apply(lambda x: formatar_valor(x, "variacao"))

            # --- STYLING FUNCTION ---
            def aplicar_estilos(df):
                # Cria um DataFrame de estilos vazio com as mesmas dimensões do DataFrame original
                styles = pd.DataFrame('', index=df.index, columns=df.columns)
                
                for i, row in df.iterrows():
                    # Aplicar zebra striping (cor de fundo alternada) para todas as células da linha
                    cor_fundo = "#fbfbfb" if i % 2 == 0 else '#ffffff'
                    
                    for col_tuple in df.columns:
                        # Estilo base com zebra striping
                        cell_style = f"background-color: {cor_fundo};"
                        
                        # Aplicar estilo para células de dados
                        if len(col_tuple) == 2 and col_tuple[1] != '':
                            # Dados faltantes
                            if row[col_tuple] == '-':
                                cell_style += ' color: #999999; font-style: italic;'
                            else:
                                # Aplicar cores condicionais para Início/Término Real
                                if col_tuple[1] in ['Início Real', 'Término Real']:
                                    row_dict = {('UGB', ''): row[('UGB', '')],
                                                ('Empreendimento', ''): row[('Empreendimento', '')]}
                                    cor_condicional = determinar_cor(row_dict, col_tuple)
                                    if cor_condicional:
                                        cell_style += f' {cor_condicional}'
                                
                                # Estilo para variação de prazo
                                elif 'VarTerm' in col_tuple[1]:
                                    if '▲' in str(row[col_tuple]):  # Atraso
                                        cell_style += ' color: #e74c3c; font-weight: 600;'
                                    elif '▼' in str(row[col_tuple]):  # Adiantamento
                                        cell_style += ' color: #2ecc71; font-weight: 600;'
                        else:
                            # Para colunas UGB e Empreendimento, manter apenas o fundo zebrado
                            pass
                        
                        styles.at[i, col_tuple] = cell_style
                
                return styles

            # --- TABLE STYLING ---
            header_styles = [
                # Estilo para o nível superior (etapas)
                {
                    'selector': 'th.level0',
                    'props': [
                        ('font-size', '12px'),
                        ('font-weight', 'bold'),
                        ('background-color', "#6c6d6d"),
                        ('border-bottom', '2px solid #ddd'),
                        ('text-align', 'center'),
                        ('white-space', 'nowrap')
                    ]
                },
                # Estilo para o nível inferior (tipos de data)
                {
                    'selector': 'th.level1',
                    'props': [
                        ('font-size', '11px'),
                        ('font-weight', 'normal'),
                        ('background-color', '#f8f9fa'),
                        ('text-align', 'center'),
                        ('white-space', 'nowrap')
                    ]
                },
                # Estilo para células de dados
                {
                    'selector': 'td',
                    'props': [
                        ('font-size', '12px'),
                        ('text-align', 'center'),
                        ('padding', '5px 8px'),
                        ('border', '1px solid #f0f0f0')
                    ]
                },
                # Estilo para cabeçalho das colunas UGB e Empreendimento
                {
                    'selector': 'th.col_heading.level0',
                    'props': [
                        ('font-size', '12px'),
                        ('font-weight', 'bold'),
                        ('background-color', '#6c6d6d'),
                        ('text-align', 'center')
                    ]
                }
            ]

            # Adicionar bordas entre grupos de colunas
            for i, etapa in enumerate(ordem_etapas_completas):
                if i > 0:  # Não aplicar para a primeira etapa
                    # Encontrar a primeira coluna de cada etapa
                    etapa_nome = sigla_para_nome_completo.get(etapa, etapa)
                    col_idx = next((idx for idx, col in enumerate(df_final.columns)
                                if col[0] == etapa_nome), None)
                    if col_idx:
                        header_styles.append({
                            'selector': f'th:nth-child({col_idx+1})',
                            'props': [('border-left', '2px solid #ddd')]
                        })
                        header_styles.append({
                            'selector': f'td:nth-child({col_idx+1})',
                            'props': [('border-left', '2px solid #ddd')]
                        })

            # Aplicar estilos condicionais
            styled_df = df_formatado.style.apply(aplicar_estilos, axis=None)
            styled_df = styled_df.set_table_styles(header_styles)

            # --- DISPLAY RESULTS ---
            st.dataframe(
                styled_df,
                height=min(35 * len(df_final) + 40, 600),
                hide_index=True,
                use_container_width=True
            )
            
            # Legend
            st.markdown("""<div style="margin-top: 10px; font-size: 12px; color: #555;">
                <strong>Legenda:</strong> 
                <span style="color: #2EAF5B; font-weight: bold;">■ Concluído antes do prazo</span> | 
                <span style="color: #C30202; font-weight: bold;">■ Concluído com atraso</span> | 
                <span style="color: #A38408; font-weight: bold;">■ Aguardando atualização</span> | 
                <span style="color: #000000; font-weight: bold;">■ Em andamento</span> | 
                <span style="color: #999; font-style: italic;"> - Dados não disponíveis</span>
            </div>""", unsafe_allow_html=True)
else:
    st.error("❌ Não foi possível carregar ou gerar os dados.")


