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
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta # <-- IMPORTANTE: ADICIONAR ESTA LINHA
from dropdown_component import simple_multiselect_dropdown
from popup import show_welcome_screen
from calculate_business_days import calculate_business_days
import traceback
import streamlit.components.v1 as components
import json
import random

# --- Bloco de Importação de Dados ---
try:
    from tratamento_dados_reais import processar_cronograma
    from tratamento_macrofluxo import tratar_macrofluxo
except ImportError:
    st.warning("Scripts de processamento não encontrados. O app usará dados de exemplo.")
    processar_cronograma = None
    tratar_macrofluxo = None

# --- ORDEM DAS ETAPAS (DEFINIDA PELO USUÁRIO) ---
ORDEM_ETAPAS_GLOBAL = [
    "PROSPEC", "LEGVENDA", "PULVENDA", "PL.LIMP", "LEG.LIMP", "ENG.LIMP", "EXECLIMP",
    "PL.TER", "LEG.TER", "ENG. TER.", "EXECTER", "PL.INFRA", "LEG.INFRA", "ENG.INFRA",
    "EXECINFRA", "ENG.PAV", "EXEC.PAV", "PUL.INFRA", "PL.RAD", "LEG.RAD", "PUL.RAD",
    "RAD", "DEM.MIN",
]

# --- Definição dos Grupos ---
GRUPOS = {
    "PLANEJAMENTO MACROFLUXO": ["PROSPECÇÃO", "LEGALIZAÇÃO PARA VENDA", "PULMÃO VENDA"],
    "LIMPEZA 'SUPRESSÃO'": ["PL.LIMP", "LEG.LIMP", "ENG. LIMP.", "EXECUÇÃO LIMP."],
    "TERRAPLANAGEM": ["PL.TER.", "LEG.TER.", "ENG. TER.", "EXECUÇÃO TER."],
    "INFRA INCIDENTE (SAA E SES)": [
        "PL.INFRA", "LEG.INFRA", "ENG. INFRA", "EXECUÇÃO INFRA", "ENG. PAV", "EXECUÇÃO PAV."
    ],
    "PULMÃO": ["PULMÃO INFRA"],
    "RADIER": ["PL.RADIER", "LEG.RADIER", "PULMÃO RADIER", "RADIER"],
    "DEMANDA MÍNIMA": ["DEMANDA MÍNIMA"],
}

SETOR = {
    "PROSPECÇÃO": ["PROSPECÇÃO"],
    "LEGALIZAÇÃO": [
        "LEGALIZAÇÃO PARA VENDA", "LEG.LIMP", "LEG.TER.", "LEG.INFRA"
    ],
    "PULMÃO": ["PULMÃO VENDA", "PULMÃO INFRA", "PULMÃO RADIER"],
    "ENGENHARIA": [
        "PL.LIMP", "ENG. LIMP.", "PL.TER.", "ENG. TER.", "PL.INFRA", "ENG. INFRA", "ENG. PAV"
    ],
    "INFRA": [
        "EXECUÇÃO LIMP.", "EXECUÇÃO TER.", "EXECUÇÃO INFRA", "EXECUÇÃO PAV.", "PL.RADIER"
    ],
    "PRODUÇÃO": ["RADIER"],
    "NOVOS PRODUTOS": ["LEG.RADIER"],
    "VENDA": ["DEMANDA MÍNIMA"],
}

# --- Mapeamentos e Padronização ---
mapeamento_etapas_usuario = {
    "PROSPECÇÃO": "PROSPEC", "LEGALIZAÇÃO PARA VENDA": "LEGVENDA", "PULMÃO VENDA": "PULVENDA",
    "PL.LIMP": "PL.LIMP", "LEG.LIMP": "LEG.LIMP", "ENG. LIMP.": "ENG.LIMP",
    "EXECUÇÃO LIMP.": "EXECLIMP", "PL.TER.": "PL.TER", "LEG.TER.": "LEG.TER",
    "ENG. TER.": "ENG. TER", "EXECUÇÃO TER.": "EXECTER", "PL.INFRA": "PL.INFRA",
    "LEG.INFRA": "LEG.INFRA", "ENG. INFRA": "ENG.INFRA", "EXECUÇÃO INFRA": "EXECINFRA",
    "ENG. PAV": "ENG.PAV", "EXECUÇÃO PAV.": "EXEC.PAV", "PULMÃO INFRA": "PUL.INFRA",
    "PL.RADIER": "PL.RAD", "LEG.RADIER": "LEG.RAD", "PULMÃO RADIER": "PUL.RAD",
    "RADIER": "RAD", "DEMANDA MÍNIMA": "DEM.MIN",
}

mapeamento_reverso = {v: k for k, v in mapeamento_etapas_usuario.items()}

sigla_para_nome_completo = {
    "PROSPEC": "PROSPECÇÃO", "LEGVENDA": "LEGALIZAÇÃO PARA VENDA", "PULVENDA": "PULMÃO VENDA",
    "PL.LIMP": "PL.LIMP", "LEG.LIMP": "LEG.LIMP", "ENG.LIMP": "ENG. LIMP.", "EXECLIMP": "EXECUÇÃO LIMP.",
    "PL.TER": "PL.TER.", "LEG.TER": "LEG.TER.", "ENG. TER": "ENG. TER.", "EXECTER": "EXECUÇÃO TER.",
    "PL.INFRA": "PL.INFRA", "LEG.INFRA": "LEG.INFRA", "ENG.INFRA": "ENG. INFRA",
    "EXECINFRA": "EXECUÇÃO INFRA", "LEG.PAV": "LEG.PAV", "ENG.PAV": "ENG. PAV",
    "EXEC.PAV": "EXECUÇÃO PAV.", "PUL.INFRA": "PULMÃO INFRA", "PL.RAD": "PL.RADIER",
    "LEG.RAD": "LEG.RADIER", "PUL.RAD": "PULMÃO RADIER", "RAD": "RADIER", "DEM.MIN": "DEMANDA MÍNIMA",
}

ORDEM_ETAPAS_NOME_COMPLETO = [sigla_para_nome_completo.get(s, s) for s in ORDEM_ETAPAS_GLOBAL]
nome_completo_para_sigla = {v: k for k, v in sigla_para_nome_completo.items()}

