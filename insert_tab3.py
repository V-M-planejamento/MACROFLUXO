# Código simples para tab3
tab3_code = '''
    # Tab3 - Linhas de Base (apenas para usuarios autorizados)
    if tab3 is not None:
        with tab3:
            st.title("Gerenciamento de Linhas de Base")
            
            # Seleção de empreendimento
            empreendimentos_baseline = df_data['Empreendimento'].unique().tolist() if not df_data.empty else []
            
            if not empreendimentos_baseline:
                st.warning("Nenhum empreendimento disponível")
            else:
                selected_empreendimento_baseline = st.selectbox(
                    "Selecione o Empreendimento",
                    empreendimentos_baseline,
                    key="baseline_emp_tab3"
                )
                
                st.divider()
                
                # === CRIAR BASELINE ===
                st.subheader("📝 Criar Nova Baseline")
                
                user_email = st.session_state.get('user_email', '')
                user_name = st.session_state.get('user_name', '')
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Empreendimento:** {selected_empreendimento_baseline}")
                    if user_name:
                        st.write(f"**Responsável:** {user_name}")
                
                with col2:
                    if st.button("Criar Baseline", use_container_width=True, type="primary", key="create_baseline_main"):
                        try:
                            version_name = take_gantt_baseline(
                                df_data, 
                                selected_empreendimento_baseline, 
                                tipo_visualizacao,
                                created_by=user_email if user_email else "usuario"
                            )
                            st.success(f"✅ Baseline {version_name} criada!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {e}")
                
                st.divider()
                
                # === APLICAR BASELINE ===
                st.subheader("📊 Aplicar Baseline ao Gráfico")
                
                baseline_options = get_baseline_options(selected_empreendimento_baseline)
                
                if baseline_options:
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        selected_baseline = st.selectbox(
                            "Selecione a baseline",
                            ["P0 (Padrão)"] + baseline_options,
                            key="apply_baseline_tab3"
                        )
                    
                    with col2:
                        if st.button("Aplicar", use_container_width=True, key="apply_baseline_btn"):
                            if selected_baseline == "P0 (Padrão)":
                                st.session_state.current_baseline = None
                                st.session_state.current_baseline_data = None
                                st.session_state.current_empreendimento = None
                                st.success("Voltou ao padrão")
                                st.rerun()
                            else:
                                baseline_data = get_baseline_data(selected_empreendimento_baseline, selected_baseline)
                                if baseline_data:
                                    st.session_state.current_baseline = selected_baseline
                                    st.session_state.current_baseline_data = baseline_data
                                    st.session_state.current_empreendimento = selected_empreendimento_baseline
                                    st.success(f"Baseline {selected_baseline} aplicada!")
                                    st.rerun()
                                else:
                                    st.error("Baseline não encontrada")
                else:
                    st.info("Nenhuma baseline disponível. Crie uma acima.")
                
                st.divider()
                
                # === LISTA DE BASELINES ===
                st.subheader("📋 Baselines Existentes")
                
                baselines = load_baselines()
                unsent_baselines = st.session_state.get('unsent_baselines', {})
                emp_unsent = unsent_baselines.get(selected_empreendimento_baseline, [])
                emp_baselines = baselines.get(selected_empreendimento_baseline, {})
                
                if emp_baselines:
                    for i, version_name in enumerate(sorted(emp_baselines.keys(), reverse=True)):
                        is_unsent = version_name in emp_unsent
                        baseline_info = emp_baselines[version_name]
                        data_criacao = baseline_info.get('date', 'N/A')
                        baseline_data_info = baseline_info.get('data', {})
                        created_by = baseline_data_info.get('created_by', 'N/A')
                        
                        col1, col2, col3 = st.columns([4, 2, 1])
                        
                        with col1:
                            status = "🟡 Pendente" if is_unsent else "🟢 Enviada"
                            st.write(f"**{version_name}** - {status}")
                            st.caption(f"Criado por: {created_by} | Data: {data_criacao}")
                        
                        with col2:
                            st.write("")  # Espaçamento
                        
                        with col3:
                            if st.button("Excluir", key=f"del_{i}", use_container_width=True):
                                if delete_baseline(selected_empreendimento_baseline, version_name):
                                    if 'unsent_baselines' in st.session_state:
                                        if version_name in st.session_state.unsent_baselines.get(selected_empreendimento_baseline, []):
                                            st.session_state.unsent_baselines[selected_empreendimento_baseline].remove(version_name)
                                    st.success("Excluída")
                                    st.rerun()
                                else:
                                    st.error("Erro ao excluir")
                        
                        if i < len(emp_baselines) - 1:
                            st.divider()
                    
                    # Estatísticas simples
                    st.divider()
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total", len(emp_baselines))
                    with col2:
                        st.metric("Pendentes", len(emp_unsent))
                    with col3:
                        st.metric("Enviadas", len(emp_baselines) - len(emp_unsent))
                else:
                    st.info("Nenhuma baseline criada ainda")

'''

lines = open('app.py', 'r', encoding='utf-8').readlines()
lines.insert(6162, tab3_code)
open('app.py', 'w', encoding='utf-8').writelines(lines)
print("Tab3 inserida!")
