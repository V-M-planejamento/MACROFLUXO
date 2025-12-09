import re

with open('popup.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Corrigir linha problemática
old_line = r"{'\u003cdiv class=\"error-message\"\u003e' + login_error + '\u003c/div\u003e' if login_error else ''}"
new_line = '""" + (f\'<div class="error-message">{login_error}</div>\' if login_error else "") + """'

content = content.replace(old_line, new_line)

with open('popup.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Arquivo corrigido com sucesso!")
