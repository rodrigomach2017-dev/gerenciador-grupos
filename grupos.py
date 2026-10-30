
import sqlite3
from pathlib import Path
from contextlib import contextmanager

# Caminho do banco de dados
BANCO = Path(__file__).resolve().parent / "grupos.db"


# ==========================================
# CONEXAO COM O BANCO DE DADOS
# ==========================================

@contextmanager
def conectar():
    conexao = sqlite3.connect(BANCO)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")

    try:
        yield conexao
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


# ==========================================
# CRIACAO DAS TABELAS
# ==========================================

def iniciar_banco():
    with conectar() as con:

        con.execute("""
        CREATE TABLE IF NOT EXISTS participante (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL
        )
        """)

        con.execute("""
        CREATE TABLE IF NOT EXISTS grupo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cor TEXT,
            grupo_pai_id INTEGER,
            FOREIGN KEY (grupo_pai_id) REFERENCES grupo(id)
        )
        """)

        con.execute("""
        CREATE TABLE IF NOT EXISTS participacao (
            participante_id INTEGER NOT NULL,
            grupo_id INTEGER NOT NULL,
            PRIMARY KEY (participante_id, grupo_id),
            FOREIGN KEY (participante_id)
                REFERENCES participante(id),
            FOREIGN KEY (grupo_id)
                REFERENCES grupo(id)
        )
        """)


# ==========================================
# CRIAR GRUPO OU SUBGRUPO
# ==========================================

def criar_grupo(nome, cor=None, grupo_pai_id=None):

    nome = nome.strip()

    if not nome:
        raise ValueError("O nome do grupo não pode ficar vazio.")

    with conectar() as con:

        if grupo_pai_id is not None:
            pai = con.execute(
                "SELECT id FROM grupo WHERE id = ?",
                (grupo_pai_id,)
            ).fetchone()

            if pai is None:
                raise ValueError("Grupo principal não encontrado.")

            # Evita criar subgrupos dentro de outros subgrupos
            nivel = con.execute(
                "SELECT grupo_pai_id FROM grupo WHERE id = ?",
                (grupo_pai_id,)
            ).fetchone()

            if nivel["grupo_pai_id"] is not None:
                raise ValueError(
                    "Não é permitido criar subgrupos dentro de subgrupos."
                )

        cursor = con.execute("""
            INSERT INTO grupo (nome, cor, grupo_pai_id)
            VALUES (?, ?, ?)
        """, (nome, cor, grupo_pai_id))

        return cursor.lastrowid


# ==========================================
# LISTAR GRUPOS E SUBGRUPOS
# ==========================================

def listar_grupos():

    with conectar() as con:

        grupos = con.execute("""
            SELECT id, nome, cor, grupo_pai_id
            FROM grupo
            ORDER BY grupo_pai_id, nome
        """).fetchall()

        if not grupos:
            print("\nNenhum grupo cadastrado.")
            return

        principais = [
            grupo for grupo in grupos
            if grupo["grupo_pai_id"] is None
        ]

        print("\n========== GRUPOS CADASTRADOS ==========")

        for grupo in principais:

            cor = grupo["cor"] or "Não definida"

            print(f"\n[{grupo['id']}] {grupo['nome']}")
            print(f"    Cor: {cor}")

            subgrupos = [
                sub for sub in grupos
                if sub["grupo_pai_id"] == grupo["id"]
            ]

            for sub in subgrupos:
                cor_sub = sub["cor"] or "Não definida"

                print(
                    f"    └── [{sub['id']}] {sub['nome']} "
                    f"(Cor: {cor_sub})"
                )


# ==========================================
# EDITAR GRUPO
# ==========================================

def editar_grupo(grupo_id, novo_nome=None, nova_cor=None):

    with conectar() as con:

        grupo = con.execute(
            "SELECT id FROM grupo WHERE id = ?",
            (grupo_id,)
        ).fetchone()

        if grupo is None:
            raise ValueError("Grupo não encontrado.")

        if novo_nome is not None:
            novo_nome = novo_nome.strip()

            if not novo_nome:
                raise ValueError("O nome não pode ficar vazio.")

            con.execute("""
                UPDATE grupo
                SET nome = ?
                WHERE id = ?
            """, (novo_nome, grupo_id))

        if nova_cor is not None:
            con.execute("""
                UPDATE grupo
                SET cor = ?
                WHERE id = ?
            """, (nova_cor, grupo_id))


