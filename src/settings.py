import os
from services.safebox import Safebox
ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) 

ARQUIVOS_TEMPORARIOS = os.path.join(ROOT_DIR, "arquivos_temporarios") 

#garante que o diretorio de download exista.
if not os.path.exists(ARQUIVOS_TEMPORARIOS):
    os.makedirs(ARQUIVOS_TEMPORARIOS)

COURIERS = {
    "remessa_express": {
            "id" : 1,
            "dias_anterior": 8,
            "enviar_para": "xxxxxxxx@xxxxxxx.com.br",
            "subject": "Email de teste remessa_express",
            "body": "Anexo arquivo RemessaExpress"
        },
        "flash":{
            "id" : 2,
            "dias_anterior": 60,
            "enviar_para": "xxxxxx@xxxxx.com.br",
            "subject": "Email de Teste flash",
            "body": "Anexo arquivo Flash"
        },
        "total_express":{
            "id": 2,
            "dias_anterior": 3,
            "enviar_para": "xxxxxx@xxxxxxx.com.br",
            "subject" : "Anexo arquivo TotalExpress",
            "body": "Anexo arquivo Flash"
        }
    }


EMAIL = {
    "smtp_server" : "mail.xxxxxxxx.com.br",
    "password" : "xxxxxxxxx",
    "sender_email" : "xxxxxx@xxxxxxx.com.br"
}

#para usar safebox em algum lugar de cima basta colocar:
# Safebox.get_secret("chave")