GRUPO_POR_ETAPA = {mapeamento_etapas_usuario.get(etapa, etapa): grupo for grupo, etapas in GRUPOS.items() for etapa in etapas}
SETOR_POR_ETAPA = {mapeamento_etapas_usuario.get(etapa, etapa): setor for setor, etapas in SETOR.items() for etapa in etapas}


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
    OFFSET_VARIACAO_TERMINO = 0.31

    CORES_POR_SETOR = {
        "PROSPECÇÃO": {"previsto": "#F7DB89", "real": "#AE8141"},
        "LEGALIZAÇÃO": {"previsto": "#cc85d4", "real": "#93369E"},
        "PULMÃO": {"previsto": "#999797", "real": "#6f6f6f"},
        "ENGENHARIA": {"previsto": "#d78c49", "real": "#be5900"},
        "INFRA": {"previsto": "#7cafdb", "real": "#125287"},
        "PRODUÇÃO": {"previsto": "#434444", "real": "#252424"},
        "NOVOS PRODUTOS": {"previsto": "#9691FD", "real": "#453ECC"},
        "VENDA": {"previsto": "#66c66d", "real": "#096710"},
        "Não especificado": {"previsto": "#ffffff", "real": "#FFFFFF"}
    }

    @classmethod
    def set_offset_variacao_termino(cls, novo_offset):
        cls.OFFSET_VARIACAO_TERMINO = novo_offset

# --- Funções do Novo Gráfico Gantt ---

# =============================================================================
# 1. FUNÇÃO DE CÁLCULO DE PERÍODO (SUBSTITUÍDA E MELHORADA)
# =============================================================================
def calcular_periodo_datas(df, meses_padding_inicio=1, meses_padding_fim=3):
    """
    Calcula o período de datas dinamicamente para um DataFrame específico.
    """
    if df.empty:
        hoje = datetime.now()
        data_min_default = (hoje - relativedelta(months=2)).replace(day=1)
        data_max_default = (hoje + relativedelta(months=4))
        data_max_default = (data_max_default.replace(day=1) + relativedelta(months=1)) - timedelta(days=1)
        return data_min_default, data_max_default

    datas = []
    colunas_data = ["Inicio_Prevista", "Termino_Prevista", "Inicio_Real", "Termino_Real"]
    for col in colunas_data:
        if col in df.columns:
            datas_validas = pd.to_datetime(df[col], errors='coerce').dropna()
            datas.extend(datas_validas.tolist())

    if not datas:
        return calcular_periodo_datas(pd.DataFrame()) # Chama o tratamento de df vazio

    data_min_real = min(datas)
    data_max_real = max(datas)

    data_inicio_final = (data_min_real - relativedelta(months=meses_padding_inicio)).replace(day=1)
    data_fim_temp = data_max_real + relativedelta(months=meses_padding_fim)
    data_fim_final = (data_fim_temp.replace(day=1) + relativedelta(months=1)) - timedelta(days=1)

    return data_inicio_final, data_fim_final


def calcular_dias_uteis_novo(data_inicio, data_fim):
    if pd.isna(data_inicio) or pd.isna(data_fim):
        return None
    
    data_inicio = pd.to_datetime(data_inicio).normalize()
    data_fim = pd.to_datetime(data_fim).normalize()
    
    sinal = 1
    if data_inicio > data_fim:
        data_inicio, data_fim = data_fim, data_inicio
        sinal = -1
    
    # Usa a função do numpy que é mais performática
    return np.busday_count(data_inicio.date(), data_fim.date()) * sinal

def obter_data_meta_assinatura_novo(df_empreendimento):
    df_meta = df_empreendimento[df_empreendimento["Etapa"] == "DEMANDA MÍNIMA"]
    if df_meta.empty:
        return None
    for col in ["Inicio_Prevista", "Inicio_Real", "Termino_Prevista", "Termino_Real"]:
        if col in df_meta.columns and pd.notna(df_meta[col].iloc[0]):
            return pd.to_datetime(df_meta[col].iloc[0])
    return None

# =============================================================================
# 2. FUNÇÃO DE CONVERSÃO DE DADOS (SUBSTITUÍDA E SIMPLIFICADA)
# =============================================================================
def converter_dados_para_gantt(df):
    if df.empty:
        # Se não há dados, retorna uma lista vazia.
        return []

    gantt_data = []
    
    # Agrupa por empreendimento para processar um de cada vez
    for empreendimento in df["Empreendimento"].unique():
        df_emp = df[df["Empreendimento"] == empreendimento].copy()
        
        tasks = []
        df_emp['Etapa'] = pd.Categorical(df_emp['Etapa'], categories=ORDEM_ETAPAS_NOME_COMPLETO, ordered=True)
        df_emp_sorted = df_emp.sort_values(by='Etapa').reset_index()

        for i, (idx, row) in enumerate(df_emp_sorted.iterrows()):
            start_date = row.get("Inicio_Prevista")
            end_date = row.get("Termino_Prevista")
            start_real = row.get("Inicio_Real")
            end_real_original = row.get("Termino_Real")
            progress = row.get("% concluído", 0)

            if pd.isna(start_date): start_date = datetime.now()
            if pd.isna(end_date): end_date = start_date + timedelta(days=30)

            is_in_progress = False
            end_real_visual = end_real_original
            if pd.notna(start_real) and progress < 100 and pd.isna(end_real_original):
                end_real_visual = datetime.now()
                is_in_progress = True

            etapa = row.get("Etapa", "UNKNOWN")
            
            vd = calcular_dias_uteis_novo(end_date, end_real_original)
            duracao_prevista_uteis = calcular_dias_uteis_novo(start_date, end_date)
            duracao_real_uteis = calcular_dias_uteis_novo(start_real, end_real_original)
            
            dd = None
            if duracao_real_uteis is not None and duracao_prevista_uteis is not None:
                dd = duracao_real_uteis - duracao_prevista_uteis
            
            task = {
                "id": f"t{i}", "name": etapa, "numero_etapa": i + 1,
                "start_previsto": start_date.strftime("%Y-%m-%d"),
                "end_previsto": end_date.strftime("%Y-%m-%d"),
                "start_real": pd.to_datetime(start_real).strftime("%Y-%m-%d") if pd.notna(start_real) else None,
                "end_real": pd.to_datetime(end_real_visual).strftime("%Y-%m-%d") if pd.notna(end_real_visual) else None,
                "setor": row.get("SETOR", "Não especificado"),
                "desc": f"{etapa} - {empreendimento}",
                "progress": int(progress),
                "is_in_progress": is_in_progress,
                "inicio_previsto": start_date.strftime("%d/%m/%y"),
                "termino_previsto": end_date.strftime("%d/%m/%y"),
                "inicio_real": pd.to_datetime(start_real).strftime("%d/%m/%y") if pd.notna(start_real) else "N/D",
                "termino_real": pd.to_datetime(end_real_original).strftime("%d/%m/%y") if pd.notna(end_real_original) else "N/D",
                "vd": int(vd) if vd is not None else None,
                "dd": int(dd) if dd is not None else None,
                "duracao_prevista": int(duracao_prevista_uteis) if duracao_prevista_uteis is not None else None,
                "duracao_real": int(duracao_real_uteis) if duracao_real_uteis is not None else None
            }
            tasks.append(task)
    
        data_meta = obter_data_meta_assinatura_novo(df_emp)
        
        project = {
            "id": f"p{len(gantt_data)}", "name": empreendimento,
            "desc": f"Projeto {empreendimento}", "tasks": tasks,
            "meta_assinatura_date": data_meta.strftime("%Y-%m-%d") if data_meta else None
        }
        gantt_data.append(project)
    
    # Retorna apenas os dados, sem o período global.
    return gantt_data

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
        valor = "".join(c for c in valor if c.isdigit() or c in [".", ","]).replace(",", ".").strip()
        if not valor: return 0.0
    try:
        val_float = float(valor)
        return val_float * 100 if val_float <= 1 else val_float
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
    if pd.notna(termino_real) and pd.notna(termino_previsto):
        diferenca_dias = calculate_business_days(termino_previsto, termino_real)
        if pd.isna(diferenca_dias): diferenca_dias = 0
        if diferenca_dias > 0: return f"V: +{diferenca_dias}d", "#89281d"
        elif diferenca_dias < 0: return f"V: {diferenca_dias}d", "#0b803c"
        else: return "V: 0d", "#666666"
    else:
        return "V: -", "#666666"

