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
import holidays
from dateutil.relativedelta import relativedelta
import traceback
import streamlit.components.v1 as components  #pulmão
import json
import random
import time

try:
    from dropdown_component import simple_multiselect_dropdown
    from popup import show_welcome_screen
    from calculate_business_days import calculate_business_days
except ImportError:
    st.warning("Componentes 'dropdown_component', 'popup' ou 'calculate_business_days' não encontrados. Alguns recursos podem não funcionar como esperado.")
    # Definir valores padrão ou mocks se necessário
    def simple_multiselect_dropdown(label, options, key, default_selected):
        return st.multiselect(label, options, default=default_selected, key=key)
    def show_welcome_screen():
        return False
    def calculate_business_days(start, end):
        if pd.isna(start) or pd.isna(end):
            return None
        return np.busday_count(pd.to_datetime(start).date(), pd.to_datetime(end).date())

# --- Bloco de Importação de Dados ---
try:
    from tratamento_dados_reais import buscar_e_processar_dados_completos
    from tratamento_macrofluxo import tratar_macrofluxo
    MODO_REAL = True
except ImportError:
    st.warning("Scripts de processamento não encontrados. O app usará dados de exemplo.")
    buscar_e_processar_dados_completos = None
    tratar_macrofluxo = None
    MODO_REAL = False

    
# --- ORDEM DAS ETAPAS (DEFINIDA PELO USUÁRIO) ---
ORDEM_ETAPAS_GLOBAL = [
    "PROSPEC", "LEGVENDA", "PULVENDA", "PL.LIMP", "LEG.LIMP", "ENG.LIMP", "PE. LIMP.", "ORÇ. LIMP.", "SUP. LIMP.", "EXECLIMP",
    "PL.TER", "LEG.TER", "ENG. TER", "PE. TER.", "ORÇ. TER.", "SUP. TER.", "EXECTER", "PL.INFRA", "LEG.INFRA", "ENG.INFRA", "PE. INFRA", "ORÇ. INFRA", "SUP. INFRA",
    "EXECINFRA", "ENG.PAV", "PE. PAV", "ORÇ. PAV", "SUP. PAV", "EXEC.PAV", "PUL.INFRA", "PL.RAD", "LEG.RAD", "PUL.RAD",
    "RAD", "DEM.MIN", "PE. ÁREAS COMUNS (URB)", "PE. ÁREAS COMUNS (ENG)", "ORÇ. ÁREAS COMUNS", "SUP. ÁREAS COMUNS", "EXECUÇÃO ÁREAS COMUNS",
]

# --- Definição dos Grupos ---
GRUPOS = {
    "VENDA": ["PROSPECÇÃO", "LEGALIZAÇÃO PARA VENDA", "PULMÃO VENDA"],
    "LIMPEZA": ["PL.LIMP", "LEG.LIMP", "ENG. LIMP.", "EXECUÇÃO LIMP.", "PE. LIMP.", "ORÇ. LIMP.", "SUP. LIMP."],
    "TERRAPLANAGEM": ["PL.TER.", "LEG.TER.", "ENG. TER.", "EXECUÇÃO TER.", "PE. TER.", "ORÇ. TER.", "SUP. TER."],
    "INFRA INCIDENTE": ["PL.INFRA", "LEG.INFRA", "ENG. INFRA", "EXECUÇÃO INFRA", "PE. INFRA", "ORÇ. INFRA", "SUP. INFRA"],
    "PAVIMENTAÇÃO": ["ENG. PAV", "EXECUÇÃO PAV.", "PE. PAV", "ORÇ. PAV", "SUP. PAV"],
    "PULMÃO": ["PULMÃO INFRA"],
    "RADIER": ["PL.RADIER", "LEG.RADIER", "PULMÃO RADIER", "RADIER"],
    "DM": ["DEMANDA MÍNIMA"],
    "EQUIPANENTOS COMUNS": ["PE. ÁREAS COMUNS (URB)", "PE. ÁREAS COMUNS (ENG)", "ORÇ. ÁREAS COMUNS", "SUP. ÁREAS COMUNS", "EXECUÇÃO ÁREAS COMUNS"],
}

SETOR = {
    "PROSPECÇÃO": ["PROSPECÇÃO"],
    "LEGALIZAÇÃO": ["LEGALIZAÇÃO PARA VENDA", "LEG.LIMP", "LEG.TER.", "LEG.INFRA", "LEG.RADIER"],
    "PULMÃO": ["PULMÃO VENDA", "PULMÃO INFRA", "PULMÃO RADIER"],
    "ENGENHARIA": ["PL.LIMP", "ENG. LIMP.", "PL.TER.", "ENG. TER.", "PL.INFRA", "ENG. INFRA", "ENG. PAV", "PE. LIMP.", "ORÇ. LIMP.", "SUP. LIMP.",
     "PE. TER.", "ORÇ. TER.", "SUP. TER.", "PE. INFRA", "ORÇ. INFRA", "SUP. INFRA", "PE. PAV", "ORÇ. PAV", "SUP. PAV", "PE. ÁREAS COMUNS (ENG)", "ORÇ. ÁREAS COMUNS", "SUP. ÁREAS COMUNS"],
    "INFRA": ["EXECUÇÃO LIMP.", "EXECUÇÃO TER.", "EXECUÇÃO INFRA", "EXECUÇÃO PAV.", "EXECUÇÃO ÁREAS COMUNS"],
    "PRODUÇÃO": ["RADIER"],
    "ARQUITETURA & URBANISMO": ["PL.RADIER", "PE. ÁREAS COMUNS (URB)"],
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
    "PE. LIMP.":"PE. LIMP.", "ORÇ. LIMP.":"ORÇ. LIMP.", "SUP. LIMP.":"SUP. LIMP.", "PE. TER.":"PE. TER.", "ORÇ. TER.":"ORÇ. TER.", "SUP. TER.":"SUP. TER.", "PE. INFRA":"PE. INFRA", 
    "ORÇ. INFRA":"ORÇ. INFRA", "SUP. INFRA":"SUP. INFRA",
    "PE. PAV":"PE. PAV", "ORÇ. PAV":"ORÇ. PAV", "SUP. PAV":"SUP. PAV",
    "PE. ÁREAS COMUNS (ENG)":"PE. ÁREAS COMUNS (ENG)", "PE. ÁREAS COMUNS (URB)":"PE. ÁREAS COMUNS (URB)", "ORÇ. ÁREAS COMUNS":"ORÇ. ÁREAS COMUNS", "SUP. ÁREAS COMUNS":"SUP. ÁREAS COMUNS", "EXECUÇÃO ÁREAS COMUNS":"EXECUÇÃO ÁREAS COMUNS",
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
    "PE. LIMP.":"PE. LIMP.", "ORÇ. LIMP.":"ORÇ. LIMP.", "SUP. LIMP.":"SUP. LIMP.", "PE. TER.":"PE. TER.", "ORÇ. TER.":"ORÇ. TER.", "SUP. TER.":"SUP. TER.", "PE. INFRA":"PE. INFRA", 
    "ORÇ. INFRA":"ORÇ. INFRA", "SUP. INFRA":"SUP. INFRA",
    "PE. ÁREAS COMUNS (ENG)":"PE. ÁREAS COMUNS (ENG)", "PE. ÁREAS COMUNS (URB)":"PE. ÁREAS COMUNS (URB)", "ORÇ. ÁREAS COMUNS":"ORÇ. ÁREAS COMUNS", "SUP. ÁREAS COMUNS":"SUP. ÁREAS COMUNS", "EXECUÇÃO ÁREAS COMUNS":"EXECUÇÃO ÁREAS COMUNS",
    "PE. PAV":"PE. PAV", "ORÇ. PAV":"ORÇ. PAV", "SUP. PAV":"SUP. PAV"
}

SUBETAPAS = {
    "ENG. LIMP.": ["PE. LIMP.", "ORÇ. LIMP.", "SUP. LIMP."],
    "ENG. TER.": ["PE. TER.", "ORÇ. TER.", "SUP. TER."],
    "ENG. INFRA": ["PE. INFRA", "ORÇ. INFRA", "SUP. INFRA"],
    "ENG. PAV": ["PE. PAV", "ORÇ. PAV", "SUP. PAV"]
}

# Mapeamento reverso para encontrar a etapa pai a partir da subetapa
ETAPA_PAI_POR_SUBETAPA = {}
for etapa_pai, subetapas in SUBETAPAS.items():
    for subetapa in subetapas:
        ETAPA_PAI_POR_SUBETAPA[subetapa] = etapa_pai

ORDEM_ETAPAS_NOME_COMPLETO = [sigla_para_nome_completo.get(s, s) for s in ORDEM_ETAPAS_GLOBAL]
nome_completo_para_sigla = {v: k for k, v in sigla_para_nome_completo.items()}

GRUPO_POR_ETAPA = {}
for grupo, etapas in GRUPOS.items():
    for etapa in etapas:
        GRUPO_POR_ETAPA[etapa] = grupo

SETOR_POR_ETAPA = {mapeamento_etapas_usuario.get(etapa, etapa): setor for setor, etapas in SETOR.items() for etapa in etapas}


# --- Configurações de Estilo ---
class StyleConfig:
    CORES_POR_SETOR = {
        "PROSPECÇÃO": {"previsto": "#FEEFC4", "real": "#AE8141"},
        "LEGALIZAÇÃO": {"previsto": "#fadbfe", "real": "#BF08D3"},
        "PULMÃO": {"previsto": "#E9E8E8", "real": "#535252"},
        "ENGENHARIA": {"previsto": "#fbe3cf", "real": "#be5900"},
        "INFRA": {"previsto": "#daebfb", "real": "#125287"},
        "PRODUÇÃO": {"previsto": "#E1DFDF", "real": "#252424"},
        "ARQUITETURA & URBANISMO": {"previsto": "#D4D3F9", "real": "#453ECC"},
        "VENDA": {"previsto": "#dffde1", "real": "#096710"},
        "Não especificado": {"previsto": "#ffffff", "real": "#FFFFFF"}
    }

    @classmethod
    def set_offset_variacao_termino(cls, novo_offset):
        cls.OFFSET_VARIACAO_TERMINO = novo_offset

# --- Funções do Novo Gráfico Gantt ---
def ajustar_datas_com_pulmao(df, meses_pulmao=0):
    df_copy = df.copy()
    if meses_pulmao > 0:
        for i, row in df_copy.iterrows():
            if "PULMÃO" in row["Etapa"].upper(): # Identifica etapas de pulmão
                # Ajusta APENAS datas PREVISTAS do pulmão
                if pd.notna(row["Termino_Prevista"]):
                    df_copy.loc[i, "Termino_Prevista"] = row["Termino_Prevista"] + relativedelta(months=meses_pulmao)
                # DATAS REAIS PERMANECEM INALTERADAS
            else:
                # Para outras etapas, ajusta APENAS datas PREVISTAS
                if pd.notna(row["Inicio_Prevista"]):
                    df_copy.loc[i, "Inicio_Prevista"] = row["Inicio_Prevista"] + relativedelta(months=meses_pulmao)
                if pd.notna(row["Termino_Prevista"]):
                    df_copy.loc[i, "Termino_Prevista"] = row["Termino_Prevista"] + relativedelta(months=meses_pulmao)
                # DATAS REAIS PERMANECEM INALTERADAS
    return df_copy

def calcular_periodo_datas(df, meses_padding_inicio=1, meses_padding_fim=36):
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
        return calcular_periodo_datas(pd.DataFrame())

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

    return np.busday_count(data_inicio.date(), data_fim.date()) * sinal

def obter_data_meta_assinatura_novo(df_empreendimento):
    df_meta = df_empreendimento[df_empreendimento["Etapa"] == "DEMANDA MÍNIMA"]
    if df_meta.empty:
        return None
    for col in ["Inicio_Prevista", "Inicio_Real", "Termino_Prevista", "Termino_Real"]:
        if col in df_meta.columns and pd.notna(df_meta[col].iloc[0]):
            return pd.to_datetime(df_meta[col].iloc[0])
    return None

# --- CÓDIGO MODIFICADO ---
def converter_dados_para_gantt(df):
    if df.empty:
        return []

    gantt_data = []

    for empreendimento in df["Empreendimento"].unique():
        df_emp = df[df["Empreendimento"] == empreendimento].copy()

        # DEBUG: Verificar etapas disponíveis
        etapas_disponiveis = df_emp["Etapa"].unique()
        # print(f"=== ETAPAS PARA {empreendimento} ===")
        for etapa in etapas_disponiveis:
            # print(f"Etapa no DF: {etapa}")

        # --- NOVA LÓGICA: Calcular datas reais para etapas pai a partir das subetapas ---
            etapas_pai_para_calcular = {}
        for etapa_pai, subetapas in SUBETAPAS.items():
            subetapas_emp = df_emp[df_emp["Etapa"].isin([nome_completo_para_sigla.get(sub, sub) for sub in subetapas])]
            
            if not subetapas_emp.empty:
                inicio_real_min = subetapas_emp["Inicio_Real"].min()
                termino_real_max = subetapas_emp["Termino_Real"].max()
                
                etapas_pai_para_calcular[etapa_pai] = {
                    "inicio_real": inicio_real_min,
                    "termino_real": termino_real_max
                }

        tasks = []
        df_emp['Etapa'] = pd.Categorical(df_emp['Etapa'], categories=ORDEM_ETAPAS_NOME_COMPLETO, ordered=True)
        df_emp_sorted = df_emp.sort_values(by='Etapa').reset_index()

        for i, (idx, row) in enumerate(df_emp_sorted.iterrows()):
            start_date = row.get("Inicio_Prevista")
            end_date = row.get("Termino_Prevista")
            start_real = row.get("Inicio_Real")
            end_real_original = row.get("Termino_Real")
            progress = row.get("% concluído", 0)

            etapa_sigla = row.get("Etapa", "UNKNOWN")
            etapa_nome_completo = sigla_para_nome_completo.get(etapa_sigla, etapa_sigla)

            # --- VERIFICAR SE É UMA ETAPA PAI E TEM DATAS CALCULADAS DAS SUBETAPAS ---
            if etapa_nome_completo in etapas_pai_para_calcular:
                dados_pai = etapas_pai_para_calcular[etapa_nome_completo]
                
                if pd.notna(dados_pai["inicio_real"]):
                    start_real = dados_pai["inicio_real"]
                if pd.notna(dados_pai["termino_real"]):
                    end_real_original = dados_pai["termino_real"]
                
                subetapas_emp = df_emp[df_emp["Etapa"].isin([nome_completo_para_sigla.get(sub, sub) for sub in SUBETAPAS[etapa_nome_completo]])]
                if not subetapas_emp.empty and "% concluído" in subetapas_emp.columns:
                    progress_subetapas = subetapas_emp["% concluído"].apply(converter_porcentagem)
                    progress = progress_subetapas.mean()

            # --- CORREÇÃO PRINCIPAL: PARA SUBETAPAS, MANTER APENAS DADOS REAIS ---
            etapa_eh_subetapa = etapa_nome_completo in ETAPA_PAI_POR_SUBETAPA
            
            if etapa_eh_subetapa:
                start_date = None
                end_date = None
                if pd.isna(start_real) and pd.isna(end_real_original):
                    continue

            # Lógica para tratar datas vazias (apenas para etapas que não são subetapas)
            if not etapa_eh_subetapa:
                if pd.isna(start_date) or start_date is None: 
                    start_date = datetime.now()
                if pd.isna(end_date) or end_date is None: 
                    end_date = start_date + timedelta(days=30)

            end_real_visual = end_real_original
            if pd.notna(start_real) and progress < 100 and pd.isna(end_real_original):
                end_real_visual = datetime.now()

            # --- CORREÇÃO DO MAPEAMENTO DE GRUPO - LÓGICA MELHORADA ---
            grupo = "Não especificado"
            
            # Tenta pelo nome completo primeiro
            if etapa_nome_completo in GRUPO_POR_ETAPA:
                grupo = GRUPO_POR_ETAPA[etapa_nome_completo]
            # Se não encontrar, tenta pela sigla
            elif etapa_sigla in GRUPO_POR_ETAPA:
                grupo = GRUPO_POR_ETAPA[etapa_sigla]
            
            # DEBUG: Mostrar mapeamento
            # print(f"Etapa: {etapa_nome_completo} (sigla: {etapa_sigla}) -> Grupo: {grupo}")

            # Duração em Meses
            dur_prev_meses = None
            if pd.notna(start_date) and pd.notna(end_date):
                dur_prev_meses = (end_date - start_date).days / 30.4375

            dur_real_meses = None
            if pd.notna(start_real) and pd.notna(end_real_original):
                dur_real_meses = (end_real_original - start_real).days / 30.4375

            # Variação de Término (VT) - em dias úteis
            vt = calculate_business_days(end_date, end_real_original)

            # Duração em dias úteis
            duracao_prevista_uteis = calculate_business_days(start_date, end_date)
            duracao_real_uteis = calculate_business_days(start_real, end_real_original)

            # Variação de Duração (VD) - em dias úteis
            vd = None
            if pd.notna(duracao_real_uteis) and pd.notna(duracao_prevista_uteis):
                vd = duracao_real_uteis - duracao_prevista_uteis

            # Lógica de Cor do Status
            status_color_class = 'status-default'
            hoje = pd.Timestamp.now().normalize()

            if progress == 100:
                if pd.notna(end_real_original) and pd.notna(end_date):
                    if end_real_original <= end_date:
                        status_color_class = 'status-green'
                    else:
                        status_color_class = 'status-red'
            elif progress < 100 and pd.notna(start_real) and pd.notna(end_real_original) and (end_real_original < hoje):
                status_color_class = 'status-yellow'  # Em andamento, mas data real já passou

            task = {
                "id": f"t{i}", "name": etapa_nome_completo, "numero_etapa": i + 1,
                "start_previsto": start_date.strftime("%Y-%m-%d") if pd.notna(start_date) and start_date is not None else None,
                "end_previsto": end_date.strftime("%Y-%m-%d") if pd.notna(end_date) and end_date is not None else None,
                "start_real": pd.to_datetime(start_real).strftime("%Y-%m-%d") if pd.notna(start_real) else None,
                "end_real": pd.to_datetime(end_real_visual).strftime("%Y-%m-%d") if pd.notna(end_real_visual) else None,
                "end_real_original_raw": pd.to_datetime(end_real_original).strftime("%Y-%m-%d") if pd.notna(end_real_original) else None,
                "setor": row.get("SETOR", "Não especificado"),
                "grupo": grupo,
                "progress": int(progress),
                "inicio_previsto": start_date.strftime("%d/%m/%y") if pd.notna(start_date) and start_date is not None else "N/D",
                "termino_previsto": end_date.strftime("%d/%m/%y") if pd.notna(end_date) and end_date is not None else "N/D",
                "inicio_real": pd.to_datetime(start_real).strftime("%d/%m/%y") if pd.notna(start_real) else "N/D",
                "termino_real": pd.to_datetime(end_real_original).strftime("%d/%m/%y") if pd.notna(end_real_original) else "N/D",
                "duracao_prev_meses": f"{dur_prev_meses:.1f}".replace('.', ',') if dur_prev_meses is not None else "-",
                "duracao_real_meses": f"{dur_real_meses:.1f}".replace('.', ',') if dur_real_meses is not None else "-",

                "vt_text": f"{int(vt):+d}d" if pd.notna(vt) else "-",
                "vd_text": f"{int(vd):+d}d" if pd.notna(vd) else "-",

                "status_color_class": status_color_class
            }
            tasks.append(task)

        data_meta = obter_data_meta_assinatura_novo(df_emp)

        project = {
            "id": f"p{len(gantt_data)}", "name": empreendimento,
            "tasks": tasks,
            "meta_assinatura_date": data_meta.strftime("%Y-%m-%d") if data_meta else None
        }
        gantt_data.append(project)

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
def filtrar_etapas_nao_concluidas_func(df):
    if df.empty or "% concluído" not in df.columns: return df
    df_copy = df.copy()
    df_copy["% concluído"] = df_copy["% concluído"].apply(converter_porcentagem)
    return df_copy[df_copy["% concluído"] < 100]

def obter_data_meta_assinatura(df_original, empreendimento):
    df_meta = df_original[(df_original["Empreendimento"] == empreendimento) & (df_original["Etapa"] == "DEM.MIN")]
    if df_meta.empty: return pd.Timestamp.max
    for col in ["Termino_Prevista", "Inicio_Prevista", "Termino_Real", "Inicio_Real"]:
        if col in df_meta.columns and pd.notna(df_meta[col].iloc[0]): return df_meta[col].iloc[0]
    return pd.Timestamp.max

def criar_ordenacao_empreendimentos(df_original):
    """
    Cria uma lista ordenada dos nomes COMPLETOS dos empreendimentos
    com base na data da meta de assinatura (DEMANDA MÍNIMA).
    """
    # Use o nome COMPLETO como chave no dicionário
    empreendimentos_meta = {emp: obter_data_meta_assinatura(df_original, emp)
                           for emp in df_original["Empreendimento"].unique()}
    # Retorna a lista de nomes COMPLETOS ordenados pela data meta
    return sorted(empreendimentos_meta.keys(), key=empreendimentos_meta.get)


def aplicar_ordenacao_final(df, empreendimentos_ordenados):
    if df.empty: return df
    ordem_empreendimentos = {emp: idx for idx, emp in enumerate(empreendimentos_ordenados)}
    df["ordem_empreendimento"] = df["Empreendimento"].map(ordem_empreendimentos)
    ordem_etapas = {etapa: idx for idx, etapa in enumerate(ORDEM_ETAPAS_GLOBAL)}
    df["ordem_etapa"] = df["Etapa"].map(ordem_etapas).fillna(len(ordem_etapas))
    df_ordenado = df.sort_values(["ordem_empreendimento", "ordem_etapa"]).drop(["ordem_empreendimento", "ordem_etapa"], axis=1)
    return df_ordenado.reset_index(drop=True)


