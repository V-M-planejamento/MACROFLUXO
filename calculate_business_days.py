import pandas as pd
import numpy as np

def calculate_business_days(start_date, end_date):
    """
    Calcula o número de dias úteis entre duas datas
    """
    if pd.isna(start_date) or pd.isna(end_date):
        return np.nan
    
    try:
        # Converter para datetime se necessário
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        
        # Calcular dias úteis
        business_days = np.busday_count(start_date.date(), end_date.date())
        return business_days
    except:
        return np.nan