def calcular_porcentagem_correta(grupo):
    if "% concluído" not in grupo.columns: return 0.0
    porcentagens = grupo["% concluído"].astype(str).apply(converter_porcentagem)
    porcentagens = porcentagens[(porcentagens >= 0) & (porcentagens <= 100)]
    if porcentagens.empty: return 0.0
    porcentagens_validas = porcentagens.dropna()
    if porcentagens_validas.empty: return 0.0
    return porcentagens_validas.mean()

def padronizar_etapa(etapa_str):
    if pd.isna(etapa_str): return "UNKNOWN"
    etapa_limpa = str(etapa_str).strip().upper()
    return mapeamento_etapas_usuario.get(etapa_limpa, etapa_limpa)


# --- Funções de Filtragem e Ordenação ---
def filtrar_etapas_nao_concluidas(df):
    if df.empty or "% concluído" not in df.columns: return df
    df_copy = df.copy()
    df_copy["% concluído"] = df_copy["% concluído"].apply(converter_porcentagem)
    return df_copy[df_copy["% concluído"] < 100]

def obter_data_meta_assinatura(df_original, empreendimento):
    df_meta = df_original[(df_original["Empreendimento"] == empreendimento) & (df_original["Etapa"] == "DEM.MIN")]
    if df_meta.empty: return pd.Timestamp.max
    for col in ["Termino_Prevista", "Inicio_Prevista", "Termino_Real", "Inicio_Real"]:
        if pd.notna(df_meta[col].iloc[0]): return df_meta[col].iloc[0]
    return pd.Timestamp.max

def criar_ordenacao_empreendimentos(df_original):
    empreendimentos_meta = {emp: obter_data_meta_assinatura(df_original, emp) for emp in df_original["Empreendimento"].unique()}
    return sorted(empreendimentos_meta.keys(), key=empreendimentos_meta.get)

def aplicar_ordenacao_final(df, empreendimentos_ordenados):
    if df.empty: return df
    ordem_empreendimentos = {emp: idx for idx, emp in enumerate(empreendimentos_ordenados)}
    df["ordem_empreendimento"] = df["Empreendimento"].map(ordem_empreendimentos)
    ordem_etapas = {etapa: idx for idx, etapa in enumerate(ORDEM_ETAPAS_GLOBAL)}
    df["ordem_etapa"] = df["Etapa"].map(ordem_etapas).fillna(len(ordem_etapas))
    df_ordenado = df.sort_values(["ordem_empreendimento", "ordem_etapa"]).drop(["ordem_empreendimento", "ordem_etapa"], axis=1)
    return df_ordenado.reset_index(drop=True)