# --- *** FUNÇÃO gerar_gantt_por_projeto MODIFICADA *** ---
def gerar_gantt_por_projeto(df, tipo_visualizacao, df_original_para_ordenacao, pulmao_status, pulmao_meses):
        """
        Gera um único gráfico de Gantt com todos os projetos.
        """
        
        # --- Processar DF SEM PULMÃO ---
        df_sem_pulmao = df.copy()
        df_gantt_sem_pulmao = df_sem_pulmao.copy()

        for col in ["Inicio_Prevista", "Termino_Prevista", "Inicio_Real", "Termino_Real"]:
            if col in df_gantt_sem_pulmao.columns:
                df_gantt_sem_pulmao[col] = pd.to_datetime(df_gantt_sem_pulmao[col], errors="coerce")

        if "% concluído" not in df_gantt_sem_pulmao.columns:
            df_gantt_sem_pulmao["% concluído"] = 0
        df_gantt_sem_pulmao["% concluído"] = df_gantt_sem_pulmao["% concluído"].fillna(0).apply(converter_porcentagem)

        # Agrega os dados (usando nomes completos)
        df_gantt_agg_sem_pulmao = df_gantt_sem_pulmao.groupby(['Empreendimento', 'Etapa']).agg(
            Inicio_Prevista=('Inicio_Prevista', 'min'),
            Termino_Prevista=('Termino_Prevista', 'max'),
            Inicio_Real=('Inicio_Real', 'min'),
            Termino_Real=('Termino_Real', 'max'),
            **{'% concluído': ('% concluído', 'max')},
            SETOR=('SETOR', 'first')
        ).reset_index()

        df_gantt_agg_sem_pulmao["Etapa"] = df_gantt_agg_sem_pulmao["Etapa"].map(sigla_para_nome_completo).fillna(df_gantt_agg_sem_pulmao["Etapa"])
        
        # Mapear o SETOR e GRUPO
        df_gantt_agg_sem_pulmao["SETOR"] = df_gantt_agg_sem_pulmao["Etapa"].map(SETOR_POR_ETAPA).fillna(df_gantt_agg_sem_pulmao["SETOR"])
        df_gantt_agg_sem_pulmao["GRUPO"] = df_gantt_agg_sem_pulmao["Etapa"].map(GRUPO_POR_ETAPA).fillna("Não especificado")

        # Converte o DataFrame FILTRADO agregado em lista de projetos
        gantt_data_base = converter_dados_para_gantt(df_gantt_agg_sem_pulmao)

        # --- SE NÃO HÁ DADOS FILTRADOS, NÃO FAZ NADA ---
        if not gantt_data_base:
            st.warning("Nenhum dado disponível para exibir.")
            return

        # --- Prepara opções de filtro ---
        filter_options = {
            "setores": ["Todos"] + sorted(list(SETOR.keys())),
            "grupos": ["Todos"] + sorted(list(GRUPOS.keys())),
            "etapas": ["Todas"] + ORDEM_ETAPAS_NOME_COMPLETO
        }

        # --- Cria um único projeto com todos os empreendimentos ---
        all_projects_data = gantt_data_base
        project_id = "p_all_projects"
        
        # Usa o primeiro projeto como base ou cria um projeto consolidado
        if all_projects_data:
            project_base = {
                "id": project_id,
                "name": "Todos os Empreendimentos",  # Nome único
                "tasks": [],
                "meta_assinatura_date": None
            }
            
            # Coleta todas as tasks de todos os projetos
            all_tasks = []
            for project in all_projects_data:
                for task in project['tasks']:
                    # Adiciona o nome do empreendimento à task para identificação
                    task_with_emp = task.copy()
                    task_with_emp['empreendimento'] = project['name']
                    all_tasks.append(task_with_emp)
            
            project_base['tasks'] = all_tasks
            project = project_base
            correct_project_index_for_js = 0
        else:
            return

        # Filtra o DF agregado para cálculo de data_min/max
        df_para_datas = df_gantt_agg_sem_pulmao

        project = project_base
        tasks_base_data = project_base['tasks'] if project_base else []

        data_min_proj, data_max_proj = calcular_periodo_datas(df_para_datas)
        total_meses_proj = ((data_max_proj.year - data_min_proj.year) * 12) + (data_max_proj.month - data_min_proj.month) + 1

        num_tasks = len(project["tasks"]) if project else 0
        if num_tasks == 0:
            st.warning("Nenhuma tarefa disponível para exibir.")
            return
        num_tasks = len(project["tasks"]) if project else 0
        # Reduz o fator de multiplicação para evitar excesso de espaço
        altura_gantt = max(400, min(800, (num_tasks * 25) + 200))  # Limita a altura máxima

        # --- Geração do HTML ---
        gantt_html = f"""
        <!DOCTYPE html>
            <html lang="pt-BR">
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                
                <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/virtual-select-plugin@1.0.39/dist/virtual-select.min.css">
                
                <style>
                    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                    html, body {{ width: 100%; height: 100%; font-family: 'Segoe UI', sans-serif; background-color: #f5f5f5; color: #333; overflow: hidden; }}
                    .gantt-container {{ width: 100%; height: 100%; background-color: white; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); overflow: hidden; position: relative; display: flex; flex-direction: column; }}
                    .gantt-main {{ display: flex; flex: 1; overflow: hidden; }}
                    .gantt-sidebar-wrapper {{ width: 680px; display: flex; flex-direction: column; flex-shrink: 0; transition: width 0.3s ease-in-out; border-right: 2px solid #e2e8f0; overflow: hidden; }}
                    .gantt-sidebar-header {{ background: linear-gradient(135deg, #4a5568, #2d3748); display: flex; flex-direction: column; height: 60px; flex-shrink: 0; }}
                    .project-title-row {{ display: flex; justify-content: space-between; align-items: center; padding: 0 15px; height: 30px; color: white; font-weight: 600; font-size: 14px; }}
                    .toggle-sidebar-btn {{ background: rgba(255,255,255,0.2); border: none; color: white; width: 24px; height: 24px; border-radius: 5px; cursor: pointer; font-size: 14px; display: flex; align-items: center; justify-content: center; transition: background-color 0.2s, transform 0.3s ease-in-out; }}
                    .toggle-sidebar-btn:hover {{ background: rgba(255,255,255,0.4); }}
                    .sidebar-grid-header-wrapper {{ display: grid; grid-template-columns: 30px 1fr; color: #d1d5db; font-size: 9px; font-weight: 600; text-transform: uppercase; height: 30px; align-items: center; }}
                    .sidebar-grid-header {{ display: grid; grid-template-columns: 2.5fr 0.9fr 0.9fr 0.6fr 0.9fr 0.9fr 0.6fr 0.5fr 0.6fr 0.6fr; padding: 0 10px; align-items: center; }}
                    .sidebar-row {{ display: grid; grid-template-columns: 2.5fr 0.9fr 0.9fr 0.6fr 0.9fr 0.9fr 0.6fr 0.5fr 0.6fr 0.6fr; border-bottom: 1px solid #eff2f5; height: 30px; padding: 0 10px; background-color: white; transition: all 0.2s ease-in-out; }}
                    .sidebar-cell {{ display: flex; align-items: center; justify-content: center; font-size: 11px; color: #4a5568; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; padding: 0 8px; border: none; }}
                    .header-cell {{ text-align: center; }}
                    .header-cell.task-name-cell {{ text-align: left; }}
                    .gantt-sidebar-content {{ background-color: #f8f9fa; flex: 1; overflow-y: auto; overflow-x: hidden; }}
                    
                    /* Estilos para agrupamento */
                    .main-task-row {{ font-weight: 600; }}
                    .main-task-row.has-subtasks {{ cursor: pointer; }}
                    .expand-collapse-btn {{
                        background: none;
                        border: none;
                        cursor: pointer;
                        width: 20px;
                        height: 20px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 12px;
                        color: #4a5568;
                        margin-right: 5px;
                    }}
                    .subtask-row {{ 
                        display: none;
                        background-color: #f8fafc;
                        padding-left: 40px;
                    }}
                    .subtask-row.visible {{ display: grid; }}
                    .gantt-subtask-row {{ 
                        display: none;
                        background-color: #f8fafc;
                    }}
                    .gantt-subtask-row.visible {{ 
                        display: block !important;
                    }}
                    
                    /* Estilo para barras de etapas pai quando subetapas estão expandidas */
                    .gantt-bar.parent-task-real.expanded {{
                        background-color: transparent !important;
                        border: 2px solid;
                        box-shadow: none;
                    }}
                    .gantt-bar.parent-task-real.expanded .bar-label {{
                        color: #000000 !important;
                        text-shadow: 0 1px 2px rgba(255,255,255,0.8);
                    }}
                    
                    .sidebar-group-wrapper {{
                        display: flex;
                        border-bottom: 1px solid #e2e8f0;
                    }}
                    .gantt-sidebar-content > .sidebar-group-wrapper:last-child {{ border-bottom: none; }}
                    .sidebar-group-title-vertical {{
                        width: 30px; background-color: #f8fafc; color: #4a5568;
                        font-size: 8px; 
                        font-weight: 700; text-transform: uppercase;
                        display: flex; align-items: center; justify-content: center;
                        writing-mode: vertical-rl; transform: rotate(180deg);
                        flex-shrink: 0; border-right: 1px solid #e2e8f0;
                        text-align: center; white-space: nowrap; overflow: hidden;
                        text-overflow: ellipsis; padding: 5px 0; letter-spacing: -0.5px;
                        align-self: flex-start;
                    }}
                    .sidebar-group-spacer {{ display: none; }}
                    .sidebar-rows-container {{ flex-grow: 1; }}
                    .sidebar-row.odd-row {{ background-color: #fdfdfd; }}
                    .sidebar-rows-container .sidebar-row:last-child {{ border-bottom: none; }}
                    .sidebar-row:hover {{ background-color: #f5f8ff; }}
                    .sidebar-cell.task-name-cell {{ justify-content: flex-start; font-weight: 600; color: #2d3748; }}
                    .sidebar-cell.status-green {{ color: #1E8449; font-weight: 700; }}
                    .sidebar-cell.status-red    {{ color: #C0392B; font-weight: 700; }}
                    .sidebar-cell.status-yellow{{ color: #B9770E; font-weight: 700; }}
                    .sidebar-cell.status-default{{ color: #566573; font-weight: 700; }}
                    .sidebar-row .sidebar-cell:nth-child(2),
                    .sidebar-row .sidebar-cell:nth-child(3),
                    .sidebar-row .sidebar-cell:nth-child(4),
                    .sidebar-row .sidebar-cell:nth-child(5),
                    .sidebar-row .sidebar-cell:nth-child(6),
                    .sidebar-row .sidebar-cell:nth-child(7),
                    .sidebar-row .sidebar-cell:nth-child(8),
                    .sidebar-row .sidebar-cell:nth-child(9),
                    .sidebar-row .sidebar-cell:nth-child(10) {{ font-size: 8px; }}
                    .gantt-row-spacer, .sidebar-row-spacer {{
                        height: 15px;
                        border: none;
                        border-bottom: 1px solid #e2e8f0; 
                        box-sizing: border-box; 
                    }}
                    .gantt-row-spacer {{ background-color: #ffffff; position: relative; z-index: 5; }}
                    .sidebar-row-spacer {{ background-color: #f8f9fa; }}
                    .gantt-sidebar-wrapper.collapsed {{ width: 250px; }}
                    .gantt-sidebar-wrapper.collapsed .sidebar-grid-header, .gantt-sidebar-wrapper.collapsed .sidebar-row {{ grid-template-columns: 1fr; padding: 0 15px 0 10px; }}
                    .gantt-sidebar-wrapper.collapsed .header-cell:not(.task-name-cell), .gantt-sidebar-wrapper.collapsed .sidebar-cell:not(.task-name-cell) {{ display: none; }}
                    .gantt-sidebar-wrapper.collapsed .toggle-sidebar-btn {{ transform: rotate(180deg); }}
                    .gantt-chart-content {{ flex: 1; overflow: auto; position: relative; background-color: white; user-select: none; cursor: grab; }}
                    .gantt-chart-content.active {{ cursor: grabbing; }}
                    .chart-container {{ position: relative; min-width: {total_meses_proj * 30}px; }}
                    .chart-header {{ background: linear-gradient(135deg, #4a5568, #2d3748); color: white; height: 60px; position: sticky; top: 0; z-index: 9; display: flex; flex-direction: column; }}
                    .year-header {{ height: 30px; display: flex; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.2); }}
                    .year-section {{ text-align: center; font-weight: 600; font-size: 12px; display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,0.1); height: 100%; }}
                    .month-header {{ height: 30px; display: flex; align-items: center; }}
                    .month-cell {{ width: 30px; height: 30px; border-right: 1px solid rgba(255,255,255,0.2); display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 500; }}
                    .chart-body {{ position: relative; }}
                    .gantt-row {{ position: relative; height: 30px; border-bottom: 1px solid #eff2f5; background-color: white; }}
                    .gantt-bar {{ position: absolute; height: 14px; top: 8px; border-radius: 3px; cursor: pointer; transition: all 0.2s ease; display: flex; align-items: center; padding: 0 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                    .gantt-bar-overlap {{ position: absolute; height: 14px; top: 8px; background-image: linear-gradient(45deg, rgba(0, 0, 0, 0.25) 25%, transparent 25%, transparent 50%, rgba(0, 0, 0, 0.25) 50%, rgba(0, 0, 0, 0.25) 75%, transparent 75%, transparent); background-size: 8px 8px; z-index: 9; pointer-events: none; border-radius: 3px; }}
                    .gantt-bar:hover {{ transform: translateY(-1px) scale(1.01); box-shadow: 0 4px 8px rgba(0,0,0,0.2); z-index: 10 !important; }}
                    .gantt-bar.previsto {{ z-index: 7; }}
                    .gantt-bar.real {{ z-index: 8; }}
                    .bar-label {{ font-size: 8px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-shadow: 0 1px 2px rgba(0,0,0,0.4); }}
                    .gantt-bar.real .bar-label {{ color: white; }}
                    .gantt-bar.previsto .bar-label {{ color: #6C6C6C; }}
                    .tooltip {{ position: fixed; background-color: #2d3748; color: white; padding: 6px 10px; border-radius: 4px; font-size: 11px; z-index: 1000; box-shadow: 0 2px 8px rgba(0,0,0,0.3); pointer-events: none; opacity: 0; transition: opacity 0.2s ease; max-width: 220px; }}
                    .tooltip.show {{ opacity: 1; }}
                    .today-line {{ position: absolute; top: 60px; bottom: 0; width: 1px; background-color: #fdf1f1; z-index: 5; box-shadow: 0 0 1px rgba(229, 62, 62, 0.6); }}
                    .month-divider {{ position: absolute; top: 60px; bottom: 0; width: 1px; background-color: #fcf6f6; z-index: 4; pointer-events: none; }}
                    .month-divider.first {{ background-color: #eeeeee; width: 1px; }}
                    .meta-line {{ position: absolute; top: 60px; bottom: 0; width: 2px; border-left: 2px dashed #8e44ad; z-index: 5; box-shadow: 0 0 4px rgba(142, 68, 173, 0.6); }}
                    .meta-line-label {{ position: absolute; top: 65px; background-color: #8e44ad; color: white; padding: 2px 5px; border-radius: 4px; font-size: 9px; font-weight: 600; white-space: nowrap; z-index: 8; transform: translateX(-50%); }}
                    .gantt-chart-content, .gantt-sidebar-content {{
                        scrollbar-width: thin;
                        scrollbar-color: transparent transparent;
                    }}
                    .gantt-chart-content:hover, .gantt-sidebar-content:hover {{
                        scrollbar-color: #d1d5db transparent;
                    }}
                    .gantt-chart-content::-webkit-scrollbar,
                    .gantt-sidebar-content::-webkit-scrollbar {{
                        height: 8px;
                        width: 8px;
                    }}
                    .gantt-chart-content::-webkit-scrollbar-track,
                    .gantt-sidebar-content::-webkit-scrollbar-track {{
                        background: transparent;
                    }}
                    .gantt-chart-content::-webkit-scrollbar-thumb,
                    .gantt-sidebar-content::-webkit-scrollbar-thumb {{
                        background-color: transparent;
                        border-radius: 4px;
                    }}
                    .gantt-chart-content:hover::-webkit-scrollbar-thumb,
                    .gantt-sidebar-content:hover::-webkit-scrollbar-thumb {{
                        background-color: #d1d5db;
                    }}
                    .gantt-chart-content:hover::-webkit-scrollbar-thumb:hover,
                    .gantt-sidebar-content:hover::-webkit-scrollbar-thumb:hover {{
                        background-color: #a8b2c1;
                    }}
                    .gantt-toolbar {{
                        position: absolute; top: 10px; right: 10px;
                        z-index: 100;
                        display: flex;
                        flex-direction: column;
                        gap: 5px;
                        background: rgba(45, 55, 72, 0.9); /* Cor de fundo escura para minimalismo */
                        border-radius: 6px;
                        padding: 5px;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                    }}
                    .toolbar-btn {{
                        background: none;
                        border: none;
                        width: 36px;
                        height: 36px;
                        border-radius: 4px;
                        cursor: pointer;
                        font-size: 20px;
                        color: white;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        transition: background-color 0.2s, box-shadow 0.2s;
                        padding: 0;
                    }}
                    .toolbar-btn:hover {{
                        background-color: rgba(255, 255, 255, 0.1);
                        box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.2);
                    }}
                    .toolbar-btn.is-fullscreen {{
                        background-color: #3b82f6; /* Cor de destaque para o botão ativo */
                        box-shadow: 0 0 0 2px #3b82f6;
                    }}
                    .toolbar-btn.is-fullscreen:hover {{
                        background-color: #2563eb;
                    }}
                    .floating-filter-menu {{
                        display: none;
                        position: absolute;
                        top: 10px; right: 50px; /* Ajuste a posição para abrir ao lado da barra de ferramentas */
                        width: 280px;
                        background: white;
                        border-radius: 8px;
                        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
                        z-index: 99;
                        padding: 15px;
                        border: 1px solid #e2e8f0;
                    }}
                    .floating-filter-menu.is-open {{
                        display: block;
                    }}
                    .filter-group {{ margin-bottom: 12px; }}
                    .filter-group label {{
                        display: block;
                        font-size: 11px; font-weight: 600;
                        color: #4a5568; margin-bottom: 4px;
                        text-transform: uppercase;
                    }}
                    .filter-group select, .filter-group input[type=number] {{
                        width: 100%;
                        padding: 6px 8px;
                        border: 1px solid #cbd5e0;
                        border-radius: 4px;
                        font-size: 13px;
                    }}
                    .filter-group-radio, .filter-group-checkbox {{
                        display: flex; align-items: center;
                        padding: 5px 0;
                    }}
                    .filter-group-radio input, .filter-group-checkbox input {{
                        width: auto; margin-right: 8px;
                    }}
                    .filter-group-radio label, .filter-group-checkbox label {{
                        font-size: 13px; font-weight: 500;
                        color: #2d3748; margin-bottom: 0; text-transform: none;
                    }}
                    .filter-apply-btn {{
                        width: 100%; padding: 8px; font-size: 14px; font-weight: 600;
                        color: white; background-color: #2d3748;
                        border: none; border-radius: 4px; cursor: pointer;
                        margin-top: 5px;
                    }}

                    .floating-filter-menu .vscomp-toggle-button {{
                        border: 1px solid #cbd5e0;
                        border-radius: 4px;
                        padding: 6px 8px;
                        font-size: 13px;
                        min-height: 30px;
                    }}
                    .floating-filter-menu .vscomp-options {{
                        font-size: 13px;
                    }}
                    .floating-filter-menu .vscomp-option {{
                        min-height: 30px;
                    }}
                    .floating-filter-menu .vscomp-search-input {{
                        height: 30px;
                        font-size: 13px;
                    }}

                </style>
            </head>
            <body>
                <script id="grupos-gantt-data" type="application/json">{json.dumps(GRUPOS)}</script>
                <script id="subetapas-data" type="application/json">{json.dumps(SUBETAPAS)}</script>
                
                <div class="gantt-container" id="gantt-container-{project['id']}">
                <div class="gantt-toolbar" id="gantt-toolbar-{project["id"]}">
                    <button class="toolbar-btn" id="filter-btn-{project["id"]}" title="Filtros">
                        <span>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
                            </svg>
                        </span>
                    </button>
                    <button class="toolbar-btn" id="fullscreen-btn-{project["id"]}" title="Tela Cheia">
                        <span>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path>
                            </svg>
                        </span>
                    </button>
                </div>

                    <div class="floating-filter-menu" id="filter-menu-{project['id']}">
                        <div class="filter-group">
                            <label for="filter-project-{project['id']}">Empreendimento</label>
                            <select id="filter-project-{project['id']}"></select>
                        </div>
                        <div class="filter-group">
                            <label for="filter-setor-{project['id']}">Setor</label>
                            
                            <div id="filter-setor-{project['id']}"></div>
                        </div>
                        <div class="filter-group">
                            <label for="filter-grupo-{project['id']}">Grupo</label>
                            
                            <div id="filter-grupo-{project['id']}"></div>
                        </div>
                        <div class="filter-group">
                            <label for="filter-etapa-{project['id']}">Etapa</label>
                            
                            <div id="filter-etapa-{project['id']}"></div>
                        </div>
                        <div class="filter-group">
                            <div class="filter-group-checkbox">
                                <input type="checkbox" id="filter-concluidas-{project['id']}">
                                <label for="filter-concluidas-{project['id']}">Mostrar apenas não concluídas</label>
                            </div>
                        </div>
                        <div class="filter-group">
                            <label>Visualização</label>
                            <div class="filter-group-radio">
                                <input type="radio" id="filter-vis-ambos-{project['id']}" name="filter-vis-{project['id']}" value="Ambos" checked>
                                <label for="filter-vis-ambos-{project['id']}">Ambos</label>
                            </div>
                            <div class="filter-group-radio">
                                <input type="radio" id="filter-vis-previsto-{project['id']}" name="filter-vis-{project['id']}" value="Previsto">
                                <label for="filter-vis-previsto-{project['id']}">Previsto</label>
                            </div>
                            <div class="filter-group-radio">
                                <input type="radio" id="filter-vis-real-{project['id']}" name="filter-vis-{project['id']}" value="Real">
                                <label for="filter-vis-real-{project['id']}">Real</label>
                            </div>
                        </div>
                        <div class="filter-group">
                            <label>Simulação Pulmão</label>
                            <div class="filter-group-radio">
                                <input type="radio" id="filter-pulmao-sem-{project['id']}" name="filter-pulmao-{project['id']}" value="Sem Pulmão">
                                <label for="filter-pulmao-sem-{project['id']}">Sem Pulmão</label>
                            </div>
                            <div class="filter-group-radio">
                                <input type="radio" id="filter-pulmao-com-{project['id']}" name="filter-pulmao-{project['id']}" value="Com Pulmão">
                                <label for="filter-pulmao-com-{project['id']}">Com Pulmão</label>
                            </div>
                            <div class="filter-group" id="pulmao-meses-group-{project['id']}" style="margin-top: 8px; display: none; padding-left: 25px;">
                                <label for="filter-pulmao-meses-{project['id']}" style="font-size: 12px; font-weight: 500;">Meses de Pulmão:</label>
                                <input type="number" id="filter-pulmao-meses-{project['id']}" value="{pulmao_meses}" min="0" max="36" step="1" style="padding: 4px 6px; font-size: 12px; height: 28px; width: 80px;">
                            </div>
                            </div>
                        <button class="filter-apply-btn" id="filter-apply-btn-{project['id']}">Aplicar Filtros</button>
                    </div>

                    <div class="gantt-main">
                        <div class="gantt-sidebar-wrapper" id="gantt-sidebar-wrapper-{project['id']}">
                            <div class="gantt-sidebar-header">
                                <div class="project-title-row">
                                    <span>{project["name"]}</span>
                                    <button class="toggle-sidebar-btn" id="toggle-sidebar-btn-{project['id']}" title="Recolher/Expandir Tabela">«</button>
                                </div>
                                <div class="sidebar-grid-header-wrapper">
                                    <div></div>
                                    <div class="sidebar-grid-header">
                                        <div class="header-cell task-name-cell">SERVIÇO</div>
                                        <div class="header-cell">INÍCIO-P</div>
                                        <div class="header-cell">TÉRMINO-P</div>
                                        <div class="header-cell">DUR-P</div>
                                        <div class="header-cell">INÍCIO-R</div>
                                        <div class="header-cell">TÉRMINO-R</div>
                                        <div class="header-cell">DUR-R</div>
                                        <div class="header-cell">%</div>
                                        <div class="header-cell">VT</div>
                                        <div class="header-cell">VD</div>
                                    </div>
                                </div>
                            </div>
                            <div class="gantt-sidebar-content" id="gantt-sidebar-content-{project['id']}"></div>
                        </div>
                        <div class="gantt-chart-content" id="gantt-chart-content-{project['id']}">
                            <div class="chart-container" id="chart-container-{project["id"]}">
                                <div class="chart-header">
                                    <div class="year-header" id="year-header-{project["id"]}"></div>
                                    <div class="month-header" id="month-header-{project["id"]}"></div>
                                </div>
                                <div class="chart-body" id="chart-body-{project["id"]}"></div>
                                <div class="today-line" id="today-line-{project["id"]}"></div>
                                <div class="meta-line" id="meta-line-{project["id"]}"></div>
                                <div class="meta-line-label" id="meta-line-label-{project["id"]}"></div>
                            </div>
                        </div>
                    </div>
                    <div class="tooltip" id="tooltip-{project["id"]}"></div>
                </div>
                
                
                <script src="https://cdn.jsdelivr.net/npm/virtual-select-plugin@1.0.39/dist/virtual-select.min.js"></script>
                

                <script>
                    // DEBUG: Verificar dados
                    console.log('Inicializando Gantt para projeto:', '{project["name"]}');
                    
                    const coresPorSetor = {json.dumps(StyleConfig.CORES_POR_SETOR)};

                    const allProjectsData = {json.dumps(gantt_data_base)};

                    let currentProjectIndex = {correct_project_index_for_js};
                    const initialProjectIndex = {correct_project_index_for_js};

                    let projectData = {json.dumps([project])};

                    // Datas originais (Python)
                    const dataMinStr = '{data_min_proj.strftime("%Y-%m-%d")}';
                    const dataMaxStr = '{data_max_proj.strftime("%Y-%m-%d")}';

                    let activeDataMinStr = dataMinStr;
                    let activeDataMaxStr = dataMaxStr;

                    const initialTipoVisualizacao = '{tipo_visualizacao}';
                    let tipoVisualizacao = '{tipo_visualizacao}';
                    const PIXELS_PER_MONTH = 30;

                    // --- ESTRUTURA DE SUBETAPAS ---
                    const SUBETAPAS = JSON.parse(document.getElementById('subetapas-data').textContent);
                    
                    // Mapeamento reverso para encontrar etapa pai
                    const ETAPA_PAI_POR_SUBETAPA = {{}};
                    for (const [etapaPai, subetapas] of Object.entries(SUBETAPAS)) {{
                        for (const subetapa of subetapas) {{
                            ETAPA_PAI_POR_SUBETAPA[subetapa] = etapaPai;
                        }}
                    }}

                    // --- INÍCIO HELPERS DE DATA E PULMÃO ---
                    const etapas_pulmao = ["PULMÃO VENDA", "PULMÃO INFRA", "PULMÃO RADIER"];
                    const etapas_sem_alteracao = ["PROSPECÇÃO", "RADIER", "DEMANDA MÍNIMA", "PE. ÁREAS COMUNS (URB)", "PE. ÁREAS COMUNS (ENG)", "ORÇ. ÁREAS COMUNS", "SUP. ÁREAS COMUNS", "EXECUÇÃO ÁREAS COMUNS"];

                    const formatDateDisplay = (dateStr) => {{
                        if (!dateStr) return "N/D";
                        const d = parseDate(dateStr);
                        if (!d || isNaN(d.getTime())) return "N/D";
                        const day = String(d.getUTCDate()).padStart(2, '0');
                        const month = String(d.getUTCMonth() + 1).padStart(2, '0');
                        const year = String(d.getUTCFullYear()).slice(-2);
                        return `${{day}}/${{month}}/${{year}}`;
                    }};

                    function addMonths(dateStr, months) {{
                        if (!dateStr) return null;
                        const date = parseDate(dateStr);
                        if (!date || isNaN(date.getTime())) return null;
                        const originalDay = date.getUTCDate();
                        date.setUTCMonth(date.getUTCMonth() + months);
                        if (date.getUTCDate() !== originalDay) {{
                            date.setUTCDate(0);
                        }}
                        return date.toISOString().split('T')[0];
                    }}
                    // --- FIM HELPERS DE DATA E PULMÃO ---

                    const filterOptions = {json.dumps(filter_options)};

                    let allTasks_baseData = {json.dumps(tasks_base_data)};

                    const initialPulmaoStatus = '{pulmao_status}';
                    const initialPulmaoMeses = {pulmao_meses};

                    let pulmaoStatus = '{pulmao_status}';
                    let filtersPopulated = false;

                    // *** INÍCIO: Variáveis Globais para Virtual Select ***
                    let vsSetor, vsGrupo, vsEtapa;
                    // *** FIM: Variáveis Globais para Virtual Select ***

                    function parseDate(dateStr) {{ 
                        if (!dateStr) return null; 
                        const [year, month, day] = dateStr.split('-').map(Number); 
                        return new Date(Date.UTC(year, month - 1, day)); 
                    }}

                    function findNewDateRange(tasks) {{
                        let minDate = null;
                        let maxDate = null;

                        const updateRange = (dateStr) => {{
                            if (!dateStr) return;
                            const date = parseDate(dateStr);
                            if (!date || isNaN(date.getTime())) return;

                            if (!minDate || date < minDate) {{
                                minDate = date;
                            }}
                            if (!maxDate || date > maxDate) {{
                                maxDate = date;
                            }}
                        }};

                        tasks.forEach(task => {{
                            updateRange(task.start_previsto);
                            updateRange(task.end_previsto);
                            updateRange(task.start_real);
                            updateRange(task.end_real_original_raw || task.end_real);
                        }});

                        return {{
                            min: minDate ? minDate.toISOString().split('T')[0] : null,
                            max: maxDate ? maxDate.toISOString().split('T')[0] : null
                        }};
                    }}

                    // --- FUNÇÕES DE AGRUPAMENTO ---
                    function organizarTasksComSubetapas(tasks) {{
                        const tasksOrganizadas = [];
                        const tasksProcessadas = new Set();
                        
                        // Primeiro, adiciona todas as etapas principais
                        tasks.forEach(task => {{
                            if (tasksProcessadas.has(task.name)) return;
                            
                            const etapaPai = ETAPA_PAI_POR_SUBETAPA[task.name];
                            
                            // Se é uma subetapa, pula por enquanto
                            if (etapaPai) return;
                            
                            // Se é uma etapa principal que tem subetapas
                            if (SUBETAPAS[task.name]) {{
                                const taskPrincipal = {{...task, isMainTask: true, expanded: false}};
                                tasksOrganizadas.push(taskPrincipal);
                                tasksProcessadas.add(task.name);
                                
                                // Adiciona subetapas
                                SUBETAPAS[task.name].forEach(subetapaNome => {{
                                    const subetapa = tasks.find(t => t.name === subetapaNome);
                                    if (subetapa) {{
                                        const subetapaComPai = {{
                                            ...subetapa, 
                                            isSubtask: true, 
                                            parentTask: task.name,
                                            visible: false
                                        }};
                                        tasksOrganizadas.push(subetapaComPai);
                                        tasksProcessadas.add(subetapaNome);
                                    }}
                                }});
                            }} else {{
                                // É uma etapa principal sem subetapas
                                tasksOrganizadas.push({{...task, isMainTask: true}});
                                tasksProcessadas.add(task.name);
                            }}
                        }});
                        
                        // Adiciona quaisquer tasks que não foram processadas (não estão no mapeamento)
                        tasks.forEach(task => {{
                            if (!tasksProcessadas.has(task.name)) {{
                                tasksOrganizadas.push({{...task, isMainTask: true}});
                                tasksProcessadas.add(task.name);
                            }}
                        }});
                        
                        return tasksOrganizadas;
                    }}

                    function toggleSubtasks(taskName) {{
                        const subtaskRows = document.querySelectorAll('.subtask-row[data-parent="' + taskName + '"]');
                        const ganttSubtaskRows = document.querySelectorAll('.gantt-subtask-row[data-parent="' + taskName + '"]');
                        const button = document.querySelector('.expand-collapse-btn[data-task="' + taskName + '"]');
                        
                        const isVisible = subtaskRows[0]?.classList.contains('visible');
                        
                        // Alterna visibilidade
                        subtaskRows.forEach(row => {{
                            row.classList.toggle('visible', !isVisible);
                        }});
                        
                        ganttSubtaskRows.forEach(row => {{
                            row.style.display = isVisible ? 'none' : 'block';
                            row.classList.toggle('visible', !isVisible);
                        }});
                        
                        // Atualiza ícone do botão
                        if (button) {{
                            button.textContent = isVisible ? '+' : '-';
                        }}
                        
                        // Atualiza estado no array de tasks
                        const taskIndex = projectData[0].tasks.findIndex(t => t.name === taskName && t.isMainTask);
                        if (taskIndex !== -1) {{
                            projectData[0].tasks[taskIndex].expanded = !isVisible;
                        }}

                        // Aplica/remove estilo nas barras reais da etapa pai
                        updateParentTaskBarStyle(taskName, !isVisible);
                    }}

                    function updateParentTaskBarStyle(taskName, isExpanded) {{
                        const parentTaskRow = document.querySelector('.gantt-row[data-task="' + taskName + '"]');
                        if (parentTaskRow) {{
                            const realBars = parentTaskRow.querySelectorAll('.gantt-bar.real');
                            realBars.forEach(bar => {{
                                if (isExpanded) {{
                                    bar.classList.add('parent-task-real', 'expanded');
                                    // Define a cor da borda com a mesma cor original
                                    const originalColor = bar.style.backgroundColor;
                                    bar.style.borderColor = originalColor;
                                }} else {{
                                    bar.classList.remove('parent-task-real', 'expanded');
                                    bar.style.borderColor = '';
                                }}
                            }});
                        }}
                    }}

                    function initGantt() {{
                        console.log('Iniciando Gantt com dados:', projectData);
                        
                        // Verificar se há dados para renderizar
                        if (!projectData || !projectData[0] || !projectData[0].tasks || projectData[0].tasks.length === 0) {{
                            console.error('Nenhum dado disponível para renderizar');
                            document.getElementById('chart-body-{project["id"]}').innerHTML = '<div style="padding: 20px; text-align: center; color: red;">Erro: Nenhum dado disponível</div>';
                            return;
                        }}

                        // Organizar tasks com estrutura de subetapas
                        projectData[0].tasks = organizarTasksComSubetapas(projectData[0].tasks);
                        allTasks_baseData = JSON.parse(JSON.stringify(projectData[0].tasks));

                        applyInitialPulmaoState();

                        if (initialPulmaoStatus === 'Com Pulmão' && initialPulmaoMeses > 0) {{
                            const {{ min: newMinStr, max: newMaxStr }} = findNewDateRange(projectData[0].tasks);
                            const newMin = parseDate(newMinStr);
                            const newMax = parseDate(newMaxStr);
                            const originalMin = parseDate(activeDataMinStr);
                            const originalMax = parseDate(activeDataMaxStr);

                            let finalMinDate = originalMin;
                            if (newMin && newMin < finalMinDate) {{
                                finalMinDate = newMin;
                            }}
                            let finalMaxDate = originalMax;
                            if (newMax && newMax > finalMaxDate) {{
                                finalMaxDate = newMax;
                            }}

                            finalMinDate = new Date(finalMinDate.getTime());
                            finalMaxDate = new Date(finalMaxDate.getTime());

                            finalMinDate.setUTCDate(1);
                            finalMaxDate.setUTCMonth(finalMaxDate.getUTCMonth() + 1, 0);

                            activeDataMinStr = finalMinDate.toISOString().split('T')[0];
                            activeDataMaxStr = finalMaxDate.toISOString().split('T')[0];
                        }}

                        renderSidebar();
                        renderHeader();
                        renderChart();
                        renderMonthDividers();
                        setupEventListeners();
                        positionTodayLine();
                        positionMetaLine();
                        populateFilters();
                    }}

                    function applyInitialPulmaoState() {{
                        if (initialPulmaoStatus === 'Com Pulmão' && initialPulmaoMeses > 0) {{
                            const offsetMeses = -initialPulmaoMeses;
                            let baseTasks = projectData[0].tasks;

                            baseTasks.forEach(task => {{
                                const etapaNome = task.name;
                                if (etapas_sem_alteracao.includes(etapaNome)) {{
                                    // Não altera datas
                                }}
                                else if (etapas_pulmao.includes(etapaNome)) {{
                                    // APENAS PREVISTO
                                    task.start_previsto = addMonths(task.start_previsto, offsetMeses);
                                    task.inicio_previsto = formatDateDisplay(task.start_previsto);
                                }}
                                else {{
                                    // APENAS PREVISTO
                                    task.start_previsto = addMonths(task.start_previsto, offsetMeses);
                                    task.end_previsto = addMonths(task.end_previsto, offsetMeses);
                                    task.inicio_previsto = formatDateDisplay(task.start_previsto);
                                    task.termino_previsto = formatDateDisplay(task.end_previsto);
                                    // NÃO modificar dados reais
                                }}
                            }});

                            allTasks_baseData = JSON.parse(JSON.stringify(baseTasks));
                        }}
                    }}

                    function renderSidebar() {{
                        const sidebarContent = document.getElementById('gantt-sidebar-content-{project['id']}');
                        const gruposGantt = JSON.parse(document.getElementById('grupos-gantt-data').textContent);
                        const tasks = projectData[0].tasks;
                        
                        if (!tasks || tasks.length === 0) {{
                            sidebarContent.innerHTML = '<div style="padding: 20px; text-align: center; color: #666;">Nenhuma tarefa disponível para os filtros aplicados</div>';
                            return;
                        }}
                        
                        let html = '';
                        let globalRowIndex = 0;
                        const groupKeys = Object.keys(gruposGantt);
                        
                        for (let i = 0; i < groupKeys.length; i++) {{
                            const grupo = groupKeys[i];
                            const tasksInGroupNames = gruposGantt[grupo].filter(etapaNome => tasks.some(t => t.name === etapaNome && !t.isSubtask));
                            if (tasksInGroupNames.length === 0) continue;
                            
                            const groupHeight = (tasksInGroupNames.length * 30);
                            html += `<div class="sidebar-group-wrapper">`;
                            html += `<div class="sidebar-group-title-vertical" style="height: ${{groupHeight}}px;"><span>${{grupo}}</span></div>`;
                            html += `<div class="sidebar-rows-container">`;
                            
                            gruposGantt[grupo].forEach(etapaNome => {{
                                const task = tasks.find(t => t.name === etapaNome && !t.isSubtask);
                                if (task) {{
                                    globalRowIndex++;
                                    const rowClass = globalRowIndex % 2 !== 0 ? 'odd-row' : '';
                                    const hasSubtasks = SUBETAPAS[task.name] && SUBETAPAS[task.name].length > 0;
                                    const mainTaskClass = hasSubtasks ? 'main-task-row has-subtasks' : 'main-task-row';
                                    
                                    html += `<div class="sidebar-row ${{mainTaskClass}} ${{rowClass}}" data-task="${{task.name}}">`;
                                    
                                    // Coluna do botão de expandir/recolher
                                    if (hasSubtasks) {{
                                        html += `<div class="sidebar-cell task-name-cell" style="display: flex; align-items: center;">`;
                                        html += `<button class="expand-collapse-btn" data-task="${{task.name}}">${{task.expanded ? '-' : '+'}}</button>`;
                                        html += `<span title="${{task.numero_etapa}}. ${{task.name}}">${{task.numero_etapa}}. ${{task.name}}</span>`;
                                        html += `</div>`;
                                    }} else {{
                                        html += `<div class="sidebar-cell task-name-cell" title="${{task.numero_etapa}}. ${{task.name}}">${{task.numero_etapa}}. ${{task.name}}</div>`;
                                    }}
                                    
                                    html += `<div class="sidebar-cell">${{task.inicio_previsto}}</div>`;
                                    html += `<div class="sidebar-cell">${{task.termino_previsto}}</div>`;
                                    html += `<div class="sidebar-cell">${{task.duracao_prev_meses}}</div>`;
                                    html += `<div class="sidebar-cell">${{task.inicio_real}}</div>`;
                                    html += `<div class="sidebar-cell">${{task.termino_real}}</div>`;
                                    html += `<div class="sidebar-cell">${{task.duracao_real_meses}}</div>`;
                                    html += `<div class="sidebar-cell ${{task.status_color_class}}">${{task.progress}}%</div>`;
                                    html += `<div class="sidebar-cell ${{task.status_color_class}}">${{task.vt_text}}</div>`;
                                    html += `<div class="sidebar-cell ${{task.status_color_class}}">${{task.vd_text}}</div>`;
                                    html += `</div>`;
                                    
                                    // Adicionar subetapas se existirem
                                    if (hasSubtasks && SUBETAPAS[task.name]) {{
                                        SUBETAPAS[task.name].forEach(subetapaNome => {{
                                            const subetapa = tasks.find(t => t.name === subetapaNome && t.isSubtask);
                                            if (subetapa) {{
                                                globalRowIndex++;
                                                const subtaskRowClass = globalRowIndex % 2 !== 0 ? 'odd-row' : '';
                                                const visibleClass = task.expanded ? 'visible' : '';
                                                html += `<div class="sidebar-row subtask-row ${{subtaskRowClass}} ${{visibleClass}}" data-parent="${{task.name}}">`;
                                                html += `<div class="sidebar-cell task-name-cell" title="${{subetapa.numero_etapa}}. • ${{subetapa.name}}">${{subetapa.numero_etapa}}. • ${{subetapa.name}}</div>`;
                                                html += `<div class="sidebar-cell">${{subetapa.inicio_previsto}}</div>`;
                                                html += `<div class="sidebar-cell">${{subetapa.termino_previsto}}</div>`;
                                                html += `<div class="sidebar-cell">${{subetapa.duracao_prev_meses}}</div>`;
                                                html += `<div class="sidebar-cell">${{subetapa.inicio_real}}</div>`;
                                                html += `<div class="sidebar-cell">${{subetapa.termino_real}}</div>`;
                                                html += `<div class="sidebar-cell">${{subetapa.duracao_real_meses}}</div>`;
                                                html += `<div class="sidebar-cell ${{subetapa.status_color_class}}">${{subetapa.progress}}%</div>`;
                                                html += `<div class="sidebar-cell ${{subetapa.status_color_class}}">${{subetapa.vt_text}}</div>`;
                                                html += `<div class="sidebar-cell ${{subetapa.status_color_class}}">${{subetapa.vd_text}}</div>`;
                                                html += `</div>`;
                                            }}
                                        }});
                                    }}
                                }}
                            }});
                            html += `</div></div>`;
                            
                            const tasksInGroup = tasksInGroupNames;
                            if (i < groupKeys.length - 1 && tasksInGroup.length > 0) {{
                                const nextGroupKey = groupKeys[i + 1];
                                const nextGroupTasks = gruposGantt[nextGroupKey].filter(etapaNome => tasks.some(t => t.name === etapaNome && !t.isSubtask));
                                if (nextGroupTasks.length > 0) {{
                                    html += `<div class="sidebar-row-spacer"></div>`;
                                }}
                            }}
                        }}
                        sidebarContent.innerHTML = html;
                        
                        // Adicionar event listeners para os botões de expandir/recolher
                        document.querySelectorAll('.expand-collapse-btn').forEach(button => {{
                            button.addEventListener('click', function(e) {{
                                e.stopPropagation();
                                const taskName = this.getAttribute('data-task');
                                toggleSubtasks(taskName);
                            }});
                        }});
                        
                        // Adicionar event listeners para as linhas principais com subetapas
                        document.querySelectorAll('.main-task-row.has-subtasks').forEach(row => {{
                            row.addEventListener('click', function() {{
                                const taskName = this.getAttribute('data-task');
                                toggleSubtasks(taskName);
                            }});
                        }});
                    }}

                    function renderHeader() {{
                        const yearHeader = document.getElementById('year-header-{project["id"]}');
                        const monthHeader = document.getElementById('month-header-{project["id"]}');
                        let yearHtml = '', monthHtml = '';
                        const yearsData = [];

                        let currentDate = parseDate(activeDataMinStr);
                        const dataMax = parseDate(activeDataMaxStr);

                        if (!currentDate || !dataMax || isNaN(currentDate.getTime()) || isNaN(dataMax.getTime())) {{
                            yearHeader.innerHTML = "Datas inválidas";
                            monthHeader.innerHTML = "";
                            return;
                        }}

                        // DECLARE estas variáveis
                        let currentYear = -1, monthsInCurrentYear = 0;

                        let totalMonths = 0;
                        while (currentDate <= dataMax && totalMonths < 240) {{
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
                            totalMonths++;
                        }}
                        if (currentYear !== -1) yearsData.push({{ year: currentYear, count: monthsInCurrentYear }});
                        yearsData.forEach(data => {{ 
                            const yearWidth = data.count * PIXELS_PER_MONTH; 
                            yearHtml += `<div class="year-section" style="width:${{yearWidth}}px">${{data.year}}</div>`; 
                        }});

                        const chartContainer = document.getElementById('chart-container-{project["id"]}');
                        if (chartContainer) {{
                            chartContainer.style.minWidth = `${{totalMonths * PIXELS_PER_MONTH}}px`;
                        }}

                        yearHeader.innerHTML = yearHtml;
                        monthHeader.innerHTML = monthHtml;
                    }}

                    function renderChart() {{
                        const chartBody = document.getElementById('chart-body-{project["id"]}');
                        const gruposGantt = JSON.parse(document.getElementById('grupos-gantt-data').textContent);
                        const tasks = projectData[0].tasks;
                        
                        if (!tasks || tasks.length === 0) {{
                            chartBody.innerHTML = '<div style="padding: 20px; text-align: center; color: #666;">Nenhuma tarefa disponível</div>';
                            return;
                        }}
                        
                        chartBody.innerHTML = '';
                        const groupKeys = Object.keys(gruposGantt);
                        let rowIndex = 0;
                        
                        for (let i = 0; i < groupKeys.length; i++) {{
                            const grupo = groupKeys[i];
                            const tasksInGroup = gruposGantt[grupo].filter(etapaNome => tasks.some(t => t.name === etapaNome && !t.isSubtask));
                            if (tasksInGroup.length === 0) continue;
                            
                            gruposGantt[grupo].forEach(etapaNome => {{
                                const task = tasks.find(t => t.name === etapaNome && !t.isSubtask);
                                if (task) {{
                                    // Linha principal
                                    const row = document.createElement('div'); 
                                    row.className = 'gantt-row';
                                    row.setAttribute('data-task', task.name);
                                    
                                    let barPrevisto = null;
                                    if (tipoVisualizacao === 'Ambos' || tipoVisualizacao === 'Previsto') {{ 
                                        barPrevisto = createBar(task, 'previsto'); 
                                        if (barPrevisto) row.appendChild(barPrevisto); 
                                    }}
                                    let barReal = null;
                                    if ((tipoVisualizacao === 'Ambos' || tipoVisualizacao === 'Real') && task.start_real && (task.end_real_original_raw || task.end_real)) {{ 
                                        barReal = createBar(task, 'real'); 
                                        if (barReal) row.appendChild(barReal); 
                                    }}
                                    if (barPrevisto && barReal) {{
                                        const s_prev = parseDate(task.start_previsto), e_prev = parseDate(task.end_previsto), s_real = parseDate(task.start_real), e_real = parseDate(task.end_real_original_raw || task.end_real);
                                        if (s_prev && e_prev && s_real && e_real && s_real <= s_prev && e_real >= e_prev) {{ 
                                            barPrevisto.style.zIndex = '8'; 
                                            barReal.style.zIndex = '7'; 
                                        }}
                                        renderOverlapBar(task, row);
                                    }}
                                    chartBody.appendChild(row);
                                    rowIndex++;
                                    
                                    // Aplica estilo se a tarefa pai estiver expandida
                                    if (task.expanded) {{
                                        updateParentTaskBarStyle(task.name, true);
                                    }}
                                    
                                    // Subetapas - SEMPRE criar as linhas, mas controlar visibilidade via CSS
                                    if (SUBETAPAS[task.name]) {{
                                        SUBETAPAS[task.name].forEach(subetapaNome => {{
                                            const subetapa = tasks.find(t => t.name === subetapaNome && t.isSubtask);
                                            if (subetapa) {{
                                                const subtaskRow = document.createElement('div'); 
                                                subtaskRow.className = 'gantt-row gantt-subtask-row';
                                                subtaskRow.setAttribute('data-parent', task.name);
                                                // Inicialmente oculto - será mostrado via toggle
                                                subtaskRow.style.display = task.expanded ? 'block' : 'none';
                                                if (task.expanded) {{
                                                    subtaskRow.classList.add('visible');
                                                }}
                                                
                                                let subBarPrevisto = null;
                                                if (tipoVisualizacao === 'Ambos' || tipoVisualizacao === 'Previsto') {{ 
                                                    subBarPrevisto = createBar(subetapa, 'previsto'); 
                                                    if (subBarPrevisto) subtaskRow.appendChild(subBarPrevisto); 
                                                }}
                                                let subBarReal = null;
                                                if ((tipoVisualizacao === 'Ambos' || tipoVisualizacao === 'Real') && subetapa.start_real && (subetapa.end_real_original_raw || subetapa.end_real)) {{ 
                                                    subBarReal = createBar(subetapa, 'real'); 
                                                    if (subBarReal) subtaskRow.appendChild(subBarReal); 
                                                }}
                                                if (subBarPrevisto && subBarReal) {{
                                                    const s_prev = parseDate(subetapa.start_previsto), e_prev = parseDate(subetapa.end_previsto), s_real = parseDate(subetapa.start_real), e_real = parseDate(subetapa.end_real_original_raw || subetapa.end_real);
                                                    if (s_prev && e_prev && s_real && e_real && s_real <= s_prev && e_real >= e_prev) {{ 
                                                        subBarPrevisto.style.zIndex = '8'; 
                                                        subBarReal.style.zIndex = '7'; 
                                                    }}
                                                    renderOverlapBar(subetapa, subtaskRow);
                                                }}
                                                chartBody.appendChild(subtaskRow);
                                                rowIndex++;
                                            }}
                                        }});
                                    }}
                                }}
                            }});
                            
                            if (i < groupKeys.length - 1 && tasksInGroup.length > 0) {{
                                const nextGroupKey = groupKeys[i + 1];
                                const nextGroupTasks = gruposGantt[nextGroupKey].filter(etapaNome => tasks.some(t => t.name === etapaNome && !t.isSubtask));
                                if (nextGroupTasks.length > 0) {{
                                    const spacerRow = document.createElement('div');
                                    spacerRow.className = 'gantt-row-spacer';
                                    chartBody.appendChild(spacerRow);
                                    rowIndex++;
                                }}
                            }}
                        }}
                    }}

                    function createBar(task, tipo) {{
                        const startDate = parseDate(tipo === 'previsto' ? task.start_previsto : task.start_real);
                        const endDate = parseDate(tipo === 'previsto' ? task.end_previsto : (task.end_real_original_raw || task.end_real));

                        if (!startDate || !endDate) {{
                            console.log('Datas inválidas para barra:', task.name, tipo);
                            return null;
                        }}
                        
                        const left = getPosition(startDate);
                        const width = Math.max(getPosition(endDate) - left + (PIXELS_PER_MONTH / 30), 5); // Mínimo de 5px
                        
                        if (width <= 0) {{
                            console.log('Largura inválida para barra:', task.name, tipo, width);
                            return null;
                        }}
                        
                        const bar = document.createElement('div'); 
                        bar.className = `gantt-bar ${{tipo}}`;
                        const coresSetor = coresPorSetor[task.setor] || coresPorSetor['Não especificado'] || {{previsto: '#cccccc', real: '#888888'}};
                        bar.style.backgroundColor = tipo === 'previsto' ? coresSetor.previsto : coresSetor.real;
                        bar.style.left = `${{left}}px`; 
                        bar.style.width = `${{width}}px`;
                        
                        // Adicionar rótulo apenas se houver espaço suficiente
                        if (width > 40) {{
                            const barLabel = document.createElement('span'); 
                            barLabel.className = 'bar-label'; 
                            barLabel.textContent = `${{task.name}} (${{task.progress}}%)`; 
                            bar.appendChild(barLabel);
                        }}
                        
                        bar.addEventListener('mousemove', e => showTooltip(e, task, tipo));
                        bar.addEventListener('mouseout', () => hideTooltip());
                        return bar;
                    }}

                    function renderOverlapBar(task, row) {{
                    if (!task.start_real || !(task.end_real_original_raw || task.end_real)) return;
                        const s_prev = parseDate(task.start_previsto), e_prev = parseDate(task.end_previsto), s_real = parseDate(task.start_real), e_real = parseDate(task.end_real_original_raw || task.end_real);
                        const overlap_start = new Date(Math.max(s_prev, s_real)), overlap_end = new Date(Math.min(e_prev, e_real));
                        if (overlap_start < overlap_end) {{
                            const left = getPosition(overlap_start), width = getPosition(overlap_end) - left + (PIXELS_PER_MONTH / 30);
                            if (width > 0) {{ 
                                const overlapBar = document.createElement('div'); 
                                overlapBar.className = 'gantt-bar-overlap'; 
                                overlapBar.style.left = `${{left}}px`; 
                                overlapBar.style.width = `${{width}}px`; 
                                row.appendChild(overlapBar); 
                            }}
                        }}
                    }}

                    function getPosition(date) {{
                        if (!date) return 0;
                        const chartStart = parseDate(activeDataMinStr);
                        if (!chartStart || isNaN(chartStart.getTime())) return 0;

                        const monthsOffset = (date.getUTCFullYear() - chartStart.getUTCFullYear()) * 12 + (date.getUTCMonth() - chartStart.getUTCMonth());
                        const dayOfMonth = date.getUTCDate() - 1;
                        const daysInMonth = new Date(date.getUTCFullYear(), date.getUTCMonth() + 1, 0).getUTCDate();
                        const fractionOfMonth = daysInMonth > 0 ? dayOfMonth / daysInMonth : 0;
                        return (monthsOffset + fractionOfMonth) * PIXELS_PER_MONTH;
                    }}

                    function positionTodayLine() {{
                        const todayLine = document.getElementById('today-line-{project["id"]}');
                        const today = new Date(), todayUTC = new Date(Date.UTC(today.getFullYear(), today.getMonth(), today.getDate()));

                        const chartStart = parseDate(activeDataMinStr);
                        const chartEnd = parseDate(activeDataMaxStr);

                        if (chartStart && chartEnd && !isNaN(chartStart.getTime()) && !isNaN(chartEnd.getTime()) && todayUTC >= chartStart && todayUTC <= chartEnd) {{ 
                            const offset = getPosition(todayUTC); 
                            todayLine.style.left = `${{offset}}px`; 
                            todayLine.style.display = 'block'; 
                        }} else {{ 
                            todayLine.style.display = 'none'; 
                        }}
                    }}

                    function positionMetaLine() {{
                        const metaLine = document.getElementById('meta-line-{project["id"]}'), metaLabel = document.getElementById('meta-line-label-{project["id"]}');
                        const metaDateStr = projectData[0].meta_assinatura_date;
                        if (!metaDateStr) {{ metaLine.style.display = 'none'; metaLabel.style.display = 'none'; return; }}

                        const metaDate = parseDate(metaDateStr);
                        const chartStart = parseDate(activeDataMinStr);
                        const chartEnd = parseDate(activeDataMaxStr);

                        if (metaDate && chartStart && chartEnd && !isNaN(metaDate.getTime()) && !isNaN(chartStart.getTime()) && !isNaN(chartEnd.getTime()) && metaDate >= chartStart && metaDate <= chartEnd) {{ 
                            const offset = getPosition(metaDate); 
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

                    function showTooltip(e, task, tipo) {{
                        const tooltip = document.getElementById('tooltip-{project["id"]}');
                        let content = `<b>${{task.name}}</b><br>`;
                        if (tipo === 'previsto') {{ content += `Previsto: ${{task.inicio_previsto}} - ${{task.termino_previsto}}<br>Duração: ${{task.duracao_prev_meses}}M`; }} else {{ content += `Real: ${{task.inicio_real}} - ${{task.termino_real}}<br>Duração: ${{task.duracao_real_meses}}M<br>Variação Término: ${{task.vt_text}}<br>Variação Duração: ${{task.vd_text}}`; }}
                        content += `<br><b>Progresso: ${{task.progress}}%</b><br>Setor: ${{task.setor}}<br>Grupo: ${{task.grupo}}`;
                        tooltip.innerHTML = content;
                        tooltip.classList.add('show');
                        const tooltipWidth = tooltip.offsetWidth;
                        const tooltipHeight = tooltip.offsetHeight;
                        const viewportWidth = window.innerWidth;
                        const viewportHeight = window.innerHeight;
                        const mouseX = e.clientX; 
                        const mouseY = e.clientY;
                        const padding = 15;
                        let left, top;
                        if ((mouseX + padding + tooltipWidth) > viewportWidth) {{
                            left = mouseX - padding - tooltipWidth;
                        }} else {{
                            left = mouseX + padding;
                        }}
                        if ((mouseY + padding + tooltipHeight) > viewportHeight) {{
                            top = mouseY - padding - tooltipHeight;
                        }} else {{
                            top = mouseY + padding;
                        }}
                        if (left < padding) left = padding;
                        if (top < padding) top = padding;
                        tooltip.style.left = `${{left}}px`;
                        tooltip.style.top = `${{top}}px`;
                    }}

                    function hideTooltip() {{ 
                        document.getElementById('tooltip-{project["id"]}').classList.remove('show'); 
                    }}

                    function renderMonthDividers() {{
                        const chartContainer = document.getElementById('chart-container-{project["id"]}');
                        chartContainer.querySelectorAll('.month-divider, .month-divider-label').forEach(el => el.remove());

                        let currentDate = parseDate(activeDataMinStr);
                        const dataMax = parseDate(activeDataMaxStr);

                        if (!currentDate || !dataMax || isNaN(currentDate.getTime()) || isNaN(dataMax.getTime())) return;

                        let totalMonths = 0;
                        while (currentDate <= dataMax && totalMonths < 240) {{
                            const left = getPosition(currentDate);
                            const divider = document.createElement('div'); 
                            divider.className = 'month-divider';
                            if (currentDate.getUTCMonth() === 0) divider.classList.add('first');
                            divider.style.left = `${{left}}px`; 
                            chartContainer.appendChild(divider);
                            currentDate.setUTCMonth(currentDate.getUTCMonth() + 1);
                            totalMonths++;
                        }}
                    }}

                    function setupEventListeners() {{
                        const ganttChartContent = document.getElementById('gantt-chart-content-{project["id"]}'), sidebarContent = document.getElementById('gantt-sidebar-content-{project['id']}');
                        const fullscreenBtn = document.getElementById('fullscreen-btn-{project["id"]}'), toggleBtn = document.getElementById('toggle-sidebar-btn-{project['id']}');
                        const filterBtn = document.getElementById('filter-btn-{project["id"]}');
                        const filterMenu = document.getElementById('filter-menu-{project['id']}');
                        const container = document.getElementById('gantt-container-{project["id"]}');

                        const applyBtn = document.getElementById('filter-apply-btn-{project["id"]}');
                        if (applyBtn) applyBtn.addEventListener('click', () => applyFiltersAndRedraw());

                        if (fullscreenBtn) fullscreenBtn.addEventListener('click', () => toggleFullscreen());

                        // Adiciona listener para o botão de filtro
                        if (filterBtn) {{
                            filterBtn.addEventListener('click', () => {{
                                filterMenu.classList.toggle('is-open');
                            }});
                        }}

                        // Fecha o menu de filtro ao clicar fora
                        document.addEventListener('click', (event) => {{
                            if (filterMenu && filterBtn && !filterMenu.contains(event.target) && !filterBtn.contains(event.target)) {{
                                filterMenu.classList.remove('is-open');
                            }}
                        }});

                        if (container) container.addEventListener('fullscreenchange', () => handleFullscreenChange());

                        if (toggleBtn) toggleBtn.addEventListener('click', () => toggleSidebar());
                        if (ganttChartContent && sidebarContent) {{
                            let isSyncing = false;
                            ganttChartContent.addEventListener('scroll', () => {{ if (!isSyncing) {{ isSyncing = true; sidebarContent.scrollTop = ganttChartContent.scrollTop; isSyncing = false; }} }});
                            sidebarContent.addEventListener('scroll', () => {{ if (!isSyncing) {{ isSyncing = true; ganttChartContent.scrollTop = sidebarContent.scrollTop; isSyncing = false; }} }});
                            let isDown = false, startX, scrollLeft;
                            ganttChartContent.addEventListener('mousedown', (e) => {{ isDown = true; ganttChartContent.classList.add('active'); startX = e.pageX - ganttChartContent.offsetLeft; scrollLeft = ganttChartContent.scrollLeft; }});
                            ganttChartContent.addEventListener('mouseleave', () => {{ isDown = false; ganttChartContent.classList.remove('active'); }});
                            ganttChartContent.addEventListener('mouseup', () => {{ isDown = false; ganttChartContent.classList.remove('active'); }});
                            ganttChartContent.addEventListener('mousemove', (e) => {{ if (!isDown) return; e.preventDefault(); const x = e.pageX - ganttChartContent.offsetLeft; const walk = (x - startX) * 2; ganttChartContent.scrollLeft = scrollLeft - walk; }});
                        }}
                    }}

                    function toggleSidebar() {{ 
                        document.getElementById('gantt-sidebar-wrapper-{project["id"]}').classList.toggle('collapsed'); 
                    }}

                    function updatePulmaoInputVisibility() {{
                        const radioCom = document.getElementById('filter-pulmao-com-{project["id"]}');
                        const mesesGroup = document.getElementById('pulmao-meses-group-{project["id"]}');
                        if (radioCom && mesesGroup) {{ 
                            if (radioCom.checked) {{
                                mesesGroup.style.display = 'block';
                            }} else {{
                                mesesGroup.style.display = 'none';
                            }}
                        }}
                    }}

                    function resetToInitialState() {{
                        currentProjectIndex = initialProjectIndex;
                        const initialProject = allProjectsData[initialProjectIndex];

                        projectData = [JSON.parse(JSON.stringify(initialProject))];
                        // Reorganizar tasks com estrutura de subetapas
                        projectData[0].tasks = organizarTasksComSubetapas(projectData[0].tasks);
                        allTasks_baseData = JSON.parse(JSON.stringify(projectData[0].tasks));

                        tipoVisualizacao = initialTipoVisualizacao;
                        pulmaoStatus = initialPulmaoStatus;

                        applyInitialPulmaoState();

                        activeDataMinStr = dataMinStr;
                        activeDataMaxStr = dataMaxStr;

                        if (initialPulmaoStatus === 'Com Pulmão' && initialPulmaoMeses > 0) {{
                            const {{ min: newMinStr, max: newMaxStr }} = findNewDateRange(projectData[0].tasks);
                            const newMin = parseDate(newMinStr);
                            const newMax = parseDate(newMaxStr);
                            const originalMin = parseDate(activeDataMinStr);
                            const originalMax = parseDate(activeDataMaxStr);

                            let finalMinDate = originalMin;
                            if (newMin && newMin < finalMinDate) {{
                                finalMinDate = newMin;
                            }}
                            let finalMaxDate = originalMax;
                            if (newMax && newMax > finalMaxDate) {{
                                finalMaxDate = newMax;
                            }}

                            finalMinDate = new Date(finalMinDate.getTime());
                            finalMaxDate = new Date(finalMaxDate.getTime());
                            finalMinDate.setUTCDate(1);
                            finalMaxDate.setUTCMonth(finalMaxDate.getUTCMonth() + 1, 0);

                            activeDataMinStr = finalMinDate.toISOString().split('T')[0];
                            activeDataMaxStr = finalMaxDate.toISOString().split('T')[0];
                        }}

                        document.getElementById('filter-project-{project["id"]}').value = initialProjectIndex;
                        
                        // *** CORREÇÃO: Reset Virtual Select ***
                        if(vsSetor) vsSetor.setValue(["Todos"]);
                        if(vsGrupo) vsGrupo.setValue(["Todos"]);
                        if(vsEtapa) vsEtapa.setValue(["Todas"]);
                        
                        document.getElementById('filter-concluidas-{project["id"]}').checked = false;

                        const visRadio = document.querySelector('input[name="filter-vis-{project['id']}"][value="' + initialTipoVisualizacao + '"]');
                        if (visRadio) visRadio.checked = true;

                        const pulmaoRadio = document.querySelector('input[name="filter-pulmao-{project['id']}"][value="' + initialPulmaoStatus + '"]');
                        if (pulmaoRadio) pulmaoRadio.checked = true;

                        document.getElementById('filter-pulmao-meses-{project["id"]}').value = initialPulmaoMeses;

                        updatePulmaoInputVisibility();

                        renderHeader();
                        renderMonthDividers();
                        renderSidebar();
                        renderChart();
                        positionTodayLine();
                        positionMetaLine();
                        updateProjectTitle();
                    }}

                    function updateProjectTitle() {{
                        const projectTitle = document.querySelector('#gantt-sidebar-wrapper-{project["id"]} .project-title-row span');
                        if (projectTitle) {{
                            projectTitle.textContent = projectData[0].name;
                        }}
                    }}

                    function toggleFullscreen() {{
                        const container = document.getElementById('gantt-container-{project["id"]}');
                        if (!document.fullscreenElement) {{
                            container.requestFullscreen().catch(err => alert('Erro: ' + err.message));
                        }} else {{
                            document.exitFullscreen();
                        }}
                    }}



                    function toggleFullscreen() {{
                        const container = document.getElementById('gantt-container-{project["id"]}');
                        if (!document.fullscreenElement) {{
                            container.requestFullscreen().catch(err => console.error('Erro ao tentar entrar em tela cheia: ' + err.message));
                        }} else {{
                            document.exitFullscreen();
                        }}
                    }}

                    function handleFullscreenChange() {{
                        const btn = document.getElementById('fullscreen-btn-{project["id"]}');
                        const container = document.getElementById('gantt-container-{project["id"]}');
                        if (document.fullscreenElement === container) {{
                            btn.innerHTML = '<span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 9l6 6m0-6l-6 6M3 20.29V5a2 2 0 012-2h14a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2v-.29"></path></svg></span>';
                            btn.classList.add('is-fullscreen');
                        }} else {{
                            btn.innerHTML = '<span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path></svg></span>';
                            btn.classList.remove('is-fullscreen');
                            document.getElementById('filter-menu-{project["id"]}').classList.remove('is-open');
                        }}
                    }}
                    function populateFilters() {{
                        if (filtersPopulated) return;

                        // Popula o select normal de Projeto
                        const selProject = document.getElementById('filter-project-{project["id"]}');
                        allProjectsData.forEach((proj, index) => {{
                            const isSelected = (index === initialProjectIndex) ? 'selected' : '';
                            selProject.innerHTML += '<option value="' + index + '" ' + isSelected + '>' + proj.name + '</option>';
                        }});

                        // Configurações comuns para Virtual Select
                        const vsConfig = {{
                            multiple: true,
                            search: true,
                            optionsCount: 6,
                            showResetButton: true,
                            resetButtonText: 'Limpar',
                            selectAllText: 'Selecionar Todos',
                            allOptionsSelectedText: 'Todos',
                            optionsSelectedText: 'selecionados',
                            searchPlaceholderText: 'Buscar...',
                            optionHeight: '30px',
                            popupDropboxBreakpoint: '3000px',
                            noOptionsText: 'Nenhuma opção encontrada',
                            noSearchResultsText: 'Nenhum resultado encontrado',
                        }};

                        // Prepara opções e inicializa Virtual Select para Setor
                        const setorOptions = filterOptions.setores.map(s => ({{ label: s, value: s }}));
                        vsSetor = VirtualSelect.init({{
                            ...vsConfig,
                            ele: '#filter-setor-{project["id"]}',
                            options: setorOptions,
                            placeholder: "Selecionar Setor(es)",
                            selectedValue: ["Todos"]
                        }});

                        // Prepara opções e inicializa Virtual Select para Grupo
                        const grupoOptions = filterOptions.grupos.map(g => ({{ label: g, value: g }}));
                        vsGrupo = VirtualSelect.init({{
                            ...vsConfig,
                            ele: '#filter-grupo-{project["id"]}',
                            options: grupoOptions,
                            placeholder: "Selecionar Grupo(s)",
                            selectedValue: ["Todos"]
                        }});

                        // Prepara opções e inicializa Virtual Select para Etapa
                        const etapaOptions = filterOptions.etapas.map(e => ({{ label: e, value: e }}));
                        vsEtapa = VirtualSelect.init({{
                            ...vsConfig,
                            ele: '#filter-etapa-{project["id"]}',
                            options: etapaOptions,
                            placeholder: "Selecionar Etapa(s)",
                            selectedValue: ["Todas"]
                        }});

                        // Configura os radios de visualização
                        const visRadio = document.querySelector('input[name="filter-vis-{project['id']}"][value="' + initialTipoVisualizacao + '"]');
                        if (visRadio) visRadio.checked = true;

                        // Configura os radios e input de Pulmão
                        const radioCom = document.getElementById('filter-pulmao-com-{project["id"]}');
                        const radioSem = document.getElementById('filter-pulmao-sem-{project["id"]}');

                        radioCom.addEventListener('change', updatePulmaoInputVisibility);
                        radioSem.addEventListener('change', updatePulmaoInputVisibility);

                        const pulmaoRadioInitial = document.querySelector('input[name="filter-pulmao-{project['id']}"][value="' + initialPulmaoStatus + '"]');
                        if(pulmaoRadioInitial) pulmaoRadioInitial.checked = true;

                        document.getElementById('filter-pulmao-meses-{project["id"]}').value = initialPulmaoMeses;

                        updatePulmaoInputVisibility();

                        filtersPopulated = true;
                    }}

                    // *** FUNÇÃO applyFiltersAndRedraw CORRIGIDA ***
                    // *** FUNÇÃO applyFiltersAndRedraw CORRIGIDA ***
                    function applyFiltersAndRedraw() {{
                        try {{
                            const selProjectIndex = parseInt(document.getElementById('filter-project-{project["id"]}').value, 10);
                            
                            // *** LEITURA CORRIGIDA dos Virtual Select ***
                            const selSetorArray = vsSetor ? vsSetor.getValue() || [] : [];
                            const selGrupoArray = vsGrupo ? vsGrupo.getValue() || [] : [];
                            const selEtapaArray = vsEtapa ? vsEtapa.getValue() || [] : [];
                            
                            const selConcluidas = document.getElementById('filter-concluidas-{project["id"]}').checked;
                            const selVis = document.querySelector('input[name="filter-vis-{project['id']}"]:checked').value;
                            const selPulmao = document.querySelector('input[name="filter-pulmao-{project['id']}"]:checked').value;
                            const selPulmaoMeses = parseInt(document.getElementById('filter-pulmao-meses-{project["id"]}').value, 10) || 0;

                            console.log('Filtros aplicados:', {{
                                setor: selSetorArray,
                                grupo: selGrupoArray,
                                etapa: selEtapaArray,
                                concluidas: selConcluidas,
                                visualizacao: selVis,
                                pulmao: selPulmao,
                                mesesPulmao: selPulmaoMeses
                            }});

                            // *** FECHAR MENU DE FILTROS ***
                            document.getElementById('filter-menu-{project["id"]}').classList.remove('is-open');

                            if (selProjectIndex !== currentProjectIndex) {{
                                currentProjectIndex = selProjectIndex;
                                const newProject = allProjectsData[selProjectIndex];
                                projectData = [JSON.parse(JSON.stringify(newProject))];
                                // Reorganizar tasks com estrutura de subetapas
                                projectData[0].tasks = organizarTasksComSubetapas(projectData[0].tasks);
                                allTasks_baseData = JSON.parse(JSON.stringify(projectData[0].tasks));
                            }}

                            let baseTasks = JSON.parse(JSON.stringify(allTasks_baseData));

                            // *** DEBUG DETALHADO DOS GRUPOS ***
                            console.log('=== DEBUG GRUPOS ===');
                            console.log('Total de tasks base:', baseTasks.length);
                            console.log('Grupos disponíveis nas tasks:', [...new Set(baseTasks.map(t => t.grupo))]);
                            console.log('Filtrando por grupo:', selGrupoArray);
                            
                            // Verificar tasks que deveriam passar no filtro
                            const tasksComGrupoFiltrado = baseTasks.filter(t => {{
                                const passaFiltro = selGrupoArray.includes(t.grupo);
                                if (passaFiltro) {{
                                    console.log('Task que passa no filtro:', t.name, '- Grupo:', t.grupo);
                                }}
                                return passaFiltro;
                            }});
                            console.log('Tasks que pertencem ao grupo filtrado:', tasksComGrupoFiltrado.length);
                            console.log('=== FIM DEBUG ===');

                            if (selPulmao === 'Com Pulmão' && selPulmaoMeses > 0) {{
                                const offsetMeses = -selPulmaoMeses;
                                console.log("Aplicando pulmão APENAS no previsto para filtros");
                                
                                baseTasks.forEach(task => {{
                                    const etapaNome = task.name;
                                    
                                    if (etapas_sem_alteracao.includes(etapaNome)) {{
                                        // Não altera datas
                                    }}
                                    else if (etapas_pulmao.includes(etapaNome)) {{
                                        // Apenas datas previstas
                                        task.start_previsto = addMonths(task.start_previsto, offsetMeses);
                                        task.inicio_previsto = formatDateDisplay(task.start_previsto);
                                    }}
                                    else {{
                                        // Apenas datas previstas
                                        task.start_previsto = addMonths(task.start_previsto, offsetMeses);
                                        task.end_previsto = addMonths(task.end_previsto, offsetMeses);
                                        
                                        task.inicio_previsto = formatDateDisplay(task.start_previsto);
                                        task.termino_previsto = formatDateDisplay(task.end_previsto);
                                    }}
                                }});
                            }}

                            let filteredTasks = baseTasks;

                            // *** LÓGICA DE FILTRO CORRIGIDA ***
                            // Filtro por Setor
                            if (selSetorArray.length > 0 && !selSetorArray.includes('Todos')) {{
                                filteredTasks = filteredTasks.filter(t => selSetorArray.includes(t.setor));
                                console.log('Após filtro setor:', filteredTasks.length);
                            }}
                            
                            // Filtro por Grupo - CORREÇÃO PRINCIPAL
                            if (selGrupoArray.length > 0 && !selGrupoArray.includes('Todos')) {{
                                filteredTasks = filteredTasks.filter(t => selGrupoArray.includes(t.grupo));
                                console.log('Após filtro grupo:', filteredTasks.length);
                                
                                // DEBUG adicional
                                if (filteredTasks.length === 0) {{
                                    console.warn('⚠️ NENHUMA TASK PASSOU NO FILTRO DE GRUPO!');
                                    console.log('Grupos filtrados:', selGrupoArray);
                                    console.log('Grupos disponíveis:', [...new Set(baseTasks.map(t => t.grupo))]);
                                }}
                            }}
                            
                            // Filtro por Etapa
                            if (selEtapaArray.length > 0 && !selEtapaArray.includes('Todas')) {{
                                filteredTasks = filteredTasks.filter(t => selEtapaArray.includes(t.name));
                                console.log('Após filtro etapa:', filteredTasks.length);
                            }}

                            // Filtro por Concluídas
                            if (selConcluidas) {{
                                filteredTasks = filteredTasks.filter(t => t.progress < 100);
                                console.log('Após filtro concluídas:', filteredTasks.length);
                            }}

                            console.log('Tasks após filtros:', filteredTasks.length);
                            console.log('Tasks filtradas:', filteredTasks);

                            // Se não há tasks após filtrar, mostrar mensagem mas permitir continuar
                            if (filteredTasks.length === 0) {{
                                console.warn('Nenhuma task passou pelos filtros aplicados');
                                // Não interromper o processo, deixar que o renderSidebar mostre a mensagem apropriada
                            }}

                            // Recalcular range de datas apenas se houver tasks
                            if (filteredTasks.length > 0) {{
                                const {{ min: newMinStr, max: newMaxStr }} = findNewDateRange(filteredTasks);
                                const newMin = parseDate(newMinStr);
                                const newMax = parseDate(newMaxStr);
                                const originalMin = parseDate(dataMinStr);
                                const originalMax = parseDate(dataMaxStr);

                                let finalMinDate = originalMin;
                                if (newMin && newMin < finalMinDate) {{
                                    finalMinDate = newMin;
                                }}

                                let finalMaxDate = originalMax;
                                if (newMax && newMax > finalMaxDate) {{
                                    finalMaxDate = newMax;
                                }}

                                finalMinDate = new Date(finalMinDate.getTime());
                                finalMaxDate = new Date(finalMaxDate.getTime());
                                finalMinDate.setUTCDate(1);
                                finalMaxDate.setUTCMonth(finalMaxDate.getUTCMonth() + 1, 0);

                                activeDataMinStr = finalMinDate.toISOString().split('T')[0];
                                activeDataMaxStr = finalMaxDate.toISOString().split('T')[0];
                            }}

                            // Atualizar dados e redesenhar
                            projectData[0].tasks = filteredTasks;
                            tipoVisualizacao = selVis;

                            renderSidebar();
                            renderHeader();
                            renderChart();
                            positionTodayLine();
                            positionMetaLine();
                            updateProjectTitle();



                        }} catch (error) {{
                            console.error('Erro ao aplicar filtros:', error);
                            alert('Erro ao aplicar filtros: ' + error.message);
                        }}
                    }}                    // DEBUG: Verificar se há dados antes de inicializar
                    console.log('Dados do projeto:', projectData);
                    console.log('Tasks base:', allTasks_baseData);
                    
                    // Inicializar o Gantt
                    initGantt();
                </script>
            </body>
            </html>
        """
        # Exibe o componente HTML no Streamlit
        components.html(gantt_html, height=altura_gantt, scrolling=True)
        st.markdown("---")
