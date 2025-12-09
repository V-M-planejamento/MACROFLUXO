"""
Script para limpar completamente os dados de login do Streamlit
Execute este script quando quiser forçar o popup de login a aparecer novamente
"""
import os
import streamlit as st

# Limpar session state
if 'user_email' in st.session_state:
    del st.session_state['user_email']
    print("✅ user_email removido do session_state")

if 'user_name' in st.session_state:
    del st.session_state['user_name']
    print("✅ user_name removido do session_state")

# Limpar arquivo JSON
config_file = '.streamlit_user_config.json'
if os.path.exists(config_file):
    os.remove(config_file)
    print(f"✅ Arquivo {config_file} deletado")
else:
    print(f"⚠️ Arquivo {config_file} não existe")

# Limpar query params
st.query_params.clear()
print("✅ Query params limpos")

print("\n🎯 Login limpo com sucesso! Recarregue a página para ver o popup.")