# ==========================================
# EXCLUIR GRUPO OU SUBGRUPO
# ==========================================

def excluir_grupo(grupo_id):

    with conectar() as con:

        grupo = con.execute(
            "SELECT id FROM grupo WHERE id = ?",
            (grupo_id,)
        ).fetchone()

        if grupo is None:
            raise ValueError("Grupo não encontrado.")

        filhos = con.execute("""
            SELECT id FROM grupo
            WHERE grupo_pai_id = ?
        """, (grupo_id,)).fetchall()

        if filhos:
            raise ValueError(
                "Este grupo possui subgrupos. "
                "Exclua os subgrupos primeiro."
            )

        con.execute("""
            DELETE FROM participacao
            WHERE grupo_id = ?
        """, (grupo_id,))

        con.execute("""
            DELETE FROM grupo
            WHERE id = ?
        """, (grupo_id,))


# ==========================================
# CADASTRAR PARTICIPANTE
# ==========================================

def cadastrar_participante(nome):

    nome = nome.strip()

    if not nome:
        raise ValueError("O nome do participante é obrigatório.")

    with conectar() as con:

        cursor = con.execute("""
            INSERT INTO participante (nome)
            VALUES (?)
        """, (nome,))

        return cursor.lastrowid


# ==========================================
# LISTAR PARTICIPANTES CADASTRADOS
# ==========================================

def listar_participantes():

    with conectar() as con:

        participantes = con.execute("""
            SELECT id, nome
            FROM participante
            ORDER BY nome
        """).fetchall()

        print("\n========== PARTICIPANTES ==========")

        if not participantes:
            print("Nenhum participante cadastrado.")
            return

        for pessoa in participantes:
            print(f"[{pessoa['id']}] {pessoa['nome']}")


# ==========================================
# ADICIONAR PARTICIPANTE AO GRUPO
# ==========================================

def adicionar_participante(participante_id, grupo_id):

    with conectar() as con:

        pessoa = con.execute(
            "SELECT id FROM participante WHERE id = ?",
            (participante_id,)
        ).fetchone()

        grupo = con.execute(
            "SELECT id FROM grupo WHERE id = ?",
            (grupo_id,)
        ).fetchone()

        if pessoa is None:
            raise ValueError("Participante não encontrado.")

        if grupo is None:
            raise ValueError("Grupo não encontrado.")

        existente = con.execute("""
            SELECT * FROM participacao
            WHERE participante_id = ? AND grupo_id = ?
        """, (participante_id, grupo_id)).fetchone()

        if existente:
            raise ValueError("Esta pessoa já participa desse grupo.")

        con.execute("""
            INSERT INTO participacao
            (participante_id, grupo_id)
            VALUES (?, ?)
        """, (participante_id, grupo_id))


# ==========================================
# REMOVER PARTICIPANTE DO GRUPO
# ==========================================

def remover_participante(participante_id, grupo_id):

    with conectar() as con:

        cursor = con.execute("""
            DELETE FROM participacao
            WHERE participante_id = ?
            AND grupo_id = ?
        """, (participante_id, grupo_id))

        if cursor.rowcount == 0:
            raise ValueError(
                "Participação não encontrada."
            )


# ==========================================
# LISTAR PARTICIPANTES DE UM GRUPO
# ==========================================

def listar_integrantes(grupo_id):

    with conectar() as con:

        grupo = con.execute("""
            SELECT nome FROM grupo
            WHERE id = ?
        """, (grupo_id,)).fetchone()

        if grupo is None:
            raise ValueError("Grupo não encontrado.")

        pessoas = con.execute("""
            SELECT participante.id, participante.nome
            FROM participante
            INNER JOIN participacao
            ON participante.id = participacao.participante_id
            WHERE participacao.grupo_id = ?
            ORDER BY participante.nome
        """, (grupo_id,)).fetchall()

        print(f"\n========== {grupo['nome']} ==========")

        if not pessoas:
            print("Nenhum participante neste grupo.")
            return

        for pessoa in pessoas:
            print(
                f"[{pessoa['id']}] {pessoa['nome']}"
            )