# --- *** FUNÇÃO gerar_gantt_consolidado MODIFICADA *** ---
def converter_dados_para_gantt_consolidado(df, etapa_selecionada):
    """
    Versão modificada para o Gantt consolidado que também calcula datas de etapas pai
    a partir das subetapas.
    """
    if df.empty:
        return []

    # Filtrar pela etapa selecionada
    sigla_selecionada = nome_completo_para_sigla.get(etapa_selecionada, etapa_selecionada)
    df_filtrado = df[df["Etapa"] == sigla_selecionada].copy()
    
    if df_filtrado.empty:
        return []

    gantt_data = []
    tasks = []

    # Para cada empreendimento na etapa selecionada
    for empreendimento in df_filtrado["Empreendimento"].unique():
        df_emp = df_filtrado[df_filtrado["Empreendimento"] == empreendimento].copy()

        # Aplicar a mesma lógica de cálculo de datas para etapas pai
        etapa_nome_completo = sigla_para_nome_completo.get(sigla_selecionada, sigla_selecionada)
        
        # Se esta etapa é uma etapa pai, calcular datas das subetapas
        if etapa_nome_completo in SUBETAPAS:
            # Buscar todas as subetapas deste empreendimento
            subetapas_siglas = [nome_completo_para_sigla.get(sub, sub) for sub in SUBETAPAS[etapa_nome_completo]]
            subetapas_emp = df[df["Empreendimento"] == empreendimento]
            subetapas_emp = subetapas_emp[subetapas_emp["Etapa"].isin(subetapas_siglas)]
            
            if not subetapas_emp.empty:
                # Calcular datas mínimas e máximas das subetapas
                inicio_real_min = subetapas_emp["Inicio_Real"].min()
                termino_real_max = subetapas_emp["Termino_Real"].max()
                
                # Atualizar as datas da etapa pai com os valores calculados
                if pd.notna(inicio_real_min):
                    df_emp["Inicio_Real"] = inicio_real_min
                if pd.notna(termino_real_max):
                    df_emp["Termino_Real"] = termino_real_max
                
                # Recalcular progresso baseado nas subetapas
                if not subetapas_emp.empty and "% concluído" in subetapas_emp.columns:
                    progress_subetapas = subetapas_emp["% concluído"].apply(converter_porcentagem)
                    df_emp["% concluído"] = progress_subetapas.mean()

        # Processar cada linha (deve ser apenas uma por empreendimento na visão consolidada)
        for i, (idx, row) in enumerate(df_emp.iterrows()):
            start_date = row.get("Inicio_Prevista")
            end_date = row.get("Termino_Prevista")
            start_real = row.get("Inicio_Real")
            end_real_original = row.get("Termino_Real")
            progress = row.get("% concluído", 0)

            # Lógica para tratar datas vazias
            if pd.isna(start_date): 
                start_date = datetime.now()
            if pd.isna(end_date): 
                end_date = start_date + timedelta(days=30)

            end_real_visual = end_real_original
            if pd.notna(start_real) and progress < 100 and pd.isna(end_real_original):
                end_real_visual = datetime.now()

            # Cálculos de duração e variação
            dur_prev_meses = None
            if pd.notna(start_date) and pd.notna(end_date):
                dur_prev_meses = (end_date - start_date).days / 30.4375

            dur_real_meses = None
            if pd.notna(start_real) and pd.notna(end_real_original):
                dur_real_meses = (end_real_original - start_real).days / 30.4375

            vt = calculate_business_days(end_date, end_real_original)
            
            duracao_prevista_uteis = calculate_business_days(start_date, end_date)
            duracao_real_uteis = calculate_business_days(start_real, end_real_original)
            
            vd = None
            if pd.notna(duracao_real_uteis) and pd.notna(duracao_prevista_uteis):
                vd = duracao_real_uteis - duracao_prevista_uteis

            # Lógica de Cor do Status
            status_color_class = 'status-default'
            hoje = pd.Timestamp.now().normalize()
            if progress == 100:
                if pd.notna(end_real_original) and pd.notna(end_date):
                    if end_real_original <= end_date:
                        status_color_class = 'status-green'
                    else:
                        status_color_class = 'status-red'
            elif progress < 100 and pd.notna(end_date) and (end_date < hoje):
                status_color_class = 'status-yellow'

            task = {
                "id": f"t{i}", 
                "name": empreendimento,  # No consolidado, o nome é o empreendimento
                "numero_etapa": i + 1,
                "start_previsto": start_date.strftime("%Y-%m-%d"),
                "end_previsto": end_date.strftime("%Y-%m-%d"),
                "start_real": pd.to_datetime(start_real).strftime("%Y-%m-%d") if pd.notna(start_real) else None,
                "end_real": pd.to_datetime(end_real_visual).strftime("%Y-%m-%d") if pd.notna(end_real_visual) else None,
                "end_real_original_raw": pd.to_datetime(end_real_original).strftime("%Y-%m-%d") if pd.notna(end_real_original) else None,
                "setor": row.get("SETOR", "Não especificado"),
                "grupo": "Consolidado",
                "progress": int(progress),
                "inicio_previsto": start_date.strftime("%d/%m/%y"),
                "termino_previsto": end_date.strftime("%d/%m/%y"),
                "inicio_real": pd.to_datetime(start_real).strftime("%d/%m/%y") if pd.notna(start_real) else "N/D",
                "termino_real": pd.to_datetime(end_real_original).strftime("%d/%m/%y") if pd.notna(end_real_original) else "N/D",
                "duracao_prev_meses": f"{dur_prev_meses:.1f}".replace('.', ',') if dur_prev_meses is not None else "-",
                "duracao_real_meses": f"{dur_real_meses:.1f}".replace('.', ',') if dur_real_meses is not None else "-",
                "vt_text": f"{int(vt):+d}d" if pd.notna(vt) else "-",
                "vd_text": f"{int(vd):+d}d" if pd.notna(vd) else "-",
                "status_color_class": status_color_class
            }
            tasks.append(task)

    # Criar um projeto único para a visão consolidada
    project = {
        "id": "p_consolidado",
        "name": f"Comparativo: {etapa_selecionada}",
        "tasks": tasks,
        "meta_assinatura_date": None
    }
    gantt_data.append(project)

    return gantt_data
