import streamlit as st
from app import converter_porcentagem 
from app import sigla_para_nome_completo 
from app import filter_dataframe
from app import simple_multiselect_dropdown as nome_completo_para_sigla
from app import get_unique_values
from app import df_data
from dropdown_component import simple_multiselect_dropdown

# PATCH: Filtro de Etapas Não Concluídas
# ============================================================================
# 1. ADICIONAR NOVA FUNÇÃO (inserir após as funções utilitárias existentes)
# ============================================================================

def filtrar_etapas_nao_concluidas(df):
    """
    Filtra o DataFrame para mostrar apenas etapas que não estão 100% concluídas.
    
    Args:
        df (pandas.DataFrame): DataFrame com dados das etapas
        
    Returns:
        pandas.DataFrame: DataFrame filtrado com apenas etapas < 100% concluídas
    """
    if df.empty or '% concluído' not in df.columns:
        return df
    
    # Converter porcentagens para formato numérico
    df_copy = df.copy()
    df_copy['% concluído'] = df_copy['% concluído'].apply(converter_porcentagem)
    
    # Filtrar apenas etapas com menos de 100% de conclusão
    df_filtrado = df_copy[df_copy['% concluído'] < 100]
    
    return df_filtrado


# ============================================================================
# 5. EXEMPLO DE IMPLEMENTAÇÃO COMPLETA DA SEÇÃO DE FILTROS
# ============================================================================