# ========================================================================================================
# 3. FUNÇÃO GERAR_GANTT (SUBSTITUÍDA COM A LÓGICA DE PERÍODO INDIVIDUAL)
# ========================================================================================================
def gerar_gantt(df, tipo_visualizacao="Ambos", filtrar_nao_concluidas=False):
    if df.empty:
        st.warning("Sem dados disponíveis para exibir o Gantt.")
        return

    df_gantt = df.copy()
    if "Empreendimento" in df_gantt.columns:
        df_gantt["Empreendimento"] = df_gantt["Empreendimento"].apply(abreviar_nome)
    
    for col in ["Inicio_Prevista", "Termino_Prevista", "Inicio_Real", "Termino_Real"]:
        if col in df_gantt.columns:
            df_gantt[col] = pd.to_datetime(df_gantt[col], errors="coerce")

    if "% concluído" not in df_gantt.columns: df_gantt["% concluído"] = 0
    df_gantt["% concluído"] = df_gantt["% concluído"].fillna(0).apply(converter_porcentagem)

    df_gantt_agg = df_gantt.groupby(['Empreendimento', 'Etapa']).agg(
        Inicio_Prevista=('Inicio_Prevista', 'min'),
        Termino_Prevista=('Termino_Prevista', 'max'),
        Inicio_Real=('Inicio_Real', 'min'),
        Termino_Real=('Termino_Real', 'max'),
        **{'% concluído': ('% concluído', 'max')},
        SETOR=('SETOR', 'first')
    ).reset_index()
    
    df_gantt_agg["Etapa"] = df_gantt_agg["Etapa"].map(sigla_para_nome_completo).fillna(df_gantt_agg["Etapa"])
    
    # A função agora só retorna os dados.
    gantt_data = converter_dados_para_gantt(df_gantt_agg)
    
    if not gantt_data:
        st.warning("Nenhum dado válido para o Gantt após a conversão.")
        return

    empreendimentos_ordenados = criar_ordenacao_empreendimentos(df)
    project_dict = {project['name']: project for project in gantt_data}
    
    # O CÁLCULO DO PERÍODO VEM PARA DENTRO DO LOOP
    for empreendimento_nome in empreendimentos_ordenados:
        if empreendimento_nome not in project_dict: continue
        
        project = project_dict[empreendimento_nome]

        # --- ALTERAÇÃO PRINCIPAL: CALCULA O PERÍODO PARA ESTE PROJETO ESPECÍFICO ---
        df_projeto_especifico = df_gantt_agg[df_gantt_agg["Empreendimento"] == empreendimento_nome]
        data_min_proj, data_max_proj = calcular_periodo_datas(df_projeto_especifico)
        total_meses_proj = ((data_max_proj.year - data_min_proj.year) * 12) + (data_max_proj.month - data_min_proj.month) + 1
        # --- FIM DA ALTERAÇÃO PRINCIPAL ---

        st.markdown(f"### {project['name']}")
        num_tasks = len(project["tasks"])
        altura_gantt = max(400, num_tasks * 35 + 150)
        
        # Usar as variáveis de período individuais no HTML
        gantt_html = f"""
            <!DOCTYPE html>
            <html lang="pt-BR">
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                    html, body {{ width: 100%; height: 100%; font-family: 'Segoe UI', sans-serif; background-color: #f5f5f5; color: #333; overflow: hidden; }}
                    .gantt-container {{ width: 100%; height: 100%; background-color: white; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); overflow: hidden; position: relative; display: flex; flex-direction: column; }}
                    .gantt-main {{ display: flex; flex: 1; position: relative; overflow: hidden; }}
                    .gantt-sidebar {{ width: 250px; background-color: #f8f9fa; border-right: 2px solid #e2e8f0; flex-shrink: 0; overflow-y: auto; z-index: 10; }}
                    .sidebar-header {{ background: linear-gradient(135deg, #4a5568, #2d3748); color: white; padding: 12px 15px; font-weight: 600; border-bottom: 1px solid #e2e8f0; position: sticky; top: 0; z-index: 11; height: 60px; display: flex; align-items: center; font-size: 14px; }}
                    .sidebar-row {{ padding: 6px 10px; border-bottom: 1px solid #e2e8f0; background-color: white; transition: background-color 0.2s ease; height: 35px; display: flex; align-items: center; justify-content: space-between; }}
                    .sidebar-row:hover {{ background-color: #f1f5f9; }}
                    .sidebar-row:nth-child(even) {{ background-color: #f8f9fa; }}
                    .sidebar-row:nth-child(even):hover {{ background-color: #e2e8f0; }}
                    .row-left {{ flex: 1; display: flex; flex-direction: column; justify-content: center; }}
                    .row-title {{ font-weight: 600; color: #2d3748; font-size: 11px; margin-bottom: 2px; }}
                    .row-dates {{ font-size: 8px; color: #4a5568; line-height: 1.2; }}
                    .row-status {{ width: 55px; height: 24px; display: flex; flex-direction: column; align-items: center; justify-content: center; border-radius: 4px; font-size: 8px; font-weight: 600; margin-left: 8px; text-align: center; }}
                    .status-complete {{ background-color: #d1fae5; color: #065f46; border: 1px solid #a7f3d0; }}
                    .status-progress {{ background-color: #fef3c7; color: #92400e; border: 1px solid #fde68a; }}
                    .status-pending {{ background-color: #e0e7ff; color: #3730a3; border: 1px solid #c7d2fe; }}
                    .status-percentage {{ font-size: 10px; font-weight: 700; }}
                    .status-variation {{ font-size: 6px; margin-top: 1px; line-height: 1; }}
                    .gantt-chart {{ flex: 1; overflow: auto; position: relative; background-color: white; user-select: none; cursor: grab; }}
                    .gantt-chart.active {{ cursor: grabbing; }}
                    .chart-container {{ position: relative; min-width: {total_meses_proj * 30}px; }}
                    .chart-header {{ background: linear-gradient(135deg, #4a5568, #2d3748); color: white; height: 60px; position: sticky; top: 0; z-index: 9; display: flex; flex-direction: column; }}
                    .year-header {{ height: 30px; display: flex; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.2); }}
                    .year-section {{ text-align: center; font-weight: 600; font-size: 12px; display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,0.1); height: 100%; }}
                    .month-header {{ height: 30px; display: flex; align-items: center; }}
                    .month-cell {{ width: 30px; height: 30px; border-right: 1px solid rgba(255,255,255,0.2); display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 500; }}
                    .chart-body {{ position: relative; padding-top: 0; }}
                    .gantt-row {{ position: relative; height: 35px; border-bottom: 1px solid #e2e8f0; background-color: white; }}
                    .gantt-row:nth-child(even) {{ background-color: #f8f9fa; }}
                    .gantt-bar {{ position: absolute; height: 11px; border-radius: 3px; cursor: pointer; transition: all 0.2s ease; display: flex; align-items: center; padding: 0 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); z-index: 6; }}
                    .gantt-bar:hover {{ transform: translateY(-1px); box-shadow: 0 4px 8px rgba(0,0,0,0.2); z-index: 10; }}
                    .gantt-bar.previsto {{ top: 5px; opacity: 0.8; }}
                    .gantt-bar.real {{ top: 16px; opacity: 1; }}
                    .bar-label {{ color: white; font-size: 8px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-shadow: 0 1px 2px rgba(0,0,0,0.4); }}
                    .tooltip {{ position: fixed; background-color: #2d3748; color: white; padding: 6px 10px; border-radius: 4px; font-size: 11px; z-index: 1000; box-shadow: 0 2px 8px rgba(0,0,0,0.3); pointer-events: none; opacity: 0; transition: opacity 0.2s ease; max-width: 220px; }}
                    .tooltip.show {{ opacity: 1; }}
                    .today-line {{ position: absolute; top: 60px; bottom: 0; width: 2px; background-color: #e53e3e; z-index: 5; box-shadow: 0 0 4px rgba(229, 62, 62, 0.6); }}
                    .bar-progress {{ position: absolute; left:0; top:0; height: 100%; background-color: rgba(0,0,0,0.25); border-radius: 3px; z-index: 1; pointer-events: none; }}
                    .month-divider {{ position: absolute; top: 60px; bottom: 0; width: 1px; background-color: #cbd5e0; z-index: 4; pointer-events: none; }}
                    .month-divider.first {{ background-color: #4a5568; width: 2px; }}
                    .fullscreen-btn {{ position: absolute; top: 10px; right: 10px; background: rgba(255, 255, 255, 0.9); border: none; border-radius: 4px; padding: 8px 12px; font-size: 14px; cursor: pointer; z-index: 100; box-shadow: 0 2px 4px rgba(0,0,0,0.2); transition: all 0.2s ease; display: flex; align-items: center; gap: 5px; }}
                    .fullscreen-btn:hover {{ background: white; box-shadow: 0 4px 8px rgba(0,0,0,0.3); transform: translateY(-1px); }}
                    .meta-line {{ position: absolute; top: 60px; bottom: 0; width: 2px; border-left: 2px dashed #8e44ad; z-index: 5; box-shadow: 0 0 4px rgba(142, 68, 173, 0.6); }}
                    .meta-line-label {{ position: absolute; top: 65px; background-color: #8e44ad; color: white; padding: 2px 5px; border-radius: 4px; font-size: 9px; font-weight: 600; white-space: nowrap; z-index: 8; transform: translateX(-50%); }}
                </style>
            </head>
            <body>
                <div class="gantt-container" id="gantt-container-{project["id"]}">
                    <button class="fullscreen-btn" id="fullscreen-btn-{project["id"]}"><span>📺</span> <span>Tela Cheia</span></button>
                    <div class="gantt-main">
                        <div class="gantt-sidebar"><div class="sidebar-header">{project["name"]}</div><div id="sidebar-content-{project["id"]}"></div></div>
                        <div class="gantt-chart">
                            <div class="chart-container" id="chart-container-{project["id"]}">
                                <div class="chart-header"><div class="year-header" id="year-header-{project["id"]}"></div><div class="month-header" id="month-header-{project["id"]}"></div></div>
                                <div class="chart-body" id="chart-body-{project["id"]}"></div>
                                <div class="today-line" id="today-line-{project["id"]}"></div>
                                <div class="meta-line" id="meta-line-{project["id"]}"></div>
                                <div class="meta-line-label" id="meta-line-label-{project["id"]}"></div>
                            </div>
                        </div>
                    </div>
                    <div class="tooltip" id="tooltip-{project["id"]}"></div>
                </div>
                <script>
                    const coresPorSetor_{project["id"]} = {json.dumps(StyleConfig.CORES_POR_SETOR)};
                    const projectData_{project["id"]} = {json.dumps([project])};
                    const dataMinStr_{project["id"]} = '{data_min_proj.strftime("%Y-%m-%d")}';
                    const dataMaxStr_{project["id"]} = '{data_max_proj.strftime("%Y-%m-%d")}';
                    const totalMeses_{project["id"]} = {total_meses_proj};
                    const PIXELS_PER_MONTH = 30;

                    function parseDate(dateStr) {{
                        if (!dateStr) return null;
                        const [year, month, day] = dateStr.split('-').map(Number);
                        return new Date(Date.UTC(year, month - 1, day));
                    }}

                    function initGantt_{project["id"]}() {{
                        renderSidebar_{project["id"]}();
                        renderHeader_{project["id"]}();
                        renderChart_{project["id"]}();
                        renderMonthDividers_{project["id"]}();
                        setupEventListeners_{project["id"]}();
                        positionTodayLine_{project["id"]}();
                        positionMetaLine_{project["id"]}();
                    }}

                    function renderSidebar_{project["id"]}() {{
                        const sidebarContent = document.getElementById('sidebar-content-{project["id"]}');
                        let html = '';
                        projectData_{project["id"]}[0].tasks.forEach(task => {{
                            let statusClass = 'status-pending', statusText = '0%', variationText = '';
                            if (task.progress === 100) {{ statusClass = 'status-complete'; statusText = '100%'; let vdDisplay = task.vd !== null ? `VD: ${{task.vd > 0 ? '+' : ''}}${{task.vd}}d` : 'VD: -'; variationText = `${{vdDisplay}}`; }}
                            else if (task.progress > 0) {{ statusClass = 'status-progress'; statusText = `${{task.progress}}%`; }}
                            let datesText = `Prev: ${{task.inicio_previsto}} &rarr; ${{task.termino_previsto}} (${{task.duracao_prevista === null ? '-' : task.duracao_prevista + 'd'}})`;
                            if (task.inicio_real) {{ datesText += `<br>Real: ${{task.inicio_real}} &rarr; ${{task.termino_real || 'N/D'}} (${{task.duracao_real === null ? '-' : task.duracao_real + 'd'}})`; }}
                            else {{ datesText += `<br>Real: N/D &rarr; N/D`; }}
                            html += `<div class="sidebar-row"><div class="row-left"><div class="row-title">${{task.numero_etapa}}. ${{task.name}}</div><div class="row-dates">${{datesText}}</div></div><div class="row-status ${{statusClass}}"><div class="status-percentage">${{statusText}}</div><div class="status-variation">${{variationText}}</div></div></div>`;
                        }});
                        sidebarContent.innerHTML = html;
                    }}
                    
                    function renderHeader_{project["id"]}() {{
                        const yearHeader = document.getElementById('year-header-{project["id"]}');
                        const monthHeader = document.getElementById('month-header-{project["id"]}');
                        let yearHtml = '', monthHtml = '';
                        const yearsData = [];
                        let currentDate = parseDate(dataMinStr_{project["id"]});
                        const dataMax = parseDate(dataMaxStr_{project["id"]});
                        let currentYear = -1, monthsInCurrentYear = 0;

                        while (currentDate <= dataMax) {{
                            const year = currentDate.getUTCFullYear();
                            if (year !== currentYear) {{
                                if (currentYear !== -1) yearsData.push({{ year: currentYear, count: monthsInCurrentYear }});
                                currentYear = year;
                                monthsInCurrentYear = 0;
                            }}
                            const monthNumber = String(currentDate.getUTCMonth() + 1).padStart(2, '0');
                            monthHtml += `<div class="month-cell">${{monthNumber}}</div>`;
                            monthsInCurrentYear++;
                            currentDate.setUTCMonth(currentDate.getUTCMonth() + 1);
                        }}
                        if (currentYear !== -1) yearsData.push({{ year: currentYear, count: monthsInCurrentYear }});
                        yearsData.forEach(data => {{
                            const yearWidth = data.count * PIXELS_PER_MONTH;
                            yearHtml += `<div class="year-section" style="width: ${{yearWidth}}px">${{data.year}}</div>`;
                        }});
                        yearHeader.innerHTML = yearHtml;
                        monthHeader.innerHTML = monthHtml;
                    }}

                    function renderChart_{project["id"]}() {{
                        const chartBody = document.getElementById('chart-body-{project["id"]}');
                        let html = '';
                        projectData_{project["id"]}[0].tasks.forEach(task => {{ html += `<div class="gantt-row" data-task-id="${{task.id}}"></div>`; }});
                        chartBody.innerHTML = html;
                        projectData_{project["id"]}[0].tasks.forEach(task => {{
                            const row = chartBody.querySelector(`[data-task-id="${{task.id}}"]`);
                            row.appendChild(createBar_{project["id"]}(task, 'previsto'));
                            if (task.start_real && task.end_real) row.appendChild(createBar_{project["id"]}(task, 'real'));
                        }});
                    }}

                    function createBar_{project["id"]}(task, tipo) {{
                        const startDate = parseDate(tipo === 'previsto' ? task.start_previsto : task.start_real);
                        const endDate = parseDate(tipo === 'previsto' ? task.end_previsto : task.end_real);
                        if (!startDate || !endDate) return document.createElement('div');

                        const left = getPosition_{project["id"]}(startDate);
                        const width = getPosition_{project["id"]}(endDate) - left + (PIXELS_PER_MONTH / 30);

                        const bar = document.createElement('div');
                        bar.className = `gantt-bar ${{tipo}}`;
                        
                        const coresSetor = coresPorSetor_{project["id"]}[task.setor];
                        const corDefault = tipo === 'previsto' ? '#cccccc' : '#888888'; // Cinza padrão
                        let corBarra = corDefault;

                        if (coresSetor) {{
                            corBarra = tipo === 'previsto' ? (coresSetor.previsto || corDefault) : (coresSetor.real || corDefault);
                        }}
                        bar.style.backgroundColor = corBarra;
                        bar.style.left = `${{left}}px`;
                        bar.style.width = `${{width}}px`;
                        
                        const barLabel = document.createElement('span');
                        barLabel.className = 'bar-label';
                        barLabel.textContent = `${{task.name}} (${{task.progress}}%)`;
                        bar.appendChild(barLabel);
                        
                        if (tipo === 'real' && task.progress > 0) {{
                            const progressBar = document.createElement('div');
                            progressBar.className = 'bar-progress';
                            progressBar.style.width = `${{task.progress}}%`;
                            bar.appendChild(progressBar);
                        }}

                        bar.addEventListener('mousemove', e => showTooltip_{project["id"]}(e, task, tipo));
                        bar.addEventListener('mouseout', () => hideTooltip_{project["id"]}());
                        return bar;
                    }}

                    function getPosition_{project["id"]}(date) {{
                        if (!date) return 0;
                        const chartStart = parseDate(dataMinStr_{project["id"]});
                        const offsetDays = (date - chartStart) / (1000 * 60 * 60 * 24);
                        return offsetDays * (PIXELS_PER_MONTH / 30);
                    }}

                    function positionTodayLine_{project["id"]}() {{
                        const todayLine = document.getElementById('today-line-{project["id"]}');
                        const today = new Date();
                        const todayUTC = new Date(Date.UTC(today.getFullYear(), today.getMonth(), today.getDate()));
                        const chartStart = parseDate(dataMinStr_{project["id"]});
                        const chartEnd = parseDate(dataMaxStr_{project["id"]});
                        if (todayUTC >= chartStart && todayUTC <= chartEnd) {{
                            const offset = getPosition_{project["id"]}(todayUTC);
                            todayLine.style.left = `${{offset}}px`;
                            todayLine.style.display = 'block';
                        }} else {{
                            todayLine.style.display = 'none';
                        }}
                    }}

                    function positionMetaLine_{project["id"]}() {{
                          const metaLine = document.getElementById('meta-line-{project["id"]}');
                          const metaLabel = document.getElementById('meta-line-label-{project["id"]}');
                          const metaDateStr = projectData_{project["id"]}[0].meta_assinatura_date;
                          if (!metaDateStr) {{ metaLine.style.display = 'none'; metaLabel.style.display = 'none'; return; }}
                          const metaDate = parseDate(metaDateStr);
                          const chartStart = parseDate(dataMinStr_{project["id"]});
                          const chartEnd = parseDate(dataMaxStr_{project["id"]});
                          if (metaDate >= chartStart && metaDate <= chartEnd) {{
                              const offset = getPosition_{project["id"]}(metaDate);
                              metaLine.style.left = `${{offset}}px`;
                              metaLabel.style.left = `${{offset}}px`;
                              metaLine.style.display = 'block';
                              metaLabel.style.display = 'block';
                              metaLabel.textContent = `Meta: ${{metaDate.toLocaleDateString('pt-BR', {{day: '2-digit', month: '2-digit', year: '2-digit', timeZone: 'UTC'}})}}`;
                          }} else {{
                              metaLine.style.display = 'none';
                              metaLabel.style.display = 'none';
                          }}
                    }}
                    
                    function showTooltip_{project["id"]}(e, task, tipo) {{
                        const tooltip = document.getElementById('tooltip-{project["id"]}');
                        let content = `<b>${{task.name}}</b><br>`;
                        if (tipo === 'previsto') {{
                            content += `Previsto: ${{task.inicio_previsto}} - ${{task.termino_previsto}}<br>Duração: ${{task.duracao_prevista ?? '-'}}d`;
                        }} else {{
                            content += `Real: ${{task.inicio_real}} - ${{task.termino_real}}<br>Duração: ${{task.duracao_real ?? '-'}}d<br>Variação Término: ${{task.vd ?? '-'}}d`;
                        }}
                        content += `<br><b>Progresso: ${{task.progress}}%</b>`;
                        tooltip.innerHTML = content;
                        tooltip.classList.add('show');
                        const containerRect = document.getElementById('gantt-container-{project["id"]}').getBoundingClientRect();
                        tooltip.style.left = `${{e.clientX - containerRect.left + 15}}px`;
                        tooltip.style.top = `${{e.clientY - containerRect.top + 15}}px`;
                    }}

                    function hideTooltip_{project["id"]}() {{
                        document.getElementById('tooltip-{project["id"]}').classList.remove('show');
                    }}

                    function renderMonthDividers_{project["id"]}() {{
                        const chartContainer = document.getElementById('chart-container-{project["id"]}');
                        chartContainer.querySelectorAll('.month-divider, .month-divider-label').forEach(el => el.remove());
                        let currentDate = parseDate(dataMinStr_{project["id"]});
                        const dataMax = parseDate(dataMaxStr_{project["id"]});
                        while (currentDate <= dataMax) {{
                            const left = getPosition_{project["id"]}(currentDate);
                            const divider = document.createElement('div');
                            divider.className = 'month-divider';
                            if (currentDate.getUTCMonth() === 0) divider.classList.add('first');
                            divider.style.left = `${{left}}px`;
                            chartContainer.appendChild(divider);
                            currentDate.setUTCMonth(currentDate.getUTCMonth() + 1);
                        }}
                    }}

                    function setupEventListeners_{project["id"]}() {{
                        const ganttChart = document.querySelector(`#gantt-container-{project["id"]} .gantt-chart`);
                        const sidebar = document.querySelector(`#gantt-container-{project["id"]} .gantt-sidebar`);
                        const fullscreenBtn = document.getElementById('fullscreen-btn-{project["id"]}');
                        if (fullscreenBtn) fullscreenBtn.addEventListener('click', () => toggleFullscreen_{project["id"]}());
                        if (ganttChart && sidebar) {{
                            ganttChart.addEventListener('scroll', () => {{ sidebar.scrollTop = ganttChart.scrollTop; }});
                            sidebar.addEventListener('scroll', () => {{ ganttChart.scrollTop = sidebar.scrollTop; }});
                            let isDown = false, startX, scrollLeft;
                            ganttChart.addEventListener('mousedown', (e) => {{ isDown = true; ganttChart.classList.add('active'); startX = e.pageX - ganttChart.offsetLeft; scrollLeft = ganttChart.scrollLeft; }});
                            ganttChart.addEventListener('mouseleave', () => {{ isDown = false; ganttChart.classList.remove('active'); }});
                            ganttChart.addEventListener('mouseup', () => {{ isDown = false; ganttChart.classList.remove('active'); }});
                            ganttChart.addEventListener('mousemove', (e) => {{
                                if (!isDown) return;
                                e.preventDefault();
                                const x = e.pageX - ganttChart.offsetLeft;
                                const walk = (x - startX) * 2;
                                ganttChart.scrollLeft = scrollLeft - walk;
                            }});
                        }}
                    }}
                    
                    function toggleFullscreen_{project["id"]}() {{
                        const container = document.getElementById('gantt-container-{project["id"]}');
                        if (!document.fullscreenElement) {{ container.requestFullscreen().catch(err => alert(`Erro: ${{err.message}}`)); }}
                        else {{ document.exitFullscreen(); }}
                    }}

                    initGantt_{project["id"]}();
                </script>
            </body>
            </html>
        """
        components.html(gantt_html, height=altura_gantt, scrolling=True)
        st.info(f"📊 {project['name']}: {len(project['tasks'])} tarefas | Período: {data_min_proj.strftime('%d/%m/%Y')} - {data_max_proj.strftime('%d/%m/%Y')}")
        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a: st.metric("Tarefas", len(project["tasks"]))
        with col_b: st.metric("Concluídas", len([t for t in project["tasks"] if t["progress"] == 100]))
        with col_c: st.metric("Em Andamento", len([t for t in project["tasks"] if 0 < t["progress"] < 100]))
        with col_d: st.metric("Com Dados Reais", len([t for t in project["tasks"] if t["start_real"]]))
        st.markdown("---")

