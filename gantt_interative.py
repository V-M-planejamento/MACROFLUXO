import streamlit as st
import streamlit.components.v1 as components
import json

# Configuração da página
st.set_page_config(
    page_title="Gantt com Linhas de Grade",
    page_icon="📊",
    layout="wide"
)

# Título da aplicação
st.title("📊 Gantt com Linhas de Grade Verticais")
st.markdown("---")

# Dados
gantt_data = [
    {"id": "p1", "name": "PROSPECÇÃO", "percent_concluido": 100, "inicio_previsto": "/Date(1725159600000)/", "termino_previsto": "/Date(1725937200000)/", "inicio_real": "/Date(1725159600000)/", "termino_real": "/Date(1725764400000)/"},
    {"id": "p2", "name": "LEGALIZAÇÃO", "percent_concluido": 100, "inicio_previsto": "/Date(1725505200000)/", "termino_previsto": "/Date(1726369200000)/", "inicio_real": "/Date(1725591600000)/", "termino_real": "/Date(1726282800000)/"},
    {"id": "p3", "name": "PULMÃO VENDA", "percent_concluido": 0, "inicio_previsto": "/Date(1728836400000)/", "termino_previsto": "/Date(1731207600000)/", "inicio_real": "/Date(1728922800000)/", "termino_real": None},
    {"id": "p4", "name": "PROJETO 2025", "percent_concluido": 0, "inicio_previsto": "/Date(1735700400000)/", "termino_previsto": "/Date(1743447600000)/", "inicio_real": None, "termino_real": None},
    {"id": "p5", "name": "FASE FINAL 2025", "percent_concluido": 0, "inicio_previsto": "/Date(1753998000000)/", "termino_previsto": "/Date(1761956400000)/", "inicio_real": None, "termino_real": None},
    {"id": "p6", "name": "PLANEJAMENTO 2026", "percent_concluido": 0, "inicio_previsto": "/Date(1767226800000)/", "termino_previsto": "/Date(1774983600000)/", "inicio_real": None, "termino_real": None},
    {"id": "p7", "name": "EXECUÇÃO 2026", "percent_concluido": 0, "inicio_previsto": "/Date(1775070000000)/", "termino_previsto": "/Date(1782846000000)/", "inicio_real": None, "termino_real": None},
]

gantt_data_json = json.dumps(gantt_data)

# CSS (removido o background do CSS para ser aplicado via JS)
gantt_css = """
body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }

.gantt-container {
    display: grid;
    grid-template-columns: 320px 1fr;
    height: 500px;
    overflow: auto;
    border: 1px solid #ddd;
    border-radius: 4px;
}

.fn-gantt-header, .fn-gantt-timeline {
    position: sticky;
    top: 0;
    z-index: 10;
    background-color: #f8f9fa;
    height: 60px;
    border-bottom: 1px solid #ddd;
}
.fn-gantt-header { grid-column: 1; grid-row: 1; border-right: 1px solid #ddd; }
.fn-gantt-timeline { grid-column: 2; grid-row: 1; }

.fn-gantt-rows { grid-column: 1; grid-row: 2; border-right: 1px solid #ddd; }
.fn-gantt-bars { grid-column: 2; grid-row: 2; position: relative; }

.fn-gantt-rows ul, .fn-gantt-bars ul { list-style: none; margin: 0; padding: 0; }
.fn-gantt-rows li, .fn-gantt-bars li {
    height: 60px;
    border-bottom: 1px solid #e0e0e0;
    box-sizing: border-box;
    position: relative;
}
.fn-gantt-rows li { padding: 5px 8px; }
.fn-gantt-rows li:nth-child(odd) { background-color: #f7f7f7; }
.fn-gantt-rows li:nth-child(even) { background-color: #fff; }

/* --- ÁREA DAS BARRAS COM FUNDO DINÂMICO PARA AS LINHAS --- */
.fn-gantt-bars ul {
    background-color: #fff; /* Cor de fundo base */
}

.fn-gantt-row-content { display: flex; justify-content: space-between; align-items: center; height: 100%; }
.task-info { flex-grow: 1; }
.task-status { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 60px; flex-shrink: 0; }
.fn-gantt-label strong { font-weight: bold; color: #333; font-size: 12px; }
.fn-gantt-dates { font-family: monospace; font-size: 10px; color: #555; line-height: 1.3; margin-top: 2px; }
.fn-gantt-percent { width: 50px; height: 24px; border: 1px solid #ccc; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 11px; background-color: #fef9e2; color: #a38408; margin-bottom: 3px; }
.percent-completed { background-color: #e6f5eb !important; color: #2eaf5b !important; border-color: #b7d4c2 !important; }
.percent-delayed { background-color: #fae6e6 !important; color: #c30202 !important; border-color: #e6b3b3 !important; }
.fn-gantt-variation { font-size: 10px; font-weight: bold; text-align: center; }
.variation-green { color: #0b803c; } .variation-red { color: #c30202; } .variation-gray { color: #666; }

.fn-gantt-timeline-header { display: flex; height: 100%; font-weight: bold; color: #495057; }
.timeline-month-vertical { flex-shrink: 0; border-right: 1px solid #e0e0e0; white-space: nowrap; display: flex; justify-content: center; align-items: flex-end; padding-bottom: 5px; }
.timeline-month-vertical > span { font-size: 11px; transform: rotate(-90deg); transform-origin: center; margin-bottom: 10px; }

.fn-gantt-bar { position: absolute; height: 16px; border-radius: 4px; cursor: pointer; z-index: 5; border: 1px solid rgba(0,0,0,0.15); }
.ganttPrevisto { background-color: #a8c5da; top: 10px; }
.ganttReal { background-color: #174c66; top: 32px; }

.options { margin-top: 20px; text-align: center; }
.options button { padding: 8px 16px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; }
"""

