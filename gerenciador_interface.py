import os
import sqlite3
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox

PRINCIPAL = "ADS — Faculdade"
CORES = ["#1e6fd9", "#2e9e4f", "#f08a1c", "#8e44ad", "#d62d2d", "#16a0a0"]

pessoas = {}                    # nome -> conjunto de projetos
projetos = {}                   # nome do projeto -> cor
mensagens = {PRINCIPAL: []}     # grupo -> lista de (autor, texto)

conexao = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'grupos.db'))
conexao.execute("PRAGMA foreign_keys = on")

conexao.execute("""
CREATE TABLE IF NOT EXISTS mensagem (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    grupo_id INTEGER NOT NULL,
    autor TEXT NOT NULL,
    texto TEXT NOT NULL,
    FOREIGN KEY (grupo_id) REFERENCES grupo(id)
)
""")
conexao.commit()

def _criar_principal():
    # o grupo principal é o grupo sem grupo_pai; os projetos são filhos dele
    linha = conexao.execute(
        "SELECT id FROM grupo WHERE nome = ? AND grupo_pai_id IS NULL", (PRINCIPAL,)).fetchone()
    if linha:
        return linha[0]
    cursor = conexao.execute("INSERT INTO grupo (nome, cor, grupo_pai_id) VALUES (?, NULL, NULL)", (PRINCIPAL,))
    conexao.commit()
    return cursor.lastrowid
 
 
ID_PRINCIPAL = _criar_principal()
 
 
def _id_pessoa(nome):
    return conexao.execute("SELECT id FROM participante WHERE nome = ?", (nome,)).fetchone()[0]
 
 
def _id_grupo(nome):
    if nome == PRINCIPAL:
        return ID_PRINCIPAL
    return conexao.execute(
        "SELECT id FROM grupo WHERE nome = ? AND grupo_pai_id = ?", (nome, ID_PRINCIPAL)).fetchone()[0]
 
 
def recarregar():
    """Lê o banco e refaz os dicionários usados pela interface."""
    pessoas.clear()
    projetos.clear()
    mensagens.clear()
    mensagens[PRINCIPAL] = []
    for (nome,) in conexao.execute("SELECT nome FROM participante ORDER BY id"):
        pessoas[nome] = set()
    for nome, cor in conexao.execute(
            "SELECT nome, cor FROM grupo WHERE grupo_pai_id = ? ORDER BY id", (ID_PRINCIPAL,)):
        projetos[nome] = cor
        mensagens[nome] = []
    for pessoa, projeto in conexao.execute("""
            SELECT pt.nome, g.nome FROM participacao pa
            JOIN participante pt ON pt.id = pa.participante_id
            JOIN grupo g ON g.id = pa.grupo_id
            WHERE g.grupo_pai_id = ?""", (ID_PRINCIPAL,)):
        pessoas[pessoa].add(projeto)
    for grupo, autor, texto in conexao.execute("""
            SELECT g.nome, m.autor, m.texto FROM mensagem m
            JOIN grupo g ON g.id = m.grupo_id ORDER BY m.id"""):
        if grupo in mensagens:
            mensagens[grupo].append((autor, texto))
 
 
def nova_pessoa(nome):
    if nome in pessoas:
        return "Essa pessoa já existe."
    conexao.execute("INSERT INTO participante (nome) VALUES (?)", (nome,))
    conexao.commit()
    recarregar()
 
 
def novo_projeto(nome):
    if nome in projetos or nome == PRINCIPAL:
        return "Esse projeto já existe."
    cor = CORES[len(projetos) % len(CORES)]
    conexao.execute("INSERT INTO grupo (nome, cor, grupo_pai_id) VALUES (?, ?, ?)", (nome, cor, ID_PRINCIPAL))
    conexao.commit()
    recarregar()
 
 
