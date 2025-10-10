import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
from datetime import datetime, timedelta

# Configuração da página
st.set_page_config(
    page_title="Gráfico de Gantt com Barras Duplas",
    page_icon="📊",
    layout="wide"
)

# Título da aplicação
st.title("📊 Gráfico de Gantt com Barras Duplas - Previsto vs Real")
st.markdown("---")

# Função para calcular o período de datas dos dados
def calcular_periodo_datas(df):
    """Calcula o período mínimo e máximo das datas nos dados"""
    if df.empty:
        return datetime(2024, 1, 1), datetime(2025, 12, 31)
    
    datas = []
    for col in ['Inicio_Prevista', 'Termino_Prevista', 'Inicio_Real', 'Termino_Real']:
        if col in df.columns:
            datas.extend(df[col].dropna().tolist())
    
    if not datas:
        return datetime(2024, 1, 1), datetime(2025, 12, 31)
    
    data_min = min(datas)
    data_max = max(datas)
    
    # Adicionar margem de 1 mês antes e depois
    data_min = data_min.replace(day=1) - timedelta(days=30)
    data_max = data_max.replace(day=28) + timedelta(days=60)
    
    return data_min, data_max

# Função para converter dados do DataFrame para formato do Gantt
def converter_dados_para_gantt(df):
    """Converte DataFrame para formato compatível com o gráfico de Gantt"""
    if df.empty:
        return [], datetime(2024, 1, 1), datetime(2025, 12, 31)
    
    data_min, data_max = calcular_periodo_datas(df)
    gantt_data = []
    
    # Agrupar por empreendimento
    for empreendimento in df['Empreendimento'].unique():
        df_emp = df[df['Empreendimento'] == empreendimento]
        
        tasks = []
        for idx, row in df_emp.iterrows():
            # Converter datas para timestamp
            start_date = row.get('Inicio_Prevista', datetime.now())
            end_date = row.get('Termino_Prevista', datetime.now() + timedelta(days=30))
            start_real = row.get('Inicio_Real', None)
            end_real = row.get('Termino_Real', None)
            
            if pd.isna(start_date):
                start_date = datetime.now()
            if pd.isna(end_date):
                end_date = start_date + timedelta(days=30)
            
            # Determinar cor baseada na etapa
            color_map = {
                'PROSPEC': 1, 'LEGVENDA': 2, 'PULVENDA': 3,
                'PL.LIMP': 4, 'LEG.LIMP': 5, 'ENG.LIMP': 6, 'EXECLIMP': 7,
                'PL.TER': 1, 'LEG.TER': 2, 'ENG.TER': 3, 'EXECTER': 4,
                'PL.INFRA': 5, 'LEG.INFRA': 6, 'ENG.INFRA': 7, 'EXECINFRA': 8,
                'ENG.PAV': 1, 'EXEC.PAV': 2, 'PUL.INFRA': 3,
                'PL.RAD': 4, 'LEG.RAD': 5, 'RAD': 6, 'DEM.MIN': 7,
                'CONTRATAÇÃO': 2
            }
            
            etapa = row.get('Etapa', 'UNKNOWN')
            color = color_map.get(etapa, 1)
            
            # Calcular progresso e status
            progress = row.get('% concluído', 0)
            
            # Calcular variação de tempo (VT e VD)
            vt = 0
            vd = 0
            
            if pd.notna(start_real):
                vt = (pd.to_datetime(start_real) - start_date).days
            
            if pd.notna(end_real):
                vd = (pd.to_datetime(end_real) - end_date).days
            
            task = {
                "id": f"t{idx}",
                "name": etapa,
                "start_previsto": start_date.strftime('%Y-%m-%d'),
                "end_previsto": end_date.strftime('%Y-%m-%d'),
                "start_real": pd.to_datetime(start_real).strftime('%Y-%m-%d') if pd.notna(start_real) else None,
                "end_real": pd.to_datetime(end_real).strftime('%Y-%m-%d') if pd.notna(end_real) else None,
                "color": color,
                "desc": f"{etapa} - {empreendimento}",
                "progress": progress,
                "empreendimento": empreendimento,
                "inicio_previsto": start_date.strftime('%d/%m/%y'),
                "termino_previsto": end_date.strftime('%d/%m/%y'),
                "inicio_real": pd.to_datetime(start_real).strftime('%d/%m/%y') if pd.notna(start_real) else None,
                "termino_real": pd.to_datetime(end_real).strftime('%d/%m/%y') if pd.notna(end_real) else None,
                "vt": vt,
                "vd": vd,
                "duracao_prevista": (end_date - start_date).days,
                "duracao_real": (pd.to_datetime(end_real) - pd.to_datetime(start_real)).days if pd.notna(start_real) and pd.notna(end_real) else None
            }
            tasks.append(task)
        
        project = {
            "id": f"p{len(gantt_data)}",
            "name": empreendimento,
            "desc": f"Projeto {empreendimento}",
            "tasks": tasks
        }
        gantt_data.append(project)
    
    return gantt_data, data_min, data_max