def implementar_secao_filtros_completa():
    """
    Exemplo de como a seção de filtros deve ficar após as modificações
    """
    # --- Seção de Filtros ---
    with st.sidebar:
        st.header("🔍 Filtros")
        
        # 1️⃣ Filtro UGB
        ugb_options = get_unique_values(df_data, "UGB")
        selected_ugb = simple_multiselect_dropdown(
            label="Filtrar por UGB",
            options=ugb_options,
            key="ugb_filter",
            default_selected=ugb_options
        )
        
        # 2️⃣ Filtro Empreendimento
        if selected_ugb:
            emp_options = get_unique_values(
                df_data[df_data["UGB"].isin(selected_ugb)], 
                "Empreendimento"
            )
        else:
            emp_options = []
            
        selected_emp = simple_multiselect_dropdown(
            label="Filtrar por Empreendimento",
            options=emp_options,
            key="empreendimento_filter",
            default_selected=emp_options
        )
        
        # 3️⃣ Filtro Etapa
        df_filtered = filter_dataframe(df_data, selected_ugb, selected_emp)
        
        if not df_filtered.empty:
            etapas_disponiveis = get_unique_values(df_filtered, "Etapa")
            
            try:
                etapas_disponiveis = sorted(
                    etapas_disponiveis,
                    key=lambda x: list(sigla_para_nome_completo.keys()).index(x) if x in sigla_para_nome_completo else 99
                )
                etapas_para_exibir = ["Todos"] + [sigla_para_nome_completo.get(e, e) for e in etapas_disponiveis]
            except NameError:
                etapas_para_exibir = ["Todos"] + etapas_disponiveis
        else:
            etapas_para_exibir = ["Todos"]
        
        selected_etapa_nome = st.selectbox(
            "Filtrar por Etapa",
            options=etapas_para_exibir
        )

        # 4️⃣ NOVO FILTRO: Etapas não concluídas (com espaçamento ajustado dos ícones)
        st.markdown("---")
        
        # Usando HTML personalizado para melhor controle do espaçamento dos ícones
        st.markdown("""
        <style>
        .filtro-nao-concluidas {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 10px;
        }
        .filtro-nao-concluidas .icone {
            margin-right: 6px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Alternativa 1: Usando colunas para melhor controle do layout
        col1, col2 = st.columns([0.1, 0.9])
        with col1:
            st.markdown("📋")  # Ícone com espaçamento controlado
        with col2:
            filtrar_nao_concluidas = st.checkbox(
                "Mostrar apenas etapas não concluídas",
                value=False,
                help="Quando marcado, mostra apenas etapas com menos de 100% de conclusão"
            )

        # Alternativa 2: Usando markdown com HTML para controle fino do espaçamento
        # st.markdown("""
        # <div class="filtro-nao-concluidas">
        #     <span class="icone">📋</span>
        #     <span>Filtro de etapas não concluídas</span>
        # </div>
        # """, unsafe_allow_html=True)
        # 
        # filtrar_nao_concluidas = st.checkbox(
        #     "Mostrar apenas etapas não concluídas",
        #     value=False,
        #     help="Quando marcado, mostra apenas etapas com menos de 100% de conclusão"
        # )

        # 5️⃣ Opção de visualização
        st.markdown("---")
        
        # Aplicando o mesmo padrão de espaçamento para consistência
        col1, col2 = st.columns([0.1, 0.9])
        with col1:
            st.markdown("👁️")  # Ícone de visualização
        with col2:
            tipo_visualizacao = st.radio("Mostrar dados:", ("Ambos", "Previsto", "Real"))

    # Aplicar filtro de etapa
    if selected_etapa_nome != "Todos" and not df_filtered.empty:
        try:
            sigla_selecionada = nome_completo_para_sigla.get(selected_etapa_nome, selected_etapa_nome)
            df_filtered = df_filtered[df_filtered["Etapa"] == sigla_selecionada]
        except NameError:
            df_filtered = df_filtered[df_filtered["Etapa"] == selected_etapa_nome]

    # APLICAR NOVO FILTRO: Etapas não concluídas
    if filtrar_nao_concluidas and not df_filtered.empty:
        df_filtered = filtrar_etapas_nao_concluidas(df_filtered)
        
        # Mostrar informação sobre o filtro aplicado com ícones bem espaçados
        if not df_filtered.empty:
            total_etapas_nao_concluidas = len(df_filtered)
            st.sidebar.success(f"✅  Mostrando {total_etapas_nao_concluidas} etapas não concluídas")
        else:
            st.sidebar.info("ℹ️  Todas as etapas estão 100% concluídas")

    return df_filtered, tipo_visualizacao, filtrar_nao_concluidas

# ============================================================================
# 6. FUNÇÃO AUXILIAR PARA MENSAGENS CONDICIONAIS (com ícones bem espaçados)
# ============================================================================

def exibir_mensagem_sem_dados(filtrar_nao_concluidas):
    """
    Exibe mensagem apropriada quando não há dados para mostrar
    
    Args:
        filtrar_nao_concluidas (bool): Se o filtro de não concluídas está ativo
    """
    if filtrar_nao_concluidas:
        st.info("ℹ️  Nenhuma etapa não concluída encontrada com os filtros aplicados.")
    else:
        st.warning("⚠️  Nenhum dado encontrado com os filtros aplicados.")

# ============================================================================
# 7. FUNÇÃO ADICIONAL PARA CUSTOMIZAÇÃO AVANÇADA DE ESPAÇAMENTO
# ============================================================================

def aplicar_estilos_customizados():
    """
    Aplica estilos CSS customizados para melhor controle do espaçamento dos ícones
    """
    st.markdown("""
    <style>
    /* Espaçamento geral para ícones em mensagens */
    .stAlert > div > div {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Espaçamento específico para checkboxes com ícones */
    .stCheckbox > label > div {
        display: flex;
        align-items: center;
        gap: 6px;
    }
    
    /* Espaçamento para radio buttons com ícones */
    .stRadio > label > div {
        display: flex;
        align-items: center;
        gap: 6px;
    }
    
    /* Classe personalizada para controle fino */
    .icone-espacado {
        margin-right: 8px !important;
        display: inline-block;
    }
    </style>
    """, unsafe_allow_html=True)

# Exemplo de uso da função de estilos:
# aplicar_estilos_customizados()

