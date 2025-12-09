import streamlit as st
import base64
import os
from datetime import datetime
import pytz

def show_welcome_screen():
    """
    Popup de login - pede apenas email do usuário
    """
    
    # Processar login do formulário
    if 'popup_email' in st.query_params:
        email = st.query_params['popup_email']
        
        if email and '@' in email:
            # Salvar email no session_state
            st.session_state.user_email = email
            
            # Limpar params e recarregar
            st.query_params.clear()
            st.rerun()
    
    # Se já tem email no session_state, não mostra popup
    if 'user_email' in st.session_state and st.session_state.user_email:
        return
    
    # Carregar background SVG
    def load_svg_as_base64():
        svg_path = 'Frame (10).svg'
        if os.path.exists(svg_path):
            try:
                with open(svg_path, 'rb') as f:
                    return base64.b64encode(f.read()).decode('utf-8')
            except:
                return ""
        return ""
    
    # Carregar logo
    def load_logo_as_base64():
        # Tentar carregar o SVG primeiro
        logo_paths = ['logoNova 1.svg', 'logoNova.svg', 'logoNova.png']
        for logo_path in logo_paths:
            if os.path.exists(logo_path):
                try:
                    with open(logo_path, 'rb') as f:
                        logo_data = base64.b64encode(f.read()).decode('utf-8')
                        if logo_path.endswith('.svg'):
                            return f"data:image/svg+xml;base64,{logo_data}"
                        else:
                            return f"data:image/png;base64,{logo_data}"
                except:
                    continue
        return ""
    
    svg_base64 = load_svg_as_base64()
    logo_base64 = load_logo_as_base64()
    bg_style = f"background-image: url('data:image/svg+xml;base64,{svg_base64}');" if svg_base64 else "background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);"
    
    
    # Data do último reboot do SERVIDOR Streamlit com horário de Brasília
    # Usa arquivo de timestamp que persiste entre TODAS as sessões
    timestamp_file = '.app_start_timestamp'
    brasilia_tz = pytz.timezone('America/Sao_Paulo')
    
    # Se o arquivo não existe, o servidor acabou de iniciar
    if not os.path.exists(timestamp_file):
        # Captura timestamp do reboot do servidor
        app_start_time = datetime.now(brasilia_tz)
        # Salva em arquivo para persistir entre sessões
        with open(timestamp_file, 'w') as f:
            f.write(app_start_time.isoformat())
    else:
        # Lê o timestamp do arquivo (quando o servidor foi iniciado)
        try:
            with open(timestamp_file, 'r') as f:
                timestamp_str = f.read().strip()
                app_start_time = datetime.fromisoformat(timestamp_str)
        except:
            # Se houver erro ao ler, recria o arquivo
            app_start_time = datetime.now(brasilia_tz)
            with open(timestamp_file, 'w') as f:
                f.write(app_start_time.isoformat())
    
    # Formata a data/hora do reboot do servidor para exibição
    last_update = app_start_time.strftime("%d/%m/%Y às %H:%M:%S")
    
    # CSS e HTML do popup
    popup_html = f"""
    <style>
        /* Esconder conteúdo principal do Streamlit */
        .main > div:not(.block-container) {{
            display: none !important;
        }}
        .block-container {{
            padding: 0 !important;
        }}
        header, .stToolbar, .stDeployButton {{
            display: none !important;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: scale(0.95); }}
            to {{ opacity: 1; transform: scale(1); }}
        }}
        
        .popup-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            {bg_style}
            background-size: cover;
            background-position: center;
            z-index: 999999;
        }}
        
        .last-update-badge {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(255, 255, 255, 0.95);
            padding: 12px 20px;
            border-radius: 25px;
            font-size: 0.85em;
            color: #666;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 1000001;
            font-weight: 500;
        }}
        
        .last-update-badge strong {{
            color: #333;
        }}
        
        .popup-container {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            display: flex;
            justify-content: flex-end;
            align-items: center;
            z-index: 1000000;
            padding: 40px;
            padding-right: 280px;
        }}
        
        .popup-card {{
            background: linear-gradient(to bottom, #ffffff 0%, #fafafa 100%);
            border-radius: 20px;
            box-shadow: 0 30px 80px rgba(0, 0, 0, 0.2), 0 0 1px rgba(0, 0, 0, 0.1);
            max-width: 480px;
            width: 100%;
            animation: fadeIn 0.5s ease-out;
            border: 1px solid rgba(255, 255, 255, 0.8);
        }}
        
        .popup-header {{
            padding: 50px 45px 30px;
            text-align: center;
            background: linear-gradient(to bottom, rgba(255, 255, 255, 0.5), transparent);
            border-radius: 20px 20px 0 0;
        }}
        
        .logo-container {{
            margin-bottom: 30px;
            display: flex;
            justify-content: center;
            align-items: center;
            filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
            width: 100%;
            max-width: 400px;
            margin-left: auto;
            margin-right: auto;
        }}
        
        .logo-container img {{
            max-width: 100px;
            width: 100px;
            height: auto;
            transition: transform 0.3s ease;
            transform: scale(1);
        }}
        
        .popup-header h2 {{
            margin: 0 0 15px 0;
            color: #1a252f;
            font-size: 1.75em;
            font-weight: 700;
            letter-spacing: -0.5px;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        }}
        
        .popup-header p {{
            margin: 0;
            color: #6c757d;
            font-size: 0.92em;
            line-height: 1.6;
            max-width: 380px;
            margin-left: auto;
            margin-right: auto;
        }}
        
        .popup-body {{
            padding: 10px 45px 50px;
        }}
        
        .input-group {{
            margin-bottom: 25px;
        }}
        
        .popup-input {{
            width: 100%;
            padding: 18px 20px;
            font-size: 1em;
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            background: #ffffff;
            color: #2c3e50;
            outline: none;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
        }}
        
        .popup-input::placeholder {{
            color: #95a5a6;
        }}
        
        .popup-input:focus {{
            border-color: #ff8c00;
            background: #ffffff;
            box-shadow: 0 0 0 4px rgba(255, 140, 0, 0.12), 0 4px 12px rgba(255, 140, 0, 0.15);
            transform: translateY(-1px);
        }}
        
        .popup-button {{
            width: 100%;
            padding: 20px;
            font-size: 1.05em;
            font-weight: 700;
            color: white;
            background: linear-gradient(135deg, #ff8c00 0%, #ff7700 100%);
            border: none;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 15px;
            box-shadow: 0 6px 20px rgba(255, 140, 0, 0.3);
            position: relative;
            overflow: hidden;
        }}
        
        .popup-button:hover {{
            background: linear-gradient(135deg, #ff7700 0%, #ff6600 100%);
            transform: translateY(-3px);
            box-shadow: 0 12px 35px rgba(255, 140, 0, 0.45);
        }}
        
        .popup-button:active {{
            transform: translateY(0);
        }}
        
        @media (max-width: 480px) {{
            .popup-container {{
                justify-content: center;
                padding: 20px;
            }}
            .popup-card {{
                margin: 15px;
            }}
            .popup-header {{
                padding: 30px 25px 20px;
            }}
            .popup-body {{
                padding: 0 25px 30px;
            }}
            .last-update-badge {{
                top: 10px;
                right: 10px;
                font-size: 0.75em;
                padding: 8px 14px;
            }}
        }}
    </style>
    
    <div class="popup-overlay"></div>
    <div class="last-update-badge">
        <strong>Última atualização:</strong> {last_update}
    </div>
    <div class="popup-container">
        <div class="popup-card">
            <div class="popup-header">
                <div class="logo-container">
                    {('<img src="' + logo_base64 + '" alt="Logo Viana e Moura" />') if logo_base64 else ''}
                </div>
                <h2>Bem-vindo ao Painel Macrofluxo</h2>
                <p>Por favor, informe seu e-mail para acessar o Painel de acompanhamento das etapas do Macrofluxo da Viana & Moura Construções.</p>
            </div>
            <div class="popup-body">
                <form method="get">
                    <div class="input-group">
                        <input type="email" name="popup_email" placeholder="Email corporativo" class="popup-input" required />
                    </div>
                    <button type="submit" class="popup-button">Acessar Painel</button>
                </form>
            </div>
        </div>
    </div>
    """
    
    st.markdown(popup_html, unsafe_allow_html=True)
    st.stop()
