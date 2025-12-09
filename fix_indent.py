#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para corrigir indentacao do bloco tab3 no app.py
"""

import re

# Ler o arquivo
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Encontrar inicio do bloco tab3 (linha ~6176) e corrigir indentação
# Todo código dentro de "with tab3:" deve ter 12 espaços de indentação

in_tab3_block = False
fixed_lines = []

for i, line in enumerate(lines):
    # Detectar início do bloco tab3
    if 'if tab3 is not None:' in line or 'with tab3:' in line:
        in_tab3_block = True
        fixed_lines.append(line)
        continue
    
    # Detectar fim do bloco tab3 (próxima função no nível global ou fim de arquivo)
    if in_tab3_block and (line.startswith('def ') or line.startswith('if __name__')):
        in_tab3_block = False
    
    # Corrigir indentação dentro do bloco tab3
    if in_tab3_block and line.strip():
        # Contar espaços atuais
        current_indent = len(line) - len(line.lstrip())
        
        # Se tem 8 espaços (segunda indentação do with), adicionar 4 para ter 12
        if current_indent == 8:
            line =  '    ' + line
        # Se tem menos que 12 espaços, ajustar para 12
        elif current_indent < 12 and not line.strip().startswith('#'):
            line = (' ' * 12) + line.lstrip()
    
    fixed_lines.append(line)

# Escrever arquivo corrigido
with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print("Indentação corrigida com sucesso!")