# Dados de exemplo (você pode substituir pelos seus dados reais)
@st.cache_data
def carregar_dados_exemplo():
    """Carrega dados de exemplo para demonstração"""
    data = {
        'Empreendimento': [
            'Residencial Alpha', 'Residencial Alpha', 'Residencial Alpha',
            'Residencial Beta', 'Residencial Beta', 'Residencial Beta',
            'Residencial Gamma', 'Residencial Gamma', 'Residencial Gamma',
            'Residencial Delta', 'Residencial Delta', 'Residencial Delta',
            'Residencial Epsilon', 'Residencial Epsilon', 'Residencial Epsilon',
            'Residencial Zeta', 'Residencial Zeta', 'Residencial Zeta'
        ],
        'Etapa': [
            'PROSPEC', 'LEGVENDA', 'PULVENDA',
            'PL.LIMP', 'LEG.LIMP', 'ENG.LIMP',
            'EXECLIMP', 'PL.TER', 'LEG.TER',
            'ENG.TER', 'EXECTER', 'PL.INFRA',
            'LEG.INFRA', 'ENG.INFRA', 'EXECINFRA',
            'CONTRATAÇÃO', 'LEG.RAD', 'RAD'
        ],
        'Inicio_Prevista': [
            datetime(2024, 1, 1), datetime(2024, 4, 1), datetime(2025, 1, 1),
            datetime(2024, 2, 15), datetime(2024, 3, 1), datetime(2024, 3, 15),
            datetime(2024, 4, 1), datetime(2024, 4, 15), datetime(2024, 5, 1),
            datetime(2024, 5, 15), datetime(2024, 6, 1), datetime(2024, 6, 15),
            datetime(2024, 7, 1), datetime(2024, 7, 15), datetime(2024, 8, 1),
            datetime(2025, 5, 16), datetime(2024, 10, 15), datetime(2024, 11, 1)
        ],
        'Termino_Prevista': [
            datetime(2024, 3, 31), datetime(2024, 12, 31), datetime(2025, 4, 30),
            datetime(2024, 2, 29), datetime(2024, 3, 14), datetime(2024, 3, 31),
            datetime(2024, 4, 14), datetime(2024, 4, 30), datetime(2024, 5, 14),
            datetime(2024, 5, 31), datetime(2024, 6, 14), datetime(2024, 6, 30),
            datetime(2024, 7, 14), datetime(2024, 7, 31), datetime(2024, 8, 14),
            datetime(2025, 6, 5), datetime(2024, 10, 31), datetime(2024, 11, 14)
        ],
        'Inicio_Real': [
            datetime(2024, 1, 1), datetime(2024, 4, 1), None,
            datetime(2024, 2, 20), datetime(2024, 3, 5), datetime(2024, 3, 20),
            None, None, None, None, None, None,
            None, None, None, datetime(2025, 3, 20), None, None
        ],
        'Termino_Real': [
            datetime(2024, 3, 31), datetime(2024, 12, 31), None,
            datetime(2024, 3, 15), datetime(2024, 3, 25), datetime(2024, 4, 10),
            None, None, None, None, None, None,
            None, None, None, datetime(2025, 6, 17), None, None
        ],
        '% concluído': [
            100, 100, 0, 100, 100, 100, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 100, 0, 0
        ]
    }
    return pd.DataFrame(data)

