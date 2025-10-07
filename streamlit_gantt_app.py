import streamlit as st
import streamlit.components.v1 as components
import json
import datetime

# Configuração da página
st.set_page_config(
    page_title="jQuery Gantt Chart Melhorado",
    page_icon="📊",
    layout="wide"
)

# Título da aplicação
st.title("📊 jQuery Gantt Chart Melhorado")
st.markdown("---")

# Dados de exemplo para o gráfico Gantt (mais próximos do repositório original)
gantt_data = [
    {
        "id": "p1", 
        "name": "Desenvolvimento Frontend", 
        "desc": "Desenvolvimento da interface do usuário", 
        "values": [
            {"id": "t1", "from": "/Date(1704067200000)/", "to": "/Date(1704326400000)/", "desc": "Criação dos componentes base", "label": "Componentes UI", "customClass": "ganttRed"},
            {"id": "t2", "from": "/Date(1704326400000)/", "to": "/Date(1704585600000)/", "desc": "Implementação da responsividade", "label": "Design Responsivo", "customClass": "ganttGreen"},
            {"id": "t3", "from": "/Date(1704585600000)/", "to": "/Date(1704844800000)/", "desc": "Testes de usabilidade", "label": "Testes UX", "customClass": "ganttBlue"}
        ]
    },
    {
        "id": "p2", 
        "name": "Desenvolvimento Backend", 
        "desc": "Desenvolvimento da API e banco de dados", 
        "values": [
            {"id": "t4", "from": "/Date(1704067200000)/", "to": "/Date(1704412800000)/", "desc": "Configuração do servidor", "label": "Setup Servidor", "customClass": "ganttOrange"},
            {"id": "t5", "from": "/Date(1704412800000)/", "to": "/Date(1704758400000)/", "desc": "Desenvolvimento das APIs", "label": "APIs REST", "customClass": "ganttPurple"},
            {"id": "t6", "from": "/Date(1704758400000)/", "to": "/Date(1705104000000)/", "desc": "Integração com banco de dados", "label": "Banco de Dados", "customClass": "ganttTeal"}
        ]
    },
    {
        "id": "p3", 
        "name": "Testes e Deploy", 
        "desc": "Testes finais e implantação", 
        "values": [
            {"id": "t7", "from": "/Date(1705104000000)/", "to": "/Date(1705363200000)/", "desc": "Testes de integração", "label": "Testes Integração", "customClass": "ganttYellow"},
            {"id": "t8", "from": "/Date(1705363200000)/", "to": "/Date(1705622400000)/", "desc": "Deploy em produção", "label": "Deploy Produção", "customClass": "ganttGreen"},
            {"id": "t9", "from": "/Date(1705622400000)/", "to": "/Date(1705708800000)/", "desc": "Monitoramento pós-deploy", "label": "Monitoramento", "customClass": "ganttBlue"}
        ]
    }
]

# Converter dados para JSON
gantt_data_json = json.dumps(gantt_data)