# ========================================================================================================
# O RESTANTE DO CÓDIGO (LÓGICA DO STREAMLIT)
# ========================================================================================================

st.set_page_config(layout="wide", page_title="Dashboard de Gantt Comparativo")
if show_welcome_screen():
    st.stop()

st.markdown("""
<style>
    div.stMultiSelect div[role="option"] input[type="checkbox"]:checked + div > div:first-child { background-color: #4a0101 !important; border-color: #4a0101 !important; }
    div.stMultiSelect [aria-selected="true"] { background-color: #f8d7da !important; color: #333 !important; border-radius: 4px; }
    div.stMultiSelect [aria-selected="true"]::after { color: #4a0101 !important; font-weight: bold; }
    .stSidebar .stMultiSelect, .stSidebar .stSelectbox, .stSidebar .stRadio { margin-bottom: 1rem; }
    .nav-button-container { position: fixed; right: 20px; top: 20%; transform: translateY(-20%); z-index: 80; background: white; padding: 5px; border-radius: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
    .nav-link { display: block; background-color: #a6abb5; color: white !important; text-decoration: none !important; border-radius: 10px; padding: 5px 10px; margin: 5px 0; text-align: center; font-weight: bold; font-size: 14px; transition: all 0.3s ease; }
    .nav-link:hover { background-color: #ff4b4b; transform: scale(1.05); }
</style>
""", unsafe_allow_html=True)

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
                df_real = df_real.rename(columns={"EMP": "Empreendimento", "%_Concluido": "% concluído"})
                if "% concluído" in df_real.columns:
                    df_real["% concluído"] = df_real["% concluído"].apply(converter_porcentagem)
                df_real_pivot = df_real.pivot_table(index=["Empreendimento", "Etapa", "% concluído"], columns="Inicio_Fim", values="Valor", aggfunc="first").reset_index()
                df_real_pivot.columns.name = None
                if "INICIO" in df_real_pivot.columns:
                    df_real_pivot = df_real_pivot.rename(columns={"INICIO": "Inicio_Real"})
                if "TERMINO" in df_real_pivot.columns:
                    df_real_pivot = df_real_pivot.rename(columns={"TERMINO": "Termino_Real"})
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
                df_previsto = df_previsto.rename(columns={"EMP": "Empreendimento", "UGB": "UGB"})
                df_previsto_pivot = df_previsto.pivot_table(index=["UGB", "Empreendimento", "Etapa"], columns="Inicio_Fim", values="Valor", aggfunc="first").reset_index()
                df_previsto_pivot.columns.name = None
                if "INICIO" in df_previsto_pivot.columns:
                    df_previsto_pivot = df_previsto_pivot.rename(columns={"INICIO": "Inicio_Prevista"})
                if "TERMINO" in df_previsto_pivot.columns:
                    df_previsto_pivot = df_previsto_pivot.rename(columns={"TERMINO": "Termino_Prevista"})
                df_previsto = df_previsto_pivot
            else:
                df_previsto = pd.DataFrame()
        except Exception as e:
            st.warning(f"Erro ao carregar dados previstos: {e}")
            df_previsto = pd.DataFrame()
            
    if df_real.empty and df_previsto.empty:
        st.warning("Nenhuma fonte de dados carregada. Usando dados de exemplo.")
        return criar_dados_exemplo()

    etapas_base_oficial = set(sigla_para_nome_completo.keys())
    etapas_nos_dados = set()
    if not df_real.empty:
        etapas_nos_dados.update(df_real["Etapa"].unique())
    if not df_previsto.empty:
        etapas_nos_dados.update(df_previsto["Etapa"].unique())

    etapas_nao_mapeadas = etapas_nos_dados - etapas_base_oficial
    
    if "UNKNOWN" in etapas_nao_mapeadas:
         etapas_nao_mapeadas.remove("UNKNOWN")

    if etapas_nao_mapeadas:
        with st.sidebar.expander("⚠️ Alerta de Dados"):
            st.warning("As seguintes etapas foram encontradas nos dados, mas não são reconhecidas. Verifique a ortografia no arquivo de origem:")
            for etapa in sorted(list(etapas_nao_mapeadas)):
                st.code(etapa)

    if not df_real.empty and not df_previsto.empty:
        df_merged = pd.merge(df_previsto, df_real[["Empreendimento", "Etapa", "Inicio_Real", "Termino_Real", "% concluído"]], on=["Empreendimento", "Etapa"], how="outer")
    elif not df_previsto.empty:
        df_merged = df_previsto.copy()
        df_merged["% concluído"] = 0.0
    elif not df_real.empty:
        df_merged = df_real.copy()
        if "UGB" not in df_merged.columns:
            df_merged["UGB"] = "UGB1"
    else:
        return criar_dados_exemplo()

    for col in ["UGB", "Inicio_Prevista", "Termino_Prevista", "Inicio_Real", "Termino_Real", "% concluído"]:
        if col not in df_merged.columns:
            df_merged[col] = pd.NaT if "data" in col else ("UGB1" if col == "UGB" else 0.0)

    df_merged["% concluído"] = df_merged["% concluído"].fillna(0)
    df_merged.dropna(subset=["Empreendimento", "Etapa"], inplace=True)

    df_merged["GRUPO"] = df_merged["Etapa"].map(GRUPO_POR_ETAPA).fillna("Não especificado")
    df_merged["SETOR"] = df_merged["Etapa"].map(SETOR_POR_ETAPA).fillna("Não especificado")

    return df_merged

