import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('data/banco_brasil_transacoes.sqlite')
cur = conn.cursor()

data_base = datetime.now()
lote = [
    (150.00, (data_base - timedelta(hours=2)).strftime('%Y-%m-%d'), (data_base - timedelta(hours=2)).strftime('%H:%M'), 'Racha do almoco', '58392-1', 'Aracaju', 'received', 'Ana Lima'),
    (21.90, (data_base - timedelta(hours=26)).strftime('%Y-%m-%d'), (data_base - timedelta(hours=26)).strftime('%H:%M'), 'Assinatura mensal', '58392-1', 'Aracaju', 'sent', 'Spotify'),
    (18.50, (data_base - timedelta(hours=50)).strftime('%Y-%m-%d'), (data_base - timedelta(hours=50)).strftime('%H:%M'), 'Viagem', '58392-1', 'Aracaju', 'sent', 'Uber'),
    (800.00, (data_base - timedelta(days=5)).strftime('%Y-%m-%d'), '10:00', 'Mesada', '58392-1', 'Aracaju', 'received', 'Mae'),
    (145.80, (data_base - timedelta(days=7)).strftime('%Y-%m-%d'), '14:30', 'Livros', '58392-1', 'Aracaju', 'sent', 'Livraria Cultura'),
    (300.00, (data_base - timedelta(days=10)).strftime('%Y-%m-%d'), '09:00', 'Freelance', '58392-1', 'Aracaju', 'deposit', 'Credito em conta'),
]

cur.executemany('INSERT INTO transactions (valor, data, hora, categoria, conta, cidade, tipo_transacao, dispositivo) VALUES (?,?,?,?,?,?,?,?)', lote)
conn.commit()
print('Inseridas:', cur.rowcount)
conn.close()