def entrar_no_projeto(pessoa, projeto):
    conexao.execute("INSERT OR IGNORE INTO participacao (participante_id, grupo_id) VALUES (?, ?)",
                    (_id_pessoa(pessoa), _id_grupo(projeto)))
    conexao.commit()
    recarregar()
 
 
def sair_do_projeto(pessoa, projeto):
    conexao.execute("DELETE FROM participacao WHERE participante_id = ? AND grupo_id = ?",
                    (_id_pessoa(pessoa), _id_grupo(projeto)))
    conexao.commit()
    recarregar()
 
 
def sair_de_tudo(pessoa):
    pid = _id_pessoa(pessoa)
    conexao.execute("DELETE FROM participacao WHERE participante_id = ?", (pid,))
    conexao.execute("DELETE FROM participante WHERE id = ?", (pid,))
    conexao.commit()
    recarregar()
 
 
def excluir_projeto(projeto):
    gid = _id_grupo(projeto)
    conexao.execute("DELETE FROM participacao WHERE grupo_id = ?", (gid,))
    conexao.execute("DELETE FROM mensagem WHERE grupo_id = ?", (gid,))
    conexao.execute("DELETE FROM grupo WHERE id = ?", (gid,))
    conexao.commit()
    recarregar()
 
 
def nova_mensagem(grupo, autor, texto):
    conexao.execute("INSERT INTO mensagem (grupo_id, autor, texto) VALUES (?, ?, ?)",
                    (_id_grupo(grupo), autor, texto))
    conexao.commit()
    recarregar()
 
 
def membros(grupo):
    if grupo == PRINCIPAL:
        return list(pessoas)
    return [p for p, ps in pessoas.items() if grupo in ps]

recarregar()


# ==== INTERFACE ====
janela = tk.Tk()
janela.title("Gerenciador de Grupos e Subgrupos")
janela.geometry("1100x520")

grupo_atual = PRINCIPAL

#barra de cima
topo = tk.Frame(janela)
topo.pack(fill="x", padx=8, pady=6)
tk.Label(topo, text="Pessoa: ").pack(side="left")
combo = ttk.Combobox(topo, state="readonly", width=20) #a caixa de seleção da pessoa
combo.pack(side="left", padx=4)

#corpo
corpo = tk.Frame(janela)
corpo.pack(fill="both", expand=True, padx=8)

#Lista de Grupos (Esquerda)
esquerda = tk.Frame(corpo)
esquerda.pack(side="left", fill="y")
tk.Label(esquerda, text="Grupos").pack()
lista_grupos = tk.Listbox(esquerda, width=24, exportselection=False, font=("Arial", 11))
lista_grupos.pack(fill="y", expand=True)

#Chat (Centro)
centro = tk.Frame(corpo)
centro.pack(side="left", fill="both", expand=True, padx=8)
tk.Label(centro, text="Chat").pack()
chat = tk.Text(centro, state="disabled", font=("Arial", 11))
chat.pack(fill="both", expand=True)
envio = tk.Frame(centro)
envio.pack(fill="x", pady=4)
campo = tk.Entry(envio)
campo.pack(side="left", fill="x", expand=True)

#Integrantes (Direita)
direita = tk.Frame(corpo)
direita.pack(side="left", fill="y")
tk.Label(direita, text="Integrantes").pack()
membros_txt = tk.Text(direita, width=22, state="disabled", font=("Arial", 11))
membros_txt.pack(fill="y", expand=True)

# ==== Funções de atualizar a tela e escrever textos ====

for t in (chat, membros_txt):
    for cor in CORES:
        t.tag_configure(cor, foreground=cor)


def escrever(widget, linhas):
    #linhas = lista de (lista_de_cores, texto)
    widget.config(state="normal")
    widget.delete(1.0, "end")
    for cores, texto in linhas:
        for c in cores:
                widget.insert("end", "● ", c)
        widget.insert("end", texto + "\n")
    widget.config(state="disabled")


def cores_da(pessoa):
    return [projetos[p] for p in sorted(pessoas.get(pessoa, [])) if p in projetos]