# Interface do usuário
col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("Configurações")
    
    # Opção para usar dados de exemplo ou upload
    usar_exemplo = st.checkbox("Usar dados de exemplo", value=True)
    
    if usar_exemplo:
        df = carregar_dados_exemplo()
        st.success(f"Carregados {len(df)} registros de exemplo")
    else:
        uploaded_file = st.file_uploader("Escolha um arquivo CSV", type="csv")
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
            # Converter colunas de data
            for col in ['Inicio_Prevista', 'Termino_Prevista', 'Inicio_Real', 'Termino_Real']:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
        else:
            df = pd.DataFrame()
    
    # Filtros
    if not df.empty:
        st.subheader("Filtros")
        
        # Filtro por empreendimento
        empreendimentos = st.multiselect(
            "Empreendimentos",
            options=df['Empreendimento'].unique(),
            default=df['Empreendimento'].unique()
        )
        
        # Filtro por etapa
        etapas = st.multiselect(
            "Etapas",
            options=df['Etapa'].unique(),
            default=df['Etapa'].unique()
        )
        
        # Aplicar filtros
        df_filtrado = df[
            (df['Empreendimento'].isin(empreendimentos)) &
            (df['Etapa'].isin(etapas))
        ]
    else:
        df_filtrado = df

with col2:
    st.subheader("Gráfico de Gantt com Barras Duplas")
    
    if not df_filtrado.empty:
        # Converter dados para formato do Gantt
        gantt_data, data_min, data_max = converter_dados_para_gantt(df_filtrado)
        
        # Calcular número de meses para o cabeçalho
        total_meses = ((data_max.year - data_min.year) * 12) + (data_max.month - data_min.month) + 1
        
        # Gerar um gráfico para cada empreendimento
        for project in gantt_data:
            st.markdown(f"### {project['name']}")
            
            # Calcular altura baseada no número de tarefas do projeto
            num_tasks = len(project['tasks'])
            altura_gantt = max(400, num_tasks * 50 + 150)
            
            # HTML e CSS do gráfico de Gantt para este empreendimento
            gantt_html = f"""
            <!DOCTYPE html>
            <html lang="pt-BR">
            <head>
                <meta charset="utf-8">
                <style>
                    * {{
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }}

                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background-color: #f5f5f5;
                        color: #333;
                    }}

                    .gantt-container {{
                        width: 100%;
                        background-color: white;
                        border-radius: 8px;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                        overflow: hidden;
                        margin-bottom: 20px;
                    }}

                    .gantt-main {{
                        display: flex;
                        height: {altura_gantt}px;
                        position: relative;
                    }}

                    /* Tabela lateral fixa - Estilo baseado na segunda imagem */
                    .gantt-sidebar {{
                        width: 360px;
                        background-color: #f8f9fa;
                        border-right: 2px solid #e2e8f0;
                        flex-shrink: 0;
                        overflow-y: auto;
                        z-index: 10;
                    }}

                    .sidebar-header {{
                        background: linear-gradient(135deg, #4a5568, #2d3748);
                        color: white;
                        padding: 15px;
                        font-weight: 600;
                        border-bottom: 1px solid #e2e8f0;
                        position: sticky;
                        top: 0;
                        z-index: 11;
                        height: 80px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 14px;
                    }}

                    .sidebar-row {{
                        padding: 8px 15px;
                        border-bottom: 1px solid #e2e8f0;
                        background-color: white;
                        transition: background-color 0.2s ease;
                        height: 50px;
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                    }}

                    .sidebar-row:hover {{
                        background-color: #f1f5f9;
                    }}

                    .sidebar-row:nth-child(even) {{
                        background-color: #f8f9fa;
                    }}

                    .sidebar-row:nth-child(even):hover {{
                        background-color: #e2e8f0;
                    }}

                    .row-left {{
                        flex: 1;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                    }}

                    .row-title {{
                        font-weight: 600;
                        color: #2d3748;
                        font-size: 14px;
                        margin-bottom: 2px;
                    }}

                    .row-desc {{
                        font-size: 10px;
                        color: #718096;
                    }}

                    .row-dates {{
                        font-size: 9px;
                        color: #4a5568;
                        line-height: 1.2;
                    }}

                    /* Status box - baseado na segunda imagem */
                    .row-status {{
                        width: 80px;
                        height: 35px;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        border-radius: 4px;
                        font-size: 10px;
                        font-weight: 600;
                        margin-left: 10px;
                    }}

                    .status-complete {{
                        background-color: #fecaca;
                        color: #991b1b;
                    }}

                    .status-progress {{
                        background-color: #fed7aa;
                        color: #9a3412;
                    }}

                    .status-pending {{
                        background-color: #e0e7ff;
                        color: #3730a3;
                    }}

                    .status-percentage {{
                        font-size: 12px;
                        font-weight: 700;
                    }}

                    .status-variation {{
                        font-size: 8px;
                        margin-top: 1px;
                    }}

                    /* Área do gráfico com rolagem horizontal e vertical */
                    .gantt-chart {{
                        flex: 1;
                        overflow: auto;
                        position: relative;
                        background-color: white;
                    }}

                    .chart-container {{
                        position: relative;
                        min-width: {total_meses * 40}px;
                        height: 100%;
                    }}

                    .chart-header {{
                        background: linear-gradient(135deg, #4a5568, #2d3748);
                        color: white;
                        height: 80px;
                        position: sticky;
                        top: 0;
                        z-index: 9;
                        display: flex;
                        flex-direction: column;
                    }}

                    .year-header {{
                        height: 40px;
                        display: flex;
                        align-items: center;
                        border-bottom: 1px solid rgba(255,255,255,0.2);
                    }}

                    .year-section {{
                        text-align: center;
                        font-weight: 600;
                        font-size: 14px;
                        border-right: 1px solid rgba(255,255,255,0.2);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        background: rgba(255,255,255,0.1);
                        height: 100%;
                    }}

                    .month-header {{
                        height: 40px;
                        display: flex;
                        align-items: center;
                    }}

                    .month-cell {{
                        width: 40px;
                        height: 40px;
                        border-right: 1px solid rgba(255,255,255,0.2);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 11px;
                        font-weight: 500;
                        background: rgba(255,255,255,0.05);
                    }}

                    .chart-body {{
                        position: relative;
                        background: 
                            repeating-linear-gradient(
                                90deg,
                                transparent,
                                transparent 39px,
                                #e2e8f0 39px,
                                #e2e8f0 40px
                            );
                        min-height: calc(100% - 80px);
                    }}

                    .chart-row {{
                        height: 50px;
                        border-bottom: 1px solid #e2e8f0;
                        position: relative;
                        background-color: white;
                    }}

                    .chart-row:nth-child(even) {{
                        background-color: #f8f9fa;
                    }}

                    /* Barras do Gantt - Estilo com barras duplas */
                    .gantt-bar {{
                        position: absolute;
                        height: 18px;
                        border-radius: 4px;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        opacity: 0.85;
                        border: 1px solid rgba(255,255,255,0.3);
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}

                    .gantt-bar-previsto {{
                        top: 8px;
                        border: 2px solid rgba(0,0,0,0.2);
                    }}

                    .gantt-bar-real {{
                        top: 28px;
                        border: 2px solid rgba(0,0,0,0.4);
                    }}

                    .gantt-bar:hover {{
                        opacity: 1;
                        transform: translateY(-1px);
                        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                    }}

                    .gantt-bar-label {{
                        color: white;
                        font-size: 9px;
                        font-weight: 500;
                        padding: 1px 4px;
                        white-space: nowrap;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        text-shadow: 0 1px 2px rgba(0,0,0,0.3);
                        line-height: 14px;
                    }}

                    /* Cores baseadas na imagem modelo - tons pastéis */
                    .bar-color-1 {{ background: linear-gradient(135deg, #d8b4fe, #c084fc); }}
                    .bar-color-2 {{ background: linear-gradient(135deg, #fed7aa, #fdba74); }}
                    .bar-color-3 {{ background: linear-gradient(135deg, #bfdbfe, #93c5fd); }}
                    .bar-color-4 {{ background: linear-gradient(135deg, #fde68a, #fcd34d); }}
                    .bar-color-5 {{ background: linear-gradient(135deg, #bbf7d0, #86efac); }}
                    .bar-color-6 {{ background: linear-gradient(135deg, #fecaca, #fca5a5); }}
                    .bar-color-7 {{ background: linear-gradient(135deg, #e0e7ff, #c7d2fe); }}
                    .bar-color-8 {{ background: linear-gradient(135deg, #fef3c7, #fde047); }}

                    /* Tooltip */
                    .tooltip {{
                        position: absolute;
                        background-color: #2d3748;
                        color: white;
                        padding: 8px 12px;
                        border-radius: 6px;
                        font-size: 11px;
                        z-index: 1000;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                        pointer-events: none;
                        opacity: 0;
                        transition: opacity 0.2s ease;
                        max-width: 250px;
                    }}

                    .tooltip.show {{
                        opacity: 1;
                    }}

                    /* Linha do dia atual */
                    .today-line {{
                        position: absolute;
                        top: 80px;
                        bottom: 0;
                        width: 2px;
                        background-color: #e53e3e;
                        z-index: 5;
                        box-shadow: 0 0 6px rgba(229, 62, 62, 0.6);
                    }}
                </style>
            </head>
            <body>
                <div class="gantt-container">
                    <div class="gantt-main">
                        <!-- Tabela lateral fixa -->
                        <div class="gantt-sidebar">
                            <div class="sidebar-header">
                                {project['name']}
                            </div>
                            <div id="sidebar-content-{project['id']}">
                                <!-- Conteúdo será preenchido via JavaScript -->
                            </div>
                        </div>
                        
                        <!-- Área do gráfico -->
                        <div class="gantt-chart">
                            <div class="chart-container">
                                <!-- Cabeçalho do gráfico -->
                                <div class="chart-header">
                                    <div class="year-header" id="year-header-{project['id']}">
                                        <!-- Anos serão preenchidos via JavaScript -->
                                    </div>
                                    <div class="month-header" id="month-header-{project['id']}">
                                        <!-- Meses serão preenchidos via JavaScript -->
                                    </div>
                                </div>
                                
                                <!-- Corpo do gráfico -->
                                <div class="chart-body" id="chart-body-{project['id']}">
                                    <!-- Linhas serão preenchidas via JavaScript -->
                                </div>
                                
                                <!-- Linha do dia atual -->
                                <div class="today-line" id="today-line-{project['id']}"></div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Tooltip -->
                <div class="tooltip" id="tooltip-{project['id']}"></div>
                
                <script>
                    // Dados do Gantt para este projeto
                    const projectData_{project['id']} = {json.dumps([project])};
                    const dataMin_{project['id']} = new Date('{data_min.strftime('%Y-%m-%d')}');
                    const dataMax_{project['id']} = new Date('{data_max.strftime('%Y-%m-%d')}');
                    const totalMeses_{project['id']} = {total_meses};
                    
                    function initGantt_{project['id']}() {{
                        renderSidebar_{project['id']}();
                        renderHeader_{project['id']}();
                        renderChart_{project['id']}();
                        setupEventListeners_{project['id']}();
                        positionTodayLine_{project['id']}();
                    }}
                    
                    function renderSidebar_{project['id']}() {{
                        const sidebarContent = document.getElementById('sidebar-content-{project['id']}');
                        let html = '';
                        
                        projectData_{project['id']}[0].tasks.forEach(task => {{
                            // Determinar status baseado no progresso
                            let statusClass = 'status-pending';
                            let statusText = '0%';
                            let variationText = '';
                            
                            if (task.progress === 100) {{
                                statusClass = 'status-complete';
                                statusText = '100%';
                                if (task.vt !== 0 || task.vd !== 0) {{
                                    variationText = `VT: ${{task.vt > 0 ? '+' : ''}}${{task.vt}}d<br>VD: ${{task.vd > 0 ? '+' : ''}}${{task.vd}}d`;
                                }}
                            }} else if (task.progress > 0) {{
                                statusClass = 'status-progress';
                                statusText = `${{task.progress}}%`;
                            }}
                            
                            // Formatação das datas conforme modelo da segunda imagem
                            let datesText = '';
                            if (task.inicio_real && task.termino_real) {{
                                const duracaoReal = task.duracao_real || 0;
                                datesText = `Prev: ${{task.inicio_previsto}} → ${{task.termino_previsto}} - (${{task.duracao_prevista}}d)<br>Real: ${{task.inicio_real}} → ${{task.termino_real}} - (${{duracaoReal}}d)`;
                            }} else {{
                                datesText = `Prev: ${{task.inicio_previsto}} → ${{task.termino_previsto}} - (${{task.duracao_prevista}}d)`;
                            }}
                            
                            html += `
                                <div class="sidebar-row">
                                    <div class="row-left">
                                        <div class="row-title">${{task.name}}</div>
                                        <div class="row-dates">${{datesText}}</div>
                                    </div>
                                    <div class="row-status ${{statusClass}}">
                                        <div class="status-percentage">${{statusText}}</div>
                                        <div class="status-variation">${{variationText}}</div>
                                    </div>
                                </div>
                            `;
                        }});
                        
                        sidebarContent.innerHTML = html;
                    }}
                    
                    function renderHeader_{project['id']}() {{
                        const yearHeader = document.getElementById('year-header-{project['id']}');
                        const monthHeader = document.getElementById('month-header-{project['id']}');
                        
                        let yearHtml = '';
                        let monthHtml = '';
                        
                        const startYear = dataMin_{project['id']}.getFullYear();
                        const endYear = dataMax_{project['id']}.getFullYear();
                        
                        // Gerar cabeçalho de anos
                        let currentDate = new Date(dataMin_{project['id']});
                        let yearSections = [];
                        
                        while (currentDate <= dataMax_{project['id']}) {{
                            const year = currentDate.getFullYear();
                            let monthCount = 0;
                            
                            // Contar meses deste ano no período
                            while (currentDate <= dataMax_{project['id']} && currentDate.getFullYear() === year) {{
                                monthCount++;
                                currentDate.setMonth(currentDate.getMonth() + 1);
                            }}
                            
                            yearSections.push({{ year, width: monthCount * 40 }});
                        }}
                        
                        yearSections.forEach(section => {{
                            yearHtml += `<div class="year-section" style="width: ${{section.width}}px">${{section.year}}</div>`;
                        }});
                        
                        // Gerar cabeçalho de meses
                        currentDate = new Date(dataMin_{project['id']});
                        const monthNames = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
                        
                        while (currentDate <= dataMax_{project['id']}) {{
                            const month = currentDate.getMonth();
                            monthHtml += `<div class="month-cell">${{monthNames[month]}}</div>`;
                            currentDate.setMonth(currentDate.getMonth() + 1);
                        }}
                        
                        yearHeader.innerHTML = yearHtml;
                        monthHeader.innerHTML = monthHtml;
                    }}
                    
                    function renderChart_{project['id']}() {{
                        const chartBody = document.getElementById('chart-body-{project['id']}');
                        let html = '';
                        
                        projectData_{project['id']}[0].tasks.forEach(task => {{
                            html += `<div class="chart-row" data-task-id="${{task.id}}"></div>`;
                        }});
                        
                        chartBody.innerHTML = html;
                        
                        // Renderizar barras após um pequeno delay para garantir que o DOM esteja pronto
                        setTimeout(() => {{
                            renderBars_{project['id']}();
                        }}, 100);
                    }}
                    
                    function renderBars_{project['id']}() {{
                        projectData_{project['id']}[0].tasks.forEach(task => {{
                            const row = document.querySelector(`[data-task-id="${{task.id}}"]`);
                            if (row) {{
                                // Criar barra prevista
                                const barPrevisto = createBar_{project['id']}(task, 'previsto');
                                row.appendChild(barPrevisto);
                                
                                // Criar barra real se existir
                                if (task.start_real && task.end_real) {{
                                    const barReal = createBar_{project['id']}(task, 'real');
                                    row.appendChild(barReal);
                                }}
                            }}
                        }});
                    }}
                    
                    function createBar_{project['id']}(task, tipo) {{
                        const startDate = tipo === 'previsto' ? new Date(task.start_previsto) : new Date(task.start_real);
                        const endDate = tipo === 'previsto' ? new Date(task.end_previsto) : new Date(task.end_real);
                        
                        // Calcular a diferença em dias desde dataMin
                        const daysFromStart = Math.floor((startDate - dataMin_{project['id']}) / (1000 * 60 * 60 * 24));
                        
                        // Calcular a duração em dias
                        const durationDays = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24)) + 1;
                        
                        // Converter para pixels (cada mês = 40px, cada dia = 40/30 ≈ 1.33px)
                        const startOffset = (daysFromStart / 30) * 40;
                        const width = (durationDays / 30) * 40;
                        
                        const bar = document.createElement('div');
                        bar.className = `gantt-bar gantt-bar-${{tipo}} bar-color-${{task.color}}`;
                        bar.style.left = `${{startOffset}}px`;
                        bar.style.width = `${{Math.max(8, width)}}px`; // Mínimo de 8px para barras muito curtas
                        bar.setAttribute('data-task', JSON.stringify(task));
                        bar.setAttribute('data-tipo', tipo);
                        
                        const label = document.createElement('div');
                        label.className = 'gantt-bar-label';
                        label.textContent = tipo === 'previsto' ? task.name : `${{task.name}} (R)`;
                        bar.appendChild(label);
                        
                        return bar;
                    }}
                    
                    function setupEventListeners_{project['id']}() {{
                        // Tooltip
                        document.addEventListener('mouseover', (e) => {{
                            if (e.target.closest('.gantt-bar') && e.target.closest('#chart-body-{project['id']}')) {{
                                showTooltip_{project['id']}(e, e.target.closest('.gantt-bar'));
                            }}
                        }});
                        
                        document.addEventListener('mouseout', (e) => {{
                            if (e.target.closest('.gantt-bar') && e.target.closest('#chart-body-{project['id']}')) {{
                                hideTooltip_{project['id']}();
                            }}
                        }});
                        
                        // Sincronização de scroll vertical entre sidebar e chart
                        const sidebar = document.querySelector('#sidebar-content-{project['id']}').parentElement;
                        const chartArea = document.querySelector('#chart-body-{project['id']}').parentElement.parentElement;
                        
                        if (sidebar && chartArea) {{
                            let isScrolling = false;
                            
                            sidebar.addEventListener('scroll', () => {{
                                if (!isScrolling) {{
                                    isScrolling = true;
                                    chartArea.scrollTop = sidebar.scrollTop;
                                    setTimeout(() => {{ isScrolling = false; }}, 10);
                                }}
                            }});
                            
                            chartArea.addEventListener('scroll', () => {{
                                if (!isScrolling) {{
                                    isScrolling = true;
                                    sidebar.scrollTop = chartArea.scrollTop;
                                    setTimeout(() => {{ isScrolling = false; }}, 10);
                                }}
                            }});
                        }}
                    }}
                    
                    function showTooltip_{project['id']}(event, bar) {{
                        const tooltip = document.getElementById('tooltip-{project['id']}');
                        const taskData = JSON.parse(bar.getAttribute('data-task'));
                        const tipo = bar.getAttribute('data-tipo');
                        
                        let tooltipContent = `
                            <strong>${{taskData.name}} (${{tipo === 'previsto' ? 'Previsto' : 'Real'}})</strong><br>
                            Empreendimento: ${{taskData.empreendimento}}<br>
                        `;
                        
                        if (tipo === 'previsto') {{
                            tooltipContent += `
                                Início Previsto: ${{taskData.inicio_previsto}}<br>
                                Término Previsto: ${{taskData.termino_previsto}}<br>
                                Duração: ${{taskData.duracao_prevista}} dias
                            `;
                        }} else {{
                            tooltipContent += `
                                Início Real: ${{taskData.inicio_real}}<br>
                                Término Real: ${{taskData.termino_real}}<br>
                                Duração: ${{taskData.duracao_real}} dias
                            `;
                            
                            if (taskData.vt !== 0) {{
                                tooltipContent += `<br>Variação Tempo: ${{taskData.vt > 0 ? '+' : ''}}${{taskData.vt}} dias`;
                            }}
                            
                            if (taskData.vd !== 0) {{
                                tooltipContent += `<br>Variação Duração: ${{taskData.vd > 0 ? '+' : ''}}${{taskData.vd}} dias`;
                            }}
                        }}
                        
                        tooltipContent += `<br>Progresso: ${{taskData.progress}}%`;
                        
                        tooltip.innerHTML = tooltipContent;
                        
                        tooltip.style.left = `${{event.pageX + 10}}px`;
                        tooltip.style.top = `${{event.pageY - 10}}px`;
                        tooltip.classList.add('show');
                    }}
                    
                    function hideTooltip_{project['id']}() {{
                        const tooltip = document.getElementById('tooltip-{project['id']}');
                        tooltip.classList.remove('show');
                    }}
                    
                    function positionTodayLine_{project['id']}() {{
                        const today = new Date();
                        const todayLine = document.getElementById('today-line-{project['id']}');
                        
                        if (today >= dataMin_{project['id']} && today <= dataMax_{project['id']}) {{
                            const daysFromStart = Math.floor((today - dataMin_{project['id']}) / (1000 * 60 * 60 * 24));
                            const offset = (daysFromStart / 30) * 40;
                            todayLine.style.left = `${{offset}}px`;
                            todayLine.style.display = 'block';
                        }} else {{
                            todayLine.style.display = 'none';
                        }}
                    }}
                    
                    // Inicializar quando a página carregar
                    document.addEventListener('DOMContentLoaded', initGantt_{project['id']});
                    
                    // Fallback para garantir inicialização
                    if (document.readyState === 'loading') {{
                        document.addEventListener('DOMContentLoaded', initGantt_{project['id']});
                    }} else {{
                        initGantt_{project['id']}();
                    }}
                </script>
            </body>
            </html>
            """
            
            # Renderizar o componente HTML para este empreendimento
            components.html(gantt_html, height=altura_gantt, scrolling=True)
            
            # Informações do empreendimento
            st.info(f"📊 {project['name']}: {len(project['tasks'])} tarefas | Período: {data_min.strftime('%d/%m/%Y')} - {data_max.strftime('%d/%m/%Y')}")
            
            # Estatísticas do empreendimento
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Tarefas", len(project['tasks']))
            with col2:
                concluidas = len([t for t in project['tasks'] if t['progress'] == 100])
                st.metric("Concluídas", concluidas)
            with col3:
                em_andamento = len([t for t in project['tasks'] if 0 < t['progress'] < 100])
                st.metric("Em Andamento", em_andamento)
            with col4:
                com_dados_reais = len([t for t in project['tasks'] if t['inicio_real'] and t['termino_real']])
                st.metric("Com Dados Reais", com_dados_reais)
            
            st.markdown("---")
    
    else:
        st.warning("Nenhum dado disponível para exibir o gráfico de Gantt.")
        st.info("💡 Marque 'Usar dados de exemplo' ou faça upload de um arquivo CSV com as colunas: Empreendimento, Etapa, Inicio_Prevista, Termino_Prevista, Inicio_Real, Termino_Real, % concluído")