# Substitua sua função gerar_gantt_consolidado inteira por esta
def gerar_gantt_consolidado(df, tipo_visualizacao, df_original_para_ordenacao, pulmao_status, pulmao_meses, etapa_selecionada_inicialmente):
    """
    Gera um gráfico de Gantt HTML consolidado que contém dados para TODAS as etapas
    e permite a troca de etapas via menu flutuante.
    
    'etapa_selecionada_inicialmente' define qual etapa mostrar no carregamento.
    """
    # # st.info(f"Exibindo visão comparativa. Etapa inicial: {etapa_selecionada_inicialmente}")

    # --- 1. Preparação dos Dados (MODIFICADO) ---
    df_gantt = df.copy() # df agora tem MÚLTIPLAS etapas

    for col in ["Inicio_Prevista", "Termino_Prevista", "Inicio_Real", "Termino_Real"]:
        if col in df_gantt.columns:
            df_gantt[col] = pd.to_datetime(df_gantt[col], errors="coerce")

    if "% concluído" not in df_gantt.columns: 
        df_gantt["% concluído"] = 0
    df_gantt["% concluído"] = df_gantt["% concluído"].fillna(0).apply(converter_porcentagem)

    # Agrupar por Etapa E Empreendimento
    df_gantt_agg = df_gantt.groupby(['Etapa', 'Empreendimento']).agg(
        Inicio_Prevista=('Inicio_Prevista', 'min'),
        Termino_Prevista=('Termino_Prevista', 'max'),
        Inicio_Real=('Inicio_Real', 'min'),
        Termino_Real=('Termino_Real', 'max'),
        **{'% concluído': ('% concluído', 'max')},
        SETOR=('SETOR', 'first')
    ).reset_index()
    
    all_data_by_stage_js = {}
    all_stage_names_full = [] # Para o novo filtro
    # Iterar por cada etapa única
    etapas_unicas_no_df = df_gantt_agg['Etapa'].unique()
    
    for i, etapa_sigla in enumerate(etapas_unicas_no_df):
        df_etapa_agg = df_gantt_agg[df_gantt_agg['Etapa'] == etapa_sigla]
        etapa_nome_completo = sigla_para_nome_completo.get(etapa_sigla, etapa_sigla)
        all_stage_names_full.append(etapa_nome_completo)
        
        tasks_base_data_for_stage = []
        
        for j, row in df_etapa_agg.iterrows():
            start_date = row.get("Inicio_Prevista")
            end_date = row.get("Termino_Prevista")
            start_real = row.get("Inicio_Real")
            end_real_original = row.get("Termino_Real")
            progress = row.get("% concluído", 0)

            if pd.isna(start_date): start_date = datetime.now()
            if pd.isna(end_date): end_date = start_date + timedelta(days=30)
            end_real_visual = end_real_original
            if pd.notna(start_real) and progress < 100 and pd.isna(end_real_original): end_real_visual = datetime.now()

            vt = calculate_business_days(end_date, end_real_original)
            duracao_prevista_uteis = calculate_business_days(start_date, end_date)
            duracao_real_uteis = calculate_business_days(start_real, end_real_original)
            vd = None
            if pd.notna(duracao_real_uteis) and pd.notna(duracao_prevista_uteis): vd = duracao_real_uteis - duracao_prevista_uteis
            status_color_class = 'status-default'
            hoje = pd.Timestamp.now().normalize()
            if progress == 100:
                if pd.notna(end_real_original) and pd.notna(end_date):
                    if end_real_original <= end_date: status_color_class = 'status-green'
                    else: status_color_class = 'status-red'
            elif progress < 100 and pd.notna(end_date) and (end_date < hoje): status_color_class = 'status-yellow'

            task = {
                "id": f"t{j}_{i}", # ID único
                "name": row["Empreendimento"], # O 'name' ainda é o Empreendimento
                "numero_etapa": j + 1,
                "start_previsto": start_date.strftime("%Y-%m-%d"),
                "end_previsto": end_date.strftime("%Y-%m-%d"),
                "start_real": pd.to_datetime(start_real).strftime("%Y-%m-%d") if pd.notna(start_real) else None,
                "end_real": pd.to_datetime(end_real_visual).strftime("%Y-%m-%d") if pd.notna(end_real_visual) else None,
                "end_real_original_raw": pd.to_datetime(end_real_original).strftime("%Y-%m-%d") if pd.notna(end_real_original) else None,
                "setor": row.get("SETOR", "Não especificado"),
                "grupo": "Consolidado", # Correto
                "progress": int(progress),
                "inicio_previsto": start_date.strftime("%d/%m/%y"),
                "termino_previsto": end_date.strftime("%d/%m/%y"),
                "inicio_real": pd.to_datetime(start_real).strftime("%d/%m/%y") if pd.notna(start_real) else "N/D",
                "termino_real": pd.to_datetime(end_real_original).strftime("%d/%m/%y") if pd.notna(end_real_original) else "N/D",
                "duracao_prev_meses": f"{(end_date - start_date).days / 30.4375:.1f}".replace('.', ',') if pd.notna(start_date) and pd.notna(end_date) else "-",
                "duracao_real_meses": f"{(end_real_original - start_real).days / 30.4375:.1f}".replace('.', ',') if pd.notna(start_real) and pd.notna(end_real_original) else "-",
                "vt_text": f"{int(vt):+d}d" if pd.notna(vt) else "-",
                "vd_text": f"{int(vd):+d}d" if pd.notna(vd) else "-",
                "status_color_class": status_color_class
            }
            tasks_base_data_for_stage.append(task)
            
        all_data_by_stage_js[etapa_nome_completo] = tasks_base_data_for_stage
    
    if not all_data_by_stage_js:
        st.warning("Nenhum dado válido para o Gantt Consolidado após a conversão.")
        return

    empreendimentos_no_df = sorted(list(df_gantt_agg["Empreendimento"].unique()))
    
    filter_options = {
        "empreendimentos": ["Todos"] + empreendimentos_no_df, # Renomeado
        "etapas_consolidadas": sorted(all_stage_names_full) # Novo (sem "Todos")
    }

    # Pegar os dados da *primeira* etapa selecionada para a renderização inicial
    tasks_base_data_inicial = all_data_by_stage_js.get(etapa_selecionada_inicialmente, [])

    # Criar um "projeto" único
    project_id = f"p_cons_{random.randint(1000, 9999)}"
    project = {
        "id": project_id,
        "name": f"Comparativo: {etapa_selecionada_inicialmente}", # Nome inicial
        "tasks": tasks_base_data_inicial, # Dados iniciais
        "meta_assinatura_date": None
    }

    df_para_datas = df_gantt_agg
    data_min_proj, data_max_proj = calcular_periodo_datas(df_para_datas)
    total_meses_proj = ((data_max_proj.year - data_min_proj.year) * 12) + (data_max_proj.month - data_min_proj.month) + 1

    num_tasks = len(project["tasks"])
        
    altura_gantt = max(400, (len(empreendimentos_no_df) * 30) + 150)

    # --- 4. Geração do HTML/JS Corrigido ---
    gantt_html = f"""
    <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            {'''
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/virtual-select-plugin@1.0.39/dist/virtual-select.min.css">
            '''}
            <style>
                /* CSS idêntico ao de gerar_gantt_por_projeto, exceto adaptações para consolidado */
                 * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                html, body {{ width: 100%; height: 100%; font-family: 'Segoe UI', sans-serif; background-color: #f5f5f5; color: #333; overflow: hidden; }}
                .gantt-container {{ width: 100%; height: 100%; background-color: white; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); overflow: hidden; position: relative; display: flex; flex-direction: column; }}
                .gantt-main {{ display: flex; flex: 1; overflow: hidden; }}
                .gantt-sidebar-wrapper {{ width: 680px; display: flex; flex-direction: column; flex-shrink: 0; transition: width 0.3s ease-in-out; border-right: 2px solid #e2e8f0; overflow: hidden; }}
                .gantt-sidebar-header {{ background: linear-gradient(135deg, #4a5568, #2d3748); display: flex; flex-direction: column; height: 60px; flex-shrink: 0; }}
                .project-title-row {{ display: flex; justify-content: space-between; align-items: center; padding: 0 15px; height: 30px; color: white; font-weight: 600; font-size: 14px; }}
                .toggle-sidebar-btn {{ background: rgba(255,255,255,0.2); border: none; color: white; width: 24px; height: 24px; border-radius: 5px; cursor: pointer; font-size: 14px; display: flex; align-items: center; justify-content: center; transition: background-color 0.2s, transform 0.3s ease-in-out; }}
                .toggle-sidebar-btn:hover {{ background: rgba(255,255,255,0.4); }}
                .sidebar-grid-header-wrapper {{ display: grid; grid-template-columns: 0px 1fr; color: #d1d5db; font-size: 9px; font-weight: 600; text-transform: uppercase; height: 30px; align-items: center; }}
                .sidebar-grid-header {{ display: grid; grid-template-columns: 2.5fr 0.9fr 0.9fr 0.6fr 0.9fr 0.9fr 0.6fr 0.5fr 0.6fr 0.6fr; padding: 0 10px; align-items: center; }}
                .sidebar-row {{ display: grid; grid-template-columns: 2.5fr 0.9fr 0.9fr 0.6fr 0.9fr 0.9fr 0.6fr 0.5fr 0.6fr 0.6fr; border-bottom: 1px solid #eff2f5; height: 30px; padding: 0 10px; background-color: white; transition: all 0.2s ease-in-out; }}
                .sidebar-cell {{ display: flex; align-items: center; justify-content: center; font-size: 11px; color: #4a5568; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; padding: 0 8px; border: none; }}
                .header-cell {{ text-align: center; }}
                .header-cell.task-name-cell {{ text-align: left; }}
                .gantt-sidebar-content {{ background-color: #f8f9fa; flex: 1; overflow-y: auto; overflow-x: hidden; }}
                .sidebar-group-wrapper {{ display: flex; border-bottom: none; }}
                .gantt-sidebar-content > .sidebar-group-wrapper:last-child {{ border-bottom: none; }}
                .sidebar-group-title-vertical {{ display: none; }}
                .sidebar-group-spacer {{ display: none; }}
                .sidebar-rows-container {{ flex-grow: 1; }}
                .sidebar-row.odd-row {{ background-color: #fdfdfd; }}
                .sidebar-rows-container .sidebar-row:last-child {{ border-bottom: none; }}
                .sidebar-row:hover {{ background-color: #f5f8ff; }}
                .sidebar-cell.task-name-cell {{ justify-content: flex-start; font-weight: 600; color: #2d3748; }}
                .sidebar-cell.status-green {{ color: #1E8449; font-weight: 700; }}
                .sidebar-cell.status-red   {{ color: #C0392B; font-weight: 700; }}
                .sidebar-cell.status-yellow{{ color: #B9770E; font-weight: 700; }}
                .sidebar-cell.status-default{{ color: #566573; font-weight: 700; }}
                .sidebar-row .sidebar-cell:nth-child(2),
                .sidebar-row .sidebar-cell:nth-child(3),
                .sidebar-row .sidebar-cell:nth-child(4),
                .sidebar-row .sidebar-cell:nth-child(5),
                .sidebar-row .sidebar-cell:nth-child(6),
                .sidebar-row .sidebar-cell:nth-child(7),
                .sidebar-row .sidebar-cell:nth-child(8),
                .sidebar-row .sidebar-cell:nth-child(9),
                .sidebar-row .sidebar-cell:nth-child(10) {{ font-size: 8px; }}
                .gantt-row-spacer, .sidebar-row-spacer {{ display: none; }}
                .gantt-sidebar-wrapper.collapsed {{ width: 250px; }}
                .gantt-sidebar-wrapper.collapsed .sidebar-grid-header, .gantt-sidebar-wrapper.collapsed .sidebar-row {{ grid-template-columns: 1fr; padding: 0 15px 0 10px; }}
                .gantt-sidebar-wrapper.collapsed .header-cell:not(.task-name-cell), .gantt-sidebar-wrapper.collapsed .sidebar-cell:not(.task-name-cell) {{ display: none; }}
                .gantt-sidebar-wrapper.collapsed .toggle-sidebar-btn {{ transform: rotate(180deg); }}
                .gantt-chart-content {{ flex: 1; overflow: auto; position: relative; background-color: white; user-select: none; cursor: grab; }}
                .gantt-chart-content.active {{ cursor: grabbing; }}
                .chart-container {{ position: relative; min-width: {total_meses_proj * 30}px; }}
                .chart-header {{ background: linear-gradient(135deg, #4a5568, #2d3748); color: white; height: 60px; position: sticky; top: 0; z-index: 9; display: flex; flex-direction: column; }}
                .year-header {{ height: 30px; display: flex; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.2); }}
                .year-section {{ text-align: center; font-weight: 600; font-size: 12px; display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,0.1); height: 100%; }}
                .month-header {{ height: 30px; display: flex; align-items: center; }}
                .month-cell {{ width: 30px; height: 30px; border-right: 1px solid rgba(255,255,255,0.2); display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 500; }}
                .chart-body {{ position: relative; }}
                .gantt-row {{ position: relative; height: 30px; border-bottom: 1px solid #eff2f5; background-color: white; }}
                .gantt-bar {{ position: absolute; height: 14px; top: 8px; border-radius: 3px; cursor: pointer; transition: all 0.2s ease; display: flex; align-items: center; padding: 0 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .gantt-bar-overlap {{ position: absolute; height: 14px; top: 8px; background-image: linear-gradient(45deg, rgba(0, 0, 0, 0.25) 25%, transparent 25%, transparent 50%, rgba(0, 0, 0, 0.25) 50%, rgba(0, 0, 0, 0.25) 75%, transparent 75%, transparent); background-size: 8px 8px; z-index: 9; pointer-events: none; border-radius: 3px; }}
                .gantt-bar:hover {{ transform: translateY(-1px) scale(1.01); box-shadow: 0 4px 8px rgba(0,0,0,0.2); z-index: 10 !important; }}
                .gantt-bar.previsto {{ z-index: 7; }}
                .gantt-bar.real {{ z-index: 8; }}
                .bar-label {{ font-size: 8px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-shadow: 0 1px 2px rgba(0,0,0,0.4); }}
                .gantt-bar.real .bar-label {{ color: white; }}
                .gantt-bar.previsto .bar-label {{ color: #6C6C6C; }}
                .tooltip {{ position: fixed; background-color: #2d3748; color: white; padding: 6px 10px; border-radius: 4px; font-size: 11px; z-index: 1000; box-shadow: 0 2px 8px rgba(0,0,0,0.3); pointer-events: none; opacity: 0; transition: opacity 0.2s ease; max-width: 220px; }}
                .tooltip.show {{ opacity: 1; }}
                .today-line {{ position: absolute; top: 60px; bottom: 0; width: 1px; background-color: #fdf1f1; z-index: 5; box-shadow: 0 0 1px rgba(229, 62, 62, 0.6); }}
                .month-divider {{ position: absolute; top: 60px; bottom: 0; width: 1px; background-color: #fcf6f6; z-index: 4; pointer-events: none; }}
                .month-divider.first {{ background-color: #eeeeee; width: 1px; }}
                .meta-line, .meta-line-label {{ display: none; }}
                .gantt-chart-content, .gantt-sidebar-content {{ scrollbar-width: thin; scrollbar-color: transparent transparent; }}
                .gantt-chart-content:hover, .gantt-sidebar-content:hover {{ scrollbar-color: #d1d5db transparent; }}
                .gantt-chart-content::-webkit-scrollbar, .gantt-sidebar-content::-webkit-scrollbar {{ height: 8px; width: 8px; }}
                .gantt-chart-content::-webkit-scrollbar-track, .gantt-sidebar-content::-webkit-scrollbar-track {{ background: transparent; }}
                .gantt-chart-content::-webkit-scrollbar-thumb, .gantt-sidebar-content::-webkit-scrollbar-thumb {{ background-color: transparent; border-radius: 4px; }}
                .gantt-chart-content:hover::-webkit-scrollbar-thumb, .gantt-sidebar-content:hover::-webkit-scrollbar-thumb {{ background-color: #d1d5db; }}
                .gantt-chart-content:hover::-webkit-scrollbar-thumb:hover, .gantt-sidebar-content:hover::-webkit-scrollbar-thumb:hover {{ background-color: #a8b2c1; }}
                .gantt-toolbar {{
                    position: absolute; top: 10px; right: 10px;
                    z-index: 100;
                    display: flex;
                    flex-direction: column;
                    gap: 5px;
                    background: rgba(45, 55, 72, 0.9); /* Cor de fundo escura para minimalismo */
                    border-radius: 6px;
                    padding: 5px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                }}
                .toolbar-btn {{
                    background: none;
                    border: none;
                    width: 36px;
                    height: 36px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 20px;
                    color: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: background-color 0.2s, box-shadow 0.2s;
                    padding: 0;
                }}
                .toolbar-btn:hover {{
                    background-color: rgba(255, 255, 255, 0.1);
                    box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.2);
                }}
                .toolbar-btn.is-fullscreen {{
                    background-color: #3b82f6; /* Cor de destaque para o botão ativo */
                    box-shadow: 0 0 0 2px #3b82f6;
                }}
                .toolbar-btn.is-fullscreen:hover {{
                    background-color: #2563eb;
                }}
                 /* *** INÍCIO: Arredondar Dropdown Virtual Select *** */
                    .floating-filter-menu .vscomp-dropbox {{
                        border-radius: 8px; /* Controla o arredondamento dos cantos do dropdown */
                        overflow: hidden;   /* Necessário para que o conteúdo interno não "vaze" pelos cantos arredondados */
                        box-shadow: 0 5px 15px rgba(0,0,0,0.2); /* Sombra para melhor visualização (opcional) */
                        border: 1px solid #ccc; /* Borda sutil (opcional) */
                    }}

                    /* Opcional: Arredondar também o campo de busca interno, se ele ficar visível no topo */
                    .floating-filter-menu .vscomp-search-wrapper {{
                    /* Remove o arredondamento padrão se houver, para não conflitar com o container */
                    border-radius: 0;
                    }}

                    /* Opcional: Garantir que a lista de opções não ultrapasse */
                    .floating-filter-menu .vscomp-options-container {{
                        /* Geralmente não precisa de arredondamento próprio se o overflow:hidden funcionar */
                    }}
                    .floating-filter-menu .vscomp-toggle-button .vscomp-value-tag .vscomp-clear-button {{
                        display: inline-flex;    /* Usa flex para alinhar o ícone interno */
                        align-items: center;     /* Alinha verticalmente o ícone */
                        justify-content: center; /* Alinha horizontalmente o ícone */
                        vertical-align: middle;  /* Ajuda no alinhamento com o texto adjacente */
                        margin-left: 4px;        /* Espaçamento à esquerda (ajuste conforme necessário) */
                        padding: 0;            /* Remove padding interno se houver */
                        position: static;        /* Garante que não use posicionamento absoluto/relativo que possa quebrar o fluxo */
                        transform: none;         /* Remove qualquer translação que possa estar desalinhando */
                    }}

                    /* Opcional: Se o próprio ícone 'X' (geralmente uma tag <i>) precisar de ajuste */
                    .floating-filter-menu .vscomp-toggle-button .vscomp-value-tag .vscomp-clear-button i {{
                    }}
                .fullscreen-btn.is-fullscreen {{
	                    font-size: 24px; padding: 5px 10px; color: white;
	                }}
	                .floating-filter-menu {{
	                    display: none;
	                    position: absolute;
	                    top: 10px; right: 50px; /* Ajuste a posição para abrir ao lado da barra de ferramentas */
	                    width: 280px;
	                    background: white;
	                    border-radius: 8px;
	                    box-shadow: 0 5px 15px rgba(0,0,0,0.3);
	                    z-index: 99;
	                    padding: 15px;
	                    border: 1px solid #e2e8f0;
	                }}
	                .floating-filter-menu.is-open {{
	                    display: block;
	                }}
                .filter-group {{ margin-bottom: 12px; }}
                .filter-group label {{
                    display: block; font-size: 11px; font-weight: 600;
                    color: #4a5568; margin-bottom: 4px;
                    text-transform: uppercase;
                }}
                .filter-group select, .filter-group input[type=number] {{
                    width: 100%; padding: 6px 8px;
                    border: 1px solid #cbd5e0; border-radius: 4px;
                    font-size: 13px;
                }}
                .filter-group-radio, .filter-group-checkbox {{
                    display: flex; align-items: center; padding: 5px 0;
                }}
                .filter-group-radio input, .filter-group-checkbox input {{
                    width: auto; margin-right: 8px;
                }}
                .filter-group-radio label, .filter-group-checkbox label {{
                    font-size: 13px; font-weight: 500;
                    color: #2d3748; margin-bottom: 0; text-transform: none;
                }}
                .filter-apply-btn {{
                    width: 100%; padding: 8px; font-size: 14px; font-weight: 600;
                    color: white; background-color: #2d3748;
                    border: none; border-radius: 4px; cursor: pointer;
                    margin-top: 5px;
                }}
                .floating-filter-menu .vscomp-toggle-button {{
                    border: 1px solid #cbd5e0;
                    border-radius: 4px;
                    padding: 6px 8px;
                    font-size: 13px;
                    min-height: 30px;
                }}
                .floating-filter-menu .vscomp-options {{
                    font-size: 13px;
                }}
                .floating-filter-menu .vscomp-option {{
                    min-height: 30px;
                }}
                .floating-filter-menu .vscomp-search-input {{
                    height: 30px;
                    font-size: 13px;
                }}
            </style>
        </head>
        <body>
            <div class="gantt-container" id="gantt-container-{project['id']}">
                    <div class="gantt-toolbar" id="gantt-toolbar-{project["id"]}">
                        <button class="toolbar-btn" id="filter-btn-{project["id"]}" title="Filtros">
                        <span>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
                            </svg>
                        </span>
                    </button>
                    <button class="toolbar-btn" id="fullscreen-btn-{project["id"]}" title="Tela Cheia">
                        <span>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path>
                            </svg>
                        </span>
                    </button>
                </div>

                <div class="floating-filter-menu" id="filter-menu-{project['id']}">
                    
                    <div class="filter-group">
                        <label for="filter-etapa-consolidada-{project['id']}">Etapa (Visão Atual)</label>
                        <select id="filter-etapa-consolidada-{project['id']}">
                            </select>
                    </div>

                    <div class="filter-group">
                        <label for="filter-empreendimento-{project['id']}">Empreendimento</label>
                        <div id="filter-empreendimento-{project['id']}"></div>
                    </div>

                    <div class="filter-group">
                        <div class="filter-group-checkbox">
                            <input type="checkbox" id="filter-concluidas-{project['id']}">
                            <label for="filter-concluidas-{project['id']}">Mostrar apenas não concluídas</label>
                        </div>
                    </div>
                    
                    <div class="filter-group">
                        <label>Visualização</label>
                        <div class="filter-group-radio">
                            <input type="radio" id="filter-vis-ambos-{project['id']}" name="filter-vis-{project['id']}" value="Ambos" checked>
                            <label for="filter-vis-ambos-{project['id']}">Ambos</label>
                        </div>
                        <div class="filter-group-radio">
                            <input type="radio" id="filter-vis-previsto-{project['id']}" name="filter-vis-{project['id']}" value="Previsto">
                            <label for="filter-vis-previsto-{project['id']}">Previsto</label>
                        </div>
                        <div class="filter-group-radio">
                            <input type="radio" id="filter-vis-real-{project['id']}" name="filter-vis-{project['id']}" value="Real">
                            <label for="filter-vis-real-{project['id']}">Real</label>
                        </div>
                    </div>

                    <div class="filter-group">
                        <label>Simulação Pulmão</label>
                        <div class="filter-group-radio">
                            <input type="radio" id="filter-pulmao-sem-{project['id']}" name="filter-pulmao-{project['id']}" value="Sem Pulmão">
                            <label for="filter-pulmao-sem-{project['id']}">Sem Pulmão</label>
                        </div>
                        <div class="filter-group-radio">
                            <input type="radio" id="filter-pulmao-com-{project['id']}" name="filter-pulmao-{project['id']}" value="Com Pulmão">
                            <label for="filter-pulmao-com-{project['id']}">Com Pulmão</label>
                        </div>
                        <div class="filter-group" id="pulmao-meses-group-{project['id']}" style="margin-top: 8px; display: none; padding-left: 25px;">
                            <label for="filter-pulmao-meses-{project['id']}" style="font-size: 12px; font-weight: 500;">Meses de Pulmão:</label>
                            <input type="number" id="filter-pulmao-meses-{project['id']}" value="{pulmao_meses}" min="0" max="36" step="1" style="padding: 4px 6px; font-size: 12px; height: 28px; width: 80px;">
                        </div>
                    </div>
                    <button class="filter-apply-btn" id="filter-apply-btn-{project['id']}">Aplicar Filtros</button>
                </div>

                <div class="gantt-main">
                    <div class="gantt-sidebar-wrapper" id="gantt-sidebar-wrapper-{project['id']}">
                        <div class="gantt-sidebar-header">
                            <div class="project-title-row">
                                <span>{project["name"]}</span>
                                <button class="toggle-sidebar-btn" id="toggle-sidebar-btn-{project['id']}" title="Recolher/Expandir Tabela">«</button>
                            </div>
                            <div class="sidebar-grid-header-wrapper">
                                <div style="width: 0px;"></div>
                                <div class="sidebar-grid-header">
                                    <div class="header-cell task-name-cell">EMPREENDIMENTO</div>
                                    <div class="header-cell">INÍCIO-P</div>
                                    <div class="header-cell">TÉRMINO-P</div>
                                    <div class="header-cell">DUR-P</div>
                                    <div class="header-cell">INÍCIO-R</div>
                                    <div class="header-cell">TÉRMINO-R</div>
                                    <div class="header-cell">DUR-R</div>
                                    <div class="header-cell">%</div>
                                    <div class="header-cell">VT</div>
                                    <div class="header-cell">VD</div>
                                </div>
                            </div>
                        </div>
                        <div class="gantt-sidebar-content" id="gantt-sidebar-content-{project['id']}"></div>
                    </div>
                    <div class="gantt-chart-content" id="gantt-chart-content-{project['id']}">
                        <div class="chart-container" id="chart-container-{project["id"]}">
                            <div class="chart-header">
                                <div class="year-header" id="year-header-{project["id"]}"></div>
                                <div class="month-header" id="month-header-{project["id"]}"></div>
                            </div>
                            <div class="chart-body" id="chart-body-{project["id"]}"></div>
                            <div class="today-line" id="today-line-{project["id"]}"></div>
                            <div class="meta-line" id="meta-line-{project["id"]}" style="display: none;"></div>
                            <div class="meta-line-label" id="meta-line-label-{project["id"]}" style="display: none;"></div>
                        </div>
                    </div>
                </div>
                <div class="tooltip" id="tooltip-{project["id"]}"></div>
            </div>

            {''''''}
            <script src="https://cdn.jsdelivr.net/npm/virtual-select-plugin@1.0.39/dist/virtual-select.min.js"></script>
            {''''''}

            <script>
                // DEBUG: Verificar dados
                console.log('Inicializando Gantt Consolidado para:', '{project["name"]}');
                
                const coresPorSetor = {json.dumps(StyleConfig.CORES_POR_SETOR)};
                
                // --- NOVAS VARIÁVEIS DE DADOS ---
                // 'projectData' armazena o estado ATUAL (inicia com a etapa selecionada)
                const projectData = [{json.dumps(project)}]; 
                // 'allDataByStage' armazena TUDO, chaveado por nome de etapa
                const allDataByStage = {json.dumps(all_data_by_stage_js)};
                
                // 'allTasks_baseData' agora armazena os dados "crus" da etapa ATUAL
                let allTasks_baseData = {json.dumps(tasks_base_data_inicial)}; 
                
                const initialStageName = {json.dumps(etapa_selecionada_inicialmente)};
                let currentStageName = initialStageName;
                // --- FIM NOVAS VARIÁVEIS ---
                
                const dataMinStr = '{data_min_proj.strftime("%Y-%m-%d")}'; // Range global
                const dataMaxStr = '{data_max_proj.strftime("%Y-%m-%d")}'; // Range global
                let tipoVisualizacao = '{tipo_visualizacao}';
                const PIXELS_PER_MONTH = 30;

                // --- Helpers de Data ---
                const formatDateDisplay = (dateStr) => {{
                    if (!dateStr) return "N/D";
                    const d = parseDate(dateStr);
                    if (!d || isNaN(d.getTime())) return "N/D";
                    const day = String(d.getUTCDate()).padStart(2, '0');
                    const month = String(d.getUTCMonth() + 1).padStart(2, '0');
                    const year = String(d.getUTCFullYear()).slice(-2);
                    return `${{day}}/${{month}}/${{year}}`;
                }};

                function addMonths(dateStr, months) {{
                    if (!dateStr) return null;
                    const date = parseDate(dateStr);
                    if (!date || isNaN(date.getTime())) return null;
                    const originalDay = date.getUTCDate();
                    date.setUTCMonth(date.getUTCMonth() + months);
                    if (date.getUTCDate() !== originalDay) {{
                        date.setUTCDate(0);
                    }}
                    return date.toISOString().split('T')[0];
                }}

                function parseDate(dateStr) {{ 
                    if (!dateStr) return null; 
                    const [year, month, day] = dateStr.split('-').map(Number); 
                    return new Date(Date.UTC(year, month - 1, day)); 
                }}

                // --- Dados de Filtro e Tasks ---
                const filterOptions = {json.dumps(filter_options)};
                // 'allTasks_baseData' (definido acima) é a base da etapa inicial

                const initialPulmaoStatus = '{pulmao_status}';
                const initialPulmaoMeses = {pulmao_meses};

                let pulmaoStatus = '{pulmao_status}';
                let filtersPopulated = false;

                // *** Variáveis Globais para Filtros ***
                // let vsSetor, vsGrupo; // REMOVIDO
                let vsEmpreendimento; 
                let selEtapaConsolidada; // Novo <select>

                // *** CONSTANTES DE ETAPA ***
                const etapas_pulmao = ["PULMÃO VENDA", "PULMÃO INFRA", "PULMÃO RADIER"];
                const etapas_sem_alteracao = ["PROSPECÇÃO", "RADIER", "DEMANDA MÍNIMA", "PE. ÁREAS COMUNS (URB)", "PE. ÁREAS COMUNS (ENG)", "ORÇ. ÁREAS COMUNS", "SUP. ÁREAS COMUNS", "EXECUÇÃO ÁREAS COMUNS"];
                
                // --- Lógica de Pulmão para Consolidado ---
                // *** aplicarLogicaPulmaoConsolidado ***
                function aplicarLogicaPulmaoConsolidado(tasks, offsetMeses, stageName) {{
                    console.log(`Aplicando pulmão de ${{offsetMeses}}m para etapa: ${{stageName}}`);

                    // Verifica o *tipo* de etapa que estamos processando
                    if (etapas_sem_alteracao.includes(stageName)) {{
                        console.log("Etapa sem alteração, retornando tasks originais.");
                        return tasks; // Não altera datas
                    
                    }} else if (etapas_pulmao.includes(stageName)) {{
                        console.log("Etapa Pulmão: movendo apenas início PREVISTO.");
                        // Para etapas de pulmão, move apenas o Início PREVISTO
                        tasks.forEach(task => {{
                            task.start_previsto = addMonths(task.start_previsto, offsetMeses);
                            // DATAS REAIS PERMANECEM INALTERADAS
                            task.inicio_previsto = formatDateDisplay(task.start_previsto);
                            // Não mexe no 'end_date' real
                        }});
                    
                    }} else {{
                        console.log("Etapa Padrão: movendo apenas PREVISTO.");
                        // Para todas as outras etapas, move apenas Início e Fim PREVISTOS
                        tasks.forEach(task => {{
                            task.start_previsto = addMonths(task.start_previsto, offsetMeses);
                            task.end_previsto = addMonths(task.end_previsto, offsetMeses);
                            // DATAS REAIS PERMANECEM INALTERADAS

                            task.inicio_previsto = formatDateDisplay(task.start_previsto);
                            task.termino_previsto = formatDateDisplay(task.end_previsto);
                            // Datas reais mantêm seus valores originais
                        }});
                    }}
                    return tasks;
                }}

                // *** FUNÇÃO CORRIGIDA: applyInitialPulmaoState ***
                function applyInitialPulmaoState() {{
                    if (initialPulmaoStatus === 'Com Pulmão' && initialPulmaoMeses > 0) {{
                        const offsetMeses = -initialPulmaoMeses;
                        let baseTasks = JSON.parse(JSON.stringify(allTasks_baseData));
                        
                        // Passa o nome da etapa inicial - APENAS DATAS PREVISTAS SERÃO MODIFICADAS
                        const tasksProcessadas = aplicarLogicaPulmaoConsolidado(baseTasks, offsetMeses, initialStageName);
                        
                        projectData[0].tasks = tasksProcessadas;
                        // Atualiza também o 'allTasks_baseData' que é a fonte "crua" da etapa atual
                        allTasks_baseData = JSON.parse(JSON.stringify(tasksProcessadas));
                    }}
                }}


                function initGantt() {{
                    console.log('Iniciando Gantt Consolidado com dados:', projectData);
                    
                    if (!projectData || !projectData[0] || !projectData[0].tasks || projectData[0].tasks.length === 0) {{
                        console.warn('Nenhum dado disponível para renderizar na etapa inicial');
                    }}

                    // NOTA: applyInitialPulmaoState foi movida para DENTRO de initGantt
                    applyInitialPulmaoState(); 
                    
                    renderSidebar();
                    renderHeader();
                    renderChart();
                    renderMonthDividers();
                    setupEventListeners();
                    positionTodayLine();
                    populateFilters();
                }}

                // *** FUNÇÃO CORRIGIDA: renderSidebar para ordenação ***
                function renderSidebar() {{
                    const sidebarContent = document.getElementById('gantt-sidebar-content-{project["id"]}');
                    let tasks = projectData[0].tasks;

                    if (!tasks || tasks.length === 0) {{
                        sidebarContent.innerHTML = '<div style="padding: 20px; text-align: center; color: #666;">Nenhum empreendimento disponível</div>';
                        return;
                    }}

                    // Ordenação dinâmica
                    const dateSortFallback = new Date(8640000000000000);

                    if (tipoVisualizacao === 'Real') {{
                        tasks.sort((a, b) => {{
                            const dateA = a.start_real ? parseDate(a.start_real) : dateSortFallback;
                            const dateB = b.start_real ? parseDate(b.start_real) : dateSortFallback;
                            if (dateA > dateB) return 1;
                            if (dateA < dateB) return -1;
                            return a.name.localeCompare(b.name);
                        }});
                    }} else {{
                        tasks.sort((a, b) => {{
                            const dateA = a.start_previsto ? parseDate(a.start_previsto) : dateSortFallback;
                            const dateB = b.start_previsto ? parseDate(b.start_previsto) : dateSortFallback;
                            if (dateA > dateB) return 1;
                            if (dateA < dateB) return -1;
                            return a.name.localeCompare(b.name);
                        }});
                    }}

                    let html = '';
                    let globalRowIndex = 0;

                    html += '<div class="sidebar-rows-container">';
                    tasks.forEach(task => {{
                        globalRowIndex++;
                        const rowClass = globalRowIndex % 2 !== 0 ? 'odd-row' : '';
                        task.numero_etapa = globalRowIndex;

                        html += '<div class="sidebar-row ' + rowClass + '">' +
                            '<div class="sidebar-cell task-name-cell" title="' + task.numero_etapa + '. ' + task.name + '">' + task.numero_etapa + '. ' + task.name + '</div>' +
                            '<div class="sidebar-cell">' + task.inicio_previsto + '</div>' +
                            '<div class="sidebar-cell">' + task.termino_previsto + '</div>' +
                            '<div class="sidebar-cell">' + task.duracao_prev_meses + '</div>' +
                            '<div class="sidebar-cell">' + task.inicio_real + '</div>' +
                            '<div class="sidebar-cell">' + task.termino_real + '</div>' +
                            '<div class="sidebar-cell">' + task.duracao_real_meses + '</div>' +
                            '<div class="sidebar-cell ' + task.status_color_class + '">' + task.progress + '%</div>' +
                            '<div class="sidebar-cell ' + task.status_color_class + '">' + task.vt_text + '</div>' +
                            '<div class="sidebar-cell ' + task.status_color_class + '">' + task.vd_text + '</div>' +
                            '</div>';
                    }});
                    html += '</div>';
                    sidebarContent.innerHTML = html;
                }}

                // *** FUNÇÃO CORRIGIDA: renderHeader ***
                function renderHeader() {{
                    const yearHeader = document.getElementById('year-header-{project["id"]}');
                    const monthHeader = document.getElementById('month-header-{project["id"]}');
                    let yearHtml = '', monthHtml = '';
                    const yearsData = [];
                    let currentDate = parseDate(dataMinStr);
                    const dataMax = parseDate(dataMaxStr);

                    if (!currentDate || !dataMax || isNaN(currentDate.getTime()) || isNaN(dataMax.getTime())) {{
                         yearHeader.innerHTML = "Datas inválidas";
                         monthHeader.innerHTML = "";
                         return;
                    }}

                    // DECLARE estas variáveis
                    let currentYear = -1, monthsInCurrentYear = 0;

                    let totalMonths = 0;
                    while (currentDate <= dataMax && totalMonths < 240) {{
                        const year = currentDate.getUTCFullYear();
                        if (year !== currentYear) {{
                            if (currentYear !== -1) yearsData.push({{ year: currentYear, count: monthsInCurrentYear }});
                            currentYear = year; 
                            monthsInCurrentYear = 0;
                        }}
                        const monthNumber = String(currentDate.getUTCMonth() + 1).padStart(2, '0');
                        monthHtml += '<div class="month-cell">' + monthNumber + '</div>';
                        monthsInCurrentYear++;
                        currentDate.setUTCMonth(currentDate.getUTCMonth() + 1);
                        totalMonths++;
                    }}
                    if (currentYear !== -1) yearsData.push({{ year: currentYear, count: monthsInCurrentYear }});
                    yearsData.forEach(data => {{ 
                        const yearWidth = data.count * PIXELS_PER_MONTH; 
                        yearHtml += '<div class="year-section" style="width:' + yearWidth + 'px">' + data.year + '</div>'; 
                    }});

                    const chartContainer = document.getElementById('chart-container-{project["id"]}');
                    if (chartContainer) {{
                        chartContainer.style.minWidth = totalMonths * PIXELS_PER_MONTH + 'px';
                    }}

                    yearHeader.innerHTML = yearHtml;
                    monthHeader.innerHTML = monthHtml;
                }}

                function renderChart() {{
                    const chartBody = document.getElementById('chart-body-{project["id"]}');
                    const tasks = projectData[0].tasks;
                    
                    if (!tasks || tasks.length === 0) {{
                        chartBody.innerHTML = '<div style="padding: 20px; text-align: center; color: #666;">Nenhum empreendimento disponível</div>';
                        return;
                    }}
                    
                    chartBody.innerHTML = '';

                    tasks.forEach(task => {{
                        const row = document.createElement('div'); 
                        row.className = 'gantt-row';
                        let barPrevisto = null;
                        if (tipoVisualizacao === 'Ambos' || tipoVisualizacao === 'Previsto') {{ 
                            barPrevisto = createBar(task, 'previsto'); 
                            row.appendChild(barPrevisto); 
                        }}
                        let barReal = null;
                        if ((tipoVisualizacao === 'Ambos' || tipoVisualizacao === 'Real') && task.start_real && (task.end_real_original_raw || task.end_real)) {{ 
                            barReal = createBar(task, 'real'); 
                            row.appendChild(barReal); 
                        }}
                        if (barPrevisto && barReal) {{
                            const s_prev = parseDate(task.start_previsto), e_prev = parseDate(task.end_previsto), s_real = parseDate(task.start_real), e_real = parseDate(task.end_real_original_raw || task.end_real);
                            if (s_prev && e_prev && s_real && e_real && s_real <= s_prev && e_real >= e_prev) {{ 
                                barPrevisto.style.zIndex = '8'; 
                                barReal.style.zIndex = '7'; 
                            }}
                            renderOverlapBar(task, row);
                        }}
                        chartBody.appendChild(row);
                    }});
                }}

                function createBar(task, tipo) {{
                    const startDate = parseDate(tipo === 'previsto' ? task.start_previsto : task.start_real);
                    const endDate = parseDate(tipo === 'previsto' ? task.end_previsto : (task.end_real_original_raw || task.end_real));
                    if (!startDate || !endDate) return document.createElement('div');
                    const left = getPosition(startDate);
                    const width = getPosition(endDate) - left + (PIXELS_PER_MONTH / 30);
                    const bar = document.createElement('div'); 
                    bar.className = 'gantt-bar ' + tipo;
                    const coresSetor = coresPorSetor[task.setor] || coresPorSetor['Não especificado'] || {{previsto: '#cccccc', real: '#888888'}};
                    bar.style.backgroundColor = tipo === 'previsto' ? coresSetor.previsto : coresSetor.real;
                    bar.style.left = left + 'px'; 
                    bar.style.width = width + 'px';
                    const barLabel = document.createElement('span'); 
                    barLabel.className = 'bar-label'; 
                    barLabel.textContent = task.name + ' (' + task.progress + '%)'; 
                    bar.appendChild(barLabel);
                    bar.addEventListener('mousemove', e => showTooltip(e, task, tipo));
                    bar.addEventListener('mouseout', () => hideTooltip());
                    return bar;
                }}

                function renderOverlapBar(task, row) {{
                   if (!task.start_real || !(task.end_real_original_raw || task.end_real)) return;
                    const s_prev = parseDate(task.start_previsto), e_prev = parseDate(task.end_previsto), s_real = parseDate(task.start_real), e_real = parseDate(task.end_real_original_raw || task.end_real);
                    const overlap_start = new Date(Math.max(s_prev, s_real)), overlap_end = new Date(Math.min(e_prev, e_real));
                    if (overlap_start < overlap_end) {{
                        const left = getPosition(overlap_start), width = getPosition(overlap_end) - left + (PIXELS_PER_MONTH / 30);
                        if (width > 0) {{ 
                            const overlapBar = document.createElement('div'); 
                            overlapBar.className = 'gantt-bar-overlap'; 
                            overlapBar.style.left = left + 'px'; 
                            overlapBar.style.width = width + 'px'; 
                            row.appendChild(overlapBar); 
                        }}
                    }}
                }}

                function getPosition(date) {{
                    if (!date) return 0;
                    const chartStart = parseDate(dataMinStr);
                    if (!chartStart || isNaN(chartStart.getTime())) return 0;
                    const monthsOffset = (date.getUTCFullYear() - chartStart.getUTCFullYear()) * 12 + (date.getUTCMonth() - chartStart.getUTCMonth());
                    const dayOfMonth = date.getUTCDate() - 1;
                    const daysInMonth = new Date(date.getUTCFullYear(), date.getUTCMonth() + 1, 0).getUTCDate();
                    const fractionOfMonth = daysInMonth > 0 ? dayOfMonth / daysInMonth : 0;
                    return (monthsOffset + fractionOfMonth) * PIXELS_PER_MONTH;
                }}

                function positionTodayLine() {{
                    const todayLine = document.getElementById('today-line-{project["id"]}');
                    const today = new Date(), todayUTC = new Date(Date.UTC(today.getFullYear(), today.getMonth(), today.getDate()));
                    const chartStart = parseDate(dataMinStr), chartEnd = parseDate(dataMaxStr);
                    if (chartStart && chartEnd && !isNaN(chartStart.getTime()) && !isNaN(chartEnd.getTime()) && todayUTC >= chartStart && todayUTC <= chartEnd) {{ 
                        const offset = getPosition(todayUTC); 
                        todayLine.style.left = offset + 'px'; 
                        todayLine.style.display = 'block'; 
                    }} else {{ 
                        todayLine.style.display = 'none'; 
                    }}
                }}

                function showTooltip(e, task, tipo) {{
                    const tooltip = document.getElementById('tooltip-{project["id"]}');
                    let content = '<b>' + task.name + '</b><br>';
                    if (tipo === 'previsto') {{ 
                        content += 'Previsto: ' + task.inicio_previsto + ' - ' + task.termino_previsto + '<br>Duração: ' + task.duracao_prev_meses + 'M'; 
                    }} else {{ 
                        content += 'Real: ' + task.inicio_real + ' - ' + task.termino_real + '<br>Duração: ' + task.duracao_real_meses + 'M<br>Variação Término: ' + task.vt_text + '<br>Variação Duração: ' + task.vd_text; 
                    }}
                    content += '<br><b>Progresso: ' + task.progress + '%</b><br>Setor: ' + task.setor + '<br>Grupo: ' + task.grupo;
                    tooltip.innerHTML = content;
                    tooltip.classList.add('show');
                    const tooltipWidth = tooltip.offsetWidth, tooltipHeight = tooltip.offsetHeight;
                    const viewportWidth = window.innerWidth, viewportHeight = window.innerHeight;
                    const mouseX = e.clientX, mouseY = e.clientY;
                    const padding = 15;
                    let left, top;
                    if ((mouseX + padding + tooltipWidth) > viewportWidth) {{ 
                        left = mouseX - padding - tooltipWidth; 
                    }} else {{ 
                        left = mouseX + padding; 
                    }}
                    if ((mouseY + padding + tooltipHeight) > viewportHeight) {{ 
                        top = mouseY - padding - tooltipHeight; 
                    }} else {{ 
                        top = mouseY + padding; 
                    }}
                    if (left < padding) left = padding;
                    if (top < padding) top = padding;
                    tooltip.style.left = left + 'px';
                    tooltip.style.top = top + 'px';
                }}

                function hideTooltip() {{ 
                    document.getElementById('tooltip-{project["id"]}').classList.remove('show'); 
                }}

                function renderMonthDividers() {{
                    const chartContainer = document.getElementById('chart-container-{project["id"]}');
                    chartContainer.querySelectorAll('.month-divider, .month-divider-label').forEach(el => el.remove());
                    let currentDate = parseDate(dataMinStr);
                    const dataMax = parseDate(dataMaxStr);
                     if (!currentDate || !dataMax || isNaN(currentDate.getTime()) || isNaN(dataMax.getTime())) return;
                    let totalMonths = 0;
                    while (currentDate <= dataMax && totalMonths < 240) {{
                        const left = getPosition(currentDate);
                        const divider = document.createElement('div'); 
                        divider.className = 'month-divider';
                        if (currentDate.getUTCMonth() === 0) divider.classList.add('first');
                        divider.style.left = left + 'px'; 
                        chartContainer.appendChild(divider);
                        currentDate.setUTCMonth(currentDate.getUTCMonth() + 1);
                        totalMonths++;
                    }}
                }}

                function setupEventListeners() {{
                    const ganttChartContent = document.getElementById('gantt-chart-content-{project["id"]}'), sidebarContent = document.getElementById('gantt-sidebar-content-{project['id']}');
                    const fullscreenBtn = document.getElementById('fullscreen-btn-{project["id"]}'), toggleBtn = document.getElementById('toggle-sidebar-btn-{project['id']}');
                    const filterBtn = document.getElementById('filter-btn-{project["id"]}');
                    const filterMenu = document.getElementById('filter-menu-{project['id']}');
                    const container = document.getElementById('gantt-container-{project["id"]}');

                    const applyBtn = document.getElementById('filter-apply-btn-{project["id"]}');
                    if (applyBtn) applyBtn.addEventListener('click', () => applyFiltersAndRedraw());

                    if (fullscreenBtn) fullscreenBtn.addEventListener('click', () => toggleFullscreen());

                    // Adiciona listener para o botão de filtro
                    if (filterBtn) {{
                        filterBtn.addEventListener('click', () => {{
                            filterMenu.classList.toggle('is-open');
                        }});
                    }}

                    // Fecha o menu de filtro ao clicar fora
                    document.addEventListener('click', (event) => {{ 
                        if (filterMenu && filterBtn && !filterMenu.contains(event.target) && !filterBtn.contains(event.target)) {{
                            filterMenu.classList.remove('is-open');
                        }}
                    }});

                    if (container) container.addEventListener('fullscreenchange', () => handleFullscreenChange());

                    if (toggleBtn) toggleBtn.addEventListener('click', () => toggleSidebar());
                    if (ganttChartContent && sidebarContent) {{
                        let isSyncing = false;
                        ganttChartContent.addEventListener('scroll', () => {{ if (!isSyncing) {{ isSyncing = true; sidebarContent.scrollTop = ganttChartContent.scrollTop; isSyncing = false; }} }});
                        sidebarContent.addEventListener('scroll', () => {{ if (!isSyncing) {{ isSyncing = true; ganttChartContent.scrollTop = sidebarContent.scrollTop; isSyncing = false; }} }});
                        let isDown = false, startX, scrollLeft;
                        ganttChartContent.addEventListener('mousedown', (e) => {{ isDown = true; ganttChartContent.classList.add('active'); startX = e.pageX - ganttChartContent.offsetLeft; scrollLeft = ganttChartContent.scrollLeft; }});
                        ganttChartContent.addEventListener('mouseleave', () => {{ isDown = false; ganttChartContent.classList.remove('active'); }});
                        ganttChartContent.addEventListener('mouseup', () => {{ isDown = false; ganttChartContent.classList.remove('active'); }});
                        ganttChartContent.addEventListener('mousemove', (e) => {{ if (!isDown) return; e.preventDefault(); const x = e.pageX - ganttChartContent.offsetLeft; const walk = (x - startX) * 2; ganttChartContent.scrollLeft = scrollLeft - walk; }});
                    }}
                }}

                function toggleSidebar() {{ 
                    document.getElementById('gantt-sidebar-wrapper-{project["id"]}').classList.toggle('collapsed'); 
                }}

                function toggleFullscreen() {{
                    const container = document.getElementById('gantt-container-{project["id"]}');
                    if (!document.fullscreenElement) {{
                        container.requestFullscreen().catch(err => alert('Erro: ' + err.message));
                    }} else {{
                        document.exitFullscreen();
                    }}
                }}

                function handleFullscreenChange() {{
                        const btn = document.getElementById('fullscreen-btn-{project["id"]}');
                        const container = document.getElementById('gantt-container-{project["id"]}');
                        if (document.fullscreenElement === container) {{
                            btn.innerHTML = '<span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 9l6 6m0-6l-6 6M3 20.29V5a2 2 0 012-2h14a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2v-.29"></path></svg></span>';
                            btn.classList.add('is-fullscreen');
                        }} else {{
                            btn.innerHTML = '<span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path></svg></span>';
                            btn.classList.remove('is-fullscreen');
                            document.getElementById('filter-menu-{project["id"]}').classList.remove('is-open');
                        }}
                    }}
                function updatePulmaoInputVisibility() {{
                    const radioCom = document.getElementById('filter-pulmao-com-{project["id"]}');
                    const mesesGroup = document.getElementById('pulmao-meses-group-{project["id"]}');
                    if (radioCom && mesesGroup) {{
                        if (radioCom.checked) {{ 
                            mesesGroup.style.display = 'block'; 
                        }} else {{ 
                            mesesGroup.style.display = 'none'; 
                        }}
                    }}
                 }}

                // *** FUNÇÃO populateFilters MODIFICADA ***
                function populateFilters() {{
                    if (filtersPopulated) return;

                    // *** 1. NOVO FILTRO DE ETAPA (Single Select) ***
                    selEtapaConsolidada = document.getElementById('filter-etapa-consolidada-{project["id"]}');
                    filterOptions.etapas_consolidadas.forEach(etapaNome => {{
                        const isSelected = (etapaNome === initialStageName) ? 'selected' : '';
                        selEtapaConsolidada.innerHTML += `<option value="${{etapaNome}}" ${{isSelected}}>${{etapaNome}}</option>`;
                    }});

                    const vsConfig = {{
                        multiple: true,
                        search: true,
                        optionsCount: 6,
                        showResetButton: true,
                        resetButtonText: 'Limpar',
                        selectAllText: 'Selecionar Todos',
                        allOptionsSelectedText: 'Todos',
                        optionsSelectedText: 'selecionados',
                        searchPlaceholderText: 'Buscar...',
                        optionHeight: '30px',
                        popupDropboxBreakpoint: '3000px',
                        noOptionsText: 'Nenhuma opção encontrada',
                        noSearchResultsText: 'Nenhum resultado encontrado',
                    }};

                    // *** 2. FILTRO DE SETOR (REMOVIDO) ***
                    // if (filterOptions.setores) {{
                    //     const setorOptions = filterOptions.setores.map(s => ({{ label: s, value: s }}));
                    //     vsSetor = VirtualSelect.init({{ ... }});
                    // }}

                    // *** 3. FILTRO DE GRUPO (REMOVIDO) ***
                    // if (filterOptions.grupos) {{
                    //     const grupoOptions = filterOptions.grupos.map(g => ({{ label: g, value: g }}));
                    //     vsGrupo = VirtualSelect.init({{ ... }});
                    // }}

                    // *** 4. FILTRO DE EMPREENDIMENTO (Renomeado) ***
                    const empreendimentoOptions = filterOptions.empreendimentos.map(e => ({{ label: e, value: e }}));
                    vsEmpreendimento = VirtualSelect.init({{ // Renomeado de vsEtapa
                        ...vsConfig,
                        ele: '#filter-empreendimento-{project["id"]}', // ID Modificado
                        options: empreendimentoOptions,
                        placeholder: "Selecionar Empreendimento(s)",
                        selectedValue: ["Todos"]
                    }});

                    // *** 5. RESTO DOS FILTROS (Idêntico) ***
                    const visRadio = document.querySelector('input[name="filter-vis-{project['id']}"][value="' + tipoVisualizacao + '"]');
                    if(visRadio) visRadio.checked = true;

                    const radioCom = document.getElementById('filter-pulmao-com-{project["id"]}');
                    const radioSem = document.getElementById('filter-pulmao-sem-{project["id"]}');
                    radioCom.addEventListener('change', updatePulmaoInputVisibility);
                    radioSem.addEventListener('change', updatePulmaoInputVisibility);
                    const pulmaoRadioInitial = document.querySelector('input[name="filter-pulmao-{project['id']}"][value="' + initialPulmaoStatus + '"]');
                    if(pulmaoRadioInitial) pulmaoRadioInitial.checked = true;
                    document.getElementById('filter-pulmao-meses-{project["id"]}').value = {pulmao_meses};
                    updatePulmaoInputVisibility();

                    filtersPopulated = true;
                }}

                // *** FUNÇÃO updateProjectTitle (Nova/Modificada) ***
                function updateProjectTitle(newStageName) {{
                    const projectTitle = document.querySelector('#gantt-sidebar-wrapper-{project["id"]} .project-title-row span');
                    if (projectTitle) {{
                        projectTitle.textContent = `Comparativo: ${{newStageName}}`;
                        // Atualiza também o 'projectData' global se necessário, embora o 'name' não seja mais usado
                        projectData[0].name = `Comparativo: ${{newStageName}}`;
                    }}
                }}

                // *** FUNÇÃO applyFiltersAndRedraw MODIFICADA ***
                function applyFiltersAndRedraw() {{
                    try {{
                        // *** 1. LER A ETAPA PRIMEIRO ***
                        const selEtapaNome = selEtapaConsolidada.value;
                        
                        // *** 2. LER OUTROS FILTROS ***
                        // const selSetorArray = vsSetor ? vsSetor.getValue() || [] : []; // REMOVIDO
                        // const selGrupoArray = vsGrupo ? vsGrupo.getValue() || [] : []; // REMOVIDO
                        const selEmpreendimentoArray = vsEmpreendimento ? vsEmpreendimento.getValue() || [] : []; // Renomeado
                        
                        const selConcluidas = document.getElementById('filter-concluidas-{project["id"]}').checked;
                        const selVis = document.querySelector('input[name="filter-vis-{project['id']}"]:checked').value;
                        const selPulmao = document.querySelector('input[name="filter-pulmao-{project['id']}"]:checked').value;
                        const selPulmaoMeses = parseInt(document.getElementById('filter-pulmao-meses-{project["id"]}').value, 10) || 0;

                        // *** FECHAR MENU DE FILTROS ***
                        document.getElementById('filter-menu-{project["id"]}').classList.remove('is-open');

                        // *** 3. ATUALIZAR DADOS BASE SE A ETAPA MUDOU ***
                        if (selEtapaNome !== currentStageName) {{
                            currentStageName = selEtapaNome;
                            // Pegar os dados "crus" para a nova etapa
                            allTasks_baseData = JSON.parse(JSON.stringify(allDataByStage[currentStageName] || []));
                            console.log(`Mudando para etapa: ${{currentStageName}}. Tasks carregadas: ${{allTasks_baseData.length}}`);
                        }}

                        // Começar com os dados da etapa (já atualizados ou não)
                        let baseTasks = JSON.parse(JSON.stringify(allTasks_baseData));

                        // *** 4. APLICAR LÓGICA DE PULMÃO (CORRIGIDO) ***
                        if (selPulmao === 'Com Pulmão' && selPulmaoMeses > 0) {{
                            const offsetMeses = -selPulmaoMeses;
                            // Passa o nome da etapa atual para a lógica - APENAS PREVISTO AFETADO
                            baseTasks = aplicarLogicaPulmaoConsolidado(baseTasks, offsetMeses, currentStageName);
                        }}

                        // *** 5. APLICAR FILTROS SECUNDÁRIOS ***
                        let filteredTasks = baseTasks;

                        // if (selSetorArray.length > 0 && !selSetorArray.includes('Todos')) {{
                        //     filteredTasks = filteredTasks.filter(t => selSetorArray.includes(t.setor));
                        // }} // REMOVIDO
                        
                        // if (selGrupoArray.length > 0 && !selGrupoArray.includes('Todos')) {{
                        //     filteredTasks = filteredTasks.filter(t => selGrupoArray.includes(t.grupo));
                        // }} // REMOVIDO
                        
                        // Lógica de filtro de empreendimento (antiga 'etapa')
                        if (selEmpreendimentoArray.length > 0 && !selEmpreendimentoArray.includes('Todos')) {{
                            filteredTasks = filteredTasks.filter(t => selEmpreendimentoArray.includes(t.name));
                        }}

                        if (selConcluidas) {{
                            filteredTasks = filteredTasks.filter(t => t.progress < 100);
                        }}

                        console.log('Empreendimentos após filtros:', filteredTasks.length);

                        // *** 6. ATUALIZAR DADOS E REDESENHAR ***
                        projectData[0].tasks = filteredTasks; // Atualiza as tarefas ativas
                        tipoVisualizacao = selVis;
                        pulmaoStatus = selPulmao;

                        // *** 7. ATUALIZAR TÍTULO DO PROJETO ***
                        updateProjectTitle(currentStageName);

                        // Redesenhar
                        renderSidebar();
                        renderChart();

                    }} catch (error) {{
                        console.error('Erro ao aplicar filtros no consolidado:', error);
                        alert('Erro ao aplicar filtros: ' + error.message);
                    }}
                }}

                // DEBUG: Verificar dados antes de inicializar
                console.log('Dados do projeto consolidado (inicial):', projectData);
                console.log('Tasks base consolidado (inicial):', allTasks_baseData);
                console.log('TODOS os dados de etapa (full):', allDataByStage);
                
                // Inicializar o Gantt Consolidado
                initGantt();
            </script>
        </body>
        </html>
    """
    components.html(gantt_html, height=altura_gantt, scrolling=True)
    # st.markdown("---") no consolidado, pois ele não é parte de um loop

