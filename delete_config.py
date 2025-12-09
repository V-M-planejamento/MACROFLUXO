"""
Script temporário para identificar e deletar o arquivo .streamlit_user_config.json
Execute com: streamlit run delete_config.py
"""
import streamlit as st
import os

st.title("🗑️ Deletar Configuração de Login")

config_file = '.streamlit_user_config.json'

st.write(f"**Diretório atual:** `{os.getcwd()}`")

if os.path.exists(config_file):
    st.error(f"❌ Arquivo `{config_file}` EXISTE!")
    
    try:
        with open(config_file, 'r') as f:
            import json
            content = json.load(f)
        st.json(content)
        
        if st.button("🗑️ DELETAR ARQUIVO", type="primary"):
            os.remove(config_file)
            st.success("✅ Arquivo deletado com sucesso!")
            st.info("Agora feche esta aba e acesse o app principal novamente")
            st.balloons()
    except Exception as e:
        st.error(f"Erro ao ler arquivo: {e}")
else:
    st.success(f"✅ Arquivo `{config_file}` NÃO existe")
    st.info("O popup deve aparecer normalmente no app principal")

st.divider()
st.write("**Todos os arquivos no diretório:**")
files = [f for f in os.listdir('.') if not f.startswith('__')]
for f in files:
    st.text(f"  - {f}")
