# Aqui ficam as funções de INSERT, SELECT, UPDATE, DELETE do banco de dados
class BaseRepository:
    def __init__(self):
        # Será trocado posteriormente pela conexão real do SQLite/PostgreSQL
        self.banco_de_dados = "Conexão Simulada"