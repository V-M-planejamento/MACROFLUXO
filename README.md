# MACROFLUXO

```
📊 SISTEMA DE DASHBOARD GANTT COMPARATIVO - ARVORE DE DECISÃO COMPLETA
│
├── 🏗️ 1. CONFIGURAÇÃO INICIAL E IMPORTAÇÕES
│   ├── Streamlit, Pandas, NumPy, Matplotlib
│   ├── from matplotlib.patches import Patch, Rectangle
│   ├── from matplotlib.legend_handler import HandlerTuple
│   ├── matplotlib.dates, matplotlib.gridspec
│   ├── datetime, timedelta, holidays, relativedelta
│   ├── traceback, streamlit.components.v1
│   ├── json, random, time
│   ├── TENTAR Importar componentes customizados:
│   │   ├── dropdown_component → simple_multiselect_dropdown
│   │   ├── popup → show_welcome_screen
│   │   ├── calculate_business_days → calculate_business_days
│   │   └── SE ImportError → Usar mocks/valores padrão
│   └── TENTAR Importar processamento de dados:
│       ├── tratamento_dados_reais → buscar_e_processar_dados_completos
│       ├── tratamento_macrofluxo → tratar_macrofluxo
│       └── SE ImportError → MODO_REAL = False (dados exemplo)
│
├── 📋 2. DEFINIÇÕES GLOBAIS E MAPEAMENTOS
│   ├── ORDEM_ETAPAS_GLOBAL (34 etapas definidas)
│   ├── GRUPOS (7 grupos: VENDA, LIMPEZA, TERRAPLANAGEM, etc.)
│   ├── SETOR (8 setores: PROSPECÇÃO, LEGALIZAÇÃO, PULMÃO, etc.)
│   ├── mapeamento_etapas_usuario (28 mapeamentos)
│   ├── mapeamento_reverso
│   ├── sigla_para_nome_completo
│   ├── SUBETAPAS (4 grupos de subetapas)
│   ├── ETAPA_PAI_POR_SUBETAPA
│   └── ORDEM_ETAPAS_NOME_COMPLETO
│
├── 🎨 3. CONFIGURAÇÕES DE ESTILO (StyleConfig)
│   ├── LARGURA_GANTT, ALTURA_GANTT_POR_ITEM, ALTURA_BARRA_GANTT
│   ├── CORES: PREVISTO, REAL, HOJE, CONCLUIDO, ATRASADO, META_ASSINATURA
│   ├── FONTES: TITULO, ETAPA, DATAS, PORCENTAGEM, VARIACAO
│   ├── CABECALHO, CELULA_PAR, CELULA_IMPAR, FUNDO_TABELA
│   ├── ESPACO_ENTRE_EMPREENDIMENTOS, OFFSET_VARIACAO_TERMINO
│   └── CORES_POR_SETOR (8 setores com cores previsto/real)
│
├── 📥 4. CARREGAMENTO E PROCESSAMENTO DE DADOS (@st.cache_data)
│   ├── DECISÃO: Qual fonte de dados usar?
│   │   ├── SE MODO_REAL = True
│   │   │   ├── TENTAR buscar_e_processar_dados_completos()
│   │   │   │   ├── Processar df_real
│   │   │   │   ├── Renomear colunas: EMP→Empreendimento, %_Concluido→% concluído
│   │   │   │   ├── Pivotar dados: Inicio_Fim→[INICIO, TERMINO]→[Inicio_Real, Termino_Real]
│   │   │   │   └── SE erro → mostrar traceback completo
│   │   │   └── TENTAR tratar_macrofluxo()
│   │   │       ├── Processar df_previsto
│   │   │       └── Pivotar: Inicio_Fim→[Inicio_Prevista, Termino_Prevista]
│   │   │
│   │   └── SE MODO_REAL = False → criar_dados_exemplo()
│   │
│   ├── DECISÃO: Como mesclar dados?
│   │   ├── SE df_real e df_previsto existem → merge outer
│   │   ├── SE apenas df_previsto → adicionar colunas real vazias
│   │   └── SE apenas df_real → adicionar colunas previsto vazias
│   │
│   └── PROCESSAMENTO PÓS-MERGE:
│       ├── Aplicar lógica de exceção para subetapas (PE, ORÇ, SUP)
│       ├── Mapear GRUPO e SETOR para cada etapa
│       ├── Verificar etapas não mapeadas → alerta na sidebar
│       └── Retornar df_merged final
│
├── 🎛️ 5. FILTROS DA SIDEBAR
│   ├── UGB: simple_multiselect_dropdown (default: todos)
│   ├── EMPREENDIMENTO: filtrado pelos UGBs selecionados
│   ├── GRUPO: filtrado por UGB+EMP anteriores
│   ├── SETOR: lista fixa dos 8 setores (default: todos)
│   ├── ETAPA: ["Todos"] + etapas disponíveis filtradas
│   ├── SIMULAÇÃO PULMÃO:
│   │   ├── Radio: "Sem Pulmão" vs "Com Pulmão"
│   │   └── SE "Com Pulmão" → number_input (0-36 meses, default:1)
│   ├── CHECKBOX: "Etapas não concluídas"
│   └── RADIO: "Mostrar dados:" → "Ambos", "Previsto", "Real"
│
├── 🔄 6. APLICAÇÃO DE FILTROS E LÓGICA DE PULMÃO
│   ├── Aplicar filtros sequenciais: UGB → EMP → GRUPO → SETOR
│   ├── DECISÃO: Modo de visualização do Gantt?
│   │   ├── SE selected_etapa_nome = "Todos" → Visão por Projeto
│   │   └── SE selected_etapa_nome = específica → Visão Consolidada
│   │
│   ├── APLICAR LÓGICA DE PULMÃO (se ativado):
│   │   ├── DEFINIR: etapas_pulmao = ["PULVENDA", "PUL.INFRA", "PUL.RAD"]
│   │   ├── DEFINIR: etapas_sem_alteracao = ["PROSPEC", "RAD", "DEM.MIN"]
│   │   ├── PARA CADA tarefa:
│   │   │   ├── SE etapa in etapas_sem_alteracao → não alterar datas
│   │   │   ├── SE etapa in etapas_pulmao → ajustar apenas datas de início
│   │   │   └── SE outra etapa → ajustar todas as datas
│   │   └── Aplicar offset_meses = -pulmao_meses
│
├── 📊 7. VISUALIZAÇÃO PRINCIPAL (TABS)
│   │
│   ├── 🗓️ TAB 1: GRÁFICO DE GANTT
│   │   ├── DECISÃO PRINCIPAL: Qual função Gantt chamar?
│   │   │   ├── SE Visão Consolidada → gerar_gantt_consolidado()
│   │   │   └── SE Visão por Projeto → gerar_gantt_por_projeto()
│   │   │
│   │   ├── FUNÇÃO gerar_gantt_por_projeto():
│   │   │   ├── PARA CADA projeto na lista ordenada:
│   │   │   │   ├── SE projeto não está nos dados filtrados → pular silenciosamente
│   │   │   │   ├── Calcular data_min_proj, data_max_proj
│   │   │   │   ├── Gerar HTML/JS personalizado para o projeto
│   │   │   │   ├── Incluir Virtual Select para filtros
│   │   │   │   ├── Estrutura de subetapas (expandir/recolher)
│   │   │   │   └── components.html() com altura dinâmica
│   │   │   └── FIM
│   │   │
│   │   ├── FUNÇÃO gerar_gantt_consolidado():
│   │   │   ├── Agrupar dados por etapa e empreendimento
│   │   │   ├── Preparar all_data_by_stage_js (todas etapas)
│   │   │   ├── Criar projeto único para comparação
│   │   │   ├── Filtro especial: selecionar etapa atual
│   │   │   └── JS permite trocar etapa sem recarregar
│   │   │
│   │   └── COMPONENTES COMUNS DO GANTT:
│   │       ├── Sidebar com grid (10 colunas)
│   │       ├── Chart com header de anos/meses
│   │       ├── Barras previsto/real com sobreposição
│   │       ├── Linhas: today-line, meta-line
│   │       ├── Tooltips interativos
│   │       ├── Controles: fullscreen, toggle sidebar, filtros flutuantes
│   │       └── Virtual Select para filtros multi-seleção
│   │
│   └── 📋 TAB 2: TABELÃO HORIZONTAL
│       ├── DECISÃO: Layout hierárquico ou horizontal?
│       │   ├── SE apenas uma etapa → layout horizontal
│       │   └── SE múltiplas etapas → layout hierárquico
│       │
│       ├── LAYOUT HIERÁRQUICO:
│       │   ├── Agrupar por empreendimento
│       │   ├── Cabecalho com totais/médias
│       │   ├── Subitens indentados para etapas
│       │   └── Estilos condicionais por status
│       │
│       ├── LAYOUT HORIZONTAL (PIVOT):
│       │   ├── Pivot table: etapas como colunas
│       │   ├── MultiIndex columns: [Etapa][Inicio_Prev, Termino_Prev, etc.]
│       │   ├── Ordenação personalizável (5 opções)
│       │   └── Colunas ordenadas por ORDEM_ETAPAS_GLOBAL
│       │
│       └── ESTILOS E FORMATAÇÃO:
│           ├── Cores condicionais baseadas em:
│           │   ├── % concluído = 100 + termino_real ≤ termino_previsto → VERDE
│           │   ├── % concluído = 100 + termino_real > termino_previsto → VERMELHO  
│           │   ├── % concluído < 100 + termino_real < hoje → AMARELO
│           │   └── Demais casos → PRETO
│           ├── Formatação de datas (DD/MM/AA)
│           ├── Variação em dias com setas (▲ ▼)
│           └── Legendas explicativas
│
├── ⚙️ 8. FUNCIONALIDADES AVANÇADAS E LÓGICAS ESPECÍFICAS
│   ├── CÁLCULO DE DIAS ÚTEIS:
│   │   ├── Usar np.busday_count ou calculate_business_days
│   │   ├── Considerar feriados (holidays)
│   │   └── Calcular variações (VT, VD)
│   │
│   ├── LÓGICA DE SUBETAPAS (ENGENHARIA):
│   │   ├── Para etapas pai (ENG. LIMP., ENG. TER., etc.):
│   │   │   ├── Calcular datas a partir das subetapas (PE, ORÇ, SUP)
│   │   │   ├── Recalcular progresso como média das subetapas
│   │   │   └── Subetapas mostram apenas dados reais
│   │   └── Controles expandir/recolher no Gantt
│   │
│   ├── ORDENAÇÃO INTELIGENTE:
│   │   ├── Empreendimentos ordenados por data de DEM.MIN
│   │   ├── Etapas ordenadas por ORDEM_ETAPAS_GLOBAL
│   │   └── No consolidado: ordenar por data de início (previsto/real)
│   │
│   └── TRATAMENTO DE DATAS E VALORES:
│       ├── converter_porcentagem() (suporta 0-1 e 0-100)
│       ├── padronizar_etapa() (mapeamento e uppercase)
│       ├── calcular_periodo_datas() com padding
│       └── Tratamento de timezones (UTC)
│
└── 🎯 9. FLUXO DE DECISÃO FINAL
    ├── INICIAR APLICAÇÃO
    │   ├── TENTAR show_welcome_screen() → SE True → st.stop()
    │   └── Configurar página wide
    │
    ├── CARREGAR DADOS
    │   ├── SE sucesso → continuar
    │   └── SE erro → mostrar dados exemplo
    │
    ├── PROCESSAR FILTROS
    │   ├── Aplicar cadeia de filtros
    │   ├── Determinar modo de visualização
    │   └── Aplicar lógica de pulmão se necessário
    │
    ├── RENDERIZAR INTERFACE
    │   ├── SE Tab Gantt selecionada:
    │   │   ├── DECIDIR entre visão consolidada ou por projeto
    │   │   └── Chamar função correspondente
    │   │
    │   └── SE Tab Tabelão selecionada:
    │       ├── DECIDIR layout (hierárquico/horizontal)
    │       ├── Processar e formatar dados
    │       └── Aplicar estilos condicionais
    │
    └── FIM
```
