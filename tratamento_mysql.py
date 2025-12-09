import pandas as pd
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import numpy as np

def buscar_dados_mysql():
    """
    Busca dados do banco MySQL AWS e retorna em formato DataFrame
    """
    try:
        # Configuração do banco (usar secrets do Streamlit)
        import streamlit as st
        DB_CONFIG = {
            'host': st.secrets["aws_db"]["host"],
            'user': st.secrets["aws_db"]["user"],
            'password': st.secrets["aws_db"]["password"],
            'database': st.secrets["aws_db"]["database"],
            'port': 3306
        }
        
        conn = mysql.connector.connect(**DB_CONFIG)
        
        # Consulta principal para dados das etapas
        query = """
        SELECT 
            e.nome as Empreendimento,
            t.nome as Etapa,
            t.data_inicio_prevista as Inicio_Prevista,
            t.data_termino_prevista as Termino_Prevista,
            t.data_inicio_real as Inicio_Real,
            t.data_termino_real as Termino_Real,
            t.percentual_concluido as `% concluído`,
            s.nome as SETOR,
            g.nome as GRUPO,
            e.ugb as UGB
        FROM tarefas t
        JOIN empreendimentos e ON t.empreendimento_id = e.id
        JOIN setores s ON t.setor_id = s.id
        JOIN grupos g ON t.grupo_id = g.id
        WHERE t.ativo = 1
        ORDER BY e.nome, t.ordem
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Processamento das datas
        date_columns = ['Inicio_Prevista', 'Termino_Prevista', 'Inicio_Real', 'Termino_Real']
        for col in date_columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
        
        return df
        
    except Exception as e:
        print(f"Erro ao buscar dados do MySQL: {e}")
        return pd.DataFrame()

def buscar_baselines_mysql():
    """
    Busca todas as baselines do banco de dados
    """
    try:
        import streamlit as st
        DB_CONFIG = {
            'host': st.secrets["aws_db"]["host"],
            'user': st.secrets["aws_db"]["user"],
            'password': st.secrets["aws_db"]["password"],
            'database': st.secrets["aws_db"]["database"],
            'port': 3306
        }
        
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT empreendimento, version_name, baseline_data, created_date, tipo_visualizacao 
        FROM gantt_baselines 
        ORDER BY created_at DESC
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        baselines = {}
        for row in results:
            empreendimento = row['empreendimento']
            version_name = row['version_name']
            
            if empreendimento not in baselines:
                baselines[empreendimento] = {}
            
            try:
                import json
                baseline_data = json.loads(row['baseline_data'])
                baselines[empreendimento][version_name] = {
                    "date": row['created_date'],
                    "data": baseline_data,
                    "tipo_visualizacao": row['tipo_visualizacao']
                }
            except:
                continue
        
        cursor.close()
        conn.close()
        
        return baselines
        
    except Exception as e:
        print(f"Erro ao buscar baselines do MySQL: {e}")
        return {}