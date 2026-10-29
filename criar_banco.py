import sqlite3

conexao = sqlite3.connect("grupos.db")

conexao.execute("PRAGMA foreign_keys = ON")

conexao.execute("""
CREATE TABLE IF NOT EXISTS participante (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL
)
""")

conexao.execute("""
CREATE TABLE IF NOT EXISTS grupo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cor TEXT,
    grupo_pai_id INTEGER,
    FOREIGN KEY (grupo_pai_id) REFERENCES grupo(id)
)
""")


conexao.execute("""
CREATE TABLE IF NOT EXISTS participacao (
    participante_id INTEGER NOT NULL,
    grupo_id INTEGER NOT NULL,
    PRIMARY KEY (participante_id, grupo_id),
    FOREIGN KEY (participante_id) REFERENCES participante(id),
    FOREIGN KEY (grupo_id) REFERENCES grupo(id)
)
""")


conexao.commit()

tabelas = conexao.execute("""
SELECT name
FROM sqlite_master
WHERE type = 'table'
AND name NOT LIKE 'sqlite_%'
ORDER BY name
""").fetchall()

print("Banco de dados criado ou aberto com sucesso!")
print("Tabelas encontradas:")

for tabela in tabelas:
    print("-", tabela[0])

conexao.close()