def criar_dados_exemplo():
    dados = {
        "UGB": ["UGB1", "UGB1", "UGB1", "UGB2", "UGB2", "UGB1"],
        "Empreendimento": ["Residencial Alfa", "Residencial Alfa", "Residencial Alfa", "Condomínio Beta", "Condomínio Beta", "Projeto Gama"],
        "Etapa": ["PROSPEC", "LEGVENDA", "PL.LIMP", "PROSPEC", "LEGVENDA", "PROSPEC"],
        "Inicio_Prevista": pd.to_datetime(["2024-01-01", "2024-02-15", "2024-04-01", "2024-01-20", "2024-03-10", "2024-05-01"]),
        "Termino_Prevista": pd.to_datetime(["2024-02-14", "2024-03-31", "2024-05-15", "2024-03-09", "2024-04-30", "2024-06-15"]),
        "Inicio_Real": pd.to_datetime(["2024-01-05", "2024-02-20", pd.NaT, "2024-01-22", "2024-03-15", pd.NaT]),
        "Termino_Real": pd.to_datetime(["2024-02-18", pd.NaT, pd.NaT, "2024-03-12", pd.NaT, pd.NaT]),
        "% concluído": [100, 50, 0, 100, 25, 0],
    }
    df_exemplo = pd.DataFrame(dados)
    df_exemplo["GRUPO"] = df_exemplo["Etapa"].map(GRUPO_POR_ETAPA).fillna("PLANEJAMENTO MACROFLUXO")
    df_exemplo["SETOR"] = df_exemplo["Etapa"].map(SETOR_POR_ETAPA).fillna("PROSPECÇÃO")
    return df_exemplo