def atualizar():
    nomes = [PRINCIPAL] + list(projetos)
    lista_grupos.delete(0, "end")
    for i, n in enumerate(nomes):
        lista_grupos.insert("end", n)
        if i > 0:
            lista_grupos.itemconfig(i, fg=projetos[n])
    lista_grupos.selection_set(nomes.index(grupo_atual))

    combo["values"] = list(pessoas)
    if combo.get() not in pessoas:
        combo.set("")

    escrever(membros_txt, [(cores_da(p), p) for p in membros(grupo_atual)])
    escrever(chat, [(cores_da(a), f"{a}: {t}") for a, t in mensagens[grupo_atual]])


def escolher_grupo(_=None):
    global grupo_atual
    sel = lista_grupos.curselection()
    if sel:
        grupo_atual = lista_grupos.get(sel[0])
        atualizar()

# avisa o Tkinter para chamar escolher_grupo sempre que o usuário clica em outro grupo
lista_grupos.bind("<<ListboxSelect>>", escolher_grupo)

# ==== Funções de Botões ====
def pessoa_escolhida():
    p = combo.get()
    if not p:
        messagebox.showinfo("Aviso", "Escolha uma pessoa na caixa 'Pessoa'.")
    else :
        return p

def acao_nova_pessoa():
    nome = simpledialog.askstring("Nova pessoa", "Nome:")
    if nome and nome.strip():
        erro = nova_pessoa(nome.strip())
        if erro:
            messagebox.showwarning("Erro", erro)
        else :
            atualizar()


def acao_novo_projeto():
    nome = simpledialog.askstring("Novo Projeto", "Nome do Projeto")
    if nome and nome.strip():
        erro = novo_projeto(nome.strip())
        if erro:
            messagebox.showerror("Error", erro)
        atualizar()


def acao_entrar():
    p = pessoa_escolhida()
    if p and grupo_atual != PRINCIPAL:
        entrar_no_projeto(p, grupo_atual)
        atualizar()


def acao_sair():
    p = pessoa_escolhida()
    if p and grupo_atual != PRINCIPAL :
        sair_do_projeto(p, grupo_atual)
        atualizar()


def acao_sair_de_tudo():
    p = pessoa_escolhida()
    if p and messagebox.askyesno("Confirmar", f"{p} vai sair do grupo principal e de todos os projetos. Continuar?"):
        sair_de_tudo(p)
        atualizar()


def acao_excluir_projeto():
    global grupo_atual
    if grupo_atual == PRINCIPAL:
        messagebox.showinfo("Aviso", "Selecione um projeto para excluir")
    elif messagebox.askyesno("Confirmar", f"Excuir este projeto '{grupo_atual}'") :
        excluir_projeto(grupo_atual)
        grupo_atual = PRINCIPAL
        atualizar()


def acao_enviar(_=None):
    p = pessoa_escolhida()
    texto = campo.get().strip()
    if not p or not texto:
        return
    if p not in membros(grupo_atual):
        messagebox.showinfo("Aviso", f"{p} não participa de '{grupo_atual}'.")
        return
    nova_mensagem(grupo_atual, p, texto)
    campo.delete(0, "end")
    atualizar()


tk.Button(envio, text="Enviar", command=acao_enviar).pack(side="left", padx=4)
campo.bind("<Return>", acao_enviar)

# Botões
botoes = tk.Frame(janela)
botoes.pack(fill="x", padx=8, pady=8)
for texto, cmd in [
    ("Nova pessoa", acao_nova_pessoa),
    ("Novo projeto", acao_novo_projeto),
    ("Entrar no projeto", acao_entrar),
    ("Sair do projeto", acao_sair),
    ("Sair de tudo", acao_sair_de_tudo),
    ("Excluir projeto", acao_excluir_projeto),
]:
    tk.Button(botoes, text=texto, command=cmd).pack(side="left", padx=3)

atualizar()
janela.mainloop()