# CSS melhorado baseado no repositório original
gantt_css = """
/* Estilos baseados no repositório original jQuery.Gantt */
.gantt-container {
    width: 100%;
    margin: 20px auto;
    border: 1px solid #ddd;
    background-color: #fff;
    font-family: Helvetica, Arial, sans-serif;
    font-size: 12px;
    border-radius: 4px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.fn-gantt {
    position: relative;
    overflow: hidden;
    border: 1px solid #ddd;
    background-color: #fff;
    border-radius: 4px;
}

.fn-gantt-header {
    background: linear-gradient(to bottom, #f8f9fa, #e9ecef);
    border-bottom: 1px solid #ddd;
    padding: 15px;
    text-align: center;
    font-weight: bold;
    color: #495057;
}

.fn-gantt-data {
    position: relative;
    overflow: hidden;
    min-height: 400px;
}

.fn-gantt-leftpanel {
    position: absolute;
    left: 0;
    top: 0;
    width: 280px;
    background-color: #f8f9fa;
    border-right: 2px solid #dee2e6;
    overflow: hidden;
    z-index: 2;
}

.fn-gantt-rightpanel {
    margin-left: 280px;
    position: relative;
    overflow-x: auto;
    overflow-y: hidden;
    background-color: #fff;
}

.fn-gantt-rows ul {
    list-style: none;
    margin: 0;
    padding: 0;
}

.fn-gantt-rows li {
    border-bottom: 1px solid #e9ecef;
    padding: 12px 15px;
    height: 50px;
    line-height: 26px;
    background-color: #f8f9fa;
    transition: background-color 0.2s ease;
}

.fn-gantt-rows li:hover {
    background-color: #e9ecef;
}

.fn-gantt-label strong {
    font-weight: bold;
    display: block;
    color: #212529;
    font-size: 13px;
}

.fn-gantt-desc {
    color: #6c757d;
    font-size: 11px;
    margin-top: 2px;
}

.fn-gantt-bars ul {
    list-style: none;
    margin: 0;
    padding: 0;
    position: relative;
    background: repeating-linear-gradient(
        90deg,
        transparent,
        transparent 29px,
        #f1f3f4 29px,
        #f1f3f4 30px
    );
}

.fn-gantt-bars li {
    height: 50px;
    border-bottom: 1px solid #e9ecef;
    position: relative;
}

.fn-gantt-bar {
    position: absolute;
    top: 10px;
    height: 30px;
    border-radius: 6px;
    cursor: pointer;
    z-index: 10;
    transition: all 0.3s ease;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    border: 1px solid rgba(255,255,255,0.2);
}

.fn-gantt-bar:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}

.fn-gantt-barlabel {
    color: #fff;
    font-size: 11px;
    font-weight: bold;
    padding: 8px 10px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 14px;
    text-shadow: 0 1px 2px rgba(0,0,0,0.3);
}

.fn-gantt-lines ul {
    list-style: none;
    margin: 0;
    padding: 0;
}

.fn-gantt-lines li {
    height: 50px;
    border-bottom: 1px solid #e9ecef;
}

/* Cores melhoradas baseadas no repositório original */
.ganttRed {
    background: linear-gradient(135deg, #dc3545, #c82333) !important;
    border-color: #bd2130 !important;
}

.ganttGreen {
    background: linear-gradient(135deg, #28a745, #218838) !important;
    border-color: #1e7e34 !important;
}

.ganttBlue {
    background: linear-gradient(135deg, #007bff, #0056b3) !important;
    border-color: #004085 !important;
}

.ganttOrange {
    background: linear-gradient(135deg, #fd7e14, #e55a00) !important;
    border-color: #d04800 !important;
}

.ganttPurple {
    background: linear-gradient(135deg, #6f42c1, #5a2d91) !important;
    border-color: #4c1d95 !important;
}

.ganttTeal {
    background: linear-gradient(135deg, #20c997, #17a085) !important;
    border-color: #138f75 !important;
}

.ganttYellow {
    background: linear-gradient(135deg, #ffc107, #e0a800) !important;
    border-color: #d39e00 !important;
    color: #212529 !important;
}

.ganttYellow .fn-gantt-barlabel {
    color: #212529 !important;
    text-shadow: none !important;
}

/* Controles de navegação melhorados */
.options {
    margin: 20px 0;
    text-align: center;
    padding: 15px;
    background-color: #f8f9fa;
    border-radius: 4px;
    border: 1px solid #dee2e6;
}

.options ul {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 8px;
}

.options li {
    display: inline-block;
}

.options button {
    padding: 8px 16px;
    background: linear-gradient(135deg, #007bff, #0056b3);
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
    font-weight: 500;
    transition: all 0.2s ease;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.options button:hover {
    background: linear-gradient(135deg, #0056b3, #004085);
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}

.options button:active {
    transform: translateY(0);
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Indicador de hoje */
.today-line {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 2px;
    background-color: #dc3545;
    z-index: 15;
    box-shadow: 0 0 4px rgba(220, 53, 69, 0.5);
}

/* Tooltip melhorado */
.gantt-tooltip {
    position: absolute;
    background-color: #212529;
    color: white;
    padding: 8px 12px;
    border-radius: 4px;
    font-size: 11px;
    z-index: 1000;
    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.2s ease;
}

.gantt-tooltip.show {
    opacity: 1;
}

/* Eixo de datas melhorado */
.fn-gantt-timeline {
    background-color: #f8f9fa;
    border-bottom: 2px solid #dee2e6;
    height: 40px;
    position: relative;
    overflow: hidden;
}

.fn-gantt-timeline-header {
    display: flex;
    height: 100%;
    align-items: center;
    font-size: 11px;
    font-weight: bold;
    color: #495057;
}

.timeline-date {
    flex: 1;
    text-align: center;
    border-right: 1px solid #dee2e6;
    padding: 0 5px;
}

/* Bootstrap 3.x re-reset */
.fn-gantt *,
.fn-gantt *:after,
.fn-gantt *:before {
    -webkit-box-sizing: content-box;
    -moz-box-sizing: content-box;
    box-sizing: content-box;
}

/* Responsividade */
@media (max-width: 768px) {
    .fn-gantt-leftpanel {
        width: 200px;
    }
    
    .fn-gantt-rightpanel {
        margin-left: 200px;
    }
    
    .options ul {
        flex-direction: column;
        align-items: center;
    }
    
    .options button {
        width: 150px;
        margin: 2px 0;
    }
}
"""