@st.cache_data
def get_unique_values(df, column):
    return sorted(df[column].dropna().unique().tolist())

@st.cache_data
def filter_dataframe(df, ugb_filter, emp_filter, grupo_filter, setor_filter):
    if not ugb_filter:
        return df.iloc[0:0]
    df_filtered = df[df["UGB"].isin(ugb_filter)]
    if emp_filter:
        df_filtered = df_filtered[df_filtered["Empreendimento"].isin(emp_filter)]
    if grupo_filter:
        df_filtered = df_filtered[df_filtered["GRUPO"].isin(grupo_filter)]
    if setor_filter:
        df_filtered = df_filtered[df_filtered["SETOR"].isin(setor_filter)]
    return df_filtered

with st.spinner("Carregando e processando dados..."):
    df_data = load_data()

if df_data is not None and not df_data.empty:
    with st.sidebar:
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image("logoNova.png", width=200)

        ugb_options = get_unique_values(df_data, "UGB")
        selected_ugb = simple_multiselect_dropdown(label="Filtrar por UGB", options=ugb_options, key="ugb_filter", default_selected=ugb_options)

        emp_options = get_unique_values(df_data[df_data["UGB"].isin(selected_ugb)], "Empreendimento") if selected_ugb else []
        selected_emp = simple_multiselect_dropdown(label="Filtrar por Empreendimento", options=emp_options, key="empreendimento_filter", default_selected=emp_options)

        df_temp = df_data[df_data["UGB"].isin(selected_ugb)]
        if selected_emp:
            df_temp = df_temp[df_temp["Empreendimento"].isin(selected_emp)]
        grupo_options = get_unique_values(df_temp, "GRUPO")
        selected_grupo = simple_multiselect_dropdown(label="Filtrar por GRUPO", options=grupo_options, key="grupo_filter", default_selected=grupo_options)

        df_temp_setor = df_data[df_data["UGB"].isin(selected_ugb)]
        if selected_emp:
            df_temp_setor = df_temp_setor[df_temp_setor["Empreendimento"].isin(selected_emp)]
        if selected_grupo:
            df_temp_setor = df_temp_setor[df_temp_setor["GRUPO"].isin(selected_grupo)]
        setor_options = list(SETOR.keys())
        selected_setor = simple_multiselect_dropdown(label="Filtrar por SETOR", options=setor_options, key="setor_filter", default_selected=setor_options)

        df_temp_filtered = filter_dataframe(df_data, selected_ugb, selected_emp, selected_grupo, selected_setor)
        if not df_temp_filtered.empty:
            etapas_disponiveis = get_unique_values(df_temp_filtered, "Etapa")
            etapas_ordenadas = [etapa for etapa in ORDEM_ETAPAS_GLOBAL if etapa in etapas_disponiveis]
            etapas_para_exibir = ["Todos"] + [sigla_para_nome_completo.get(e, e) for e in etapas_ordenadas]
        else:
            etapas_para_exibir = ["Todos"]
        selected_etapa_nome = st.selectbox("Filtrar por Etapa", options=etapas_para_exibir)

        st.markdown("---")
        filtrar_nao_concluidas = st.checkbox("Etapas não concluídas", value=False, help="Quando marcado, mostra apenas etapas com menos de 100% de conclusão")
        st.markdown("---")
        tipo_visualizacao = st.radio("Mostrar dados:", ("Ambos", "Previsto", "Real"))

    df_filtered = filter_dataframe(df_data, selected_ugb, selected_emp, selected_grupo, selected_setor)

    if selected_etapa_nome != "Todos" and not df_filtered.empty:
        sigla_selecionada = nome_completo_para_sigla.get(selected_etapa_nome, selected_etapa_nome)
        df_filtered = df_filtered[df_filtered["Etapa"] == sigla_selecionada]

    if filtrar_nao_concluidas and not df_filtered.empty:
        df_filtered = filtrar_etapas_nao_concluidas(df_filtered)

    st.title("Macrofluxo")
    tab1, tab2 = st.tabs(["Gráfico de Gantt", "Tabelão Horizontal"])

 
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

