import tkinter as tk
from tkinter import ttk, simpledialog, messagebox

PRINCIPAL = "ADS — Faculdade"
CORES = ["#1e6fd9", "#2e9e4f", "#f08a1c", "#8e44ad", "#d62d2d", "#16a0a0"]

# ==== DADOS PROVISÓRIOS ENQUANTO NÃO INTEGRAMOS AO BANCO DE DADOS ====

pessoas = {}                    # nome -> conjunto de projetos
projetos = {}                   # nome do projeto -> cor
mensagens = {PRINCIPAL: []}     # grupo -> lista__grupos de (autor, texto)

def nova_pessoa(nome):
    if nome in pessoas:
        return "Essa pessoa já existe."
    pessoas[nome] = set()


def novo_projeto(nome):
    if nome in projetos or nome == PRINCIPAL:
        return "Esse projeto já existe."
    projetos[nome] = CORES[len(projetos) % len(CORES)]
    mensagens[nome] = []


def entrar_no_projeto(pessoa, projeto):
    pessoas[pessoa].add(projeto)


def sair_do_projeto(pessoa, projeto):
    pessoas[pessoa].discard(projeto)


def sair_de_tudo(pessoa):
    pessoas.pop(pessoa, None)


def excluir_projeto(projeto):
    projetos.pop(projeto, None)
    mensagens.pop(projeto, None)
    for p in pessoas.values():
        p.discard(projeto)


def membros(grupo):
    if grupo == PRINCIPAL:
        return list(pessoas)
    return [p for p, ps in pessoas.items() if grupo in ps]


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

#Lista_lista__grupos de Grupos (Esquerda)
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
    #linhas = lista__grupos de (lista__grupos_de_cores, texto)
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
    mensagens[grupo_atual].append((p, texto))
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