# HTML melhorado com funcionalidades do repositório original
html_code = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=Edge;chrome=1">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>jQuery Gantt Chart Melhorado</title>
    <style>
        {gantt_css}
    </style>
</head>
<body>
    <div class="gantt-container">
        <div class="gantt"></div>
    </div>
    
    <div class="options">
        <ul>
            <li><button class="setToday">📅 Hoje</button></li>
            <li><button class="zoomOut">🔍➖ Zoom Out</button></li>
            <li><button class="zoomIn">🔍➕ Zoom In</button></li>
            <li><button class="prevWeek">⬅️ Sem. Anterior</button></li>
            <li><button class="nextWeek">➡️ Próx. Semana</button></li>
            <li><button class="prevDay">⬅️ Dia Anterior</button></li>
            <li><button class="nextDay">➡️ Próx. Dia</button></li>
            <li><button class="prevMonth">⬅️ Mês Anterior</button></li>
            <li><button class="nextMonth">➡️ Próx. Mês</button></li>
            <li><button class="clear">🗑️ Limpar</button></li>
        </ul>
    </div>

    <script src="https://code.jquery.com/jquery-1.11.0.min.js"></script>
    <script>
        // jQuery Gantt Plugin melhorado baseado no repositório original
        (function($) {{
            "use strict";
            
            $.fn.gantt = function(options) {{
                var settings = $.extend({{
                    source: [],
                    navigate: "buttons",
                    scale: "days",
                    maxScale: "months",
                    minScale: "hours",
                    itemsPerPage: 10,
                    onItemClick: function(data) {{ return; }},
                    onAddClick: function(dt, rowId) {{ return; }},
                    onRender: function() {{ return; }}
                }}, options);
                
                var $element = this;
                var data = settings.source;
                var currentDate = new Date();
                var viewStart = new Date();
                var viewEnd = new Date();
                
                // Limpar conteúdo existente
                $element.empty();
                
                // Criar estrutura melhorada
                var $ganttContainer = $('<div class="fn-gantt"></div>');
                var $header = $('<div class="fn-gantt-header"><h3>📊 Gráfico de Gantt Interativo</h3></div>');
                var $dataPanel = $('<div class="fn-gantt-data"></div>');
                var $leftPanel = $('<div class="fn-gantt-leftpanel"><div class="fn-gantt-rows"><ul></ul></div></div>');
                var $rightPanel = $('<div class="fn-gantt-rightpanel"><div class="fn-gantt-timeline"></div><div class="fn-gantt-bars"><ul></ul></div><div class="fn-gantt-lines"><ul></ul></div></div>');
                
                $dataPanel.append($leftPanel).append($rightPanel);
                $ganttContainer.append($header).append($dataPanel);
                $element.append($ganttContainer);
                
                // Criar tooltip
                var $tooltip = $('<div class="gantt-tooltip"></div>');
                $('body').append($tooltip);
                
                // Processar dados e encontrar datas
                var minDate = new Date();
                var maxDate = new Date();
                
                for (var i = 0; i < data.length; i++) {{
                    for (var j = 0; j < data[i].values.length; j++) {{
                        var fromStr = data[i].values[j].from.replace(/\/Date\\((\\d+)\\)\//, "$1");
                        var toStr = data[i].values[j].to.replace(/\/Date\\((\\d+)\\)\//, "$1");
                        var from = new Date(parseInt(fromStr));
                        var to = new Date(parseInt(toStr));
                        
                        if (i === 0 && j === 0) {{
                            minDate = new Date(from);
                            maxDate = new Date(to);
                        }} else {{
                            if (from < minDate) minDate = new Date(from);
                            if (to > maxDate) maxDate = new Date(to);
                        }}
                    }}
                }}
                
                // Adicionar margem às datas
                minDate.setDate(minDate.getDate() - 3);
                maxDate.setDate(maxDate.getDate() + 3);
                viewStart = new Date(minDate);
                viewEnd = new Date(maxDate);
                
                function renderGantt() {{
                    var totalDays = Math.ceil((viewEnd - viewStart) / (1000 * 60 * 60 * 24));
                    var dayWidth = 40; // pixels por dia (aumentado para melhor visualização)
                    var totalWidth = totalDays * dayWidth;
                    
                    // Limpar conteúdo anterior
                    $leftPanel.find('ul').empty();
                    $rightPanel.find('.fn-gantt-bars ul').empty();
                    $rightPanel.find('.fn-gantt-lines ul').empty();
                    $rightPanel.find('.fn-gantt-timeline').empty();
                    
                    // Criar timeline de datas
                    var $timeline = $('<div class="fn-gantt-timeline-header"></div>');
                    for (var d = new Date(viewStart); d <= viewEnd; d.setDate(d.getDate() + 1)) {{
                        var dateStr = (d.getDate() < 10 ? '0' : '') + d.getDate() + '/' + 
                                     ((d.getMonth() + 1) < 10 ? '0' : '') + (d.getMonth() + 1);
                        $timeline.append('<div class="timeline-date" style="width: ' + dayWidth + 'px;">' + dateStr + '</div>');
                    }}
                    $rightPanel.find('.fn-gantt-timeline').append($timeline);
                    
                    // Criar linhas e barras
                    var $rowsList = $leftPanel.find('ul');
                    var $barsList = $rightPanel.find('.fn-gantt-bars ul');
                    var $linesList = $rightPanel.find('.fn-gantt-lines ul');
                    
                    for (var i = 0; i < data.length; i++) {{
                        // Criar linha do projeto
                        var $row = $('<li><span class="fn-gantt-label"><strong>' + data[i].name + '</strong></span><span class="fn-gantt-desc">' + data[i].desc + '</span></li>');
                        $rowsList.append($row);
                        
                        // Criar container para barras
                        var $barContainer = $('<li></li>');
                        
                        // Criar barras para cada tarefa
                        for (var j = 0; j < data[i].values.length; j++) {{
                            var task = data[i].values[j];
                            var fromStr = task.from.replace(/\/Date\\((\\d+)\\)\//, "$1");
                            var toStr = task.to.replace(/\/Date\\((\\d+)\\)\//, "$1");
                            var from = new Date(parseInt(fromStr));
                            var to = new Date(parseInt(toStr));
                            
                            var startOffset = Math.floor((from - viewStart) / (1000 * 60 * 60 * 24)) * dayWidth;
                            var duration = Math.ceil((to - from) / (1000 * 60 * 60 * 24)) * dayWidth;
                            
                            if (startOffset >= 0 && startOffset < totalWidth) {{
                                var $bar = $('<div class="fn-gantt-bar ' + (task.customClass || '') + '"><span class="fn-gantt-barlabel">' + task.label + '</span></div>');
                                $bar.css({{
                                    'left': startOffset + 'px',
                                    'width': Math.max(duration, 30) + 'px'
                                }});
                                
                                // Adicionar eventos melhorados
                                $bar.click((function(taskData) {{
                                    return function() {{
                                        settings.onItemClick(taskData);
                                    }};
                                }})(task));
                                
                                // Tooltip melhorado
                                $bar.hover(
                                    function(e) {{
                                        var taskInfo = task.label + '<br>' + 
                                                     'Início: ' + from.toLocaleDateString('pt-BR') + '<br>' +
                                                     'Fim: ' + to.toLocaleDateString('pt-BR');
                                        if (task.desc) {{
                                            taskInfo += '<br>' + task.desc;
                                        }}
                                        $tooltip.html(taskInfo).addClass('show');
                                        $tooltip.css({{
                                            'left': e.pageX + 10 + 'px',
                                            'top': e.pageY - 10 + 'px'
                                        }});
                                    }},
                                    function() {{
                                        $tooltip.removeClass('show');
                                    }}
                                );
                                
                                $bar.mousemove(function(e) {{
                                    $tooltip.css({{
                                        'left': e.pageX + 10 + 'px',
                                        'top': e.pageY - 10 + 'px'
                                    }});
                                }});
                                
                                $barContainer.append($bar);
                            }}
                        }}
                        
                        $barsList.append($barContainer);
                        $linesList.append($('<li></li>'));
                    }}
                    
                    // Adicionar linha do "hoje"
                    var todayOffset = Math.floor((currentDate - viewStart) / (1000 * 60 * 60 * 24)) * dayWidth;
                    if (todayOffset >= 0 && todayOffset < totalWidth) {{
                        var $todayLine = $('<div class="today-line"></div>');
                        $todayLine.css('left', todayOffset + 'px');
                        $rightPanel.find('.fn-gantt-bars').append($todayLine);
                    }}
                    
                    // Definir largura do painel direito
                    $rightPanel.find('.fn-gantt-bars, .fn-gantt-lines, .fn-gantt-timeline').css('width', totalWidth + 'px');
                    
                    // Definir altura do painel de dados
                    var rowHeight = 50;
                    var totalHeight = data.length * rowHeight + 40; // +40 para o timeline
                    $dataPanel.css('height', Math.max(450, totalHeight) + 'px');
                }}
                
                // Funções de navegação melhoradas
                window.ganttNavigation = {{
                    setToday: function() {{
                        var today = new Date();
                        viewStart = new Date(today);
                        viewStart.setDate(viewStart.getDate() - 7);
                        viewEnd = new Date(today);
                        viewEnd.setDate(viewEnd.getDate() + 14);
                        renderGantt();
                    }},
                    zoomIn: function() {{
                        var center = new Date((viewStart.getTime() + viewEnd.getTime()) / 2);
                        var range = (viewEnd - viewStart) / 4;
                        viewStart = new Date(center.getTime() - range);
                        viewEnd = new Date(center.getTime() + range);
                        renderGantt();
                    }},
                    zoomOut: function() {{
                        var center = new Date((viewStart.getTime() + viewEnd.getTime()) / 2);
                        var range = (viewEnd - viewStart);
                        viewStart = new Date(center.getTime() - range);
                        viewEnd = new Date(center.getTime() + range);
                        renderGantt();
                    }},
                    moveView: function(days) {{
                        viewStart.setDate(viewStart.getDate() + days);
                        viewEnd.setDate(viewEnd.getDate() + days);
                        renderGantt();
                    }}
                }};
                
                // Renderização inicial
                renderGantt();
                settings.onRender();
                
                return this;
            }};
            
        }})(jQuery);
        
        // Inicializar o gráfico Gantt melhorado
        $(document).ready(function() {{
            var data = {gantt_data_json};
            
            $(".gantt").gantt({{
                source: data,
                navigate: "buttons",
                scale: "days",
                maxScale: "months",
                minScale: "hours",
                itemsPerPage: 10,
                onItemClick: function(data) {{
                    alert("📋 Tarefa: " + data.label + "\\n📅 ID: " + data.id + "\\n📝 Descrição: " + (data.desc || "Sem descrição"));
                }},
                onAddClick: function(dt, rowId) {{
                    alert("➕ Espaço vazio clicado\\n📅 Data: " + dt + "\\n📋 Linha: " + rowId);
                }},
                onRender: function() {{
                    console.log("✅ Gráfico de Gantt renderizado com sucesso");
                }}
            }});
            
            // Eventos dos botões melhorados
            $(".setToday").click(function() {{
                if (window.ganttNavigation) {{
                    window.ganttNavigation.setToday();
                }}
            }});
            
            $(".zoomOut").click(function() {{
                if (window.ganttNavigation) {{
                    window.ganttNavigation.zoomOut();
                }}
            }});
            
            $(".zoomIn").click(function() {{
                if (window.ganttNavigation) {{
                    window.ganttNavigation.zoomIn();
                }}
            }});
            
            $(".prevWeek").click(function() {{
                if (window.ganttNavigation) {{
                    window.ganttNavigation.moveView(-7);
                }}
            }});
            
            $(".nextWeek").click(function() {{
                if (window.ganttNavigation) {{
                    window.ganttNavigation.moveView(7);
                }}
            }});
            
            $(".prevDay").click(function() {{
                if (window.ganttNavigation) {{
                    window.ganttNavigation.moveView(-1);
                }}
            }});
            
            $(".nextDay").click(function() {{
                if (window.ganttNavigation) {{
                    window.ganttNavigation.moveView(1);
                }}
            }});
            
            $(".prevMonth").click(function() {{
                if (window.ganttNavigation) {{
                    window.ganttNavigation.moveView(-30);
                }}
            }});
            
            $(".nextMonth").click(function() {{
                if (window.ganttNavigation) {{
                    window.ganttNavigation.moveView(30);
                }}
            }});
            
            $(".clear").click(function() {{
                if (confirm("🗑️ Tem certeza que deseja limpar o gráfico?")) {{
                    $(".gantt").empty();
                    alert("✅ Gráfico limpo com sucesso!");
                }}
            }});
        }});
    </script>
</body>
</html>
"""

# Interface do Streamlit melhorada
st.markdown("### 📋 Funcionalidades Implementadas")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("""
    **🎨 Visual:**
    - Design moderno com gradientes
    - Cores vibrantes e consistentes
    - Tooltips informativos
    - Linha indicadora do "hoje"
    - Timeline de datas no topo
    """)

with col2:
    st.success("""
    **⚡ Funcionalidades:**
    - Navegação completa (zoom, dias, semanas, meses)
    - Clique nas barras para detalhes
    - Hover para informações rápidas
    - Botão "Hoje" funcional
    - Responsividade melhorada
    """)

with col3:
    st.warning("""
    **🔧 Tecnologias:**
    - jQuery 1.11.0
    - CSS3 com gradientes e animações
    - JavaScript ES5 compatível
    - Layout responsivo
    - Integração Streamlit otimizada
    """)

st.markdown("### 📊 Gráfico de Gantt Melhorado")

# Renderizar o componente HTML melhorado
components.html(html_code, height=700, scrolling=True)

# Seção de comparação
st.markdown("### 🔄 Comparação com o Repositório Original")

comparison_data = {
    "Funcionalidade": [
        "Navegação por botões",
        "Zoom In/Out",
        "Cores personalizadas",
        "Tooltips informativos", 
        "Linha do 'hoje'",
        "Timeline de datas",
        "Design responsivo",
        "Animações CSS",
        "Clique em barras",
        "Gradientes visuais"
    ],
    "Repositório Original": [
        "✅ Sim", "✅ Sim", "✅ Sim", "❌ Não", "❌ Não",
        "❌ Básico", "❌ Limitado", "❌ Não", "✅ Sim", "❌ Não"
    ],
    "Versão Melhorada": [
        "✅ Sim", "✅ Sim", "✅ Sim", "✅ Sim", "✅ Sim",
        "✅ Completo", "✅ Sim", "✅ Sim", "✅ Sim", "✅ Sim"
    ]
}

st.table(comparison_data)

# Exibir dados JSON melhorados
st.markdown("### 📄 Dados do Gráfico (JSON)")
with st.expander("Ver dados JSON melhorados"):
    st.json(gantt_data)

# Instruções de uso melhoradas
st.markdown("### 📖 Como Usar")
st.markdown("""
**🎯 Funcionalidades Principais:**

1. **📊 Visualização**: O gráfico mostra projetos e tarefas em uma linha temporal moderna com cores vibrantes
2. **🖱️ Interação**: Clique nas barras para ver detalhes completos das tarefas
3. **💡 Tooltips**: Passe o mouse sobre as barras para informações rápidas
4. **🧭 Navegação**: Use os botões para navegar por diferentes períodos:
   - 📅 **Hoje**: Centraliza a visualização na data atual
   - 🔍 **Zoom**: Aproxima ou afasta a visualização temporal
   - ⬅️➡️ **Navegação**: Move por dias, semanas ou meses
5. **🎨 Visual**: Cada tarefa tem cores específicas com gradientes e animações
6. **📱 Responsivo**: Funciona bem em dispositivos móveis e desktop
7. **📈 Timeline**: Eixo de datas no topo para melhor orientação temporal
8. **🔴 Indicador**: Linha vermelha mostra a data atual

**🚀 Melhorias Implementadas:**
- Design moderno baseado no repositório original
- Funcionalidades de navegação totalmente funcionais
- Tooltips informativos com detalhes das tarefas
- Animações suaves e efeitos visuais
- Layout responsivo para diferentes telas
- Cores e gradientes profissionais
""")

# Rodapé melhorado
st.markdown("---")
st.markdown("**🚀 Desenvolvido com Streamlit + jQuery.Gantt Melhorado | Baseado no repositório mbielanczuk/jQuery.Gantt**")

