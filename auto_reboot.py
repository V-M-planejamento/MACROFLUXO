# auto_reboot.py
# Módulo para reiniciar automaticamente o Streamlit a cada 3 horas

import streamlit as st
from datetime import datetime, timedelta
import pytz
import os
import sys

# Configuração
REBOOT_INTERVAL_HOURS = 3
TIMESTAMP_FILE = '.app_start_timestamp'

def check_and_reboot():
    """
    Verifica se passou o tempo de reboot e reinicia o app se necessário.
    Chame esta função no início do seu app.py
    """
    brasilia_tz = pytz.timezone('America/Sao_Paulo')
    
    # Verificar se arquivo de timestamp existe
    if not os.path.exists(TIMESTAMP_FILE):
        # Primeira execução - criar timestamp
        current_time = datetime.now(brasilia_tz)
        with open(TIMESTAMP_FILE, 'w') as f:
            f.write(current_time.isoformat())
        return False  # Não precisa reboot, acabou de iniciar
    
    # Ler timestamp do arquivo
    try:
        with open(TIMESTAMP_FILE, 'r') as f:
            timestamp_str = f.read().strip()
            start_time = datetime.fromisoformat(timestamp_str)
    except Exception as e:
        # Se houver erro, recria o timestamp
        current_time = datetime.now(brasilia_tz)
        with open(TIMESTAMP_FILE, 'w') as f:
            f.write(current_time.isoformat())
        return False
    
    # Verificar tempo decorrido
    current_time = datetime.now(brasilia_tz)
    
    # Garantir que ambos os datetimes têm timezone info
    if start_time.tzinfo is None:
        start_time = brasilia_tz.localize(start_time)
    
    elapsed = current_time - start_time
    elapsed_hours = elapsed.total_seconds() / 3600
    
    # Debug info (opcional)
    if 'last_reboot_check' not in st.session_state:
        st.session_state.last_reboot_check = current_time
        print(f"[AUTO-REBOOT] App iniciou às: {start_time.strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"[AUTO-REBOOT] Tempo decorrido: {elapsed_hours:.2f} horas")
        print(f"[AUTO-REBOOT] Próximo reboot em: {REBOOT_INTERVAL_HOURS - elapsed_hours:.2f} horas")
    
    # Se passou o tempo de reboot
    if elapsed_hours >= REBOOT_INTERVAL_HOURS:
        print(f"[AUTO-REBOOT] {elapsed_hours:.2f} horas decorridas. Iniciando reboot...")
        
        # Deletar timestamp para criar novo no próximo boot
        try:
            os.remove(TIMESTAMP_FILE)
            print(f"[AUTO-REBOOT] Timestamp deletado. Reboot em andamento...")
        except:
            pass
        
        # Limpar cache do Streamlit
        st.cache_data.clear()
        st.cache_resource.clear()
        
        # Limpar session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        # Mostrar mensagem e reiniciar
        st.warning("⏰ Reinicialização automática em andamento...")
        st.info(f"O servidor estava ativo por {elapsed_hours:.1f} horas. Fazendo reboot...")
        
        # Forçar rerun (reiniciar a execução)
        st.rerun()
    
    return False


def get_uptime_info():
    """
    Retorna informações sobre o uptime atual do servidor.
    Útil para exibir ao usuário.
    """
    if not os.path.exists(TIMESTAMP_FILE):
        return {
            'started_at': None,
            'uptime_hours': 0,
            'next_reboot_in_hours': REBOOT_INTERVAL_HOURS
        }
    
    try:
        brasilia_tz = pytz.timezone('America/Sao_Paulo')
        
        with open(TIMESTAMP_FILE, 'r') as f:
            timestamp_str = f.read().strip()
            start_time = datetime.fromisoformat(timestamp_str)
        
        if start_time.tzinfo is None:
            start_time = brasilia_tz.localize(start_time)
        
        current_time = datetime.now(brasilia_tz)
        elapsed = current_time - start_time
        elapsed_hours = elapsed.total_seconds() / 3600
        next_reboot_hours = REBOOT_INTERVAL_HOURS - elapsed_hours
        
        return {
            'started_at': start_time,
            'uptime_hours': elapsed_hours,
            'next_reboot_in_hours': max(0, next_reboot_hours),
            'uptime_str': format_uptime(elapsed)
        }
    except:
        return {
            'started_at': None,
            'uptime_hours': 0,
            'next_reboot_in_hours': REBOOT_INTERVAL_HOURS
        }


def format_uptime(delta):
    """Formata timedelta em string legível"""
    hours = int(delta.total_seconds() // 3600)
    minutes = int((delta.total_seconds() % 3600) // 60)
    
    if hours > 0:
        return f"{hours}h {minutes}min"
    else:
        return f"{minutes}min"


def show_uptime_badge():
    """
    Mostra um badge com informações de uptime.
    Chame no sidebar ou onde preferir.
    """
    info = get_uptime_info()
    
    if info['started_at']:
        st.sidebar.markdown("---")
        st.sidebar.caption("⏱️ **Uptime do Servidor**")
        st.sidebar.caption(f"Ativo há: **{info['uptime_str']}**")
        st.sidebar.caption(f"Próximo reboot: **{info['next_reboot_in_hours']:.1f}h**")
        
        # Barra de progresso
        progress = min(1.0, info['uptime_hours'] / REBOOT_INTERVAL_HOURS)
        st.sidebar.progress(progress)
