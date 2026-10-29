import sqlite3


def conectar():
    conexao = sqlite3.connect("grupos.db")
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def criar_participante(nome):
    conexao = conectar()
    cursor = conexao.execute("INSERT INTO participante (nome) VALUES (?)", (nome,))
    conexao.commit()
    novo_id = cursor.lastrowid
    conexao.close()
    return novo_id


def criar_grupo_principal(nome):
    conexao = conectar()
    cursor = conexao.execute("INSERT INTO grupo (nome) VALUES (?)", (nome,))
    conexao.commit()
    novo_id = cursor.lastrowid
    conexao.close()
    return novo_id


def criar_subgrupo(nome, cor, grupo_pai_id):
    conexao = conectar()
    cursor = conexao.execute(
        "INSERT INTO grupo (nome, cor, grupo_pai_id) VALUES (?, ?, ?)",
        (nome, cor, grupo_pai_id),
    )
    conexao.commit()
    novo_id = cursor.lastrowid
    conexao.close()
    return novo_id


def entrar_no_grupo(participante_id, grupo_id):
    conexao = conectar()

    
    linha = conexao.execute(
        "SELECT grupo_pai_id FROM grupo WHERE id = ?", (grupo_id,)
    ).fetchone()

    if linha is None:
        conexao.close()
        print("Erro: esse grupo não existe.")
        return False
    grupo_pai_id = linha[0]

    
    if grupo_pai_id is not None:
        esta_no_principal = conexao.execute(
            "SELECT 1 FROM participacao WHERE participante_id = ? AND grupo_id = ?",
            (participante_id, grupo_pai_id),
        ).fetchone()

        if esta_no_principal is None:
            conexao.close()
            print("Erro: precisa entrar no grupo principal primeiro.")
            return False

    
    conexao.execute(
        "INSERT OR IGNORE INTO participacao (participante_id, grupo_id) VALUES (?, ?)",
        (participante_id, grupo_id),
    )
    conexao.commit()
    conexao.close()
    return True


def sair_do_subgrupo(participante_id, grupo_id):
    
    conexao = conectar()
    cursor = conexao.execute(
        "DELETE FROM participacao WHERE participante_id = ? AND grupo_id = ?",
        (participante_id, grupo_id),
    )
    conexao.commit()
    removidos = cursor.rowcount
    conexao.close()
    return removidos > 0


def sair_de_tudo(participante_id):
    
    conexao = conectar()
    cursor = conexao.execute(
        "DELETE FROM participacao WHERE participante_id = ?",
        (participante_id,),
    )
    conexao.commit()
    removidos = cursor.rowcount
    conexao.close()
    return removidos


def excluir_subgrupo(grupo_id):
    
    conexao = conectar()
    conexao.execute("DELETE FROM participacao WHERE grupo_id = ?", (grupo_id,))
    conexao.execute("DELETE FROM grupo WHERE id = ?", (grupo_id,))
    conexao.commit()
    conexao.close()


def listar_membros(grupo_id):
    conexao = conectar()
    linhas = conexao.execute(
        """
        SELECT participante.nome
        FROM participacao
        JOIN participante ON participante.id = participacao.participante_id
        WHERE participacao.grupo_id = ?
        ORDER BY participante.id
        """,
        (grupo_id,),
    ).fetchall()
    conexao.close()
    return [linha[0] for linha in linhas]


def listar_projetos_do_participante(participante_id):
    conexao = conectar()
    linhas = conexao.execute(
        """
        SELECT grupo.nome, grupo.cor
        FROM participacao
        JOIN grupo ON grupo.id = participacao.grupo_id
        WHERE participacao.participante_id = ?
        ORDER BY grupo.id
        """,
        (participante_id,),
    ).fetchall()
    conexao.close()
    return linhas

def listar_grupos():
    conexao = conectar()
    linhas = conexao.execute(
        "SELECT id, nome, cor, grupo_pai_id FROM grupo ORDER BY id"
    ).fetchall()
    conexao.close()
    return linhas


def listar_participantes():
    conexao = conectar()
    linhas = conexao.execute(
        "SELECT id, nome FROM participante ORDER BY id"
    ).fetchall()
    conexao.close()
    return linhas


def mostrar_grupos():
    print("\nGrupos:")
    for id_grupo, nome, cor, pai in listar_grupos():
        if pai is None:
            print(f"  [{id_grupo}] {nome} (grupo principal)")
        else:
            print(f"  [{id_grupo}] {nome} - cor: {cor} (subgrupo do grupo {pai})")


def mostrar_participantes():
    print("\nParticipantes:")
    for id_participante, nome in listar_participantes():
        print(f"  [{id_participante}] {nome}")


def ler_numero(texto):
    while True:
        try:
            return int(input(texto))
        except ValueError:
            print("Digite apenas números.")


def menu():
    while True:
        print("\n=== GERENCIADOR DE GRUPOS ===")
        print("1 - Criar grupo principal")
        print("2 - Criar subgrupo")
        print("3 - Cadastrar participante")
        print("4 - Entrar em um grupo")
        print("5 - Sair de um grupo")
        print("6 - Sair de tudo")
        print("7 - Excluir subgrupo")
        print("8 - Ver membros de um grupo")
        print("9 - Ver projetos de um participante")
        print("0 - Encerrar")
        opcao = input("Escolha: ")

        try:
            if opcao == "1":
                nome = input("Nome do grupo principal: ")
                novo_id = criar_grupo_principal(nome)
                print("Grupo criado com id", novo_id)

            elif opcao == "2":
                mostrar_grupos()
                nome = input("Nome do subgrupo: ")
                cor = input("Cor do subgrupo: ")
                pai = ler_numero("Id do grupo principal: ")
                novo_id = criar_subgrupo(nome, cor, pai)
                print("Subgrupo criado com id", novo_id)

            elif opcao == "3":
                nome = input("Nome do participante: ")
                novo_id = criar_participante(nome)
                print("Participante cadastrado com id", novo_id)

            elif opcao == "4":
                mostrar_participantes()
                mostrar_grupos()
                pessoa = ler_numero("Id do participante: ")
                grupo = ler_numero("Id do grupo: ")
                if entrar_no_grupo(pessoa, grupo):
                    print("Entrou no grupo!")

            elif opcao == "5":
                mostrar_participantes()
                mostrar_grupos()
                pessoa = ler_numero("Id do participante: ")
                grupo = ler_numero("Id do grupo: ")
                if sair_do_subgrupo(pessoa, grupo):
                    print("Saiu do grupo!")
                else:
                    print("Essa pessoa não estava nesse grupo.")

            elif opcao == "6":
                mostrar_participantes()
                pessoa = ler_numero("Id do participante: ")
                total = sair_de_tudo(pessoa)
                print(f"Saiu de {total} grupo(s).")

            elif opcao == "7":
                mostrar_grupos()
                grupo = ler_numero("Id do subgrupo a excluir: ")
                excluir_subgrupo(grupo)
                print("Subgrupo excluído.")

            elif opcao == "8":
                mostrar_grupos()
                grupo = ler_numero("Id do grupo: ")
                print("Membros:", listar_membros(grupo))

            elif opcao == "9":
                mostrar_participantes()
                pessoa = ler_numero("Id do participante: ")
                print("Projetos:", listar_projetos_do_participante(pessoa))

            elif opcao == "0":
                print("Encerrando...")
                break

            else:
                print("Opção inválida.")

        except sqlite3.IntegrityError:
            print("Erro: confira se os ids digitados existem.")


if __name__ == "__main__":
    menu()

