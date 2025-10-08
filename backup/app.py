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
import streamlit.components.v1 as components
import json

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
        "PROSPECÇÃO": {"previsto": "#ffdea1", "real": "#6C3F00"}, 
        "LEGALIZAÇÃO": {"previsto": "#ebc7ef", "real": "#63006E"}, #
        "PULMÃO": {"previsto": "#bdbdbd", "real": "#5f5f5f"}, #
        "ENGENHARIA": {"previsto": "#ffe1af", "real": "#be5900"}, #
        "INFRA": {"previsto": "#b9ddfc", "real": "#003C6C"}, #
        "PRODUÇÃO": {"previsto": "#5E605F", "real": "#121212"}, #
        "NOVOS PRODUTOS": {"previsto": "#9691FD", "real": "#453ECC"}, #
        "VENDA": {"previsto": "#c6e7c8", "real": "#014606"} #
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

# ==============================================================================
# # --- Funções de Geração do Gráfico ---
# ==============================================================================

def gerar_gantt(df, tipo_visualizacao="Ambos", filtrar_nao_concluidas=False):
    """
    Gera gráficos de Gantt interativos em HTML para cada empreendimento.
    """
    if df.empty:
        st.warning("Sem dados disponíveis para exibir o Gantt.")
        return

    df_original_completo = df.copy()

    if "Empreendimento" in df.columns:
        df["Empreendimento"] = df["Empreendimento"].apply(abreviar_nome)
        df_original_completo["Empreendimento"] = df_original_completo["Empreendimento"].apply(abreviar_nome)

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

    # Processar dados para formato interativo
    def converter_para_ms_date(data):
        if pd.isna(data):
            return None
        timestamp_ms = int(data.timestamp() * 1000)
        return f"/Date({timestamp_ms})/"
    
    # Agrupar por empreendimento
    for empreendimento in empreendimentos_ordenados:
        if empreendimento not in df["Empreendimento"].unique():
            continue
            
        df_emp = df[df["Empreendimento"] == empreendimento].copy()
        
        # Converter para formato JSON
        tarefas = []
        for idx, row in df_emp.iterrows():
            percent = int(row.get("% concluído", 0))
            etapa_sigla = row.get("Etapa", "")
            etapa_nome = sigla_para_nome_completo.get(etapa_sigla, etapa_sigla)
            
            tarefa = {
                "id": f"p{idx}",
                "name": etapa_nome,
                "desc": etapa_nome,
                "percent_concluido": percent,
                "inicio_previsto": converter_para_ms_date(row.get("Inicio_Prevista")),
                "termino_previsto": converter_para_ms_date(row.get("Termino_Prevista")),
                "inicio_real": converter_para_ms_date(row.get("Inicio_Real")),
                "termino_real": converter_para_ms_date(row.get("Termino_Real")),
                "assigned": ""
            }
            tarefas.append(tarefa)
        
        dados_json = json.dumps(tarefas)
        
        # Gerar HTML do gráfico
        html_gantt = gerar_html_gantt_interativo(empreendimento, dados_json, tipo_visualizacao)
        
        # Renderizar
        st.markdown(f"### 🏢 {empreendimento}")
        components.html(html_gantt, height=700, scrolling=True)
        st.markdown("---")