# ==========================================
# MENU PRINCIPAL
# ==========================================

def menu():

    while True:

        print("\n" + "=" * 42)
        print("       SISTEMA DE GERENCIAMENTO")
        print("             DE GRUPOS")
        print("=" * 42)

        print("1 - Criar grupo principal")
        print("2 - Criar subgrupo")
        print("3 - Listar grupos e subgrupos")
        print("4 - Editar grupo")
        print("5 - Excluir grupo ou subgrupo")
        print("6 - Cadastrar participante")
        print("7 - Adicionar participante ao grupo")
        print("8 - Remover participante do grupo")
        print("9 - Listar participantes cadastrados")
        print("10 - Ver integrantes de um grupo")
        print("0 - Sair")

        opcao = input("\nEscolha uma opção: ").strip()

        try:

            if opcao == "1":

                nome = input("Nome do grupo: ")
                cor = input("Cor do grupo: ").strip() or None

                grupo_id = criar_grupo(nome, cor)

                print(
                    f"\nGrupo criado com sucesso! ID: {grupo_id}"
                )

            elif opcao == "2":

                listar_grupos()

                pai = int(input("\nID do grupo principal: "))
                nome = input("Nome do subgrupo: ")
                cor = input("Cor do subgrupo: ").strip() or None

                grupo_id = criar_grupo(nome, cor, pai)

                print(
                    f"\nSubgrupo criado com sucesso! ID: {grupo_id}"
                )

            elif opcao == "3":

                listar_grupos()

            elif opcao == "4":

                listar_grupos()

                grupo_id = int(input("\nID do grupo para editar: "))

                nome = input(
                    "Novo nome (Enter para manter): "
                ).strip()

                cor = input(
                    "Nova cor (Enter para manter): "
                ).strip()

                editar_grupo(
                    grupo_id,
                    novo_nome=nome if nome else None,
                    nova_cor=cor if cor else None
                )

                print("\nGrupo atualizado com sucesso!")

            elif opcao == "5":

                listar_grupos()

                grupo_id = int(input("\nID do grupo para excluir: "))

                confirmar = input(
                    "Tem certeza que deseja excluir? (s/n): "
                ).lower()

                if confirmar == "s":
                    excluir_grupo(grupo_id)
                    print("\nGrupo excluído com sucesso!")
                else:
                    print("\nOperação cancelada.")

            elif opcao == "6":

                nome = input("Nome do participante: ")

                pessoa_id = cadastrar_participante(nome)

                print(
                    f"\nParticipante cadastrado! ID: {pessoa_id}"
                )

            elif opcao == "7":

                listar_participantes()
                listar_grupos()

                pessoa_id = int(
                    input("\nID do participante: ")
                )

                grupo_id = int(
                    input("ID do grupo: ")
                )

                adicionar_participante(
                    pessoa_id,
                    grupo_id
                )

                print("\nParticipante adicionado com sucesso!")

            elif opcao == "8":

                listar_grupos()

                grupo_id = int(input("\nID do grupo: "))

                listar_integrantes(grupo_id)

                pessoa_id = int(
                    input("\nID do participante para remover: ")
                )

                remover_participante(
                    pessoa_id,
                    grupo_id
                )

                print("\nParticipante removido do grupo!")

            elif opcao == "9":

                listar_participantes()

            elif opcao == "10":

                listar_grupos()

                grupo_id = int(
                    input("\nID do grupo: ")
                )

                listar_integrantes(grupo_id)

            elif opcao == "0":

                print("\nPrograma encerrado. Até mais!")
                break

            else:

                print("\nOpção inválida. Tente novamente.")

        except ValueError as erro:

            print(f"\nErro: {erro}")

        except sqlite3.IntegrityError as erro:

            print(f"\nErro no banco de dados: {erro}")

        except sqlite3.Error as erro:

            print(f"\nErro no SQLite: {erro}")

        except Exception as erro:

            print(f"\nOcorreu um erro: {erro}")


# ==========================================
# EXECUCAO DO PROGRAMA
# ==========================================

if __name__ == "__main__":

    iniciar_banco()

    print("\nBanco de dados conectado com sucesso!")

    menu()