# HTML com a lógica JS para criar as linhas de grade
html_code = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <title>Gantt com Linhas de Grade</title>
    <style>{gantt_css}</style>
</head>
<body>
    <div class="gantt-container">
        <div class="fn-gantt-header"></div>
        <div class="fn-gantt-timeline"></div>
        <div class="fn-gantt-rows"><ul></ul></div>
        <div class="fn-gantt-bars"><ul></ul></div>
    </div>
    <div class="options">
        <button class="zoomOut">🔍➖ Zoom Out</button>
        <button class="zoomIn">🔍➕ Zoom In</button>
    </div>

    <script src="https://code.jquery.com/jquery-1.11.0.min.js"></script>
    <script>
    (function($  ) {{
        "use strict";
        
        const parseMsDate = ms => ms ? new Date(parseInt(ms.match(/\d+/)[0])) : null;
        const umDia = 86400000;

        function calcularDiasCorridos(inicio, fim) {{
            if (!inicio || !fim) return null;
            const i = new Date(inicio.getFullYear(), inicio.getMonth(), inicio.getDate());
            const f = new Date(fim.getFullYear(), fim.getMonth(), fim.getDate());
            return Math.round((f - i) / umDia) + 1;
        }}

        $.fn.gantt = function(options) {{
            const $container = this;
            const data = options.source;
            let viewStart, viewEnd;
            let dayWidth = 5; // Largura inicial de cada dia

            function initialize() {{
                const allDates = data.flatMap(d => [parseMsDate(d.inicio_previsto), parseMsDate(d.termino_previsto), parseMsDate(d.inicio_real), parseMsDate(d.termino_real)]).filter(Boolean);
                const minDate = allDates.length > 0 ? new Date(Math.min.apply(null, allDates)) : new Date();
                const maxDate = allDates.length > 0 ? new Date(Math.max.apply(null, allDates)) : new Date();
                
                viewStart = new Date(minDate.getFullYear(), minDate.getMonth(), 1);
                viewEnd = new Date(maxDate.getFullYear(), maxDate.getMonth() + 2, 0);
                renderGantt();
            }}
            
            function renderGantt() {{
                const $leftUl = $container.find('.fn-gantt-rows ul').empty();
                const $rightUl = $container.find(".fn-gantt-bars ul").empty();
                const $timeline = $container.find(".fn-gantt-timeline").empty();
                
                const $timelineHeader = $('<div class="fn-gantt-timeline-header"></div>');
                let totalWidth = 0;
                let monthMap = {{}};

                for (let d = new Date(viewStart); d <= viewEnd; d.setDate(d.getDate() + 1)) {{
                    const monthKey = `${{d.getFullYear()}}-${{d.getMonth()}}`;
                    if (!monthMap[monthKey]) monthMap[monthKey] = 0;
                    monthMap[monthKey]++;
                }}

                Object.keys(monthMap).forEach(key => {{
                    const [year, month] = key.split('-');
                    const monthStr = `${{('0'+(parseInt(month)+1)).slice(-2)}}/${{year.slice(-2)}}`;
                    const monthWidth = monthMap[key] * dayWidth;
                    $timelineHeader.append(`<div class="timeline-month-vertical" style="width: ${{monthWidth}}px"><span>${{monthStr}}</span></div>`);
                    totalWidth += monthWidth;
                }});

                $timeline.append($timelineHeader);
                $container.find('.fn-gantt-bars').css('width', totalWidth + 'px');

                // *** ADICIONA AS LINHAS DE GRADE VERTICAIS VIA JAVASCRIPT ***
                const gridLineColor = '#f0f0f0';
                $rightUl.css({{
                    'background-image': `repeating-linear-gradient(to right, transparent 0, transparent ${{dayWidth - 1}}px, ${{gridLineColor}} ${{dayWidth - 1}}px, ${{gridLineColor}} ${{dayWidth}}px)`,
                    'background-size': `${{dayWidth}}px 100%`
                }});

                data.forEach(item => {{
                    const inicioP = parseMsDate(item.inicio_previsto), terminoP = parseMsDate(item.termino_previsto);
                    const inicioR = parseMsDate(item.inicio_real), terminoR = parseMsDate(item.termino_real);
                    const diasP = calcularDiasCorridos(inicioP, terminoP), diasR = calcularDiasCorridos(inicioR, terminoR);
                    const textoP = `Prev: ${{formatDate(inicioP)}} - ${{formatDate(terminoP)}} (${{diasP ? diasP + 'd' : ''}})`, textoR = `Real: ${{formatDate(inicioR)}} - ${{formatDate(terminoR)}} (${{diasR ? diasR + 'd' : ''}})`;
                    const variacao = calcularVariacao(terminoR, terminoP);
                    const classePercent = item.percent_concluido === 100 ? (terminoR && terminoP && terminoR <= terminoP ? 'percent-completed' : 'percent-delayed') : '';
                    
                    const rowHtml = `<li><div class="fn-gantt-row-content"><div class="task-info"><div class="fn-gantt-label"><strong>${{item.name}}</strong></div><div class="fn-gantt-dates"><div>${{textoP}}</div><div>${{textoR}}</div></div></div><div class="task-status"><div class="fn-gantt-percent ${{classePercent}}">${{item.percent_concluido}}%</div><div class="fn-gantt-variation ${{variacao.classeCSS}}">${{variacao.texto}}</div></div></div></li>`;
                    $leftUl.append(rowHtml);
                    
                    const $barRow = $('<li></li>');
                    if (inicioP) {{
                        const start = ((inicioP - viewStart) / umDia) * dayWidth;
                        const width = (diasP || 1) * dayWidth;
                        $barRow.append(`<div class="fn-gantt-bar ganttPrevisto" style="left: ${{start}}px; width: ${{width}}px;"></div>`);
                    }}
                    if (inicioR) {{
                        const start = ((inicioR - viewStart) / umDia) * dayWidth;
                        const width = (calcularDiasCorridos(inicioR, terminoR || new Date()) || 1) * dayWidth;
                        $barRow.append(`<div class="fn-gantt-bar ganttReal" style="left: ${{start}}px; width: ${{width}}px;"></div>`);
                    }}
                    $rightUl.append($barRow);
                }});
            }}
            
            const formatDate = d => d ? `${{('0'+d.getDate()).slice(-2)}}/${{('0'+(d.getMonth()+1)).slice(-2)}}/${{String(d.getFullYear()).slice(-2)}}` : 'N/D';
            
            function calcularVariacao(real, previsto) {{
                if (!real || !previsto) return {{ texto: 'V: -', classeCSS: 'variation-gray' }};
                const diff = Math.round((real - previsto) / umDia);
                if (diff < 0) return {{ texto: `V: ${{diff}}d`, classeCSS: 'variation-green' }};
                if (diff > 0) return {{ texto: `V: +${{diff}}d`, classeCSS: 'variation-red' }};
                return {{ texto: 'V: 0d', classeCSS: 'variation-gray' }};
            }}

            initialize();

            $('.zoomIn').on('click', () => {{ dayWidth = Math.min(50, dayWidth + 2); renderGantt(); }});
            $('.zoomOut').on('click', () => {{ dayWidth = Math.max(5, dayWidth - 2); renderGantt(); }});
        }};
    }}(jQuery));

    $(document).ready(() => {{ $(".gantt-container").gantt({{ source: {gantt_data_json} }}); }});
    </script>
</body>
</html>
"""

# Renderizar o componente HTML no Streamlit
components.html(html_code, height=550, scrolling=False)
