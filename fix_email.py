# Script para corrigir logica de email na tab3
lines = open('app.py', 'r', encoding='utf-8').readlines()

# Linha 6261: adicionar user_name
lines.insert(6254, '                user_name = st.session_state.get("user_name", "")\n')

# Linha 6261: mudar caption
lines[6261] = '                    st.caption(f"Usuario: **{user_name}** ({user_email})")\n'

# Remover linhas 6262-6269 (else e configure_email_dialog)
del lines[6262:6270]

open('app.py', 'w', encoding='utf-8').writelines(lines)
print("Corrigido!")