# Instruções de uso
with st.expander("ℹ️ Como usar"):
    st.markdown("""
    ### Funcionalidades do Gráfico de Gantt com Barras Duplas:
    
    **🎯 Características principais:**
    - **Barras duplas**: Uma barra para dados previstos e outra para dados reais
    - **Cabeçalho dinâmico**: Datas ajustadas automaticamente ao período dos dados
    - **Alinhamento perfeito**: Barras alinhadas com as datas correspondentes
    - **Gráfico por empreendimento**: Cada empreendimento tem seu próprio gráfico
    - **Cabeçalho personalizado**: Nome do empreendimento no cabeçalho da tabela lateral
    - **Altura uniformizada**: Cabeçalho e linhas com altura padronizada
    - **Rolagem sincronizada**: Vertical entre tabela e gráfico
    - **Informações detalhadas**: Datas previstas, reais e variações (VT/VD)
    - **Status visual**: Cores baseadas no progresso
    - **Tooltips informativos**: Detalhes específicos para cada tipo de barra
    - **Linha do dia atual**: Indicador visual da data atual
    
    **📊 Como usar:**
    1. Use os dados de exemplo ou faça upload de um arquivo CSV
    2. Aplique filtros por empreendimento e etapa
    3. Cada empreendimento será exibido em um gráfico separado
    4. **Barra superior**: Dados previstos
    5. **Barra inferior**: Dados reais (quando disponíveis)
    6. Use a rolagem horizontal para navegar no tempo
    7. Use a rolagem vertical para ver todas as tarefas (sincronizada)
    8. Passe o mouse sobre as barras para ver detalhes específicos
    
    **📁 Formato do arquivo CSV:**
    - `Empreendimento`: Nome do projeto
    - `Etapa`: Fase do projeto (ex: PROSPEC, LEGVENDA, CONTRATAÇÃO, etc.)
    - `Inicio_Prevista`: Data de início prevista (formato: YYYY-MM-DD)
    - `Termino_Prevista`: Data de término prevista (formato: YYYY-MM-DD)
    - `Inicio_Real`: Data de início real (formato: YYYY-MM-DD) - opcional
    - `Termino_Real`: Data de término real (formato: YYYY-MM-DD) - opcional
    - `% concluído`: Percentual de conclusão (0-100)
    
    **🎨 Melhorias implementadas:**
    - **Barras duplas**: Visualização clara de previsto vs real
    - **Cabeçalho dinâmico**: Anos e meses ajustados ao período dos dados
    - **Alinhamento de datas**: Barras posicionadas corretamente nas datas
    - **Tooltips específicos**: Informações diferentes para cada tipo de barra
    - **Cálculo automático**: Período de datas calculado automaticamente
    - **Estatísticas expandidas**: Incluindo contagem de tarefas com dados reais
    """)

# Rodapé
st.markdown("---")
st.markdown("**📊 Gráfico de Gantt com Barras Duplas** - Desenvolvido com Streamlit")
