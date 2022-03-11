from services.db_sqlsrv import SQLServer
from services.pier import Pier
from jobs.getAddressPerson import get_address
from datetime import datetime, timedelta

from settings import ARQUIVOS_TEMPORARIOS, COURIERS
from services.email_sender import send_email

import csv
import os
import unidecode


class Endereco:

    def __init__(self, rua, cidade, bairro, estado, cep) -> None:
        self.rua = rua
        self.cidade = cidade
        self.bairro = bairro
        self.estado = estado
        self.cep = cep
        self._normalize()

    def _normalize(self):
        rua_aux = unidecode.unidecode(self.rua)
        cidade_aux = unidecode.unidecode(self.cidade)
        bairro_aux = unidecode.unidecode(self.bairro)
        estado_aux = unidecode.unidecode(self.estado)

        self.rua_normalized = ''.join(e for e in rua_aux if e.isalnum()).casefold()
        self.cidade_normalized = ''.join(e for e in cidade_aux if e.isalnum()).casefold()
        self.bairro_normalized = ''.join(e for e in bairro_aux if e.isalnum()).casefold()
        self.estado_normalized = ''.join(e for e in estado_aux if e.isalnum()).casefold()
        self.cep_normalized = ''.join(e for e in self.cep if e.isalnum()).casefold()
    def __eq__(self, other):
        return (
            self.rua_normalized == other.rua_normalized and
            self.bairro_normalized== other.bairro_normalized and
            self.cidade_normalized == other.cidade_normalized and
            self.estado_normalized== other.estado_normalized and
            self.cep_normalized== self.cep_normalized
        ) 

    def __str__(self) -> str:
         return f"""Endereco (
Rua: {self.rua} 
Bairro: {self.bairro_normalized}
Cidade: {self.cidade}
Estado: {self.estado}
CEP: {self.cep})"""


def atualizar_enderecos(db_rastreamento_cartoes, courier_id, days_before_now, receiver_email, filename, subject, body):
    
    db_cursor = db_rastreamento_cartoes.connect()

    pier = Pier()

    days_before_now = -(days_before_now)
    
    cmd = """
      SELECT objetos.id
        ,objetos.data_postagem
        ,objetos.data_baixa
        ,objetos.id_externo
        ,objetos.id_conta
        ,objetos.flg_devolvido
        ,objetos.data_atualizacao
      ,enderecos.id
      ,enderecos.rua
      ,enderecos.bairro
      ,enderecos.cidade
      ,enderecos.uf
      ,enderecos.cep
      ,his.hawb_id
    FROM objetos
    INNER JOIN (select * from historico_objetos where id in (select max(id) from historico_objetos group by objeto_id)) his on objetos.id = his.objeto_id
    JOIN enderecos on enderecos.id = objetos.endereco_id

    WHERE 
    flg_entregue != 1 
    and flg_devolvido = 1
    and data_baixa > DATEADD(day, ?, DATEDIFF(day, 0, GETDATE()))
    and courier_id = ?
    and enderecos.id = objetos.endereco_id
    order by data_baixa DESC;
  """
    #traz objetos devolvidos e não entregues com data_baixa >= days_before_now
    db_cursor.execute(cmd, days_before_now, courier_id)

    registros = db_cursor.fetchall()

    filepath_remessa = os.path.join(ARQUIVOS_TEMPORARIOS, filename)

    with open(filepath_remessa, 'w', encoding='UTF8', newline="\n") as file:
        writer = csv.writer(file, delimiter=";")
        HEADER = ["ID_CONTA", "TIPO_ENDERECO", "NOME", "ENDERECO",
                  "BAIRRO", "CIDADE", "ESTADO", "CEP", "COD_RASTREIO", "AWB"]
        writer.writerow(HEADER)

        for registro in registros:
            id_conta = registro.id_conta

            status_request, address_request, conta_request = get_address(
                id_conta, pier)

            if status_request != 200:
                continue

            address = address_request["content"][0]
            dataUltimaAtualizacao = address["dataUltimaAtualizacao"]
            #compara se existe data de atualizacao endereco e se existe registro.data_postagem
            if dataUltimaAtualizacao != None and registro.data_postagem != None:

                #converte a data removendo Z(UTC)
                address_ultima_atualizacao = dataUltimaAtualizacao.replace(
                    "Z", "")
                ultima_atualizacao = datetime.fromisoformat(
                    address_ultima_atualizacao)

                # dia de execução
                hoje = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
                #calcula o dia de ontem
                ontem = hoje - timedelta(days=1)
                print(f"registro.data_postagem: {registro.data_postagem}\nultima_atualizacao: {ultima_atualizacao}\nhoje: {hoje}\nontem: {ontem}")
                #compara se a data de postagem é antes da data de atualizacão de endereco e se a data de atualizacao está entre ontem e hoje
                #caso positivo, então registra-se o novo endereco e demais informacoes para inserir no arquivo
                if(registro.data_postagem < ultima_atualizacao and ontem <= ultima_atualizacao <= hoje):
                    antigo_endereco = [registro.id_conta, "ANTIGO", conta_request["nome"], registro.rua,
                                       registro.bairro, registro.cidade, registro.uf, registro.cep, registro.id_externo, registro.hawb_id]

                    rua = f"{address['logradouro']} {address['numero']} {address['complemento']}"
                    

                    novo_endereco = [registro.id_conta, "NOVO", conta_request["nome"], rua, address["bairro"],
                                     address["cidade"], address["uf"], address["cep"], registro.id_externo,  registro.hawb_id]


                    endereco_antigo = Endereco(registro.rua, registro.bairro, registro.cidade, registro.uf, registro.cep)
                    endereco_novo = Endereco(rua, address["bairro"], address["cidade"], address["uf"], address["cep"])

                    if(endereco_antigo != endereco_novo):
                        writer.writerow(antigo_endereco)
                        writer.writerow(novo_endereco)

    send_email(receiver=receiver_email, filename=filename, subject=subject, body=body)


def main():      
    db_rastreamento_cartoes = SQLServer()
    for courier, item in COURIERS.items():
        print(f"Enviando para {courier}")

        courier_id = item["id"]
        dias = item["dias_anterior"]
        email= item["enviar_para"]
        subject = item["subject"]
        body = item["body"]
       
        atualizar_enderecos(db_rastreamento_cartoes=db_rastreamento_cartoes, courier_id=courier_id, days_before_now=dias, receiver_email=email, filename="remessa.csv", subject=subject, body=body)

    db_rastreamento_cartoes.close()

if __name__=='__main__':
    main()