# --- FUNÇÃO PRINCIPAL DE GANTT (DISPATCHER) ---
def gerar_gantt(df, tipo_visualizacao, filtrar_nao_concluidas, df_original_para_ordenacao, pulmao_status, pulmao_meses, etapa_selecionada_inicialmente):
    """
    Decide qual Gantt gerar com base na seleção da etapa inicial.
    """
    if df.empty:
        st.warning("Sem dados disponíveis para exibir o Gantt.")
        return

    # A decisão do modo é baseada no parâmetro, não mais no conteúdo do DF
    is_consolidated_view = etapa_selecionada_inicialmente != "Todos"

    if is_consolidated_view:
        gerar_gantt_consolidado(
            df, 
            tipo_visualizacao, 
            df_original_para_ordenacao, 
            pulmao_status, 
            pulmao_meses,
            etapa_selecionada_inicialmente
        )
    else:
        # Agora gera apenas UM gráfico com todos os empreendimentos
        gerar_gantt_por_projeto(
            df, 
            tipo_visualizacao, 
            df_original_para_ordenacao, 
            pulmao_status, 
            pulmao_meses
        )

# O restante do código Streamlit...
st.set_page_config(layout="wide", page_title="Dashboard de Gantt Comparativo")

# Tente executar a tela de boas-vindas. Se os arquivos não existirem, apenas pule.
try:
    if show_welcome_screen():
        st.stop()
