# Script para reescrever tab3 com design moderno tipo dashboard
import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Encontrar início e fim da tab3
start_marker = "# Tab3 - Linhas de Base (apenas para usuarios autorizados)"
end_marker = "# Ações de sistema"

# Extrair partes antes e depois
parts = content.split(start_marker)
before = parts[0]

# Encontrar onde termina a tab3
after_parts = parts[1].split(end_marker)
after = end_marker + after_parts[1]

# Novo código da tab3 com design moderno
new_tab3 = '''# Tab3 - Linhas de Base (apenas para usuarios autorizados)
    if tab3 is not None:
        with tab3:
            # CSS para design moderno tipo dashboard
            st.markdown("""
                <style>
                /* Container principal */
                .dashboard-container {
                    background: white;
                    padding: 2rem;
                    border-radius: 12px;
                }
                
                /* Header */
                .dashboard-title {
                    font-size: 2rem;
                    font-weight: 700;
                    color: #1a1a1a;
                    margin-bottom: 0.5rem;
                }
                
                .dashboard-subtitle {
                    font-size: 0.95rem;
                    color: #6b7280;
                    margin-bottom: 2.5rem;
                }
                
                /* Cards */
                .baseline-card {
                    background: #ffffff;
                    border: 1px solid #e5e7eb;
                    border-radius: 8px;
                    padding: 1.5rem;
                    margin-bottom: 1.5rem;
                    transition: box-shadow 0.2s;
                }
                
                .baseline-card:hover {
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                }
                
                /* Labels */
                .field-label {
                    font-size: 0.75rem;
                    font-weight: 600;
                    color: #6b7280;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    margin-bottom: 0.5rem;
                }
                
                .field-value {
                    font-size: 0.95rem;
                    color: #1f2937;
                    font-weight: 500;
                }
                
                /* Status badges */
                .status-badge {
                    display: inline-block;
                    padding: 0.25rem 0.75rem;
                    border-radius: 12px;
                    font-size: 0.75rem;
                    font-weight: 600;
                }
                
                .status-active {
                    background: #d1fae5;
                    color: #065f46;
                }
                
                .status-pending {
                    background: #fef3c7;
                    color: #92400e;
                }
                
                /* Tabela moderna */
                .modern-table {
                    width: 100%;
                    border-collapse: separate;
                    border-spacing: 0;
                    margin-top: 1rem;
                }
                
                .modern-table th {
                    background: #f9fafb;
                    padding: 0.75rem 1rem;
                    text-align: left;
                    font-size: 0.75rem;
                    font-weight: 600;
                    color: #6b7280;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    border-bottom: 1px solid #e5e7eb;
                }
                
                .modern-table td {
                    padding: 1rem;
                    border-bottom: 1px solid #f3f4f6;
                    font-size: 0.875rem;
                    color: #1f2937;
                }
                
                .modern-table tr:hover {
                    background: #f9fafb;
                }
                
                /* Seção divider */
                .section-space {
                    height: 3rem;
                }
                </style>
            """, unsafe_allow_html=True)
            
            # Header principal
            st.markdown('<div class="dashboard-title">Linhas de Base</div>', unsafe_allow_html=True)
            st.markdown('<div class="dashboard-subtitle">Gerencie snapshots do cronograma do projeto</div>', unsafe_allow_html=True)
            
            # Seleção de empreendimento
            empreendimentos_baseline = df_data['Empreendimento'].unique().tolist() if not df_data.empty else []
            
            if not empreendimentos_baseline:
                st.warning("⚠️ Nenhum empreendimento disponível")
            else:
                col1, col2, col3 = st.columns([3, 3, 2])
                
                with col1:
                    selected_empreendimento_baseline = st.selectbox(
                        "Selecione o Empreendimento",
                        empreendimentos_baseline,
                        key="baseline_emp_tab3",
                        label_visibility="collapsed"
                    )
                
                # Espaçamento
                st.markdown('<div class="section-space"></div>', unsafe_allow_html=True)
                
                # === CRIAR NOVA BASELINE ===
                user_email = st.session_state.get('user_email', '')
                user_name = st.session_state.get('user_name', '')
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown("### Criar Nova Baseline")
                    st.markdown(f"""
                        <div style="margin-top: 1rem;">
                            <div class="field-label">Empreendimento</div>
                            <div class="field-value">{selected_empreendimento_baseline}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if user_name and user_email:
                        st.markdown(f"""
                            <div style="margin-top: 1rem;">
                                <div class="field-label">Responsável</div>
                                <div class="field-value">{user_name} • {user_email}</div>
                            </div>
                        """, unsafe_allow_html=True)
                
                with col2:
                    st.write("")
                    st.write("")
                    if st.button("✨ Criar Baseline", use_container_width=True, type="primary", key="create_baseline_main"):
                        try:
                            version_name = take_gantt_baseline(
                                df_data, 
                                selected_empreendimento_baseline, 
                                tipo_visualizacao,
                                created_by=user_email if user_email else "usuario"
                            )
                            st.success(f"✅ Baseline **{version_name}** criada!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro: {e}")
                
                # Espaçamento
                st.markdown('<div class="section-space"></div>', unsafe_allow_html=True)
                
                # === APLICAR BASELINE ===
                st.markdown("### Aplicar ao Gráfico")
                
                baseline_options = get_baseline_options(selected_empreendimento_baseline)
                
                if baseline_options:
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        selected_baseline = st.selectbox(
                            "Baseline",
                            ["P0 (Padrão)"] + baseline_options,
                            key="apply_baseline_tab3"
                        )
                    
                    with col2:
                        st.write("")
                        if st.button("📊 Aplicar", use_container_width=True, key="apply_baseline_btn"):
                            if selected_baseline == "P0 (Padrão)":
                                st.session_state.current_baseline = None
                                st.session_state.current_baseline_data = None
                                st.session_state.current_empreendimento = None
                                st.success("✅ Padrão restaurado")
                                st.rerun()
                            else:
                                baseline_data = get_baseline_data(selected_empreendimento_baseline, selected_baseline)
                                if baseline_data:
                                    st.session_state.current_baseline = selected_baseline
                                    st.session_state.current_baseline_data = baseline_data
                                    st.session_state.current_empreendimento = selected_empreendimento_baseline
                                    st.success(f"✅ Baseline **{selected_baseline}** aplicada!")
                                    st.rerun()
                                else:
                                    st.error("❌ Baseline não encontrada")
                else:
                    st.info("ℹ️ Nenhuma baseline disponível. Crie uma acima.")
                
                # Espaçamento
                st.markdown('<div class="section-space"></div>', unsafe_allow_html=True)
                
                # === BASELINES EXISTENTES ===
                st.markdown("### Baselines Criadas")
                
                baselines = load_baselines()
                unsent_baselines = st.session_state.get('unsent_baselines', {})
                emp_unsent = unsent_baselines.get(selected_empreendimento_baseline, [])
                emp_baselines = baselines.get(selected_empreendimento_baseline, {})
                
                if emp_baselines:
                    # Tabela moderna
                    for i, version_name in enumerate(sorted(emp_baselines.keys(), reverse=True)):
                        is_unsent = version_name in emp_unsent
                        baseline_info = emp_baselines[version_name]
                        data_criacao = baseline_info.get('date', 'N/A')
                        baseline_data_info = baseline_info.get('data', {})
                        created_by = baseline_data_info.get('created_by', 'N/A')
                        
                        with st.container():
                            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                            
                            with col1:
                                st.markdown(f"**{version_name}**")
                                st.caption(f"👤 {created_by}")
                            
                            with col2:
                                st.caption("Data de Criação")
                                st.write(data_criacao)
                            
                            with col3:
                                status_class = "status-pending" if is_unsent else "status-active"
                                status_text = "Pendente" if is_unsent else "Enviada"
                                st.markdown(f'<span class="status-badge {status_class}">{status_text}</span>', unsafe_allow_html=True)
                            
                            with col4:
                                if st.button("🗑️", key=f"del_{i}", help="Excluir", use_container_width=True):
                                    if delete_baseline(selected_empreendimento_baseline, version_name):
                                        if 'unsent_baselines' in st.session_state:
                                            if version_name in st.session_state.unsent_baselines.get(selected_empreendimento_baseline, []):
                                                st.session_state.unsent_baselines[selected_empreendimento_baseline].remove(version_name)
                                        st.success("✅ Excluída")
                                        st.rerun()
                                    else:
                                        st.error("❌ Erro ao excluir")
                            
                            if i < len(emp_baselines) - 1:
                                st.divider()
                    
                    # Estatísticas
                    st.markdown('<div class="section-space"></div>', unsafe_allow_html=True)
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Total", len(emp_baselines))
                    with col2:
                        st.metric("Pendentes", len(emp_unsent))
                    with col3:
                        st.metric("Enviadas", len(emp_baselines) - len(emp_unsent))
                else:
                    st.info("📋 Nenhuma baseline criada ainda")
            
            # '''

# Juntar tudo
new_content = before + start_marker + new_tab3 + after

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Tab3 reescrita com design moderno!")
