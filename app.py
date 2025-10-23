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
import streamlit.components.v1 as components
import json
import random

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
    "VENDA": ["PROSPECÇÃO", "LEGALIZAÇÃO PARA VENDA", "PULMÃO VENDA"],
    "LIMPEZA": ["PL.LIMP", "LEG.LIMP", "ENG. LIMP.", "EXECUÇÃO LIMP."],
    "TERRAPLANAGEM": ["PL.TER.", "LEG.TER.", "ENG. TER.", "EXECUÇÃO TER."],
    "INFRA INCIDENTE": ["PL.INFRA", "LEG.INFRA", "ENG. INFRA", "EXECUÇÃO INFRA"],
    "PAVIMENTAÇÃO": ["ENG. PAV", "EXECUÇÃO PAV."],
    "PULMÃO": ["PULMÃO INFRA"],
    "RADIER": ["PL.RADIER", "LEG.RADIER", "PULMÃO RADIER", "RADIER"],
    "DM": ["DEMANDA MÍNIMA"],
}

SETOR = {
    "PROSPECÇÃO": ["PROSPECÇÃO"],
    "LEGALIZAÇÃO": ["LEGALIZAÇÃO PARA VENDA", "LEG.LIMP", "LEG.TER.", "LEG.INFRA", "LEG.RADIER"],
    "PULMÃO": ["PULMÃO VENDA", "PULMÃO INFRA", "PULMÃO RADIER"],
    "ENGENHARIA": ["PL.LIMP", "ENG. LIMP.", "PL.TER.", "ENG. TER.", "PL.INFRA", "ENG. INFRA", "ENG. PAV"],
    "INFRA": ["EXECUÇÃO LIMP.", "EXECUÇÃO TER.", "EXECUÇÃO INFRA", "EXECUÇÃO PAV."],
    "PRODUÇÃO": ["RADIER"],
    "NOVOS PRODUTOS": ["PL.RADIER"],
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
        "PROSPECÇÃO": {"previsto": "#FEEFC4", "real": "#AE8141"},
        "LEGALIZAÇÃO": {"previsto": "#fadbfe", "real": "#BF08D3"},
        "PULMÃO": {"previsto": "#E9E8E8", "real": "#535252"},
        "ENGENHARIA": {"previsto": "#fbe3cf", "real": "#be5900"},
        "INFRA": {"previsto": "#daebfb", "real": "#125287"},
        "PRODUÇÃO": {"previsto": "#E1DFDF", "real": "#252424"},
        "NOVOS PRODUTOS": {"previsto": "#D4D3F9", "real": "#453ECC"},
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
                # Ajusta a data de término do pulmão
                if pd.notna(row["Termino_Prevista"]):
                    df_copy.loc[i, "Termino_Prevista"] = row["Termino_Prevista"] + relativedelta(months=meses_pulmao)
                if pd.notna(row["Termino_Real"]):
                    df_copy.loc[i, "Termino_Real"] = row["Termino_Real"] + relativedelta(months=meses_pulmao)

                # Ajusta as datas das etapas subsequentes
                # Supondo que as etapas estão ordenadas ou que a lógica de dependência é tratada em outro lugar
                # Para este exemplo, vamos ajustar as datas de início e término das etapas seguintes
                # que dependem diretamente do término de uma etapa de pulmão.
                # Isso é uma simplificação e pode precisar de uma lógica de dependência mais robusta.
                for j in range(i + 1, len(df_copy)):
                    if pd.notna(df_copy.loc[j, "Inicio_Prevista"]):
                        df_copy.loc[j, "Inicio_Prevista"] = df_copy.loc[j, "Inicio_Prevista"] + relativedelta(months=meses_pulmao)
                    if pd.notna(df_copy.loc[j, "Termino_Prevista"]):
                        df_copy.loc[j, "Termino_Prevista"] = df_copy.loc[j, "Termino_Prevista"] + relativedelta(months=meses_pulmao)
                    if pd.notna(df_copy.loc[j, "Inicio_Real"]):
                        df_copy.loc[j, "Inicio_Real"] = df_copy.loc[j, "Inicio_Real"] + relativedelta(months=meses_pulmao)
                    if pd.notna(df_copy.loc[j, "Termino_Real"]):
                        df_copy.loc[j, "Termino_Real"] = df_copy.loc[j, "Termino_Real"] + relativedelta(months=meses_pulmao)
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

            end_real_visual = end_real_original
            if pd.notna(start_real) and progress < 100 and pd.isna(end_real_original):
                end_real_visual = datetime.now()

            etapa = row.get("Etapa", "UNKNOWN")
            
            # --- INÍCIO DA MODIFICAÇÃO ---
            # Adiciona o GRUPO para que o JS possa filtrar
            etapa_sigla = nome_completo_para_sigla.get(etapa, etapa)
            grupo = GRUPO_POR_ETAPA.get(etapa_sigla, "Não especificado")
            # --- FIM DA MODIFICAÇÃO ---

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
            elif progress < 100 and pd.notna(end_date) and (end_date < hoje):
                    status_color_class = 'status-yellow' # Em andamento, mas já atrasado

            task = {
                "id": f"t{i}", "name": etapa, "numero_etapa": i + 1,
                "start_previsto": start_date.strftime("%Y-%m-%d"),
                "end_previsto": end_date.strftime("%Y-%m-%d"),
                "start_real": pd.to_datetime(start_real).strftime("%Y-%m-%d") if pd.notna(start_real) else None,
                "end_real": pd.to_datetime(end_real_visual).strftime("%Y-%m-%d") if pd.notna(end_real_visual) else None,
                # --- INÍCIO DA MODIFICAÇÃO ---
                "end_real_original_raw": pd.to_datetime(end_real_original).strftime("%Y-%m-%d") if pd.notna(end_real_original) else None,
                # --- FIM DA MODIFICAÇÃO ---
                "setor": row.get("SETOR", "Não especificado"),
                # --- INÍCIO DA MODIFICAÇÃO ---
                "grupo": grupo,
                # --- FIM DA MODIFICAÇÃO ---
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
    
        data_meta = obter_data_meta_assinatura_novo(df_emp)
        
        project = {
            "id": f"p{len(gantt_data)}", "name": empreendimento,
            "tasks": tasks,
            "meta_assinatura_date": data_meta.strftime("%Y-%m-%d") if data_meta else None
        }
        gantt_data.append(project)
    
    return gantt_data
# --- FIM DO CÓDIGO MODIFICADO ---

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
        if col in df_meta.columns and pd.notna(df_meta[col].iloc[0]): return df_meta[col].iloc[0]
    return pd.Timestamp.max

def criar_ordenacao_empreendimentos(df_original):
    # Use abreviar_nome para consistência com o que é exibido no gráfico
    empreendimentos_meta = {abreviar_nome(emp): obter_data_meta_assinatura(df_original, emp) for emp in df_original["Empreendimento"].unique()}
    return sorted(empreendimentos_meta.keys(), key=empreendimentos_meta.get)


def aplicar_ordenacao_final(df, empreendimentos_ordenados):
    if df.empty: return df
    ordem_empreendimentos = {emp: idx for idx, emp in enumerate(empreendimentos_ordenados)}
    df["ordem_empreendimento"] = df["Empreendimento"].map(ordem_empreendimentos)
    ordem_etapas = {etapa: idx for idx, etapa in enumerate(ORDEM_ETAPAS_GLOBAL)}
    df["ordem_etapa"] = df["Etapa"].map(ordem_etapas).fillna(len(ordem_etapas))
    df_ordenado = df.sort_values(["ordem_empreendimento", "ordem_etapa"]).drop(["ordem_empreendimento", "ordem_etapa"], axis=1)
    return df_ordenado.reset_index(drop=True)


def gerar_gantt_por_projeto(df, tipo_visualizacao, df_original_para_ordenacao, pulmao_status, pulmao_meses):
    """
    Gera e exibe um gráfico de Gantt interativo para cada projeto.
    
    Args:
        df (pd.DataFrame): O DataFrame filtrado pelo Streamlit (estado "Sem Pulmão").
        tipo_visualizacao (str): "Ambos", "Previsto" ou "Real".
        df_original_para_ordenacao (pd.DataFrame): O DF original, não filtrado, 
                                                 usado para determinar a ordem dos projetos.
        pulmao_status (str): "Com Pulmão" ou "Sem Pulmão" (da sidebar).
        pulmao_meses (int): Número de meses de pulmão (da sidebar).
    """

    # --- Processar DF SEM PULMÃO (AGORA O ÚNICO DF) ---
    df_sem_pulmao = df.copy()
    
    df_gantt_sem_pulmao = df_sem_pulmao.copy()
    if "Empreendimento" in df_gantt_sem_pulmao.columns:
        df_gantt_sem_pulmao["Empreendimento"] = df_gantt_sem_pulmao["Empreendimento"].apply(abreviar_nome)
    
    for col in ["Inicio_Prevista", "Termino_Prevista", "Inicio_Real", "Termino_Real"]:
        if col in df_gantt_sem_pulmao.columns:
            df_gantt_sem_pulmao[col] = pd.to_datetime(df_gantt_sem_pulmao[col], errors="coerce")
    
    if "% concluído" not in df_gantt_sem_pulmao.columns: 
        df_gantt_sem_pulmao["% concluído"] = 0
    
    df_gantt_sem_pulmao["% concluído"] = df_gantt_sem_pulmao["% concluído"].fillna(0).apply(converter_porcentagem)
    
    # Agrega os dados
    df_gantt_agg_sem_pulmao = df_gantt_sem_pulmao.groupby(['Empreendimento', 'Etapa']).agg(
        Inicio_Prevista=('Inicio_Prevista', 'min'),
        Termino_Prevista=('Termino_Prevista', 'max'),
        Inicio_Real=('Inicio_Real', 'min'),
        Termino_Real=('Termino_Real', 'max'),
        **{'% concluído': ('% concluído', 'max')},
        SETOR=('SETOR', 'first')
    ).reset_index()
    
    # Mapeia siglas para nomes completos
    df_gantt_agg_sem_pulmao["Etapa"] = df_gantt_agg_sem_pulmao["Etapa"].map(sigla_para_nome_completo).fillna(df_gantt_agg_sem_pulmao["Etapa"])

    # Converte o DataFrame agregado em uma lista de projetos (formato JSON)
    # Esta é a fonte de dados única para o JS
    gantt_data_base = converter_dados_para_gantt(df_gantt_agg_sem_pulmao)

    if not gantt_data_base:
        st.warning("Nenhum dado válido para o Gantt após a conversão.")
        return

    # Prepara opções de filtro para o menu flutuante
    filter_options = {
        "setores": ["Todos"] + sorted(list(SETOR.keys())),
        "grupos": ["Todos"] + sorted(list(GRUPOS.keys())),
        "etapas": ["Todas"] + ORDEM_ETAPAS_NOME_COMPLETO
    }

    # Obtém a lista ordenada de projetos (nomes completos)
    empreendimentos_ordenados = criar_ordenacao_empreendimentos(df_original_para_ordenacao)

    # Dicionário de projetos com nomes ABREVIADOS como chaves
    projects_base_dict = {project['name']: project for project in gantt_data_base}
    
    # Mapa de nome ABREVIADO -> Índice na lista gantt_data_base
    project_name_to_index_map = {project['name']: i for i, project in enumerate(gantt_data_base)}


    # Itera sobre os projetos na ordem definida
    for project_index_loop, empreendimento_nome_original in enumerate(empreendimentos_ordenados):

        # ### CORREÇÃO DO BUG "TELA BRANCA" ###
        # Abrevia o nome para corresponder às chaves do dicionário
        empreendimento_nome_abreviado = abreviar_nome(empreendimento_nome_original)

        # Busca o projeto usando o nome abreviado
        project_base = projects_base_dict.get(empreendimento_nome_abreviado)
        
        # Define o projeto inicial (sempre "sem pulmão" do Python)
        project = project_base 
        
        # Filtra o DF agregado para calcular o range de datas inicial
        df_para_datas = df_gantt_agg_sem_pulmao[df_gantt_agg_sem_pulmao["Empreendimento"] == empreendimento_nome_abreviado]

        if not project:
            st.warning(f"Projeto '{empreendimento_nome_original}' (abreviado para '{empreendimento_nome_abreviado}') não foi encontrado nos dados do Gantt. Pulando.")
            continue 

        # Obtém o índice correto deste projeto dentro da lista gantt_data_base
        correct_project_index_for_js = project_name_to_index_map.get(empreendimento_nome_abreviado)
        
        if correct_project_index_for_js is None:
            st.warning(f"Projeto '{empreendimento_nome_abreviado}' não foi encontrado no mapa de índice. Pulando.")
            continue
        
        # Pega as tarefas base (sempre "sem pulmão")
        tasks_base_data = project_base['tasks'] if project_base else []
        
        # Calcula o período de datas inicial (para o zoom do Python)
        data_min_proj, data_max_proj = calcular_periodo_datas(df_para_datas)
        total_meses_proj = ((data_max_proj.year - data_min_proj.year) * 12) + (data_max_proj.month - data_min_proj.month) + 1

        num_tasks = len(project["tasks"]) if project else 0 
        if num_tasks == 0: 
            st.warning(f"Projeto '{empreendimento_nome_abreviado}' não possui tarefas válidas. Pulando.")
            continue # Pula se não houver tarefas

        # Define a altura do componente HTML
        altura_gantt = max(400, (num_tasks * 30) + 150) # Altura da linha 30px

        # --- Geração do HTML ---
        gantt_html = f"""
        <!DOCTYPE html>
            <html lang="pt-BR">
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    /* ... (Todo o seu CSS idêntico ao fornecido anteriormente) ... */
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
                     .fullscreen-btn {{
                         position: absolute; top: 10px; right: 10px;
                         background: rgba(255, 255, 255, 0.9); border: none; border-radius: 4px;
                         padding: 8px 12px; font-size: 14px; cursor: pointer;
                         z-index: 100; box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                         transition: all 0.2s ease; display: flex; align-items: center; gap: 5px;
                     }}
                     .fullscreen-btn.is-fullscreen {{
                         font-size: 24px;
                         padding: 5px 10px;
                         color: #2d3748;
                     }}
                     .floating-filter-menu {{
                         display: none;
                         position: absolute;
                         top: 55px; right: 10px;
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
                     .filter-group select, .filter-group input {{
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
                </style>
            </head>
            <body>
                <script id="grupos-gantt-data" type="application/json">{json.dumps(GRUPOS)}</script>
                <div class="gantt-container" id="gantt-container-{project['id']}">
                    <button class="fullscreen-btn" id="fullscreen-btn-{project["id"]}"><span>📺</span> <span>Tela Cheia</span></button>

                    <div class="floating-filter-menu" id="filter-menu-{project['id']}">
                        <div class="filter-group">
                            <label for="filter-project-{project['id']}">Empreendimento</label>
                            <select id="filter-project-{project['id']}"></select>
                        </div>
                        <div class="filter-group">
                            <label for="filter-setor-{project['id']}">Setor</label>
                            <select id="filter-setor-{project['id']}"></select>
                        </div>
                        <div class="filter-group">
                            <label for="filter-grupo-{project['id']}">Grupo</label>
                            <select id="filter-grupo-{project['id']}"></select>
                        </div>
                        <div class="filter-group">
                            <label for="filter-etapa-{project['id']}">Etapa</label>
                            <select id="filter-etapa-{project['id']}"></select>
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
                
                <script>
                    const coresPorSetor_{project["id"]} = {json.dumps(StyleConfig.CORES_POR_SETOR)};
                    
                    const allProjectsData_{project["id"]} = {json.dumps(gantt_data_base)};
                    
                    let currentProjectIndex_{project["id"]} = {correct_project_index_for_js};
                    const initialProjectIndex_{project["id"]} = {correct_project_index_for_js};
                    
                    let projectData_{project["id"]} = {json.dumps([project])};
                    
                    // Datas originais (Python)
                    const dataMinStr_{project["id"]} = '{data_min_proj.strftime("%Y-%m-%d")}';
                    const dataMaxStr_{project["id"]} = '{data_max_proj.strftime("%Y-%m-%d")}';
                    
                    // ### INÍCIO DA MODIFICAÇÃO (DATAS DINÂMICAS) ###
                    // 'dataMinStr/dataMaxStr' são os originais, 'active' são os atuais
                    let activeDataMinStr_{project["id"]} = dataMinStr_{project["id"]};
                    let activeDataMaxStr_{project["id"]} = dataMaxStr_{project["id"]};
                    // ### FIM DA MODIFICAÇÃO (DATAS DINÂMICAS) ###

                    const initialTipoVisualizacao_{project["id"]} = '{tipo_visualizacao}';
                    let tipoVisualizacao_{project["id"]} = '{tipo_visualizacao}';
                    const PIXELS_PER_MONTH = 30;

                    // --- INÍCIO HELPERS DE DATA E PULMÃO ---
                    const etapas_pulmao_{project["id"]} = ["PULMÃO VENDA", "PULMÃO INFRA", "PULMÃO RADIER"];
                    const etapas_sem_alteracao_{project["id"]} = ["PROSPECÇÃO", "RADIER", "DEMANDA MÍNIMA"];

                    const formatDateDisplay_{project["id"]} = (dateStr) => {{
                        if (!dateStr) return "N/D";
                        const d = parseDate(dateStr);
                        if (!d || isNaN(d.getTime())) return "N/D";
                        const day = String(d.getUTCDate()).padStart(2, '0');
                        const month = String(d.getUTCMonth() + 1).padStart(2, '0');
                        const year = String(d.getUTCFullYear()).slice(-2);
                        return `${{day}}/${{month}}/${{year}}`;
                    }};

                    function addMonths_{project["id"]}(dateStr, months) {{
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

                    const filterOptions_{project["id"]} = {json.dumps(filter_options)};

                    let allTasks_baseData_{project["id"]} = {json.dumps(tasks_base_data)};

                    const initialPulmaoStatus_{project["id"]} = '{pulmao_status}';
                    const initialPulmaoMeses_{project["id"]} = {pulmao_meses};

                    let pulmaoStatus_{project["id"]} = '{pulmao_status}';
                    let filtersPopulated_{project["id"]} = false;

                    function parseDate(dateStr) {{ if (!dateStr) return null; const [year, month, day] = dateStr.split('-').map(Number); return new Date(Date.UTC(year, month - 1, day)); }}

                    // ### INÍCIO DA MODIFICAÇÃO (DATAS DINÂMICAS) ###
                    // Nova função para encontrar o range de datas das tarefas
                    function findNewDateRange_{project["id"]}(tasks) {{
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
                            // Checa o 'end_real_original_raw' se existir, senão o 'end_real'
                            updateRange(task.end_real_original_raw || task.end_real); 
                        }});

                        return {{
                            min: minDate ? minDate.toISOString().split('T')[0] : null,
                            max: maxDate ? maxDate.toISOString().split('T')[0] : null
                        }};
                    }}
                    // ### FIM DA MODIFICAÇÃO (DATAS DINÂMICAS) ###


                    function initGantt_{project["id"]}() {{
                        applyInitialPulmaoState_{project["id"]}();
                        
                        // ### INÍCIO DA MODIFICAÇÃO (DATAS DINÂMICAS) ###
                        // Recalcula o range de datas se o estado inicial for "Com Pulmão"
                        if (initialPulmaoStatus_{project["id"]} === 'Com Pulmão' && initialPulmaoMeses_{project["id"]} > 0) {{
                            // projectData_[0].tasks já foi modificado por applyInitialPulmaoState_
                            const {{ min: newMinStr, max: newMaxStr }} = findNewDateRange_{project["id"]}(projectData_{project["id"]}[0].tasks);
                            const newMin = parseDate(newMinStr);
                            const newMax = parseDate(newMaxStr);
                            const originalMin = parseDate(activeDataMinStr_{project["id"]});
                            const originalMax = parseDate(activeDataMaxStr_{project["id"]});

                            let finalMinDate = originalMin;
                            if (newMin && newMin < finalMinDate) {{
                                finalMinDate = newMin;
                            }}
                            let finalMaxDate = originalMax;
                            if (newMax && newMax > finalMaxDate) {{
                                finalMaxDate = newMax;
                            }}

                            // Copia as datas para não modificar as originais
                            finalMinDate = new Date(finalMinDate.getTime());
                            finalMaxDate = new Date(finalMaxDate.getTime());

                            finalMinDate.setUTCDate(1); // Início do mês
                            finalMaxDate.setUTCMonth(finalMaxDate.getUTCMonth() + 1, 0); // Fim do mês
                            
                            activeDataMinStr_{project["id"]} = finalMinDate.toISOString().split('T')[0];
                            activeDataMaxStr_{project["id"]} = finalMaxDate.toISOString().split('T')[0];
                        }}
                        // ### FIM DA MODIFICAÇÃO (DATAS DINÂMICAS) ###
                        
                        renderSidebar_{project["id"]}();
                        renderHeader_{project["id"]}();
                        renderChart_{project["id"]}();
                        renderMonthDividers_{project["id"]}();
                        setupEventListeners_{project["id"]}();
                        positionTodayLine_{project["id"]}();
                        positionMetaLine_{project["id"]}();
                        populateFilters_{project["id"]}();
                    }}

                    function applyInitialPulmaoState_{project["id"]}() {{
                        const initialPulmaoStatus = initialPulmaoStatus_{project["id"]};
                        const initialPulmaoMeses = initialPulmaoMeses_{project["id"]};

                        if (initialPulmaoStatus === 'Com Pulmão' && initialPulmaoMeses > 0) {{
                            const offsetMeses = -initialPulmaoMeses;
                            let baseTasks = projectData_{project["id"]}[0].tasks; 

                            baseTasks.forEach(task => {{
                                const etapaNome = task.name;
                                if (etapas_sem_alteracao_{project["id"]}.includes(etapaNome)) {{
                                }}
                                else if (etapas_pulmao_{project["id"]}.includes(etapaNome)) {{
                                    task.start_previsto = addMonths_{project["id"]}(task.start_previsto, offsetMeses);
                                    task.start_real = addMonths_{project["id"]}(task.start_real, offsetMeses);
                                    task.inicio_previsto = formatDateDisplay_{project["id"]}(task.start_previsto);
                                    task.inicio_real = formatDateDisplay_{project["id"]}(task.start_real);
                                }}
                                else {{
                                    task.start_previsto = addMonths_{project["id"]}(task.start_previsto, offsetMeses);
                                    task.end_previsto = addMonths_{project["id"]}(task.end_previsto, offsetMeses);
                                    task.start_real = addMonths_{project["id"]}(task.start_real, offsetMeses);

                                    if (task.end_real_original_raw) {{
                                        task.end_real_original_raw = addMonths_{project["id"]}(task.end_real_original_raw, offsetMeses);
                                        task.end_real = task.end_real_original_raw;
                                    }} else if (task.end_real) {{
                                        task.end_real = addMonths_{project["id"]}(task.end_real, offsetMeses);
                                    }}
                                    task.inicio_previsto = formatDateDisplay_{project["id"]}(task.start_previsto);
                                    task.termino_previsto = formatDateDisplay_{project["id"]}(task.end_previsto);
                                    task.inicio_real = formatDateDisplay_{project["id"]}(task.start_real);
                                    task.termino_real = formatDateDisplay_{project["id"]}(task.end_real_original_raw);
                                }}
                            }});
                            
                            allTasks_baseData_{project["id"]} = JSON.parse(JSON.stringify(baseTasks));
                        }}
                    }}

                    function renderSidebar_{project["id"]}() {{
                        const sidebarContent = document.getElementById('gantt-sidebar-content-{project["id"]}');
                        const gruposGantt = JSON.parse(document.getElementById('grupos-gantt-data').textContent);
                        const tasks = projectData_{project["id"]}[0].tasks;
                        let html = '';
                        let globalRowIndex = 0;
                        const groupKeys = Object.keys(gruposGantt);
                        for (let i = 0; i < groupKeys.length; i++) {{
                            const grupo = groupKeys[i];
                            const tasksInGroupNames = gruposGantt[grupo].filter(etapaNome => tasks.some(t => t.name === etapaNome));
                            if (tasksInGroupNames.length === 0) continue;
                            const groupHeight = (tasksInGroupNames.length * 30);
                            html += `<div class="sidebar-group-wrapper">`;
                            html += `<div class="sidebar-group-title-vertical" style="height: ${{groupHeight}}px;"><span>${{grupo}}</span></div>`;
                            html += `<div class="sidebar-rows-container">`;
                            gruposGantt[grupo].forEach(etapaNome => {{
                                const task = tasks.find(t => t.name === etapaNome);
                                if (task) {{
                                    globalRowIndex++;
                                    const rowClass = globalRowIndex % 2 !== 0 ? 'odd-row' : '';
                                    html += `<div class="sidebar-row ${{rowClass}}"><div class="sidebar-cell task-name-cell" title="${{task.numero_etapa}}. ${{task.name}}">${{task.numero_etapa}}. ${{task.name}}</div><div class="sidebar-cell">${{task.inicio_previsto}}</div><div class="sidebar-cell">${{task.termino_previsto}}</div><div class="sidebar-cell">${{task.duracao_prev_meses}}</div><div class="sidebar-cell">${{task.inicio_real}}</div><div class="sidebar-cell">${{task.termino_real}}</div><div class="sidebar-cell">${{task.duracao_real_meses}}</div><div class="sidebar-cell ${{task.status_color_class}}">${{task.progress}}%</div><div class="sidebar-cell ${{task.status_color_class}}">${{task.vt_text}}</div><div class="sidebar-cell ${{task.status_color_class}}">${{task.vd_text}}</div></div>`;
                                }}
                            }});
                            html += `</div></div>`;
                            const tasksInGroup = tasksInGroupNames;
                            if (i < groupKeys.length - 1 && tasksInGroup.length > 0) {{
                                const nextGroupKey = groupKeys[i + 1];
                                const nextGroupTasks = gruposGantt[nextGroupKey].filter(etapaNome => tasks.some(t => t.name === etapaNome));
                                if (nextGroupTasks.length > 0) {{
                                    html += `<div class="sidebar-row-spacer"></div>`;
                                }}
                            }}
                        }}
                        sidebarContent.innerHTML = html;
                    }}

                    function renderHeader_{project["id"]}() {{
                        const yearHeader = document.getElementById('year-header-{project["id"]}');
                        const monthHeader = document.getElementById('month-header-{project["id"]}');
                        let yearHtml = '', monthHtml = '';
                        const yearsData = [];
                        
                        // ### INÍCIO DA MODIFICAÇÃO (DATAS DINÂMICAS) ###
                        // Usa as datas ATIVAS
                        let currentDate = parseDate(activeDataMinStr_{project["id"]});
                        const dataMax = parseDate(activeDataMaxStr_{project["id"]});
                        // ### FIM DA MODIFICAÇÃO (DATAS DINÂMICAS) ###

                        let currentYear = -1, monthsInCurrentYear = 0;
                        
                        if (!currentDate || !dataMax || isNaN(currentDate.getTime()) || isNaN(dataMax.getTime())) {{
                             yearHeader.innerHTML = "Datas inválidas";
                             monthHeader.innerHTML = "";
                             return;
                        }}

                        let totalMonths = 0; // Prevenção de loop infinito
                        while (currentDate <= dataMax && totalMonths < 240) {{ // Limite de 20 anos
                            const year = currentDate.getUTCFullYear();
                            if (year !== currentYear) {{
                                if (currentYear !== -1) yearsData.push({{ year: currentYear, count: monthsInCurrentYear }});
                                currentYear = year; monthsInCurrentYear = 0;
                            }}
                            const monthNumber = String(currentDate.getUTCMonth() + 1).padStart(2, '0');
                            monthHtml += `<div class="month-cell">${{monthNumber}}</div>`;
                            monthsInCurrentYear++;
                            currentDate.setUTCMonth(currentDate.getUTCMonth() + 1);
                            totalMonths++;
                        }}
                        if (currentYear !== -1) yearsData.push({{ year: currentYear, count: monthsInCurrentYear }});
                        yearsData.forEach(data => {{ const yearWidth = data.count * PIXELS_PER_MONTH; yearHtml += `<div class="year-section" style="width:${{yearWidth}}px">${{data.year}}</div>`; }});
                        
                        // Atualiza a largura total do container do gráfico
                        const chartContainer = document.getElementById('chart-container-{project["id"]}');
                        if (chartContainer) {{
                             chartContainer.style.minWidth = `${{totalMonths * PIXELS_PER_MONTH}}px`;
                        }}

                        yearHeader.innerHTML = yearHtml;
                        monthHeader.innerHTML = monthHtml;
                    }}

                    function renderChart_{project["id"]}() {{
                        const chartBody = document.getElementById('chart-body-{project["id"]}');
                        const gruposGantt = JSON.parse(document.getElementById('grupos-gantt-data').textContent);
                        const tasks = projectData_{project["id"]}[0].tasks;
                        chartBody.innerHTML = '';
                        const groupKeys = Object.keys(gruposGantt);
                        for (let i = 0; i < groupKeys.length; i++) {{
                            const grupo = groupKeys[i];
                            const tasksInGroup = gruposGantt[grupo].filter(etapaNome => tasks.some(t => t.name === etapaNome));
                            if (tasksInGroup.length === 0) continue;
                            gruposGantt[grupo].forEach(etapaNome => {{
                                const task = tasks.find(t => t.name === etapaNome);
                                if (task) {{
                                    const row = document.createElement('div'); row.className = 'gantt-row';
                                    let barPrevisto = null;
                                    if (tipoVisualizacao_{project["id"]} === 'Ambos' || tipoVisualizacao_{project["id"]} === 'Previsto') {{ barPrevisto = createBar_{project["id"]}(task, 'previsto'); row.appendChild(barPrevisto); }}
                                    let barReal = null;
                                    if ((tipoVisualizacao_{project["id"]} === 'Ambos' || tipoVisualizacao_{project["id"]} === 'Real') && task.start_real && (task.end_real_original_raw || task.end_real)) {{ barReal = createBar_{project["id"]}(task, 'real'); row.appendChild(barReal); }}
                                    if (barPrevisto && barReal) {{
                                        const s_prev = parseDate(task.start_previsto), e_prev = parseDate(task.end_previsto), s_real = parseDate(task.start_real), e_real = parseDate(task.end_real_original_raw || task.end_real);
                                        if (s_prev && e_prev && s_real && e_real && s_real <= s_prev && e_real >= e_prev) {{ barPrevisto.style.zIndex = '8'; barReal.style.zIndex = '7'; }}
                                        renderOverlapBar_{project["id"]}(task, row);
                                    }}
                                    chartBody.appendChild(row);
                                }}
                            }});
                            if (i < groupKeys.length - 1 && tasksInGroup.length > 0) {{
                                const nextGroupKey = groupKeys[i + 1];
                                const nextGroupTasks = gruposGantt[nextGroupKey].filter(etapaNome => tasks.some(t => t.name === etapaNome));
                                if (nextGroupTasks.length > 0) {{
                                    const spacerRow = document.createElement('div');
                                    spacerRow.className = 'gantt-row-spacer';
                                    chartBody.appendChild(spacerRow);
                                }}
                            }}
                        }}
                    }}

                    function createBar_{project["id"]}(task, tipo) {{
                        const startDate = parseDate(tipo === 'previsto' ? task.start_previsto : task.start_real);
                        // ### INÍCIO DA MODIFICAÇÃO (DATAS DINÂMICAS) ###
                        // Garante que usa a data final correta (a original ou a calculada)
                        const endDate = parseDate(tipo === 'previsto' ? task.end_previsto : (task.end_real_original_raw || task.end_real));
                        // ### FIM DA MODIFICAÇÃO (DATAS DINÂMICAS) ###
                        
                        if (!startDate || !endDate) return document.createElement('div');
                        const left = getPosition_{project["id"]}(startDate);
                        const width = getPosition_{project["id"]}(endDate) - left + (PIXELS_PER_MONTH / 30);
                        const bar = document.createElement('div'); bar.className = `gantt-bar ${{tipo}}`;
                        const coresSetor = coresPorSetor_{project["id"]}[task.setor] || coresPorSetor_{project["id"]}['Não especificado'] || {{previsto: '#cccccc', real: '#888888'}};
                        bar.style.backgroundColor = tipo === 'previsto' ? coresSetor.previsto : coresSetor.real;
                        bar.style.left = `${{left}}px`; bar.style.width = `${{width}}px`;
                        const barLabel = document.createElement('span'); barLabel.className = 'bar-label'; barLabel.textContent = `${{task.name}} (${{task.progress}}%)`; bar.appendChild(barLabel);
                        bar.addEventListener('mousemove', e => showTooltip_{project["id"]}(e, task, tipo));
                        bar.addEventListener('mouseout', () => hideTooltip_{project["id"]}());
                        return bar;
                    }}

                    function renderOverlapBar_{project["id"]}(task, row) {{
                       if (!task.start_real || !(task.end_real_original_raw || task.end_real)) return;
                       // ### INÍCIO DA MODIFICAÇÃO (DATAS DINÂMICAS) ###
                        const s_prev = parseDate(task.start_previsto), e_prev = parseDate(task.end_previsto), s_real = parseDate(task.start_real), e_real = parseDate(task.end_real_original_raw || task.end_real);
                       // ### FIM DA MODIFICAÇÃO (DATAS DINÂMICAS) ###
                        const overlap_start = new Date(Math.max(s_prev, s_real)), overlap_end = new Date(Math.min(e_prev, e_real));
                        if (overlap_start < overlap_end) {{
                            const left = getPosition_{project["id"]}(overlap_start), width = getPosition_{project["id"]}(overlap_end) - left + (PIXELS_PER_MONTH / 30);
                            if (width > 0) {{ const overlapBar = document.createElement('div'); overlapBar.className = 'gantt-bar-overlap'; overlapBar.style.left = `${{left}}px`; overlapBar.style.width = `${{width}}px`; row.appendChild(overlapBar); }}
                        }}
                    }}

                    function getPosition_{project["id"]}(date) {{
                        if (!date) return 0;
                        // ### INÍCIO DA MODIFICAÇÃO (DATAS DINÂMICAS) ###
                        // Usa a data ATIVA
                        const chartStart = parseDate(activeDataMinStr_{project["id"]});
                        // ### FIM DA MODIFICAÇÃO (DATAS DINÂMICAS) ###
                        if (!chartStart || isNaN(chartStart.getTime())) return 0;

                        const monthsOffset = (date.getUTCFullYear() - chartStart.getUTCFullYear()) * 12 + (date.getUTCMonth() - chartStart.getUTCMonth());
                        const dayOfMonth = date.getUTCDate() - 1;
                        const daysInMonth = new Date(date.getUTCFullYear(), date.getUTCMonth() + 1, 0).getUTCDate();
                        const fractionOfMonth = daysInMonth > 0 ? dayOfMonth / daysInMonth : 0;
                        return (monthsOffset + fractionOfMonth) * PIXELS_PER_MONTH;
                    }}

                    function positionTodayLine_{project["id"]}() {{
                        const todayLine = document.getElementById('today-line-{project["id"]}');
                        const today = new Date(), todayUTC = new Date(Date.UTC(today.getFullYear(), today.getMonth(), today.getDate()));
                        
                        // ### INÍCIO DA MODIFICAÇÃO (DATAS DINÂMICAS) ###
                        const chartStart = parseDate(activeDataMinStr_{project["id"]});
                        const chartEnd = parseDate(activeDataMaxStr_{project["id"]});
                        // ### FIM DA MODIFICAÇÃO (DATAS DINÂMICAS) ###

                        if (chartStart && chartEnd && !isNaN(chartStart.getTime()) && !isNaN(chartEnd.getTime()) && todayUTC >= chartStart && todayUTC <= chartEnd) {{ 
                            const offset = getPosition_{project["id"]}(todayUTC); 
                            todayLine.style.left = `${{offset}}px`; 
                            todayLine.style.display = 'block'; 
                        }} else {{ 
                            todayLine.style.display = 'none'; 
                        }}
                    }}

                    function positionMetaLine_{project["id"]}() {{
                        const metaLine = document.getElementById('meta-line-{project["id"]}'), metaLabel = document.getElementById('meta-line-label-{project["id"]}');
                        const metaDateStr = projectData_{project["id"]}[0].meta_assinatura_date;
                        if (!metaDateStr) {{ metaLine.style.display = 'none'; metaLabel.style.display = 'none'; return; }}
                        
                        const metaDate = parseDate(metaDateStr);
                        // ### INÍCIO DA MODIFICAÇÃO (DATAS DINÂMICAS) ###
                        const chartStart = parseDate(activeDataMinStr_{project["id"]});
                        const chartEnd = parseDate(activeDataMaxStr_{project["id"]});
                        // ### FIM DA MODIFICAÇÃO (DATAS DINÂMICAS) ###
                        
                        if (metaDate && chartStart && chartEnd && !isNaN(metaDate.getTime()) && !isNaN(chartStart.getTime()) && !isNaN(chartEnd.getTime()) && metaDate >= chartStart && metaDate <= chartEnd) {{ 
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

                    function hideTooltip_{project["id"]}() {{ document.getElementById('tooltip-{project["id"]}').classList.remove('show'); }}

                    function renderMonthDividers_{project["id"]}() {{
                        const chartContainer = document.getElementById('chart-container-{project["id"]}');
                        chartContainer.querySelectorAll('.month-divider, .month-divider-label').forEach(el => el.remove());
                        
                        // ### INÍCIO DA MODIFICAÇÃO (DATAS DINÂMICAS) ###
                        let currentDate = parseDate(activeDataMinStr_{project["id"]});
                        const dataMax = parseDate(activeDataMaxStr_{project["id"]});
                        // ### FIM DA MODIFICAÇÃO (DATAS DINÂMICAS) ###

                        if (!currentDate || !dataMax || isNaN(currentDate.getTime()) || isNaN(dataMax.getTime())) return;

                        let totalMonths = 0; // Prevenção de loop infinito
                        while (currentDate <= dataMax && totalMonths < 240) {{ // Limite de 20 anos
                            const left = getPosition_{project["id"]}(currentDate);
                            const divider = document.createElement('div'); divider.className = 'month-divider';
                            if (currentDate.getUTCMonth() === 0) divider.classList.add('first');
                            divider.style.left = `${{left}}px`; chartContainer.appendChild(divider);
                            currentDate.setUTCMonth(currentDate.getUTCMonth() + 1);
                            totalMonths++;
                        }}
                    }}

                    function setupEventListeners_{project["id"]}() {{
                        const ganttChartContent = document.getElementById('gantt-chart-content-{project["id"]}'), sidebarContent = document.getElementById('gantt-sidebar-content-{project['id']}');
                        const fullscreenBtn = document.getElementById('fullscreen-btn-{project["id"]}'), toggleBtn = document.getElementById('toggle-sidebar-btn-{project['id']}');
                        const container = document.getElementById('gantt-container-{project["id"]}');

                        const applyBtn = document.getElementById('filter-apply-btn-{project["id"]}');
                        if (applyBtn) applyBtn.addEventListener('click', () => applyFiltersAndRedraw_{project["id"]}());

                        if (fullscreenBtn) fullscreenBtn.addEventListener('click', () => toggleFullscreenOrMenu_{project["id"]}());

                        if (container) container.addEventListener('fullscreenchange', () => handleFullscreenChange_{project["id"]}());

                        if (toggleBtn) toggleBtn.addEventListener('click', () => toggleSidebar_{project["id"]}());
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

                    function toggleSidebar_{project["id"]}() {{ document.getElementById('gantt-sidebar-wrapper-{project["id"]}').classList.toggle('collapsed'); }}

                    // --- INÍCIO DAS NOVAS FUNÇÕES JS ---

                    function updatePulmaoInputVisibility_{project["id"]}() {{
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

                    function resetToInitialState_{project["id"]}() {{
                        // 1. Resetar o índice e os dados do projeto
                        currentProjectIndex_{project["id"]} = initialProjectIndex_{project["id"]};
                        const initialProject = allProjectsData_{project["id"]}[initialProjectIndex_{project["id"]}];
                        
                        projectData_{project["id"]} = [JSON.parse(JSON.stringify(initialProject))];
                        allTasks_baseData_{project["id"]} = JSON.parse(JSON.stringify(initialProject.tasks));
                        
                        // 2. Resetar variáveis de estado globais
                        tipoVisualizacao_{project["id"]} = initialTipoVisualizacao_{project["id"]};
                        pulmaoStatus_{project["id"]} = initialPulmaoStatus_{project["id"]};
                        
                        applyInitialPulmaoState_{project["id"]}();

                        // ### INÍCIO DA MODIFICAÇÃO (DATAS DINÂMICAS) ###
                        // 3. Resetar o range de datas ativo para o original do Python
                        activeDataMinStr_{project["id"]} = dataMinStr_{project["id"]};
                        activeDataMaxStr_{project["id"]} = dataMaxStr_{project["id"]};
                        
                        // 3b. RE-CALCULAR o range inicial se o pulmão da sidebar estava ativo
                        if (initialPulmaoStatus_{project["id"]} === 'Com Pulmão' && initialPulmaoMeses_{project["id"]} > 0) {{
                            const {{ min: newMinStr, max: newMaxStr }} = findNewDateRange_{project["id"]}(projectData_{project["id"]}[0].tasks);
                            const newMin = parseDate(newMinStr);
                            const newMax = parseDate(newMaxStr);
                            const originalMin = parseDate(activeDataMinStr_{project["id"]});
                            const originalMax = parseDate(activeDataMaxStr_{project["id"]});

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
                            
                            activeDataMinStr_{project["id"]} = finalMinDate.toISOString().split('T')[0];
                            activeDataMaxStr_{project["id"]} = finalMaxDate.toISOString().split('T')[0];
                        }}
                        // ### FIM DA MODIFICAÇÃO (DATAS DINÂMICAS) ###


                        // 4. Resetar a UI do menu de filtros
                        document.getElementById('filter-project-{project["id"]}').value = initialProjectIndex_{project["id"]};
                        document.getElementById('filter-setor-{project["id"]}').value = 'Todos';
                        document.getElementById('filter-grupo-{project["id"]}').value = 'Todos';
                        document.getElementById('filter-etapa-{project["id"]}').value = 'Todas';
                        document.getElementById('filter-concluidas-{project["id"]}').checked = false;
                        
                        const visRadio = document.querySelector(`input[name="filter-vis-{project['id']}"][value="${{initialTipoVisualizacao_{project["id"]}}}"]`);
                        if (visRadio) visRadio.checked = true;
                        
                        const pulmaoRadio = document.querySelector(`input[name="filter-pulmao-{project['id']}"][value="${{initialPulmaoStatus_{project["id"]}}}"]`);
                        if (pulmaoRadio) pulmaoRadio.checked = true;

                        document.getElementById('filter-pulmao-meses-{project["id"]}').value = initialPulmaoMeses_{project["id"]};
                        
                        updatePulmaoInputVisibility_{project["id"]}();

                        // 5. Redesenhar TUDO (inclusive o header)
                        // ### INÍCIO DA MODIFICAÇÃO (DATAS DINÂMICAS) ###
                        renderHeader_{project["id"]}();
                        renderMonthDividers_{project["id"]}();
                        renderSidebar_{project["id"]}();
                        renderChart_{project["id"]}();
                        positionTodayLine_{project["id"]}();
                        positionMetaLine_{project["id"]}();
                        updateProjectTitle_{project["id"]}();
                        // ### FIM DA MODIFICAÇÃO (DATAS DINÂMICAS) ###
                    }}


                    function updateProjectTitle_{project["id"]}() {{
                        const projectTitle = document.querySelector(`#gantt-sidebar-wrapper-{project["id"]} .project-title-row span`);
                        if (projectTitle) {{
                            projectTitle.textContent = projectData_{project["id"]}[0].name;
                        }}
                    }}

                    function toggleFullscreen_{project["id"]}() {{
                        const container = document.getElementById('gantt-container-{project["id"]}');
                        if (!document.fullscreenElement) {{
                            container.requestFullscreen().catch(err => alert(`Erro: ${{err.message}}`));
                        }} else {{
                            document.exitFullscreen();
                        }}
                    }}

                    function toggleFilterMenu_{project["id"]}() {{
                        document.getElementById('filter-menu-{project["id"]}').classList.toggle('is-open');
                    }}

                    function toggleFullscreenOrMenu_{project["id"]}() {{
                        const container = document.getElementById('gantt-container-{project["id"]}');
                        if (document.fullscreenElement === container) {{
                            toggleFilterMenu_{project["id"]}();
                        }} else {{
                            toggleFullscreen_{project["id"]}();
                        }}
                    }}

                    function handleFullscreenChange_{project["id"]}() {{
                        const btn = document.getElementById('fullscreen-btn-{project["id"]}');
                        const container = document.getElementById('gantt-container-{project["id"]}');
                        if (document.fullscreenElement === container) {{
                            btn.innerHTML = '<span>&#9776;</span>'; 
                            btn.classList.add('is-fullscreen');
                        }} else {{
                            btn.innerHTML = '<span>📺</span> <span>Tela Cheia</span>';
                            btn.classList.remove('is-fullscreen');
                            document.getElementById('filter-menu-{project["id"]}').classList.remove('is-open');
                            resetToInitialState_{project["id"]}();
                        }}
                    }}

                    function populateFilters_{project["id"]}() {{
                        if (filtersPopulated_{project["id"]}) return; 

                        const selProject = document.getElementById('filter-project-{project["id"]}');
                        allProjectsData_{project["id"]}.forEach((proj, index) => {{
                            const isSelected = (index === initialProjectIndex_{project["id"]}) ? 'selected' : '';
                            selProject.innerHTML += `<option value="${{index}}" ${{isSelected}}>${{proj.name}}</option>`;
                        }});

                        const selSetor = document.getElementById('filter-setor-{project["id"]}');
                        filterOptions_{project["id"]}.setores.forEach(s => {{
                            selSetor.innerHTML += `<option value="${{s}}">${{s}}</option>`;
                        }});

                        const selGrupo = document.getElementById('filter-grupo-{project["id"]}');
                        filterOptions_{project["id"]}.grupos.forEach(g => {{
                            selGrupo.innerHTML += `<option value="${{g}}">${{g}}</option>`;
                        }});

                        const selEtapa = document.getElementById('filter-etapa-{project["id"]}');
                        filterOptions_{project["id"]}.etapas.forEach(e => {{
                            selEtapa.innerHTML += `<option value="${{e}}">${{e}}</option>`;
                        }});

                        document.querySelector(`input[name="filter-vis-{project['id']}"][value="${{initialTipoVisualizacao_{project["id"]}}}"]`).checked = true;

                        const radioCom = document.getElementById('filter-pulmao-com-{project["id"]}');
                        const radioSem = document.getElementById('filter-pulmao-sem-{project["id"]}');
                        
                        radioCom.addEventListener('change', updatePulmaoInputVisibility_{project["id"]});
                        radioSem.addEventListener('change', updatePulmaoInputVisibility_{project["id"]});

                        document.querySelector(`input[name="filter-pulmao-{project['id']}"][value="${{initialPulmaoStatus_{project["id"]}}}"]`).checked = true;

                        document.getElementById('filter-pulmao-meses-{project["id"]}').value = initialPulmaoMeses_{project["id"]};

                        updatePulmaoInputVisibility_{project["id"]}();

                        filtersPopulated_{project["id"]} = true;
                    }}

                    function applyFiltersAndRedraw_{project["id"]}() {{
                        
                        const selProjectIndex = parseInt(document.getElementById('filter-project-{project["id"]}').value, 10);
                        const selSetor = document.getElementById('filter-setor-{project["id"]}').value;
                        const selGrupo = document.getElementById('filter-grupo-{project["id"]}').value;
                        const selEtapa = document.getElementById('filter-etapa-{project["id"]}').value;
                        const selConcluidas = document.getElementById('filter-concluidas-{project["id"]}').checked;
                        const selVis = document.querySelector(`input[name="filter-vis-{project['id']}"]:checked`).value;
                        const selPulmao = document.querySelector(`input[name="filter-pulmao-{project['id']}"]:checked`).value;
                        const selPulmaoMeses = parseInt(document.getElementById('filter-pulmao-meses-{project["id"]}').value, 10) || 0;


                        if (selProjectIndex !== currentProjectIndex_{project["id"]}) {{
                            currentProjectIndex_{project["id"]} = selProjectIndex;
                            const newProject = allProjectsData_{project["id"]}[selProjectIndex];
                            
                            projectData_{project["id"]} = [JSON.parse(JSON.stringify(newProject))];
                            
                            allTasks_baseData_{project["id"]} = JSON.parse(JSON.stringify(newProject.tasks));
                        }}

                        
                        let baseTasks = JSON.parse(JSON.stringify(allTasks_baseData_{project["id"]}));

                        if (selPulmao === 'Com Pulmão' && selPulmaoMeses > 0) {{
                            const offsetMeses = -selPulmaoMeses; 

                            baseTasks.forEach(task => {{
                                const etapaNome = task.name; 

                                if (etapas_sem_alteracao_{project["id"]}.includes(etapaNome)) {{
                                }}
                                else if (etapas_pulmao_{project["id"]}.includes(etapaNome)) {{
                                    task.start_previsto = addMonths_{project["id"]}(task.start_previsto, offsetMeses);
                                    task.start_real = addMonths_{project["id"]}(task.start_real, offsetMeses);
                                    task.inicio_previsto = formatDateDisplay_{project["id"]}(task.start_previsto);
                                    task.inicio_real = formatDateDisplay_{project["id"]}(task.start_real);
                                }}
                                else {{
                                    task.start_previsto = addMonths_{project["id"]}(task.start_previsto, offsetMeses);
                                    task.end_previsto = addMonths_{project["id"]}(task.end_previsto, offsetMeses);
                                    task.start_real = addMonths_{project["id"]}(task.start_real, offsetMeses);

                                    if (task.end_real_original_raw) {{
                                        task.end_real_original_raw = addMonths_{project["id"]}(task.end_real_original_raw, offsetMeses);
                                        task.end_real = task.end_real_original_raw;
                                    }} else if (task.end_real) {{
                                        task.end_real = addMonths_{project["id"]}(task.end_real, offsetMeses);
                                    }}
                                    
                                    task.inicio_previsto = formatDateDisplay_{project["id"]}(task.start_previsto);
                                    task.termino_previsto = formatDateDisplay_{project["id"]}(task.end_previsto);
                                    task.inicio_real = formatDateDisplay_{project["id"]}(task.start_real);
                                    task.termino_real = formatDateDisplay_{project["id"]}(task.end_real_original_raw);
                                }}
                            }});
                        }}
                        
                        let filteredTasks = baseTasks; 
                        
                        if (selSetor !== 'Todos') {{
                            filteredTasks = filteredTasks.filter(t => t.setor === selSetor);
                        }}
                        if (selGrupo !== 'Todos') {{
                            filteredTasks = filteredTasks.filter(t => t.grupo === selGrupo);
                        }}
                        if (selEtapa !== 'Todas') {{
                            filteredTasks = filteredTasks.filter(t => t.name === selEtapa);
                        }}
                        if (selConcluidas) {{
                            filteredTasks = filteredTasks.filter(t => t.progress < 100);
                        }}

                        // ### INÍCIO DA MODIFICAÇÃO (DATAS DINÂMICAS) ###
                        // 6. Recalcular o range de datas
                        
                        // Pega as datas originais do Python (do projeto ATUAL)
                        // NOTA: dataMinStr_ e dataMaxStr_ são do PRIMEIRO projeto renderizado
                        // Se o usuário MUDAR de projeto, precisamos das datas desse NOVO projeto
                        // Para simplificar, vamos usar as datas do projeto original do Python
                        // (dataMinStr_) E expandir a partir daí.
                        
                        const originalMin = parseDate(dataMinStr_{project["id"]});
                        const originalMax = parseDate(dataMaxStr_{project["id"]});
                        
                        const {{ min: newMinStr, max: newMaxStr }} = findNewDateRange_{project["id"]}(filteredTasks);
                        const newMin = parseDate(newMinStr);
                        const newMax = parseDate(newMaxStr);

                        let finalMinDate = originalMin;
                        // Se a nova data mínima (com pulmão) for anterior, use-a
                        if (newMin && newMin < finalMinDate) {{
                            finalMinDate = newMin;
                        }}
                        
                        let finalMaxDate = originalMax;
                        // Se a nova data máxima (com pulmão) for posterior, use-a
                        if (newMax && newMax > finalMaxDate) {{
                            finalMaxDate = newMax;
                        }}

                        // Copia as datas para não modificar as originais
                        finalMinDate = new Date(finalMinDate.getTime());
                        finalMaxDate = new Date(finalMaxDate.getTime());
                        
                        // Garante que o range do gráfico comece no dia 01 do mês
                        finalMinDate.setUTCDate(1);
                        // Garante que o range do gráfico termine no último dia do mês
                        finalMaxDate.setUTCMonth(finalMaxDate.getUTCMonth() + 1, 0);

                        activeDataMinStr_{project["id"]} = finalMinDate.toISOString().split('T')[0];
                        activeDataMaxStr_{project["id"]} = finalMaxDate.toISOString().split('T')[0];
                        // ### FIM DA MODIFICAÇÃO (DATAS DINÂMICAS) ###


                        // 7. Atualizar os dados globais do JS
                        projectData_{project["id"]}[0].tasks = filteredTasks;
                        tipoVisualizacao_{project["id"]} = selVis; 
                        pulmaoStatus_{project["id"]} = selPulmao; 

                        // 8. Redesenhar TUDO (inclusive o header)
                        // ### INÍCIO DA MODIFICAÇÃO (DATAS DINÂMICAS) ###
                        renderHeader_{project["id"]}();
                        renderMonthDividers_{project["id"]}();
                        renderSidebar_{project["id"]}();
                        renderChart_{project["id"]}();
                        positionTodayLine_{project["id"]}();
                        positionMetaLine_{project["id"]}(); 
                        updateProjectTitle_{project["id"]}();
                        // ### FIM DA MODIFICAÇÃO (DATAS DINÂMICAS) ###

                        // 9. Esconder o menu de filtros
                        toggleFilterMenu_{project["id"]}();
                    }}
                    
                    initGantt_{project["id"]}();
                </script>
            </body>
            </html>
        """
        # Exibe o componente HTML no Streamlit
        components.html(gantt_html, height=altura_gantt, scrolling=True)
        st.markdown("---")


# Substitua sua função gerar_gantt_consolidado inteira por esta
def gerar_gantt_consolidado(df, tipo_visualizacao, df_original_para_ordenacao, pulmao_status, pulmao_meses):
    """
    Gera um gráfico de Gantt HTML consolidado (baseado no ..._por_projeto)
    com funcionalidades completas de filtro e ordenação dinâmica.
    """
    
    # --- 1. Preparação dos Dados (similar ao antigo consolidado) ---
    etapa_sigla = df['Etapa'].iloc[0]
    etapa_nome_completo = sigla_para_nome_completo.get(etapa_sigla, etapa_sigla)

    df_gantt = df.copy()
    df_gantt["Empreendimento"] = df_gantt["Empreendimento"].apply(abreviar_nome)

    for col in ["Inicio_Prevista", "Termino_Prevista", "Inicio_Real", "Termino_Real"]:
        if col in df_gantt.columns:
            df_gantt[col] = pd.to_datetime(df_gantt[col], errors="coerce")

    if "% concluído" not in df_gantt.columns: df_gantt["% concluído"] = 0
    df_gantt["% concluído"] = df_gantt["% concluído"].fillna(0).apply(converter_porcentagem)

    df_gantt_agg = df_gantt.groupby('Empreendimento').agg(
        Inicio_Prevista=('Inicio_Prevista', 'min'),
        Termino_Prevista=('Termino_Prevista', 'max'),
        Inicio_Real=('Inicio_Real', 'min'),
        Termino_Real=('Termino_Real', 'max'),
        **{'% concluído': ('% concluído', 'max')},
        SETOR=('SETOR', 'first')
    ).reset_index()

    # --- 2. Conversão para o formato de "Tasks" (Base) ---
    # Converte os empreendimentos em "tasks" para o JS
    tasks_base_data = []
    for i, row in df_gantt_agg.iterrows():
        start_date = row.get("Inicio_Prevista")
        end_date = row.get("Termino_Prevista")
        start_real = row.get("Inicio_Real")
        end_real_original = row.get("Termino_Real")
        progress = row.get("% concluído", 0)

        if pd.isna(start_date): start_date = datetime.now()
        if pd.isna(end_date): end_date = start_date + timedelta(days=30)

        end_real_visual = end_real_original
        if pd.notna(start_real) and progress < 100 and pd.isna(end_real_original):
            end_real_visual = datetime.now()

        # Variação de Término (VT)
        vt = calculate_business_days(end_date, end_real_original)
        
        # Duração em dias úteis
        duracao_prevista_uteis = calculate_business_days(start_date, end_date)
        duracao_real_uteis = calculate_business_days(start_real, end_real_original)

        # Variação de Duração (VD)
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
            "id": f"t{i}", "name": row["Empreendimento"], "numero_etapa": i + 1,
            "start_previsto": start_date.strftime("%Y-%m-%d"),
            "end_previsto": end_date.strftime("%Y-%m-%d"),
            "start_real": pd.to_datetime(start_real).strftime("%Y-%m-%d") if pd.notna(start_real) else None,
            "end_real": pd.to_datetime(end_real_visual).strftime("%Y-%m-%d") if pd.notna(end_real_visual) else None,
            "end_real_original_raw": pd.to_datetime(end_real_original).strftime("%Y-%m-%d") if pd.notna(end_real_original) else None,
            "setor": row.get("SETOR", "Não especificado"),
            "grupo": "Consolidado", # Grupo fixo para lógica de filtro
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
        tasks_base_data.append(task)
    
    if not tasks_base_data:
        st.warning("Nenhum dado válido para o Gantt Consolidado após a conversão.")
        return

    # --- 3. Preparação dos Filtros e Projeto Único ---
    filter_options = {
        "setores": ["Todos"] + sorted(list(df_gantt_agg["SETOR"].unique())),
        "grupos": ["Todos", "Consolidado"], # Grupo fixo
        "etapas": ["Todos"] + sorted(list(df_gantt_agg["Empreendimento"].unique())) # "Etapas" agora são os Empreendimentos
    }

    # Criar um "projeto" único que contém os empreendimentos como "tarefas"
    project_id = f"p_cons_{random.randint(1000, 9999)}"
    project = {
        "id": project_id, 
        "name": f"Comparativo: {etapa_nome_completo}",
        "tasks": tasks_base_data, # Passa os dados "base" (sem pulmão)
        "meta_assinatura_date": None # Sem meta de assinatura nesta visão
    }
    
    # O estado inicial do pulmão (da sidebar) é usado para a renderização inicial
    # O JS recalculará depois
    df_para_datas = df_gantt_agg

    data_min_proj, data_max_proj = calcular_periodo_datas(df_para_datas)
    total_meses_proj = ((data_max_proj.year - data_min_proj.year) * 12) + (data_max_proj.month - data_min_proj.month) + 1

    num_tasks = len(project["tasks"])
    if num_tasks == 0: 
        st.warning("Nenhum empreendimento para exibir.")
        return 

    altura_gantt = max(400, (num_tasks * 30) + 150) # 30px por linha de empreendimento

    # --- 4. Geração do HTML/JS (Copiado de ..._por_projeto e adaptado) ---
    # A maior parte do HTML/CSS é idêntica
    gantt_html = f"""
    <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                /* CSS idêntico ao de gerar_gantt_por_projeto */
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
                
                /* Remove a borda do grupo, pois não há grupos */
                .sidebar-group-wrapper {{
                    display: flex;
                    border-bottom: none; 
                }}
                .gantt-sidebar-content > .sidebar-group-wrapper:last-child {{ border-bottom: none; }}
                
                /* Esconde o título vertical do grupo */
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

                /* Remove o spacer pois não há grupos */
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
                
                /* Esconde a linha da meta, pois não é usada aqui */
                .meta-line, .meta-line-label {{ display: none; }}

                /* Scrollbar (idêntico) */
                .gantt-chart-content, .gantt-sidebar-content {{ scrollbar-width: thin; scrollbar-color: transparent transparent; }}
                .gantt-chart-content:hover, .gantt-sidebar-content:hover {{ scrollbar-color: #d1d5db transparent; }}
                .gantt-chart-content::-webkit-scrollbar, .gantt-sidebar-content::-webkit-scrollbar {{ height: 8px; width: 8px; }}
                .gantt-chart-content::-webkit-scrollbar-track, .gantt-sidebar-content::-webkit-scrollbar-track {{ background: transparent; }}
                .gantt-chart-content::-webkit-scrollbar-thumb, .gantt-sidebar-content::-webkit-scrollbar-thumb {{ background-color: transparent; border-radius: 4px; }}
                .gantt-chart-content:hover::-webkit-scrollbar-thumb, .gantt-sidebar-content:hover::-webkit-scrollbar-thumb {{ background-color: #d1d5db; }}
                .gantt-chart-content:hover::-webkit-scrollbar-thumb:hover, .gantt-sidebar-content:hover::-webkit-scrollbar-thumb:hover {{ background-color: #a8b2c1; }}

                /* Menu Flutuante (idêntico) */
                .fullscreen-btn {{
                    position: absolute; top: 10px; right: 10px;
                    background: rgba(255, 255, 255, 0.9); border: none; border-radius: 4px;
                    padding: 8px 12px; font-size: 14px; cursor: pointer;
                    z-index: 100; box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                    transition: all 0.2s ease; display: flex; align-items: center; gap: 5px;
                }}
                .fullscreen-btn.is-fullscreen {{
                    font-size: 24px; padding: 5px 10px; color: #2d3748;
                }}
                .floating-filter-menu {{
                    display: none; position: absolute;
                    top: 55px; right: 10px; width: 280px;
                    background: white; border-radius: 8px;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.3);
                    z-index: 99; padding: 15px; border: 1px solid #e2e8f0;
                }}
                .floating-filter-menu.is-open {{ display: block; }}
                .filter-group {{ margin-bottom: 12px; }}
                .filter-group label {{
                    display: block; font-size: 11px; font-weight: 600;
                    color: #4a5568; margin-bottom: 4px;
                    text-transform: uppercase;
                }}
                .filter-group select, .filter-group input {{
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
            </style>
        </head>
        <body>
            <div class="gantt-container" id="gantt-container-{project['id']}">
                <button class="fullscreen-btn" id="fullscreen-btn-{project["id"]}"><span>📺</span> <span>Tela Cheia</span></button>

                <div class="floating-filter-menu" id="filter-menu-{project['id']}">
                    <div class="filter-group">
                        <label for="filter-setor-{project['id']}">Setor</label>
                        <select id="filter-setor-{project['id']}"></select>
                    </div>
                    <div class="filter-group">
                        <label for="filter-grupo-{project['id']}">Grupo</label>
                        <select id="filter-grupo-{project['id']}"></select>
                    </div>
                    <div class="filter-group">
                        <label for="filter-etapa-{project['id']}">Empreendimento</label>
                        <select id="filter-etapa-{project['id']}"></select>
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
                            <div class="meta-line" id="meta-line-{project["id"]}"></div>
                            <div class="meta-line-label" id="meta-line-label-{project["id"]}"></div>
                        </div>
                    </div>
                </div>
                <div class="tooltip" id="tooltip-{project["id"]}"></div>
            </div>
            
            <script>
                const coresPorSetor_{project["id"]} = {json.dumps(StyleConfig.CORES_POR_SETOR)};
                // Passa um *único* projeto
                const projectData_{project["id"]} = [{json.dumps(project)}]; 
                const dataMinStr_{project["id"]} = '{data_min_proj.strftime("%Y-%m-%d")}';
                const dataMaxStr_{project["id"]} = '{data_max_proj.strftime("%Y-%m-%d")}';
                let tipoVisualizacao_{project["id"]} = '{tipo_visualizacao}';
                const PIXELS_PER_MONTH = 30;

                // --- Helpers de Data e Pulmão (Idênticos) ---
                const etapas_pulmao_{project["id"]} = ["PULMÃO VENDA", "PULMÃO INFRA", "PULMÃO RADIER"];
                const etapas_sem_alteracao_{project["id"]} = ["PROSPECÇÃO", "RADIER", "DEMANDA MÍNIMA"];

                const formatDateDisplay_{project["id"]} = (dateStr) => {{
                    if (!dateStr) return "N/D";
                    const d = parseDate(dateStr);
                    if (!d || isNaN(d.getTime())) return "N/D";
                    const day = String(d.getUTCDate()).padStart(2, '0');
                    const month = String(d.getUTCMonth() + 1).padStart(2, '0');
                    const year = String(d.getUTCFullYear()).slice(-2);
                    return `${{day}}/${{month}}/${{year}}`;
                }};

                function addMonths_{project["id"]}(dateStr, months) {{
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
                
                function parseDate(dateStr) {{ if (!dateStr) return null; const [year, month, day] = dateStr.split('-').map(Number); return new Date(Date.UTC(year, month - 1, day)); }}

                // --- Dados de Filtro e Tasks (Adaptados) ---
                const filterOptions_{project["id"]} = {json.dumps(filter_options)};
                // Passa a lista de tasks "base" (empreendimentos)
                const allTasks_baseData_{project["id"]} = {json.dumps(tasks_base_data)};
                
                let pulmaoStatus_{project["id"]} = '{pulmao_status}';
                let filtersPopulated_{project["id"]} = false;

                function initGantt_{project["id"]}() {{
                    applyInitialPulmaoState_{project["id"]}();
                    renderSidebar_{project["id"]}(); // Esta função agora também ordena
                    renderHeader_{project["id"]}();
                    renderChart_{project["id"]}();
                    renderMonthDividers_{project["id"]}();
                    setupEventListeners_{project["id"]}();
                    positionTodayLine_{project["id"]}();
                    positionMetaLine_{project["id"]}(); // Esta função não fará nada (display: none)
                    populateFilters_{project["id"]}();
                }}

                // --- applyInitialPulmaoState (Idêntica) ---
                // Esta lógica funciona perfeitamente, pois a "etapa" (PROSPEC, etc.)
                // está armazenada em `etapa_nome_completo` no Python, e não nos dados da task.
                // A lógica de pulmão do JS se baseia no *nome* da etapa (task.name),
                // que no nosso caso é o NOME DO EMPREENDIMENTO, então não vai bater
                // com "PULMÃO VENDA", etc.
                //
                // !!! CORREÇÃO !!!
                // A lógica de pulmão do JS *não vai funcionar* porque `task.name` é "Residencial Alfa"
                // e não "PULMÃO VENDA". A lógica de pulmão deve ser aplicada com base na
                // *etapa consolidada* que estamos vendo.
                
                // Vamos buscar a etapa sigla do python
                const etapaConsolidada_sigla_{project["id"]} = "{etapa_sigla}";
                
                // Mapeamento de siglas (para o JS)
                const etapas_pulmao_js_{project["id"]} = ["PULVENDA", "PUL.INFRA", "PUL.RAD"];
                const etapas_sem_alteracao_js_{project["id"]} = ["PROSPEC", "RAD", "DEM.MIN"];

                // --- Lógica de Pulmão (Adaptada para Visão Consolidada) ---
                function aplicarLogicaPulmaoConsolidado(tasks, offsetMeses) {{
                    // Verifica se a *etapa inteira* que estamos vendo deve ser afetada
                    
                    // 1. Etapas que não mudam
                    if (etapas_sem_alteracao_js_{project["id"]}.includes(etapaConsolidada_sigla_{project["id"]})) {{
                        // Nenhuma data é alterada
                    }}
                    // 2. Etapas de pulmão (só muda início)
                    else if (etapas_pulmao_js_{project["id"]}.includes(etapaConsolidada_sigla_{project["id"]})) {{
                        tasks.forEach(task => {{
                            task.start_previsto = addMonths_{project["id"]}(task.start_previsto, offsetMeses);
                            task.start_real = addMonths_{project["id"]}(task.start_real, offsetMeses);
                            task.inicio_previsto = formatDateDisplay_{project["id"]}(task.start_previsto);
                            task.inicio_real = formatDateDisplay_{project["id"]}(task.start_real);
                        }});
                    }}
                    // 3. Todas as outras etapas (muda tudo)
                    else {{
                        tasks.forEach(task => {{
                            task.start_previsto = addMonths_{project["id"]}(task.start_previsto, offsetMeses);
                            task.end_previsto = addMonths_{project["id"]}(task.end_previsto, offsetMeses);
                            task.start_real = addMonths_{project["id"]}(task.start_real, offsetMeses);

                            if (task.end_real_original_raw) {{
                                task.end_real_original_raw = addMonths_{project["id"]}(task.end_real_original_raw, offsetMeses);
                                task.end_real = task.end_real_original_raw;
                            }} else if (task.end_real) {{
                                task.end_real = addMonths_{project["id"]}(task.end_real, offsetMeses);
                            }}
                            
                            task.inicio_previsto = formatDateDisplay_{project["id"]}(task.start_previsto);
                            task.termino_previsto = formatDateDisplay_{project["id"]}(task.end_previsto);
                            task.inicio_real = formatDateDisplay_{project["id"]}(task.start_real);
                            task.termino_real = formatDateDisplay_{project["id"]}(task.end_real_original_raw);
                        }});
                    }}
                    return tasks;
                }}

                function applyInitialPulmaoState_{project["id"]}() {{
                    const initialPulmaoStatus = '{pulmao_status}';
                    const initialPulmaoMeses = {pulmao_meses};

                    if (initialPulmaoStatus === 'Com Pulmão' && initialPulmaoMeses > 0) {{
                        const offsetMeses = -initialPulmaoMeses;
                        let baseTasks = projectData_{project["id"]}[0].tasks; // Modifica os dados do projeto diretamente
                        
                        // Aplica a nova lógica consolidada
                        projectData_{project["id"]}[0].tasks = aplicarLogicaPulmaoConsolidado(baseTasks, offsetMeses);
                    }}
                }}

                // --- ### FUNÇÃO renderSidebar MODIFICADA ### ---
                // Esta é a principal mudança para a ordenação
                function renderSidebar_{project["id"]}() {{
                    const sidebarContent = document.getElementById('gantt-sidebar-content-{project["id"]}');
                    
                    // Usa as tarefas filtradas do projectData (que são os empreendimentos)
                    let tasks = projectData_{project["id"]}[0].tasks;
                    
                    // ### INÍCIO DA NOVA LÓGICA DE ORDENAÇÃO (SOLICITADA PELO USUÁRIO) ###
                    const dateSortFallback = new Date(8640000000000000); // Data muito no futuro para nulos
                    
                    if (tipoVisualizacao_{project["id"]} === 'Real') {{
                        // Ordena por data de início real
                        tasks.sort((a, b) => {{
                            const dateA = a.start_real ? parseDate(a.start_real) : dateSortFallback;
                            const dateB = b.start_real ? parseDate(b.start_real) : dateSortFallback;
                            if (dateA > dateB) return 1;
                            if (dateA < dateB) return -1;
                            // Se as datas forem iguais, ordena por nome
                            return a.name.localeCompare(b.name);
                        }});
                    }} else {{
                        // Ordena por data de início previsto (default para 'Ambos' e 'Previsto')
                        tasks.sort((a, b) => {{
                            const dateA = a.start_previsto ? parseDate(a.start_previsto) : dateSortFallback;
                            const dateB = b.start_previsto ? parseDate(b.start_previsto) : dateSortFallback;
                            if (dateA > dateB) return 1;
                            if (dateA < dateB) return -1;
                            return a.name.localeCompare(b.name);
                        }});
                    }}
                    // ### FIM DA NOVA LÓGICA DE ORDENAÇÃO ###

                    let html = '';
                    let globalRowIndex = 0;
                    
                    // Não há grupos, apenas um container de linhas
                    html += `<div class="sidebar-rows-container">`;
                    
                    tasks.forEach(task => {{
                        globalRowIndex++;
                        const rowClass = globalRowIndex % 2 !== 0 ? 'odd-row' : '';
                        
                        // Re-numera as tasks com base na nova ordem
                        task.numero_etapa = globalRowIndex; 
                        
                        // 'task.name' é o nome do Empreendimento
                        html += `<div class="sidebar-row ${{rowClass}}">
                            <div class="sidebar-cell task-name-cell" title="${{task.numero_etapa}}. ${{task.name}}">${{task.numero_etapa}}. ${{task.name}}</div>
                            <div class="sidebar-cell">${{task.inicio_previsto}}</div>
                            <div class="sidebar-cell">${{task.termino_previsto}}</div>
                            <div class="sidebar-cell">${{task.duracao_prev_meses}}</div>
                            <div class="sidebar-cell">${{task.inicio_real}}</div>
                            <div class="sidebar-cell">${{task.termino_real}}</div>
                            <div class="sidebar-cell">${{task.duracao_real_meses}}</div>
                            <div class="sidebar-cell ${{task.status_color_class}}">${{task.progress}}%</div>
                            <div class="sidebar-cell ${{task.status_color_class}}">${{task.vt_text}}</div>
                            <div class="sidebar-cell ${{task.status_color_class}}">${{task.vd_text}}</div>
                        </div>`;
                    }});
                    html += `</div>`;
                    sidebarContent.innerHTML = html;
                }}

                // --- renderHeader (Idêntica) ---
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
                            currentYear = year; monthsInCurrentYear = 0;
                        }}
                        const monthNumber = String(currentDate.getUTCMonth() + 1).padStart(2, '0');
                        monthHtml += `<div class="month-cell">${{monthNumber}}</div>`;
                        monthsInCurrentYear++;
                        currentDate.setUTCMonth(currentDate.getUTCMonth() + 1);
                    }}
                    if (currentYear !== -1) yearsData.push({{ year: currentYear, count: monthsInCurrentYear }});
                    yearsData.forEach(data => {{ const yearWidth = data.count * PIXELS_PER_MONTH; yearHtml += `<div class="year-section" style="width:${{yearWidth}}px">${{data.year}}</div>`; }});
                    yearHeader.innerHTML = yearHtml;
                    monthHeader.innerHTML = monthHtml;
                }}

                // --- ### FUNÇÃO renderChart MODIFICADA ### ---
                function renderChart_{project["id"]}() {{
                    const chartBody = document.getElementById('chart-body-{project["id"]}');
                    // Lê as tarefas (que já foram ordenadas pela renderSidebar)
                    const tasks = projectData_{project["id"]}[0].tasks;
                    chartBody.innerHTML = '';
                    
                    // Itera diretamente sobre as tarefas, sem grupos
                    tasks.forEach(task => {{
                        const row = document.createElement('div'); row.className = 'gantt-row';
                        let barPrevisto = null;
                        if (tipoVisualizacao_{project["id"]} === 'Ambos' || tipoVisualizacao_{project["id"]} === 'Previsto') {{ barPrevisto = createBar_{project["id"]}(task, 'previsto'); row.appendChild(barPrevisto); }}
                        let barReal = null;
                        if ((tipoVisualizacao_{project["id"]} === 'Ambos' || tipoVisualizacao_{project["id"]} === 'Real') && task.start_real && task.end_real) {{ barReal = createBar_{project["id"]}(task, 'real'); row.appendChild(barReal); }}
                        if (barPrevisto && barReal) {{
                            const s_prev = parseDate(task.start_previsto), e_prev = parseDate(task.end_previsto), s_real = parseDate(task.start_real), e_real = parseDate(task.end_real);
                            if (s_prev && e_prev && s_real && e_real && s_real <= s_prev && e_real >= e_prev) {{ barPrevisto.style.zIndex = '8'; barReal.style.zIndex = '7'; }}
                            renderOverlapBar_{project["id"]}(task, row);
                        }}
                        chartBody.appendChild(row);
                    }});
                    // Remove a lógica de spacer de grupo
                }}

                // --- createBar (Idêntica, 'task.name' agora é Empreendimento, o que é correto) ---
                function createBar_{project["id"]}(task, tipo) {{
                    const startDate = parseDate(tipo === 'previsto' ? task.start_previsto : task.start_real);
                    const endDate = parseDate(tipo === 'previsto' ? task.end_previsto : task.end_real);
                    if (!startDate || !endDate) return document.createElement('div');
                    const left = getPosition_{project["id"]}(startDate);
                    const width = getPosition_{project["id"]}(endDate) - left + (PIXELS_PER_MONTH / 30);
                    const bar = document.createElement('div'); bar.className = `gantt-bar ${{tipo}}`;
                    const coresSetor = coresPorSetor_{project["id"]}[task.setor] || coresPorSetor_{project["id"]}['Não especificado'] || {{previsto: '#cccccc', real: '#888888'}};
                    bar.style.backgroundColor = tipo === 'previsto' ? coresSetor.previsto : coresSetor.real;
                    bar.style.left = `${{left}}px`; bar.style.width = `${{width}}px`;
                    const barLabel = document.createElement('span'); barLabel.className = 'bar-label'; 
                    barLabel.textContent = `${{task.name}} (${{task.progress}}%)`; // task.name é o Empreendimento
                    bar.appendChild(barLabel);
                    bar.addEventListener('mousemove', e => showTooltip_{project["id"]}(e, task, tipo));
                    bar.addEventListener('mouseout', () => hideTooltip_{project["id"]}());
                    return bar;
                }}

                // --- renderOverlapBar (Idêntica) ---
                function renderOverlapBar_{project["id"]}(task, row) {{
                   if (!task.start_real || !task.end_real) return;
                    const s_prev = parseDate(task.start_previsto), e_prev = parseDate(task.end_previsto), s_real = parseDate(task.start_real), e_real = parseDate(task.end_real);
                    const overlap_start = new Date(Math.max(s_prev, s_real)), overlap_end = new Date(Math.min(e_prev, e_real));
                    if (overlap_start < overlap_end) {{
                        const left = getPosition_{project["id"]}(overlap_start), width = getPosition_{project["id"]}(overlap_end) - left + (PIXELS_PER_MONTH / 30);
                        if (width > 0) {{ const overlapBar = document.createElement('div'); overlapBar.className = 'gantt-bar-overlap'; overlapBar.style.left = `${{left}}px`; overlapBar.style.width = `${{width}}px`; row.appendChild(overlapBar); }}
                    }}
                }}

                // --- getPosition (Idêntica) ---
                function getPosition_{project["id"]}(date) {{
                    if (!date) return 0;
                    const chartStart = parseDate(dataMinStr_{project["id"]});
                    const monthsOffset = (date.getUTCFullYear() - chartStart.getUTCFullYear()) * 12 + (date.getUTCMonth() - chartStart.getUTCMonth());
                    const dayOfMonth = date.getUTCDate() - 1;
                    const daysInMonth = new Date(date.getUTCFullYear(), date.getUTCMonth() + 1, 0).getUTCDate();
                    const fractionOfMonth = daysInMonth > 0 ? dayOfMonth / daysInMonth : 0;
                    return (monthsOffset + fractionOfMonth) * PIXELS_PER_MONTH;
                }}

                // --- positionTodayLine (Idêntica) ---
                function positionTodayLine_{project["id"]}() {{
                    const todayLine = document.getElementById('today-line-{project["id"]}');
                    const today = new Date(), todayUTC = new Date(Date.UTC(today.getFullYear(), today.getMonth(), today.getDate()));
                    const chartStart = parseDate(dataMinStr_{project["id"]}), chartEnd = parseDate(dataMaxStr_{project["id"]});
                    if (todayUTC >= chartStart && todayUTC <= chartEnd) {{ const offset = getPosition_{project["id"]}(todayUTC); todayLine.style.left = `${{offset}}px`; todayLine.style.display = 'block'; }} else {{ todayLine.style.display = 'none'; }}
                }}

                // --- positionMetaLine (Idêntica, mas não fará nada) ---
                function positionMetaLine_{project["id"]}() {{
                    const metaLine = document.getElementById('meta-line-{project["id"]}'), metaLabel = document.getElementById('meta-line-label-{project["id"]}');
                    const metaDateStr = projectData_{project["id"]}[0].meta_assinatura_date;
                    if (!metaDateStr) {{ metaLine.style.display = 'none'; metaLabel.style.display = 'none'; return; }}
                    // ... (o resto do código não será executado)
                }}

                // --- showTooltip (Idêntica, 'task.name' é Empreendimento) ---
                function showTooltip_{project["id"]}(e, task, tipo) {{
                    const tooltip = document.getElementById('tooltip-{project["id"]}');
                    let content = `<b>${{task.name}}</b><br>`; // task.name é Empreendimento
                    if (tipo === 'previsto') {{ content += `Previsto: ${{task.inicio_previsto}} - ${{task.termino_previsto}}<br>Duração: ${{task.duracao_prev_meses}}M`; }} else {{ content += `Real: ${{task.inicio_real}} - ${{task.termino_real}}<br>Duração: ${{task.duracao_real_meses}}M<br>Variação Término: ${{task.vt_text}}<br>Variação Duração: ${{task.vd_text}}`; }}
                    content += `<br><b>Progresso: ${{task.progress}}%</b><br>Setor: ${{task.setor}}<br>Grupo: ${{task.grupo}}`;
                    
                    tooltip.innerHTML = content;
                    tooltip.classList.add('show'); 
                    const tooltipWidth = tooltip.offsetWidth, tooltipHeight = tooltip.offsetHeight;
                    const viewportWidth = window.innerWidth, viewportHeight = window.innerHeight;
                    const mouseX = e.clientX, mouseY = e.clientY;
                    const padding = 15;
                    let left, top;
                    if ((mouseX + padding + tooltipWidth) > viewportWidth) {{ left = mouseX - padding - tooltipWidth; }} else {{ left = mouseX + padding; }}
                    if ((mouseY + padding + tooltipHeight) > viewportHeight) {{ top = mouseY - padding - tooltipHeight; }} else {{ top = mouseY + padding; }}
                    if (left < padding) left = padding;
                    if (top < padding) top = padding;
                    tooltip.style.left = `${{left}}px`;
                    tooltip.style.top = `${{top}}px`;
                }}

                function hideTooltip_{project["id"]}() {{ document.getElementById('tooltip-{project["id"]}').classList.remove('show'); }}
                
                // --- renderMonthDividers (Idêntica) ---
                function renderMonthDividers_{project["id"]}() {{
                    const chartContainer = document.getElementById('chart-container-{project["id"]}');
                    chartContainer.querySelectorAll('.month-divider, .month-divider-label').forEach(el => el.remove());
                    let currentDate = parseDate(dataMinStr_{project["id"]});
                    const dataMax = parseDate(dataMaxStr_{project["id"]});
                    while (currentDate <= dataMax) {{
                        const left = getPosition_{project["id"]}(currentDate);
                        const divider = document.createElement('div'); divider.className = 'month-divider';
                        if (currentDate.getUTCMonth() === 0) divider.classList.add('first');
                        divider.style.left = `${{left}}px`; chartContainer.appendChild(divider);
                        currentDate.setUTCMonth(currentDate.getUTCMonth() + 1);
                    }}
                }}

                // --- setupEventListeners (Idêntica) ---
                function setupEventListeners_{project["id"]}() {{
                    const ganttChartContent = document.getElementById('gantt-chart-content-{project["id"]}'), sidebarContent = document.getElementById('gantt-sidebar-content-{project['id']}');
                    const fullscreenBtn = document.getElementById('fullscreen-btn-{project["id"]}'), toggleBtn = document.getElementById('toggle-sidebar-btn-{project['id']}');
                    const container = document.getElementById('gantt-container-{project["id"]}');

                    const applyBtn = document.getElementById('filter-apply-btn-{project["id"]}');
                    if (applyBtn) applyBtn.addEventListener('click', () => applyFiltersAndRedraw_{project["id"]}());
                    if (fullscreenBtn) fullscreenBtn.addEventListener('click', () => toggleFullscreenOrMenu_{project["id"]}());
                    if (container) container.addEventListener('fullscreenchange', () => handleFullscreenChange_{project["id"]}());
                    if (toggleBtn) toggleBtn.addEventListener('click', () => toggleSidebar_{project["id"]}());
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

                // --- Funções de Toggle (Idênticas) ---
                function toggleSidebar_{project["id"]}() {{ document.getElementById('gantt-sidebar-wrapper-{project["id"]}').classList.toggle('collapsed'); }}
                function toggleFullscreen_{project["id"]}() {{
                    const container = document.getElementById('gantt-container-{project["id"]}');
                    if (!document.fullscreenElement) {{
                        container.requestFullscreen().catch(err => alert(`Erro: ${{err.message}}`));
                    }} else {{
                        document.exitFullscreen();
                    }}
                }}
                function toggleFilterMenu_{project["id"]}() {{
                    document.getElementById('filter-menu-{project["id"]}').classList.toggle('is-open');
                }}
                function toggleFullscreenOrMenu_{project["id"]}() {{
                    const container = document.getElementById('gantt-container-{project["id"]}');
                    if (document.fullscreenElement === container) {{
                        toggleFilterMenu_{project["id"]}();
                    }} else {{
                        toggleFullscreen_{project["id"]}();
                    }}
                }}
                function handleFullscreenChange_{project["id"]}() {{
                    const btn = document.getElementById('fullscreen-btn-{project["id"]}');
                    const container = document.getElementById('gantt-container-{project["id"]}');
                    if (document.fullscreenElement === container) {{
                        btn.innerHTML = '<span>&#9776;</span>';
                        btn.classList.add('is-fullscreen');
                    }} else {{
                        btn.innerHTML = '<span>📺</span> <span>Tela Cheia</span>';
                        btn.classList.remove('is-fullscreen');
                        document.getElementById('filter-menu-{project["id"]}').classList.remove('is-open');
                    }}
                }}

                // --- populateFilters (Idêntica, usa filterOptions_... adaptado) ---
                function populateFilters_{project["id"]}() {{
                    if (filtersPopulated_{project["id"]}) return; 

                    const selSetor = document.getElementById('filter-setor-{project["id"]}');
                    filterOptions_{project["id"]}.setores.forEach(s => {{
                        selSetor.innerHTML += `<option value="${{s}}">${{s}}</option>`;
                    }});

                    const selGrupo = document.getElementById('filter-grupo-{project["id"]}');
                    filterOptions_{project["id"]}.grupos.forEach(g => {{
                        selGrupo.innerHTML += `<option value="${{g}}">${{g}}</option>`;
                    }});

                    const selEtapa = document.getElementById('filter-etapa-{project["id"]}');
                    filterOptions_{project["id"]}.etapas.forEach(e => {{
                        selEtapa.innerHTML += `<option value="${{e}}">${{e}}</option>`;
                    }});

                    document.querySelector(`input[name="filter-vis-{project['id']}"][value="${{tipoVisualizacao_{project["id"]}}}"]`).checked = true;
                    
                    const radioCom = document.getElementById('filter-pulmao-com-{project["id"]}');
                    const radioSem = document.getElementById('filter-pulmao-sem-{project["id"]}');
                    const mesesGroup = document.getElementById('pulmao-meses-group-{project["id"]}');
                    const updatePulmaoInputVisibility_{project["id"]} = () => {{
                        if (radioCom.checked) {{ mesesGroup.style.display = 'block'; }} 
                        else {{ mesesGroup.style.display = 'none'; }}
                    }};
                    radioCom.addEventListener('change', updatePulmaoInputVisibility_{project["id"]});
                    radioSem.addEventListener('change', updatePulmaoInputVisibility_{project["id"]});
                    document.querySelector(`input[name="filter-pulmao-{project['id']}"][value="${{pulmaoStatus_{project["id"]}}}"]`).checked = true;
                    document.getElementById('filter-pulmao-meses-{project["id"]}').value = {pulmao_meses};
                    updatePulmaoInputVisibility_{project["id"]}();
                    
                    filtersPopulated_{project["id"]} = true;
                }}

                // --- ### FUNÇÃO applyFiltersAndRedraw MODIFICADA ### ---
                function applyFiltersAndRedraw_{project["id"]}() {{
                    // 1. Ler os valores dos filtros
                    const selSetor = document.getElementById('filter-setor-{project["id"]}').value;
                    const selGrupo = document.getElementById('filter-grupo-{project["id"]}').value;
                    const selEtapa = document.getElementById('filter-etapa-{project["id"]}').value; // Este é o Empreendimento
                    const selConcluidas = document.getElementById('filter-concluidas-{project["id"]}').checked;
                    const selVis = document.querySelector(`input[name="filter-vis-{project['id']}"]:checked`).value;
                    const selPulmao = document.querySelector(`input[name="filter-pulmao-{project['id']}"]:checked`).value;
                    const selPulmaoMeses = parseInt(document.getElementById('filter-pulmao-meses-{project["id"]}').value, 10) || 0;

                    // 2. Obter os dados base (cópia profunda)
                    let baseTasks = JSON.parse(JSON.stringify(allTasks_baseData_{project["id"]}));

                    // 3. Aplicar lógica de Pulmão (se necessário)
                    if (selPulmao === 'Com Pulmão' && selPulmaoMeses > 0) {{
                        const offsetMeses = -selPulmaoMeses;
                        // Aplica a lógica de pulmão *consolidada*
                        baseTasks = aplicarLogicaPulmaoConsolidado(baseTasks, offsetMeses);
                    }}
                    
                    let filteredTasks = baseTasks;

                    // 4. Aplicar filtros de Setor, Grupo, Etapa(Empreendimento) e Concluídas
                    if (selSetor !== 'Todos') {{
                        filteredTasks = filteredTasks.filter(t => t.setor === selSetor);
                    }}
                    if (selGrupo !== 'Todos') {{
                        filteredTasks = filteredTasks.filter(t => t.grupo === selGrupo);
                    }}
                    if (selEtapa !== 'Todos') {{
                        // 'selEtapa' agora é um nome de Empreendimento
                        filteredTasks = filteredTasks.filter(t => t.name === selEtapa); 
                    }}
                    if (selConcluidas) {{
                        filteredTasks = filteredTasks.filter(t => t.progress < 100);
                    }}

                    // 5. Atualizar os dados globais do JS
                    projectData_{project["id"]}[0].tasks = filteredTasks;
                    tipoVisualizacao_{project["id"]} = selVis; // <-- Isso aciona a nova ordenação
                    pulmaoStatus_{project["id"]} = selPulmao;

                    // 6. Redesenhar o gráfico e a tabela
                    // renderSidebar irá ler o novo 'tipoVisualizacao_' e ordenar corretamente
                    renderSidebar_{project["id"]}(); 
                    renderChart_{project["id"]}();

                    // 7. Esconder o menu de filtros
                    toggleFilterMenu_{project["id"]}();
                }}

                initGantt_{project["id"]}();
            </script>
        </body>
        </html>
    """
    components.html(gantt_html, height=altura_gantt, scrolling=True)
    # st.markdown("---") no consolidado, pois ele não é parte de um loop

# --- FUNÇÃO PRINCIPAL DE GANTT (DISPATCHER) ---
def gerar_gantt(df, tipo_visualizacao, filtrar_nao_concluidas, df_original_para_ordenacao, pulmao_status, pulmao_meses):
    if df.empty:
        st.warning("Sem dados disponíveis para exibir o Gantt.")
        return

    etapas_unicas_no_df = df['Etapa'].unique()
    is_single_etapa_view = len(etapas_unicas_no_df) == 1

    if is_single_etapa_view:
        st.info("Exibindo visão comparativa para a etapa selecionada.")
        
        # --- Aplicar lógica de pulmão AQUI para a visão consolidada ---
        df_para_consolidado = df.copy()
        if pulmao_status == "Com Pulmão" and pulmao_meses > 0:
            colunas_data_todas = ["Inicio_Prevista", "Termino_Prevista", "Inicio_Real", "Termino_Real"]
            colunas_data_inicio = ["Inicio_Prevista", "Inicio_Real"]
            
            for col in colunas_data_todas:
                if col in df_para_consolidado.columns:
                    df_para_consolidado[col] = pd.to_datetime(df_para_consolidado[col], errors='coerce')

            offset_meses = -int(pulmao_meses)
            
            def aplicar_offset_meses(data):
                if pd.isna(data) or data is pd.NaT: return pd.NaT
                try: return data + relativedelta(months=offset_meses)
                except Exception: return pd.NaT

            etapas_pulmao = ["PULVENDA", "PUL.INFRA", "PUL.RAD"]
            etapas_sem_alteracao = ["PROSPEC", "RAD", "DEM.MIN"]
            
            mask_nao_mexer = df_para_consolidado['Etapa'].isin(etapas_sem_alteracao)
            mask_shift_inicio_apenas = df_para_consolidado['Etapa'].isin(etapas_pulmao)
            mask_shift_tudo = (~mask_nao_mexer) & (~mask_shift_inicio_apenas)

            for col in colunas_data_todas:
                if col in df_para_consolidado.columns:
                    df_para_consolidado.loc[mask_shift_tudo, col] = df_para_consolidado.loc[mask_shift_tudo, col].apply(aplicar_offset_meses)
            
            for col in colunas_data_inicio:
                if col in df_para_consolidado.columns:
                    df_para_consolidado.loc[mask_shift_inicio_apenas, col] = df_para_consolidado.loc[mask_shift_inicio_apenas, col].apply(aplicar_offset_meses)

        gerar_gantt_consolidado(df_para_consolidado, tipo_visualizacao, df_original_para_ordenacao, pulmao_status, pulmao_meses)
    else:
        gerar_gantt_por_projeto(df, tipo_visualizacao, df_original_para_ordenacao, pulmao_status, pulmao_meses)

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

# --- Bloco Principal ---
with st.spinner("Carregando e processando dados..."):
    df_data = load_data()

    # --- INÍCIO DE LÓGICA E INDENTAÇÃO ---
    # Verifica se os dados foram carregados com sucesso
    if df_data is not None and not df_data.empty:
        
        # Todo o código da aplicação agora está DENTRO deste 'if'
        with st.sidebar:
            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                try:
                    st.image("logoNova.png", width=200)
                except:
                    st.warning("Logo 'logoNova.png' não encontrada.")


            ugb_options = get_unique_values(df_data, "UGB")
            
            # Tente usar o dropdown customizado. Se falhar, use o multiselect padrão.
            try:
                selected_ugb = simple_multiselect_dropdown(label="Filtrar por UGB", options=ugb_options, key="ugb_filter", default_selected=ugb_options)
            except NameError:
                st.warning("Arquivo `dropdown_component.py` não encontrado. Usando filtro padrão.")
                selected_ugb = st.multiselect("Filtrar por UGB", options=ugb_options, default=ugb_options)
            except Exception as e:
                st.warning(f"Erro ao carregar `dropdown_component.py`: {e}. Usando filtro padrão.")
                selected_ugb = st.multiselect("Filtrar por UGB", options=ugb_options, default=ugb_options)


            emp_options = get_unique_values(df_data[df_data["UGB"].isin(selected_ugb)], "Empreendimento") if selected_ugb else []
            
            try:
                selected_emp = simple_multiselect_dropdown(label="Filtrar por EMP", options=emp_options, key="empreendimento_filter", default_selected=emp_options)
            except NameError:
                selected_emp = st.multiselect("Filtrar por EMP", options=emp_options, default=emp_options)
            except Exception:
                selected_emp = st.multiselect("Filtrar por EMP", options=emp_options, default=emp_options)


            df_temp = df_data[df_data["UGB"].isin(selected_ugb)]
            if selected_emp:
                df_temp = df_temp[df_temp["Empreendimento"].isin(selected_emp)]
            grupo_options = get_unique_values(df_temp, "GRUPO")
            
            try:
                selected_grupo = simple_multiselect_dropdown(label="Filtrar por GRUPO", options=grupo_options, key="grupo_filter", default_selected=grupo_options)
            except NameError:
                selected_grupo = st.multiselect("Filtrar por GRUPO", options=grupo_options, default=grupo_options)
            except Exception:
                selected_grupo = st.multiselect("Filtrar por GRUPO", options=grupo_options, default=grupo_options)


            df_temp_setor = df_data[df_data["UGB"].isin(selected_ugb)]
            if selected_emp:
                df_temp_setor = df_temp_setor[df_temp_setor["Empreendimento"].isin(selected_emp)]
            if selected_grupo:
                df_temp_setor = df_temp_setor[df_temp_setor["GRUPO"].isin(selected_grupo)]
            setor_options = list(SETOR.keys())
            
            try:
                selected_setor = simple_multiselect_dropdown(label="Filtrar por SETOR", options=setor_options, key="setor_filter", default_selected=setor_options)
            except NameError:
                selected_setor = st.multiselect("Filtrar por SETOR", options=setor_options, default=setor_options)
            except Exception:
                selected_setor = st.multiselect("Filtrar por SETOR", options=setor_options, default=setor_options)


            df_temp_filtered = filter_dataframe(df_data, selected_ugb, selected_emp, selected_grupo, selected_setor)
            if not df_temp_filtered.empty:
                etapas_disponiveis = get_unique_values(df_temp_filtered, "Etapa")
                etapas_ordenadas = [etapa for etapa in ORDEM_ETAPAS_GLOBAL if etapa in etapas_disponiveis]
                etapas_para_exibir = ["Todos"] + [sigla_para_nome_completo.get(e, e) for e in etapas_ordenadas]
            else:
                etapas_para_exibir = ["Todos"]
            selected_etapa_nome = st.selectbox("Filtrar por Etapa", options=etapas_para_exibir)

            st.markdown("---")

            # --- COM/SEM PULMÃO ---
            st.markdown("##### Simulação de Cenário")
            pulmao_status = st.radio(
                "Opção de Pulmão:",
                ("Sem Pulmão", "Com Pulmão"),
                key="pulmao_status_radio",
                horizontal=True,
                help="Define o estado inicial do gráfico (com ou sem pulmão)."
            )

            pulmao_meses = 0
            if pulmao_status == "Com Pulmão":
                pulmao_meses = st.number_input(
                    "Período do Pulmão (em meses)",
                    min_value=0,
                    max_value=36,
                    value=1, # Valor padrão alterado para 1, mas pode ser o que você preferir
                    step=1,
                    key="pulmao_meses_input"
                )
        
            st.markdown("---")
            filtrar_nao_concluidas = st.checkbox("Etapas não concluídas", value=False, help="Quando marcado, mostra apenas etapas com menos de 100% de conclusão")
            st.markdown("---")
            tipo_visualizacao = st.radio("Mostrar dados:", ("Ambos", "Previsto", "Real"))

        df_filtered = filter_dataframe(df_data, selected_ugb, selected_emp, selected_grupo, selected_setor)

        # Lógica do filtro de etapa única
        if selected_etapa_nome != "Todos" and not df_filtered.empty:
            sigla_selecionada = nome_completo_para_sigla.get(selected_etapa_nome, selected_etapa_nome)
            df_filtered = df_filtered[df_filtered["Etapa"] == sigla_selecionada]

        if filtrar_nao_concluidas and not df_filtered.empty:
            df_filtered = filtrar_etapas_nao_concluidas(df_filtered)

        # --- LÓGICA DE APLICAÇÃO DO PULMÃO FOI MOVIDA ---
        # A lógica de pulmão não é mais aplicada aqui para o gráfico principal.
        # Ela é aplicada dentro de gerar_gantt (para visão consolidada)
        # ou dentro de gerar_gantt_por_projeto (para a visão por projeto)
        df_para_exibir = df_filtered.copy() # df_para_exibir agora é os dados filtrados, mas SEM pulmão
        
        # --- FIM DA MODIFICAÇÃO DA LÓGICA DE PULMÃO ---

        st.title("Macrofluxo")
        tab1, tab2 = st.tabs(["Gráfico de Gantt", "Tabelão Horizontal"])

        with tab1:
            st.markdown("""
            <div class="nav-button-container">
                <a href="#inicio" class="nav-link">↑</a>
                <a href="#visao-detalhada" class="nav-link">↓</a>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown('<div id="inicio"></div>', unsafe_allow_html=True)

            st.subheader("Gantt Comparativo")
            if df_para_exibir.empty:
                st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
            else:
                # --- MODIFICADO ---
                # Passa o df_para_exibir (que é o df_filtered, sem pulmão)
                # e também o status e os meses do pulmão
                gerar_gantt(df_para_exibir.copy(), tipo_visualizacao, filtrar_nao_concluidas, df_data, pulmao_status, pulmao_meses)
                # --- FIM DA MODIFICAÇÃO ---

            st.markdown('<div id="visao-detalhada"></div>', unsafe_allow_html=True)
            
            st.subheader("Visão Detalhada por Empreendimento")
            
            # --- MODIFICADO ---
            # A tabela detalhada precisa refletir o estado do pulmão da barra lateral,
            # então precisamos aplicar a lógica de pulmão aqui também,
            # mas apenas para esta tabela.
            
            df_detalhes = df_para_exibir.copy() # Começa com os dados filtrados

            # Aplicar lógica de pulmão para a tabela detalhada
            if pulmao_status == "Com Pulmão" and pulmao_meses > 0:
                colunas_data_todas = ["Inicio_Prevista", "Termino_Prevista", "Inicio_Real", "Termino_Real"]
                colunas_data_inicio = ["Inicio_Prevista", "Inicio_Real"]
                
                for col in colunas_data_todas:
                    if col in df_detalhes.columns:
                        df_detalhes[col] = pd.to_datetime(df_detalhes[col], errors='coerce')

                offset_meses = -int(pulmao_meses)
                
                def aplicar_offset_meses(data):
                    if pd.isna(data) or data is pd.NaT: return pd.NaT
                    try: return data + relativedelta(months=offset_meses)
                    except Exception: return pd.NaT

                etapas_pulmao = ["PULVENDA", "PUL.INFRA", "PUL.RAD"]
                etapas_sem_alteracao = ["PROSPEC", "RAD", "DEM.MIN"]
                
                mask_nao_mexer = df_detalhes['Etapa'].isin(etapas_sem_alteracao)
                mask_shift_inicio_apenas = df_detalhes['Etapa'].isin(etapas_pulmao)
                mask_shift_tudo = (~mask_nao_mexer) & (~mask_shift_inicio_apenas)

                for col in colunas_data_todas:
                    if col in df_detalhes.columns:
                        df_detalhes.loc[mask_shift_tudo, col] = df_detalhes.loc[mask_shift_tudo, col].apply(aplicar_offset_meses)
                
                for col in colunas_data_inicio:
                    if col in df_detalhes.columns:
                        df_detalhes.loc[mask_shift_inicio_apenas, col] = df_detalhes.loc[mask_shift_inicio_apenas, col].apply(aplicar_offset_meses)
            # --- FIM DA LÓGICA DE PULMÃO PARA TABELA ---


            if df_detalhes.empty: # Verifique df_detalhes em vez de df_para_exibir
                st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
            else:
                # df_detalhes = df_para_exibir.copy() # Esta linha é removida, já foi definida
                
                empreendimentos_ordenados_por_meta = criar_ordenacao_empreendimentos(df_data)
                
                if filtrar_nao_concluidas:
                    df_detalhes = filtrar_etapas_nao_concluidas(df_detalhes)

                if df_detalhes.empty:
                    st.info("ℹ️ Nenhuma etapa não concluída encontrada para os filtros selecionados.")
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

                    if '% concluído' in df_detalhes.columns and not df_agregado.empty and df_agregado['Percentual_Concluido'].max() <= 1:
                        df_agregado['Percentual_Concluido'] *= 100

                    df_agregado['Var. Term'] = df_agregado.apply(
                        lambda row: calculate_business_days(row['Termino_Prevista'], row['Termino_Real']), axis=1
                    )
                    
                    df_agregado['ordem_empreendimento'] = pd.Categorical(
                        df_agregado['Empreendimento'],
                        categories=empreendimentos_ordenados_por_meta,
                        ordered=True
                    )
                    
                    ordem_etapas = list(sigla_para_nome_completo.keys())
                    df_agregado['Etapa_Ordem'] = df_agregado['Etapa'].apply(lambda x: ordem_etapas.index(x) if x in ordem_etapas else len(ordem_etapas))
                    
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
                        st.info("ℹ️ Nenhum dado para exibir na tabela detalhada com os filtros atuais.")
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
            
            # --- MODIFICADO ---
            # O tabelão também precisa refletir o estado do pulmão da barra lateral.
            # Usarei o mesmo df_detalhes que foi processado para a "Visão Detalhada" na tab1.
            # (A lógica de pulmão já foi aplicada a df_detalhes)
            
            if df_detalhes.empty: # Usando df_detalhes
                st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
            else:
                # df_detalhes = df_para_exibir.copy() # Removido, já temos df_detalhes
                
                # if filtrar_nao_concluidas: # Removido, df_detalhes já foi filtrado
                #     df_detalhes = filtrar_etapas_nao_concluidas(df_detalhes)
                
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

                ordem_etapas_completas = list(sigla_para_nome_completo.keys())
                df_detalhes_tabelao['Etapa_Ordem'] = df_detalhes_tabelao['Etapa'].apply(
                    lambda x: ordem_etapas_completas.index(x) if x in ordem_etapas_completas else len(ordem_etapas_completas)
                )
                
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
                    if not df_detalhes_tabelao.empty and df_detalhes_tabelao['% concluído'].max() <= 1:
                        df_detalhes_tabelao['% concluído'] *= 100

                if 'ordem_index' in df_detalhes_tabelao.columns:
                    agg_dict['ordem_index'] = ('ordem_index', 'first')

                df_agregado = df_detalhes_tabelao.groupby(['UGB', 'Empreendimento', 'Etapa']).agg(**agg_dict).reset_index()
                
                df_agregado['Var. Term'] = df_agregado.apply(lambda row: calculate_business_days(row['Termino_Prevista'], row['Termino_Real']), axis=1)

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