except NameError:
    st.warning("Arquivo `popup.py` não encontrado. Pulando tela de boas-vindas.")
except Exception as e:
    st.warning(f"Erro ao carregar `popup.py`: {e}")


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

    if buscar_e_processar_dados_completos:
        try:
            # --- CORREÇÃO APLICADA AQUI ---
            df_real_resultado = buscar_e_processar_dados_completos()
            # -------------------------------

            if df_real_resultado is not None and not df_real_resultado.empty:
                df_real = df_real_resultado.copy()
                df_real["Etapa"] = df_real["Etapa"].apply(padronizar_etapa)
                # Renomeia colunas ANTES do pivot se os nomes originais forem diferentes
                df_real = df_real.rename(columns={"EMP": "Empreendimento", "%_Concluido": "% concluído"})

                # Converte porcentagem antes do pivot
                if "% concluído" in df_real.columns:
                    df_real["% concluído"] = df_real["% concluído"].apply(converter_porcentagem)
                else:
                    # Adiciona a coluna se não existir, para evitar erro no pivot
                    df_real["% concluído"] = 0.0

                # Verifica se 'Inicio_Fim' e 'Valor' existem antes de pivotar
                if "Inicio_Fim" in df_real.columns and "Valor" in df_real.columns:
                    df_real_pivot = df_real.pivot_table(
                        index=["Empreendimento", "Etapa", "% concluído"], # Inclui % concluído no índice
                        columns="Inicio_Fim",
                        values="Valor",
                        aggfunc="first"
                    ).reset_index()
                    df_real_pivot.columns.name = None # Remove o nome do índice das colunas

                    # Renomeia APÓS o pivot
                    if "INICIO" in df_real_pivot.columns:
                        df_real_pivot = df_real_pivot.rename(columns={"INICIO": "Inicio_Real"})
                    if "TERMINO" in df_real_pivot.columns:
                        df_real_pivot = df_real_pivot.rename(columns={"TERMINO": "Termino_Real"})
                    df_real = df_real_pivot # Atualiza df_real com o resultado pivotado
                else:
                     # st.warning("Colunas 'Inicio_Fim' ou 'Valor' não encontradas nos dados reais. Pivot não aplicado.")
                     # Mantém df_real como está, mas garante colunas esperadas
                     if "Inicio_Real" not in df_real.columns: df_real["Inicio_Real"] = pd.NaT
                     if "Termino_Real" not in df_real.columns: df_real["Termino_Real"] = pd.NaT

            else:
                # st.info("Nenhum dado real retornado por buscar_e_processar_dados_completos().")
                df_real = pd.DataFrame() # Garante que seja um DF vazio
        except Exception as e:
            st.error(f"Erro detalhado ao processar dados reais: {e}")
            import traceback
            # st.error(traceback.format_exc()) # Mostra o traceback completo para depuração
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

    if not df_real.empty and not df_previsto.empty:
        df_merged = pd.merge(df_previsto, df_real[["Empreendimento", "Etapa", "Inicio_Real", "Termino_Real", "% concluído"]], on=["Empreendimento", "Etapa"], how="outer")

        # --- Lógica de Exceção para Etapas Apenas no Real ---
    etapas_excecao = [
        "PE. LIMP.", "ORÇ. LIMP.", "SUP. LIMP.",
        "PE. TER.", "ORÇ. TER.", "SUP. TER.", 
        "PE. INFRA", "ORÇ. INFRA", "SUP. INFRA",
        "PE. PAV", "ORÇ. PAV", "SUP. PAV"
    ]

    # Identifica linhas onde o previsto (Inicio_Prevista) é nulo, mas a etapa é de exceção
    filtro_excecao = df_merged["Etapa"].isin(etapas_excecao) & df_merged["Inicio_Prevista"].isna()
    df_merged.loc[filtro_excecao, "Inicio_Prevista"] = df_merged.loc[filtro_excecao, "Inicio_Real"]
    df_merged.loc[filtro_excecao, "Termino_Prevista"] = df_merged.loc[filtro_excecao, "Termino_Real"]

    # CORREÇÃO: Buscar UGB correta para as subetapas
    if not df_previsto.empty:
        # Criar mapeamento de UGB por empreendimento
        ugb_por_empreendimento = df_previsto.groupby('Empreendimento')['UGB'].first().to_dict()
        
        # Para cada subetapa sem UGB, buscar a UGB do empreendimento correspondente
        for idx in df_merged[filtro_excecao & df_merged["UGB"].isna()].index:
            empreendimento = df_merged.loc[idx, 'Empreendimento']
            if empreendimento in ugb_por_empreendimento:
                df_merged.loc[idx, 'UGB'] = ugb_por_empreendimento[empreendimento]
        

        # Verifica se há etapas não mapeadas
    if etapas_nao_mapeadas:

        # CSS para estilizar o sininho e o popup
        st.markdown("""
        <style>
        .macrofluxo-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 20px;
        }

        .macrofluxo-title {
            font-size: 32px;
            font-weight: bold;
            color: #1f77b4;
            margin: 0;
        }

        .notification-bell {
            position: relative;
            display: inline-block;
            cursor: pointer;
            font-size: 24px;
            margin-left: -30px;
            margin-top: 7px;
        }

        .notification-icon {
            width: 24px;
            height: 24px;
            color: #ff6b00;
        }

        .notification-bell:hover .notification-icon {
            color: #ff4500;
        }

        .notification-popup {
            display: none;
            position: absolute;
            background-color: #ffcc00;
            border: 1px solid #ff9900;
            border-radius: 5px;
            padding: 15px;
            min-width: 300px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            z-index: 1000;
            left: 30px;
            top: 0;
        }

        .notification-bell:hover .notification-popup {
            display: block;
        }

        .notification-content {
            color: #333;
            font-size: 14px;
        }

        .etapa-code {
            background-color: #f8f9fa;
            padding: 5px;
            margin: 3px 0;
            border-radius: 3px;
            font-family: monospace;
            font-size: 12px;
        }
        </style>
        """, unsafe_allow_html=True)

        # HTML para o cabeçalho com título e ícone de notificação
        etapas_html = "".join([f'<div class="etapa-code">{etapa}</div>' for etapa in sorted(list(etapas_nao_mapeadas))])

        st.markdown(f"""
        <div class="macrofluxo-header">
            <h1 class="macrofluxo-title">Macrofluxo</h1>
            <div class="notification-bell">
                <svg class="notification-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                </svg>
                <div class="notification-popup">
                    <div class="notification-content">
                        <strong>⚠️ Alerta de Dados</strong><br><br>
                        As seguintes etapas foram encontradas nos dados, mas não são reconhecidas. 
                        Verifique a ortografia no arquivo de origem:
                        <br><br>
                        {etapas_html}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        # Quando não há etapas não mapeadas, mostra apenas o título sem o ícone
        st.markdown("""
        <div class="macrofluxo-header">
            <h1 class="macrofluxo-title">Macrofluxo</h1>
        </div>
        """, unsafe_allow_html=True)

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

# --- Bloco Principal ---
with st.spinner("Carregando e processando dados..."):
    df_data = load_data()
    if df_data is not None and not df_data.empty:
        with st.sidebar:
            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                try:
                    st.image("logoNova.png", width=200)
                except:
                    # st.warning("Logo 'logoNova.png' não encontrada.")
                    pass
        
            st.markdown("---")
            # Título centralizado
            st.markdown("""
            <div style='
                margin: 1px 0 -70px 0; 
                padding: 12px 16px;
                border-radius: 6px;
                height: 60px;
                display: flex;
                justify-content: flex-start;
                align-items: center;
            '>
                <h4 style='
                    color: #707070; 
                    margin: 0; 
                    font-weight: 600;
                    font-size: 18px;
                    text-align: left;
                '>Filtros:</h4>
            </div>
            """, unsafe_allow_html=True)
            
            # Filtro UGB centralizado
            st.markdown("""
            <style>
            .stMultiSelect [data-baseweb="select"] {
                margin: 0 auto;
            }
            .stMultiSelect > div > div {
                display: flex;
                justify-content: center;
            }
            </style>
            """, unsafe_allow_html=True)
            
            ugb_options = get_unique_values(df_data, "UGB")
            
            # Inicializar session_state para UGB se não existir
            if 'selected_ugb' not in st.session_state:
                st.session_state.selected_ugb = ugb_options  # Todos selecionados por padrão
            
            # Usar o valor da session_state no multiselect
            selected_ugb = simple_multiselect_dropdown(
                "UGB",
                options=ugb_options,
                key="ugb_multiselect"
            )
            
            # Atualizar session_state com a seleção atual
            st.session_state.selected_ugb = selected_ugb
            
            # Botão centralizado
            st.markdown("""
            <style>
            .stButton > button {
                width: 100%;
                display: block;
                margin: 0 auto;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Definir valores padrão para os filtros removidos
            selected_emp = get_unique_values(df_data[df_data["UGB"].isin(selected_ugb)], "Empreendimento") if selected_ugb else []
            selected_grupo = get_unique_values(df_data, "GRUPO")
            selected_setor = list(SETOR.keys())

            # Filtrar o DataFrame com base apenas na UGB para determinar as etapas disponíveis
            df_temp_filtered = filter_dataframe(df_data, selected_ugb, selected_emp, selected_grupo, selected_setor)
            if not df_temp_filtered.empty:
                etapas_disponiveis = get_unique_values(df_temp_filtered, "Etapa")
                etapas_ordenadas = [etapa for etapa in ORDEM_ETAPAS_GLOBAL if etapa in etapas_disponiveis]
                etapas_para_exibir = ["Todos"] + [sigla_para_nome_completo.get(e, e) for e in etapas_ordenadas]
            else:
                etapas_para_exibir = ["Todos"]
            
            # Inicializa o estado da visualização se não existir
            if 'consolidated_view' not in st.session_state:
                st.session_state.consolidated_view = False
                st.session_state.selected_etapa_nome = "Todos" # Valor inicial

            # Função de callback para alternar o estado
            def toggle_consolidated_view():
                st.session_state.consolidated_view = not st.session_state.consolidated_view
                if st.session_state.consolidated_view:
                    # Se for para consolidar, pega a primeira etapa disponível (ou uma lógica mais robusta se necessário)
                    etapa_para_consolidar = next((e for e in etapas_para_exibir if e != "Todos"), "Todos")
                    st.session_state.selected_etapa_nome = etapa_para_consolidar
                else:
                    st.session_state.selected_etapa_nome = "Todos"

            # Botão de ativação da visão etapa - já centralizado pelo CSS acima
            button_label = "Aplicar Visão Etapa" if not st.session_state.consolidated_view else "Voltar para Visão EMP"
            st.button(button_label, on_click=toggle_consolidated_view, use_container_width=True)
            
            # Mensagens centralizadas
            st.markdown("""
            <style>
            .stSuccess, .stInfo {
                text-align: center;
            }
            </style>
            """, unsafe_allow_html=True)
            
            etapas_nao_mapeadas = []  # Você precisa definir esta variável com os dados apropriados
            
            # Define a variável que será usada no resto do código
            selected_etapa_nome = st.session_state.selected_etapa_nome

            # Exibe a etapa selecionada quando no modo consolidado (alerta abaixo do botão)
            if st.session_state.consolidated_view:
                st.success(f"**Visão Consolidada Ativa:** {selected_etapa_nome}")
                # # st.info("💡 Esta visão mostra todos os empreendimentos para uma etapa específica")

            filtrar_nao_concluidas = False
            
            # Definir valores padrão para os filtros removidos
            pulmao_status = "Sem Pulmão"
            pulmao_meses = 0
            tipo_visualizacao = "Ambos"  

        # --- FIM DO NOVO LAYOUT ---
        # Mantemos a chamada a filter_dataframe, mas com os valores padrão para EMP, GRUPO e SETOR
        df_filtered = filter_dataframe(df_data, selected_ugb, selected_emp, selected_grupo, selected_setor)

        # 2. Determinar o modo de visualização (agora baseado no st.session_state)
        is_consolidated_view = st.session_state.consolidated_view

        # 3. NOVO: Se for visão consolidada, AINDA filtramos pela etapa aqui.
        if is_consolidated_view and not df_filtered.empty:
            sigla_selecionada = nome_completo_para_sigla.get(selected_etapa_nome, selected_etapa_nome)
            df_filtered = df_filtered[df_filtered["Etapa"] == sigla_selecionada]
        df_para_exibir = df_filtered.copy()
        # Criar a lista de ordenação de empreendimentos (necessário para ambas as tabelas)
        empreendimentos_ordenados_por_meta = criar_ordenacao_empreendimentos(df_data)
        # Copiar o dataframe filtrado para ser usado nas tabelas
        df_detalhes = df_para_exibir.copy()
        # A lógica de pulmão foi removida da sidebar, então não é mais aplicada aqui.
        tab1, tab2 = st.tabs(["Gráfico de Gantt", "Tabelão Horizontal"])
        with tab1:
            st.subheader("Gantt Comparativo")
            if df_para_exibir.empty:
                st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
                pass
            else:
                df_para_gantt = filter_dataframe(df_data, selected_ugb, selected_emp, selected_grupo, selected_setor)

                gerar_gantt(
                    df_para_gantt.copy(), # Passa o DF filtrado (sem filtro de etapa/concluídas)
                    tipo_visualizacao, 
                    filtrar_nao_concluidas, # Passa o *estado* do checkbox
                    df_data, 
                    pulmao_status, 
                    pulmao_meses,
                    selected_etapa_nome  # Novo parâmetro
                )
            st.markdown('<div id="visao-detalhada"></div>', unsafe_allow_html=True)
            st.subheader("Visão Detalhada por Empreendimento")

            if df_detalhes.empty: # Verifique df_detalhes
                st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
                pass
            else:
                hoje = pd.Timestamp.now().normalize()

                for col in ['Inicio_Prevista', 'Termino_Prevista', 'Inicio_Real', 'Termino_Real']:
                    if col in df_detalhes.columns:
                        df_detalhes[col] = pd.to_datetime(df_detalhes[col], errors='coerce')

                df_agregado = df_detalhes.groupby(['Empreendimento', 'Etapa']).agg(
                    Inicio_Prevista=('Inicio_Prevista', 'min'),
                    Termino_Prevista=('Termino_Prevista', 'max'),
                    Inicio_Real=('Inicio_Real', 'min'),
                    Termino_Real=('Termino_Real', 'max'),
                    Percentual_Concluido=('% concluído', 'max') if '% concluído' in df_detalhes.columns else ('% concluído', lambda x: 0)
                ).reset_index()

                if '% concluído' in df_detalhes.columns and not df_agregado.empty and (df_agregado['Percentual_Concluido'].fillna(0).max() <= 1):
                    df_agregado['Percentual_Concluido'] *= 100

                df_agregado['Var. Term'] = df_agregado.apply(
                    lambda row: calculate_business_days(row['Termino_Prevista'], row['Termino_Real']), axis=1
                )
                
                df_agregado['ordem_empreendimento'] = pd.Categorical(
                    df_agregado['Empreendimento'],
                    categories=empreendimentos_ordenados_por_meta,
                    ordered=True
                )
                
                # 1. Mapear a etapa para sua ordem global (agora incluindo subetapas)
                def get_global_order_linear(etapa):
                    try:
                        return ORDEM_ETAPAS_GLOBAL.index(etapa)
                    except ValueError:
                        return len(ORDEM_ETAPAS_GLOBAL) # Coloca no final se não for encontrada

                df_agregado['Etapa_Ordem'] = df_agregado['Etapa'].apply(get_global_order_linear)
                
                # 2. Ordenar: Empreendimento, Ordem da Etapa (linear)
                df_ordenado = df_agregado.sort_values(by=['ordem_empreendimento', 'Etapa_Ordem'])

                st.write("---")

                etapas_unicas = df_ordenado['Etapa'].unique()
                usar_layout_horizontal = len(etapas_unicas) == 1

                tabela_final_lista = []
                
                if usar_layout_horizontal:
                    tabela_para_processar = df_ordenado.copy()
                    tabela_para_processar['Etapa'] = tabela_para_processar['Etapa'].map(sigla_para_nome_completo)
                    tabela_final_lista.append(tabela_para_processar)
                else:
                    for _, grupo in df_ordenado.groupby('ordem_empreendimento', sort=False):
                        if grupo.empty:
                            continue

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
                    st.info("ℹ️ Nenhum dado para exibir na tabela detalhada com os filtros atuais")
                    pass
                else:
                    tabela_final = pd.concat(tabela_final_lista, ignore_index=True)

                    def aplicar_estilo(df_para_estilo, layout_horizontal):
                        if df_para_estilo.empty:
                            return df_para_estilo.style

                        def estilo_linha(row):
                            style = [''] * len(row)
                            
                            if not layout_horizontal and 'Empreendimento / Etapa' in row.index and str(row['Empreendimento / Etapa']).startswith('📂'):
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

        with tab2:
            st.subheader("Tabelão Horizontal")
            
            if df_detalhes.empty: # Usando df_detalhes
                st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
                pass
            else:
                hoje = pd.Timestamp.now().normalize()

                df_detalhes_tabelao = df_detalhes.rename(columns={
                    'Termino_prevista': 'Termino_Prevista',
                    'Termino_real': 'Termino_Real'
                })
                
                for col in ['Inicio_Prevista', 'Termino_Prevista', 'Inicio_Real', 'Termino_Real']:
                    if col in df_detalhes_tabelao.columns:
                        df_detalhes_tabelao[col] = df_detalhes_tabelao[col].replace('-', pd.NA)
                        df_detalhes_tabelao[col] = pd.to_datetime(df_detalhes_tabelao[col], errors='coerce')

                df_detalhes_tabelao['Conclusao_Valida'] = False
                if '% concluído' in df_detalhes_tabelao.columns:
                    mask = (
                        (df_detalhes_tabelao['% concluído'] == 100) &
                        (df_detalhes_tabelao['Termino_Real'].notna()) &
                        ((df_detalhes_tabelao['Termino_Prevista'].isna()) |
                        (df_detalhes_tabelao['Termino_Real'] <= df_detalhes_tabelao['Termino_Prevista']))
                    )
                    df_detalhes_tabelao.loc[mask, 'Conclusao_Valida'] = True

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

                # 1. Mapear a etapa para sua ordem global (agora incluindo subetapas)
                def get_global_order_linear_tabelao(etapa):
                    try:
                        return ORDEM_ETAPAS_GLOBAL.index(etapa)
                    except ValueError:
                        return len(ORDEM_ETAPAS_GLOBAL) # Coloca no final se não for encontrada

                df_detalhes_tabelao['Etapa_Ordem'] = df_detalhes_tabelao['Etapa'].apply(get_global_order_linear_tabelao)

                # Lógica para anular datas previstas de subetapas
                subetapas_list = list(ETAPA_PAI_POR_SUBETAPA.keys())
                
                # Cria uma máscara para identificar as linhas que são subetapas
                mask_subetapa = df_detalhes_tabelao['Etapa'].isin(subetapas_list)
                
                # Anula as datas previstas (Inicio_Prevista e Termino_Prevista) para as subetapas
                df_detalhes_tabelao.loc[mask_subetapa, 'Inicio_Prevista'] = pd.NaT
                df_detalhes_tabelao.loc[mask_subetapa, 'Termino_Prevista'] = pd.NaT
                
                if classificar_por in ['Data de Início Previsto (Mais antiga)', 'Data de Término Previsto (Mais recente)']:
                    coluna_data = 'Inicio_Prevista' if 'Início' in classificar_por else 'Termino_Prevista'
                    
                    df_detalhes_ordenado = df_detalhes_tabelao.sort_values(
                        by=[coluna_data, 'UGB', 'Empreendimento', 'Etapa'],
                        ascending=[ordem == 'Crescente', True, True, True],
                        na_position='last'
                    )
                    
                    ordem_ugb_emp = df_detalhes_ordenado.groupby(['UGB', 'Empreendimento']).first().reset_index()
                    ordem_ugb_emp = ordem_ugb_emp.sort_values(
                        by=coluna_data,
                        ascending=(ordem == 'Crescente'),
                        na_position='last'
                    )
                    ordem_ugb_emp['ordem_index'] = range(len(ordem_ugb_emp))
                    
                    df_detalhes_tabelao = df_detalhes_tabelao.merge(
                        ordem_ugb_emp[['UGB', 'Empreendimento', 'ordem_index']],
                        on=['UGB', 'Empreendimento'],
                        how='left'
                    )
                
                agg_dict = {
                    'Inicio_Prevista': ('Inicio_Prevista', 'min'),
                    'Termino_Prevista': ('Termino_Prevista', 'max'),
                    'Inicio_Real': ('Inicio_Real', 'min'),
                    'Termino_Real': ('Termino_Real', 'max'),
                    'Concluido_Valido': ('Conclusao_Valida', 'any')
                }
                
                if '% concluído' in df_detalhes_tabelao.columns:
                    agg_dict['Percentual_Concluido'] = ('% concluído', 'max')
                    if not df_detalhes_tabelao.empty and (df_detalhes_tabelao['% concluído'].fillna(0).max() <= 1):
                        df_detalhes_tabelao['% concluído'] *= 100

                if 'ordem_index' in df_detalhes_tabelao.columns:
                    agg_dict['ordem_index'] = ('ordem_index', 'first')

                df_agregado = df_detalhes_tabelao.groupby(['UGB', 'Empreendimento', 'Etapa']).agg(**agg_dict).reset_index()
                
                df_agregado['Var. Term'] = df_agregado.apply(lambda row: calculate_business_days(row['Termino_Prevista'], row['Termino_Real']), axis=1)

                # Variável que estava faltando, definida a partir da ORDEM_ETAPAS_GLOBAL
                ordem_etapas_completas = ORDEM_ETAPAS_GLOBAL

                df_agregado['Etapa_Ordem'] = df_agregado['Etapa'].apply(
                    lambda x: ordem_etapas_completas.index(x) if x in ordem_etapas_completas else len(ordem_etapas_completas)
                )

                if classificar_por in ['Data de Início Previsto (Mais antiga)', 'Data de Término Previsto (Mais recente)']:
                    df_ordenado = df_agregado.sort_values(
                        by=['ordem_index', 'UGB', 'Empreendimento', 'Etapa_Ordem'],
                        ascending=[True, True, True, True]
                    )
                else:
                    df_ordenado = df_agregado.sort_values(
                        by=opcoes_classificacao[classificar_por],
                        ascending=(ordem == 'Crescente')
                    )
                
                st.write("---")

                df_pivot = df_ordenado.pivot_table(
                    index=['UGB', 'Empreendimento'],
                    columns='Etapa',
                    values=['Inicio_Prevista', 'Termino_Prevista', 'Inicio_Real', 'Termino_Real', 'Var. Term'],
                    aggfunc='first'
                )

                etapas_existentes_no_pivot = df_pivot.columns.get_level_values(1).unique()
                colunas_ordenadas = []
                
                for etapa in ordem_etapas_completas:
                    if etapa in etapas_existentes_no_pivot:
                        for tipo in ['Inicio_Prevista', 'Termino_Prevista', 'Inicio_Real', 'Termino_Real', 'Var. Term']:
                            if (tipo, etapa) in df_pivot.columns:
                                colunas_ordenadas.append((tipo, etapa))
                
                df_final = df_pivot[colunas_ordenadas].reset_index()

                if classificar_por in ['Data de Início Previsto (Mais antiga)', 'Data de Término Previsto (Mais recente)']:
                    ordem_linhas_final = df_ordenado[['UGB', 'Empreendimento']].drop_duplicates().reset_index(drop=True)
                    
                    df_final = df_final.set_index(['UGB', 'Empreendimento'])
                    df_final = df_final.reindex(pd.MultiIndex.from_frame(ordem_linhas_final))
                    df_final = df_final.reset_index()

                novos_nomes = []
                for col in df_final.columns:
                    if col[0] in ['UGB', 'Empreendimento']:
                        novos_nomes.append((col[0], ''))
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

                def formatar_valor(valor, tipo):
                    if pd.isna(valor):
                        return "-"
                    if tipo == 'data':
                        return valor.strftime("%d/%m/%Y")
                    if tipo == 'variacao':
                        return f"{'▼' if valor > 0 else '▲'} {abs(int(valor))} dias"
                    return str(valor)

                def determinar_cor(row, col_tuple):
                    if len(col_tuple) == 2 and (col_tuple[1] in ['Início Real', 'Término Real']):
                        etapa_nome_completo = col_tuple[0]
                        etapa_sigla = nome_completo_para_sigla.get(etapa_nome_completo)
                        
                        if etapa_sigla:
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
                                
                                if percentual == 100:
                                    if pd.notna(termino_real) and pd.notna(termino_previsto):
                                        if termino_real < termino_previsto:
                                            return "color: #2EAF5B; font-weight: bold;"
                                        elif termino_real > termino_previsto:
                                            return "color: #C30202; font-weight: bold;"
                                elif pd.notna(termino_real) and (termino_real < hoje):
                                    return "color: #A38408; font-weight: bold;"
                    
                    return ""

                df_formatado = df_final.copy()
                for col_tuple in df_formatado.columns:
                    if len(col_tuple) == 2 and col_tuple[1] != '':
                        if any(x in col_tuple[1] for x in ["Início Prev.", "Término Prev.", "Início Real", "Término Real"]):
                            df_formatado[col_tuple] = df_formatado[col_tuple].apply(lambda x: formatar_valor(x, "data"))
                        elif "VarTerm" in col_tuple[1]:
                            df_formatado[col_tuple] = df_formatado[col_tuple].apply(lambda x: formatar_valor(x, "variacao"))

                def aplicar_estilos(df):
                    styles = pd.DataFrame('', index=df.index, columns=df.columns)
                    
                    for i, row in df.iterrows():
                        cor_fundo = "#fbfbfb" if i % 2 == 0 else '#ffffff'
                        
                        for col_tuple in df.columns:
                            cell_style = f"background-color: {cor_fundo};"
                            
                            if len(col_tuple) == 2 and col_tuple[1] != '':
                                if row[col_tuple] == '-':
                                    cell_style += ' color: #999999; font-style: italic;'
                                else:
                                    if col_tuple[1] in ['Início Real', 'Término Real']:
                                        row_dict = {('UGB', ''): row[('UGB', '')],
                                                    ('Empreendimento', ''): row[('Empreendimento', '')]}
                                        cor_condicional = determinar_cor(row_dict, col_tuple)
                                        if cor_condicional:
                                            cell_style += f' {cor_condicional}'
                                    
                                    elif 'VarTerm' in col_tuple[1]:
                                        if '▲' in str(row[col_tuple]):
                                            cell_style += ' color: #e74c3c; font-weight: 600;'
                                        elif '▼' in str(row[col_tuple]):
                                            cell_style += ' color: #2ecc71; font-weight: 600;'
                            
                            styles.at[i, col_tuple] = cell_style
                    
                    return styles

                header_styles = [
                    {'selector': 'th.level0', 'props': [('font-size', '12px'), ('font-weight', 'bold'), ('background-color', "#6c6d6d"), ('border-bottom', '2px solid #ddd'), ('text-align', 'center'), ('white-space', 'nowrap')]},
                    {'selector': 'th.level1', 'props': [('font-size', '11px'), ('font-weight', 'normal'), ('background-color', '#f8f9fa'), ('text-align', 'center'), ('white-space', 'nowrap')]},
                    {'selector': 'td', 'props': [('font-size', '12px'), ('text-align', 'center'), ('padding', '5px 8px'), ('border', '1px solid #f0f0f0')]},
                    {'selector': 'th.col_heading.level0', 'props': [('font-size', '12px'), ('font-weight', 'bold'), ('background-color', '#6c6d6d'), ('text-align', 'center')]}
                ]

                for i, etapa in enumerate(ordem_etapas_completas):
                    if i > 0:
                        etapa_nome = sigla_para_nome_completo.get(etapa, etapa)
                        col_idx = next((idx for idx, col in enumerate(df_final.columns) if col[0] == etapa_nome), None)
                        if col_idx:
                            header_styles.append({'selector': f'th:nth-child({col_idx+1})', 'props': [('border-left', '2px solid #ddd')]})
                            header_styles.append({'selector': f'td:nth-child({col_idx+1})', 'props': [('border-left', '2px solid #ddd')]})

                styled_df = df_formatado.style.apply(aplicar_estilos, axis=None)
                styled_df = styled_df.set_table_styles(header_styles)

                st.dataframe(
                    styled_df,
                    height=min(35 * len(df_final) + 40, 600),
                    hide_index=True,
                    use_container_width=True
                )
                
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
