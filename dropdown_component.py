import streamlit as st

def simple_multiselect_dropdown(label, options, key, default_selected=None):
    """
    Componente simples de multiselect dropdown usando st.multiselect
    """
    if default_selected is None:
        default_selected = []
    
    return st.multiselect(label, options, default=default_selected, key=key)

