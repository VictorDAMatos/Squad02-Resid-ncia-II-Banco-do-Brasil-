from fastapi import APIRouter, HTTPException
import sqlite3
from pydantic import BaseModel

router = APIRouter(tags=["🏦 Core Bancário"])

# SCHEMAS (DTOs)
class AgenciaCreate(BaseModel):
    nome: str
    numero: str
    endereco: str

class ContaCreate(BaseModel):
    numero: str
    saldo: float
    cliente_id: int
    agencia_id: int

class CartaoCreate(BaseModel):
    numero: str
    validade: str
    cvv: str
    limite: float
    conta_id: int

# ENDPOINTS

@router.post("/agencias", status_code=201)
def criar_agencia(agencia: AgenciaCreate):
    conexao = sqlite3.connect('data/banco_brasil_transacoes.sqlite')
    cursor = conexao.cursor()
    cursor.execute("INSERT INTO Agencia (nome, numero, endereco) VALUES (?, ?, ?)",
                   (agencia.nome, agencia.numero, agencia.endereco))
    conexao.commit()
    id_gerado = cursor.lastrowid
    conexao.close()
    return {"sucesso": True, "id_agencia": id_gerado}

@router.post("/contas", status_code=201)
def criar_conta(conta: ContaCreate):
    conexao = sqlite3.connect('data/banco_brasil_transacoes.sqlite')
    cursor = conexao.cursor()
    cursor.execute("INSERT INTO Conta (numero, saldo, cliente_id, agencia_id) VALUES (?, ?, ?, ?)",
                   (conta.numero, conta.saldo, conta.cliente_id, conta.agencia_id))
    conexao.commit()
    id_gerado = cursor.lastrowid
    conexao.close()
    return {"sucesso": True, "id_conta": id_gerado}

@router.post("/cartoes", status_code=201)
def criar_cartao(cartao: CartaoCreate):
    conexao = sqlite3.connect('data/banco_brasil_transacoes.sqlite')
    cursor = conexao.cursor()
    cursor.execute("INSERT INTO Cartao (numero, validade, cvv, limite, conta_id) VALUES (?, ?, ?, ?, ?)",
                   (cartao.numero, cartao.validade, cartao.cvv, cartao.limite, cartao.conta_id))
    conexao.commit()
    id_gerado = cursor.lastrowid
    conexao.close()
    return {"sucesso": True, "id_cartao": id_gerado}