def gerar_html_gantt_interativo(nome_empreendimento, dados_json, tipo_visualizacao="Ambos"):
    """
    Gera o HTML completo do gráfico Gantt interativo.
    """
    
    # Mapear tipo de visualização
    tipo_viz_map = {
        "Ambos": "ambos",
        "Previsto": "previsto",
        "Real": "real"
    }
    tipo_viz_default = tipo_viz_map.get(tipo_visualizacao, "ambos")
    
    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <title>Gantt - {nome_empreendimento}</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
        .gantt-container {{ width: 100%; margin: 20px auto; background-color: #fff; font-size: 13px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); overflow: hidden; border: 1px solid #e1e5e9; position: relative; }}
        .gantt-container.fullscreen {{ position: fixed; top: 0; left: 0; width: 100vw !important; height: 100vh !important; margin: 0; border-radius: 0; z-index: 9999; }}
        .fn-gantt {{ position: relative; overflow: hidden; background-color: #fff; border-radius: 8px; }}
        .gantt-toolbar {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 12px 20px; display: flex; align-items: center; gap: 15px; color: white; font-weight: 500; }}
        .gantt-toolbar .logo {{ font-size: 18px; font-weight: bold; margin-right: 20px; }}
        .toolbar-group {{ display: flex; align-items: center; gap: 8px; }}
        .toolbar-label {{ font-size: 12px; opacity: 0.9; }}
        .toolbar-select {{ background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; outline: none; }}
        .toolbar-select option {{ background: #667eea; color: white; }}
        .fullscreen-btn {{ background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); color: white; padding: 6px 12px; border-radius: 4px; font-size: 16px; cursor: pointer; transition: all 0.2s; outline: none; margin-left: auto; }}
        .fullscreen-btn:hover {{ background: rgba(255,255,255,0.3); transform: scale(1.05); }}
        .fn-gantt-data {{ position: relative; overflow: hidden; min-height: 400px; display: flex; }}
        .fn-gantt-leftpanel {{ min-width: 500px; max-width: 1200px; background-color: #fafbfc; border-right: 1px solid #e1e5e9; overflow: hidden; flex-shrink: 0; display: flex; flex-direction: column; }}
        .gantt-header {{ display: flex; background: linear-gradient(180deg, #f8f9fa 0%, #f1f3f4 100%); border-bottom: 1px solid #e1e5e9; font-weight: 600; font-size: 11px; color: #5f6368; height: 40px; align-items: center; position: relative; }}
        .header-col {{ padding: 0 8px; display: flex; align-items: center; text-transform: uppercase; letter-spacing: 0.3px; font-size: 10px; position: relative; overflow: hidden; white-space: nowrap; }}
        .header-col.etapa {{ min-width: 100px; flex: 0 0 auto; }}
        .header-col.datas {{ min-width: 200px; flex: 0 0 auto; }}
        .header-col.status {{ min-width: 100px; flex: 0 0 auto; text-align: center; justify-content: center; }}
        .column-resizer {{ position: absolute; right: 0; top: 0; bottom: 0; width: 8px; cursor: col-resize; background: transparent; z-index: 10; transition: background-color 0.2s; }}
        .column-resizer:hover {{ background-color: rgba(102, 126, 234, 0.3); }}
        .column-resizer.resizing {{ background-color: rgba(102, 126, 234, 0.5); }}
        .fn-gantt-rows ul {{ list-style: none; margin: 0; padding: 0; }}
        .fn-gantt-rows li {{ display: flex; height: 80px; border-bottom: 1px solid #f1f3f4; background-color: #fff; transition: all 0.2s ease; align-items: center; cursor: pointer; }}
        .fn-gantt-rows li:nth-child(even) {{ background-color: #fafbfc; }}
        .fn-gantt-rows li:hover {{ background-color: #e8f0fe; }}
        .data-col {{ padding: 8px; display: flex; flex-direction: column; justify-content: center; font-size: 11px; overflow: hidden; }}
        .data-col.etapa {{ font-weight: 600; color: #202124; font-size: 13px; flex: 0 0 auto; }}
        .data-col.datas {{ color: #5f6368; font-size: 10px; line-height: 1.6; flex: 0 0 auto; }}
        .data-col.datas .linha-data {{ margin: 2px 0; font-family: 'Courier New', monospace; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .data-col.status {{ display: flex; flex-direction: column; gap: 4px; align-items: center; flex: 0 0 auto; }}
        .status-box {{ width: 90%; height: 20px; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 600; border: 1px solid; }}
        .status-verde {{ background-color: #d4edda; color: #1F8944; border-color: #c3e6cb; }}
        .status-vermelho {{ background-color: #f8d7da; color: #721c24; border-color: #f5c6cb; }}
        .status-amarelo {{ background-color: #fff3cd; color: #856404; border-color: #f9e29c; }}
        .status-cinza {{ background-color: #e9ecef; color: #495057; border-color: #ced4da; }}
        .fn-gantt-rightpanel {{ flex: 1; position: relative; overflow-x: scroll !important; overflow-y: hidden; background-color: #fff; }}
        .fn-gantt-timeline {{ background: linear-gradient(180deg, #f8f9fa 0%, #f1f3f4 100%); border-bottom: 1px solid #e1e5e9; height: 40px; position: relative; overflow: visible; display: flex; align-items: center; min-width: max-content; }}
        .timeline-date-month {{ flex: 0 0 100px; text-align: center; border-right: 1px solid #e1e5e9; font-size: 11px; font-weight: 500; color: #5f6368; height: 100%; display: flex; align-items: center; justify-content: center; text-transform: uppercase; letter-spacing: 0.3px; writing-mode: vertical-rl; text-orientation: mixed; transform: rotate(180deg); padding: 8px 0; }}
        .timeline-date-month:hover {{ background-color: rgba(255,255,255,0.5); }}
        .fn-gantt-bars ul {{ list-style: none; margin: 0; padding: 0; position: relative; min-width: max-content; background: repeating-linear-gradient(90deg, transparent, transparent 99px, #f8f9fa 99px, #f8f9fa 100px); }}
        .fn-gantt-bars li {{ height: 80px; border-bottom: 1px solid #f1f3f4; position: relative; transition: background-color 0.2s ease; }}
        .fn-gantt-bars li:nth-child(even) {{ background-color: rgba(250, 251, 252, 0.5); }}
        .fn-gantt-bars li:hover {{ background-color: rgba(232, 240, 254, 0.3); }}
        .today-line {{ position: absolute; top: 0; bottom: 0; width: 2px; background-color: #ea4335; z-index: 15; pointer-events: none; }}
        .today-line::before {{ content: ''; position: absolute; top: -5px; left: -4px; width: 10px; height: 10px; background-color: #ea4335; border-radius: 50%; }}
        .fn-gantt-bar {{ position: absolute; height: 20px; border-radius: 4px; cursor: pointer; z-index: 10; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: 0 2px 4px rgba(0,0,0,0.15); overflow: hidden; }}
        .fn-gantt-bar.previsto {{ top: 20px; background-color: #4A90E2; opacity: 0.85; }}
        .fn-gantt-bar.real {{ top: 45px; background-color: #F5A623; opacity: 0.85; }}
        .fn-gantt-bar:hover {{ transform: scale(1.02); box-shadow: 0 4px 8px rgba(0,0,0,0.25); z-index: 20; opacity: 1; }}
        .fn-gantt-barlabel {{ color: #fff; font-size: 10px; font-weight: 600; padding: 0 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 20px; text-shadow: 0 1px 2px rgba(0,0,0,0.3); }}
        .gantt-controls {{ padding: 15px 20px; background: linear-gradient(180deg, #f8f9fa 0%, #f1f3f4 100%); border-top: 1px solid #e1e5e9; display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; }}
        .control-btn {{ padding: 8px 16px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 500; transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: 0 2px 4px rgba(0,0,0,0.1); outline: none; }}
        .control-btn:hover {{ transform: translateY(-1px); box-shadow: 0 4px 8px rgba(0,0,0,0.15); }}
        .control-btn:active {{ transform: translateY(0); box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .control-btn.resetBtn {{ background: linear-gradient(135deg, #f5576c, #f093fb); }}
        .gantt-legend {{ position: absolute; top: 10px; right: 20px; background: rgba(255,255,255,0.95); padding: 8px 12px; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); font-size: 11px; z-index: 100; }}
        .legend-item {{ display: flex; align-items: center; gap: 8px; margin: 4px 0; }}
        .legend-color {{ width: 20px; height: 12px; border-radius: 2px; }}
    </style>
</head>
<body>
    <div class="gantt-container" id="ganttContainer">
        <div class="gantt-toolbar">
            <div class="logo">📊 {nome_empreendimento}</div>
            <div class="toolbar-group">
                <span class="toolbar-label">Visualização:</span>
                <select class="toolbar-select" id="viewSelect">
                    <option value="ambos" {'selected' if tipo_viz_default == 'ambos' else ''}>Ambos</option>
                    <option value="previsto" {'selected' if tipo_viz_default == 'previsto' else ''}>Previsto</option>
                    <option value="real" {'selected' if tipo_viz_default == 'real' else ''}>Real</option>
                </select>
            </div>
            <button class="fullscreen-btn" id="fullscreenBtn" title="Tela Cheia">⛶</button>
        </div>
        <div class="fn-gantt">
            <div class="fn-gantt-data">
                <div class="fn-gantt-leftpanel">
                    <div class="gantt-header">
                        <div class="header-col etapa" id="col-etapa">ETAPA<div class="column-resizer" data-column="etapa"></div></div>
                        <div class="header-col datas" id="col-datas">DATAS E DURAÇÃO<div class="column-resizer" data-column="datas"></div></div>
                        <div class="header-col status" id="col-status">STATUS</div>
                    </div>
                    <div class="fn-gantt-rows"><ul></ul></div>
                </div>
                <div class="fn-gantt-rightpanel">
                    <div class="fn-gantt-timeline"></div>
                    <div class="fn-gantt-bars"><ul></ul></div>
                    <div class="gantt-legend">
                        <div class="legend-item"><div class="legend-color" style="background-color: #4A90E2;"></div><span>Previsto</span></div>
                        <div class="legend-item"><div class="legend-color" style="background-color: #F5A623;"></div><span>Real</span></div>
                    </div>
                </div>
            </div>
        </div>
        <div class="gantt-controls">
            <button class="control-btn resetBtn">🔄 Redefinir</button>
            <button class="control-btn setToday">📅 Hoje</button>
            <button class="control-btn zoomOut">🔍➖ Zoom Out</button>
            <button class="control-btn zoomIn">🔍➕ Zoom In</button>
            <button class="control-btn prevDay">⬅️ Anterior</button>
            <button class="control-btn nextDay">➡️ Próximo</button>
        </div>
    </div>
    <script src="https://code.jquery.com/jquery-1.11.0.min.js"></script>
    <script>
    var columnWidths = {{etapa: 180, datas: 320, status: 150}};
    function initFullscreen() {{
        var $container = $('#ganttContainer'), $btn = $('#fullscreenBtn'), isFullscreen = false;
        $btn.on('click', function() {{
            if (!isFullscreen) {{
                $container.addClass('fullscreen'); $btn.html('⛶'); $btn.attr('title', 'Sair da Tela Cheia'); isFullscreen = true;
                if ($container[0].requestFullscreen) $container[0].requestFullscreen();
                else if ($container[0].webkitRequestFullscreen) $container[0].webkitRequestFullscreen();
            }} else {{
                $container.removeClass('fullscreen'); $btn.html('⛶'); $btn.attr('title', 'Tela Cheia'); isFullscreen = false;
                if (document.exitFullscreen) document.exitFullscreen();
                else if (document.webkitExitFullscreen) document.webkitExitFullscreen();
            }}
        }});
        $(document).on('fullscreenchange webkitfullscreenchange', function() {{
            if (!document.fullscreenElement && !document.webkitFullscreenElement) {{
                $container.removeClass('fullscreen'); $btn.html('⛶'); $btn.attr('title', 'Tela Cheia'); isFullscreen = false;
            }}
        }});
    }}
    function initColumnResizing() {{
        var isResizing = false, currentColumn = null, startX = 0, startWidth = 0;
        $('.column-resizer').on('mousedown', function(e) {{
            isResizing = true; currentColumn = $(this).data('column'); startX = e.pageX; startWidth = columnWidths[currentColumn];
            $(this).addClass('resizing'); $('body').css('cursor', 'col-resize'); e.preventDefault();
        }});
        $(document).on('mousemove', function(e) {{
            if (!isResizing) return;
            var diff = e.pageX - startX, newWidth = Math.max(100, startWidth + diff);
            columnWidths[currentColumn] = newWidth; updateColumnWidths();
        }});
        $(document).on('mouseup', function() {{
            if (isResizing) {{ isResizing = false; $('.column-resizer').removeClass('resizing'); $('body').css('cursor', 'default'); }}
        }});
    }}
    function updateColumnWidths() {{
        $('#col-etapa').css('width', columnWidths.etapa + 'px');
        $('#col-datas').css('width', columnWidths.datas + 'px');
        $('#col-status').css('width', columnWidths.status + 'px');
        $('.data-col.etapa').css('width', columnWidths.etapa + 'px');
        $('.data-col.datas').css('width', columnWidths.datas + 'px');
        $('.data-col.status').css('width', columnWidths.status + 'px');
        var totalWidth = columnWidths.etapa + columnWidths.datas + columnWidths.status;
        $('.fn-gantt-leftpanel').css('width', totalWidth + 'px');
    }}
    (function($) {{
        "use strict";
        function parseMsDate(msDateString) {{
            if (!msDateString) return null;
            var match = msDateString.match(/\/Date\((\d+)\)\//);
            if (match && match[1]) return new Date(parseInt(match[1]));
            return null;
        }}
        function calcularDiasUteis(dataInicio, dataFim) {{
            if (!dataInicio || !dataFim) return 0;
            var dias = 0, atual = new Date(dataInicio), fim = new Date(dataFim);
            while (atual <= fim) {{
                var diaSemana = atual.getDay();
                if (diaSemana !== 0 && diaSemana !== 6) dias++;
                atual.setDate(atual.getDate() + 1);
            }}
            return dias;
        }}
        function calcularVariacaoTermino(terminoReal, terminoPrevisto) {{
            if (!terminoReal || !terminoPrevisto) return {{ texto: 'V: -', valor: 0 }};
            var diff = Math.floor((terminoReal - terminoPrevisto) / (1000 * 60 * 60 * 24));
            if (diff === 0) return {{ texto: 'V: 0d', valor: 0 }};
            return {{ texto: 'V: ' + (diff > 0 ? '+' : '') + diff + 'd', valor: diff }};
        }}
        function calcularVariacaoDuracao(diasReal, diasPrevisto) {{
            if (!diasReal || !diasPrevisto) return {{ texto: 'D: -', valor: 0 }};
            var diff = diasReal - diasPrevisto;
            if (diff === 0) return {{ texto: 'D: 0d', valor: 0 }};
            return {{ texto: 'D: ' + (diff > 0 ? '+' : '') + diff + 'd', valor: diff }};
        }}
        function determinarStatusCor(percentual, terminoReal, terminoPrevisto) {{
            var hoje = new Date(); hoje.setHours(0, 0, 0, 0);
            var status = 'status-cinza';
            if (percentual === 100) {{
                if (terminoReal && terminoPrevisto) {{
                    if (terminoReal < terminoPrevisto) status = 'status-verde';
                    else if (terminoReal > terminoPrevisto) status = 'status-vermelho';
                }}
            }} else if (percentual > 0 && percentual < 100) {{
                if (terminoReal && terminoReal < hoje) status = 'status-amarelo';
            }}
            return status;
        }}
        $.fn.gantt = function(options) {{
            var settings = $.extend({{ source: [] }}, options);
            var data = settings.source, viewStart = new Date(), viewEnd = new Date();
            var initialViewStart, initialViewEnd, monthWidth = 100;
            var tipoVisualizacao = '{tipo_viz_default}';
            function findDateLimits() {{
                var allDates = [];
                for (var i = 0; i < data.length; i++) {{
                    var task = data[i];
                    var startPrev = parseMsDate(task.inicio_previsto), endPrev = parseMsDate(task.termino_previsto);
                    var startReal = parseMsDate(task.inicio_real), endReal = parseMsDate(task.termino_real);
                    if (startPrev) allDates.push(startPrev); if (endPrev) allDates.push(endPrev);
                    if (startReal) allDates.push(startReal); if (endReal) allDates.push(endReal);
                }}
                var validDates = allDates.filter(function(date) {{ return date !== null; }});
                if (validDates.length === 0) {{ minDate = new Date(); maxDate = new Date(); }}
                else {{ minDate = new Date(Math.min.apply(null, validDates)); maxDate = new Date(Math.max.apply(null, validDates)); }}
            }}
            var minDate, maxDate;
            findDateLimits();
            minDate.setDate(minDate.getDate() - 5); maxDate.setDate(maxDate.getDate() + 90);
            viewStart = new Date(minDate); viewEnd = new Date(maxDate);
            initialViewStart = new Date(viewStart); initialViewEnd = new Date(viewEnd);
            function formatarData(date) {{
                if (!date) return '-';
                var dia = String(date.getDate()).padStart(2, '0'), mes = String(date.getMonth() + 1).padStart(2, '0');
                var ano = String(date.getFullYear()).slice(-2);
                return dia + '/' + mes + '/' + ano;
            }}
            function renderGantt() {{
                var $leftPanel = $('.fn-gantt-leftpanel .fn-gantt-rows ul'), $rightBars = $('.fn-gantt-bars ul');
                var $timeline = $('.fn-gantt-timeline');
                $leftPanel.empty(); $rightBars.empty(); $timeline.empty();
                var totalMonths = (viewEnd.getFullYear() - viewStart.getFullYear()) * 12 + (viewEnd.getMonth() - viewStart.getMonth()) + 1;
                var totalWidth = totalMonths * monthWidth;
                $timeline.css('min-width', totalWidth + 'px'); $('.fn-gantt-bars ul').css('min-width', totalWidth + 'px');
                var currentMonth = new Date(viewStart.getFullYear(), viewStart.getMonth(), 1);
                while (currentMonth <= viewEnd) {{
                    var dateStr = String(currentMonth.getMonth() + 1).padStart(2, '0') + '/' + String(currentMonth.getFullYear()).slice(-2);
                    $timeline.append('<div class="timeline-date-month">' + dateStr + '</div>');
                    currentMonth.setMonth(currentMonth.getMonth() + 1);
                }}
                for (var i = 0; i < data.length; i++) {{
                    var task = data[i];
                    var inicioPrevisto = parseMsDate(task.inicio_previsto), terminoPrevisto = parseMsDate(task.termino_previsto);
                    var inicioReal = parseMsDate(task.inicio_real), terminoReal = parseMsDate(task.termino_real);
                    var hoje = new Date();
                    if (!terminoReal && inicioReal && task.percent_concluido > 0 && task.percent_concluido < 100) terminoReal = hoje;
                    var diasUteisPrev = calcularDiasUteis(inicioPrevisto, terminoPrevisto);
                    var diasUteisReal = calcularDiasUteis(inicioReal, terminoReal);
                    var variacaoTerm = calcularVariacaoTermino(terminoReal, terminoPrevisto);
                    var variacaoDur = calcularVariacaoDuracao(diasUteisReal, diasUteisPrev);
                    var statusCor = determinarStatusCor(task.percent_concluido, terminoReal, terminoPrevisto);
                    var $row = $('<li></li>');
                    var $colEtapa = $('<div class="data-col etapa"></div>');
                    $colEtapa.text(task.name); $row.append($colEtapa);
                    var $colDatas = $('<div class="data-col datas"></div>');
                    var textoPrev = 'Prev: ' + formatarData(inicioPrevisto) + ' → ' + formatarData(terminoPrevisto) + ' (' + diasUteisPrev + 'd)';
                    var textoReal = 'Real: ' + formatarData(inicioReal) + ' → ' + formatarData(terminoReal) + ' (' + diasUteisReal + 'd)';
                    $colDatas.append('<div class="linha-data">' + textoPrev + '</div>');
                    $colDatas.append('<div class="linha-data">' + textoReal + '</div>');
                    $row.append($colDatas);
                    var $colStatus = $('<div class="data-col status"></div>');
                    $colStatus.append('<div class="status-box ' + statusCor + '">' + task.percent_concluido + '%</div>');
                    $colStatus.append('<div class="status-box status-cinza">' + variacaoTerm.texto + '</div>');
                    $colStatus.append('<div class="status-box status-cinza">' + variacaoDur.texto + '</div>');
                    $row.append($colStatus);
                    $leftPanel.append($row);
                    var $barRow = $('<li></li>');
                    function calcularPosicaoBarra(dataInicio, dataFim) {{
                        if (!dataInicio || !dataFim) return null;
                        var startMonth = new Date(dataInicio.getFullYear(), dataInicio.getMonth(), 1);
                        var endMonth = new Date(dataFim.getFullYear(), dataFim.getMonth(), 1);
                        var leftPos = ((startMonth.getFullYear() - viewStart.getFullYear()) * 12 + (startMonth.getMonth() - viewStart.getMonth())) * monthWidth;
                        var daysInStartMonth = new Date(dataInicio.getFullYear(), dataInicio.getMonth() + 1, 0).getDate();
                        leftPos += (dataInicio.getDate() / daysInStartMonth) * monthWidth;
                        var rightPos = ((endMonth.getFullYear() - viewStart.getFullYear()) * 12 + (endMonth.getMonth() - viewStart.getMonth())) * monthWidth;
                        var daysInEndMonth = new Date(dataFim.getFullYear(), dataFim.getMonth() + 1, 0).getDate();
                        rightPos += (dataFim.getDate() / daysInEndMonth) * monthWidth;
                        return {{ left: leftPos, width: rightPos - leftPos }};
                    }}
                    if (tipoVisualizacao === 'ambos' || tipoVisualizacao === 'previsto') {{
                        var posPrevisto = calcularPosicaoBarra(inicioPrevisto, terminoPrevisto);
                        if (posPrevisto) {{
                            var $barPrevisto = $('<div class="fn-gantt-bar previsto"></div>');
                            $barPrevisto.css({{ left: posPrevisto.left + 'px', width: posPrevisto.width + 'px' }});
                            $barPrevisto.append('<span class="fn-gantt-barlabel">' + task.name + ' (Prev)</span>');
                            $barRow.append($barPrevisto);
                        }}
                    }}
                    if (tipoVisualizacao === 'ambos' || tipoVisualizacao === 'real') {{
                        var posReal = calcularPosicaoBarra(inicioReal, terminoReal);
                        if (posReal) {{
                            var $barReal = $('<div class="fn-gantt-bar real"></div>');
                            $barReal.css({{ left: posReal.left + 'px', width: posReal.width + 'px' }});
                            $barReal.append('<span class="fn-gantt-barlabel">' + task.name + ' (Real)</span>');
                            $barRow.append($barReal);
                        }}
                    }}
                    $rightBars.append($barRow);
                }}
                updateColumnWidths();
                $('.today-line').remove();
                var today = new Date(), todayMonth = new Date(today.getFullYear(), today.getMonth(), 1);
                var todayPosition = ((todayMonth.getFullYear() - viewStart.getFullYear()) * 12 + (todayMonth.getMonth() - viewStart.getMonth())) * monthWidth;
                var daysInMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0).getDate();
                todayPosition += (today.getDate() / daysInMonth) * monthWidth;
                var $todayLine = $('<div class="today-line"></div>');
                $todayLine.css('left', todayPosition + 'px');
                $('.fn-gantt-bars ul').append($todayLine);
            }}
            renderGantt();
            $(".resetBtn").on('click', function() {{ viewStart = new Date(initialViewStart); viewEnd = new Date(initialViewEnd); renderGantt(); }});
            $(".setToday").on('click', function() {{ var today = new Date(); viewStart = new Date(today.getFullYear(), today.getMonth() - 3, 1); viewEnd = new Date(today.getFullYear(), today.getMonth() + 6, 0); renderGantt(); }});
            $(".zoomIn").on('click', function() {{ var currentMonths = (viewEnd.getFullYear() - viewStart.getFullYear()) * 12 + (viewEnd.getMonth() - viewStart.getMonth()); if (currentMonths > 3) {{ viewStart.setMonth(viewStart.getMonth() + 1); viewEnd.setMonth(viewEnd.getMonth() - 1); renderGantt(); }} }});
            $(".zoomOut").on('click', function() {{ viewStart.setMonth(viewStart.getMonth() - 1); viewEnd.setMonth(viewEnd.getMonth() + 1); renderGantt(); }});
            $(".prevDay").on('click', function() {{ viewStart.setMonth(viewStart.getMonth() - 1); viewEnd.setMonth(viewEnd.getMonth() - 1); renderGantt(); }});
            $(".nextDay").on('click', function() {{ viewStart.setMonth(viewStart.getMonth() + 1); viewEnd.setMonth(viewEnd.getMonth() + 1); renderGantt(); }});
            $("#viewSelect").on('change', function() {{ tipoVisualizacao = $(this).val(); renderGantt(); }});
        }};
    }})(jQuery);
    $(document).ready(function() {{
        $(".fn-gantt").gantt({{ source: {dados_json} }});
        setTimeout(function() {{ initColumnResizing(); initFullscreen(); }}, 100);
    }});
    </script>
</body>
</html>
"""


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

