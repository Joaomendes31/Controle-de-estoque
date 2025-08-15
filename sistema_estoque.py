import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox, Event
from datetime import datetime
from banco import (
    validar_login, cadastrar_usuario, adicionar_produto, 
    obter_produtos, registrar_movimentacao, obter_movimentacoes,
    produtos_estoque_baixo, exportar_estoque_csv, 
    importar_produtos_csv, remover_produto, atualizar_quantidade_produto
)

# Configuração de tema
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class EstoqueApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Controle de Estoque - SQLite")
        self.root.geometry("1000x700")
        self.root.minsize(900, 600)
        
        # Configuração de atalhos
        self.root.bind('<Return>', self.processar_enter)
        self.root.bind('<Escape>', lambda e: self.root.focus())
        self.botao_ativo = None
        
        # Cores
        self.cor_principal = "#2E8B57"
        self.cor_secundaria = "#3CB371"
        self.cor_texto = "#FFFFFF"
        self.cor_alerta = "#FF6347"
        
        # Frame principal
        self.main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.usuario_logado = None
        self.tela_login()
        self.verificar_estoque_baixo_periodicamente()
    
    def verificar_estoque_baixo_periodicamente(self):
        """Verifica estoque baixo a cada 5 minutos (300000ms)"""
        if hasattr(self, 'usuario_logado') and self.usuario_logado:
            self.mostrar_alerta_estoque_baixo()
        self.root.after(300000, self.verificar_estoque_baixo_periodicamente)
    
    def mostrar_alerta_estoque_baixo(self):
        """Mostra alerta de estoque baixo"""
        produtos_baixos = produtos_estoque_baixo()
        if produtos_baixos:
            mensagem = "⚠️ ALERTA: Os seguintes produtos estão com estoque baixo:\n\n"
            for produto in produtos_baixos:
                mensagem += f"• {produto[1]} (Qtd: {produto[3]})\n"
            
            # Mostra alerta apenas se a janela principal estiver focada
            if self.root.focus_displayof():
                messagebox.showwarning("Estoque Baixo", mensagem)
    
    def processar_enter(self, event):
        """Processa o pressionamento da tecla Enter"""
        if self.botao_ativo and self.botao_ativo.winfo_ismapped():
            self.botao_ativo.invoke()
    
    def limpar_tela(self):
        """Limpa todos os widgets do frame principal"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.botao_ativo = None
    
    def tela_login(self):
        self.limpar_tela()
        
        login_frame = ctk.CTkFrame(self.main_frame, corner_radius=15)
        login_frame.pack(expand=True, pady=50)
        
        # Logo/título
        ctk.CTkLabel(
            login_frame, 
            text="CONTROLE DE ESTOQUE", 
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=(30, 20))
        
        # Campo de usuário
        ctk.CTkLabel(login_frame, text="Usuário:").pack(pady=(0, 5))
        self.entry_user = ctk.CTkEntry(
            login_frame, 
            width=250,
            placeholder_text="Digite seu usuário"
        )
        self.entry_user.pack(pady=5)
        self.entry_user.bind('<Return>', lambda e: self.entry_senha.focus())
        
        # Campo de senha
        ctk.CTkLabel(login_frame, text="Senha:").pack(pady=(10, 5))
        self.entry_senha = ctk.CTkEntry(
            login_frame, 
            width=250,
            show="*",
            placeholder_text="Digite sua senha"
        )
        self.entry_senha.pack(pady=5)
        
        # Botão de login
        self.login_btn = ctk.CTkButton(
            login_frame,
            text="Entrar",
            command=self.fazer_login,
            width=200,
            height=40,
            fg_color=self.cor_principal,
            hover_color=self.cor_secundaria
        )
        self.login_btn.pack(pady=30)
        
        # Configura o botão ativo para esta tela
        self.botao_ativo = self.login_btn
        self.entry_senha.bind('<Return>', lambda e: self.login_btn.invoke())
    
    def fazer_login(self):
        """Função para processar o login"""
        usuario = self.entry_user.get()
        senha = self.entry_senha.get()
        
        if usuario and senha:
            usuario_validado = validar_login(usuario, senha)
            if usuario_validado:
                self.usuario_logado = usuario_validado
                self.menu_principal()
                self.mostrar_alerta_estoque_baixo()  # Verifica estoque ao logar
            else:
                messagebox.showerror("Erro", "Credenciais inválidas!")
        else:
            messagebox.showerror("Erro", "Preencha todos os campos!")
    
    def menu_principal(self):
        self.limpar_tela()
        
        # Frame de cabeçalho
        header_frame = ctk.CTkFrame(
            self.main_frame, 
            height=80,
            fg_color=self.cor_principal
        )
        header_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            header_frame,
            text=f"Bem-vindo, {self.usuario_logado['nome']}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.cor_texto
        ).pack(side="left", padx=20, pady=10)
        
        # Botão de logout
        logout_btn = ctk.CTkButton(
            header_frame,
            text="Sair",
            command=self.tela_login,
            width=80,
            fg_color="#FF6347",
            hover_color="#FF4500"
        )
        logout_btn.pack(side="right", padx=20)
        
        # Frame dos botões
        buttons_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        buttons_frame.pack(fill="both", expand=True)
        
        # Botões principais
        botoes = [
            ("📦 Cadastrar Produto", self.tela_cadastro_produto),
            ("🔍 Consultar Estoque", self.tela_consulta_estoque),
            ("✏️ Editar Quantidade", self.tela_editar_quantidade),
            ("✖️ Remover Produto", self.tela_remover_produto),
            ("⬆️ Registrar Entrada", self.tela_registrar_entrada),
            ("⬇️ Registrar Saída", self.tela_registrar_saida),
            ("📊 Movimentações", self.tela_movimentacoes),
            ("📤 Exportar CSV", self.exportar_csv),
            ("📥 Importar CSV", self.importar_csv)
        ]
        
        # Organiza os botões em uma grade 3x3
        for i, (texto, comando) in enumerate(botoes):
            row = i // 3
            col = i % 3
            
            btn = ctk.CTkButton(
                buttons_frame,
                text=texto,
                command=comando,
                width=200,
                height=80,
                corner_radius=10,
                fg_color=self.cor_principal,
                hover_color=self.cor_secundaria,
                font=ctk.CTkFont(size=14),
                compound="top"
            )
            btn.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
            
            buttons_frame.grid_rowconfigure(row, weight=1)
            buttons_frame.grid_columnconfigure(col, weight=1)
    
    def criar_janela_popup(self, titulo, largura=600, altura=500, comando_enter=None):
        """Cria uma janela popup com tratamento de Enter e Escape"""
        popup = ctk.CTkToplevel(self.root)
        popup.title(titulo)
        popup.geometry(f"{largura}x{altura}")
        popup.transient(self.root)
        popup.grab_set()
        
        if comando_enter:
            popup.bind('<Return>', lambda e: comando_enter())
        popup.bind('<Escape>', lambda e: popup.destroy())
        
        frame = ctk.CTkFrame(popup, corner_radius=15)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        return frame, popup
    
    def tela_cadastro_produto(self):
        frame, popup = self.criar_janela_popup("Cadastrar Produto")
        
        self.nome_produto = ctk.CTkEntry(frame, placeholder_text="Ex: Caneta Azul")
        self.desc_produto = ctk.CTkEntry(frame, placeholder_text="Descrição detalhada")
        self.quant_produto = ctk.CTkEntry(frame, placeholder_text="0")
        self.estoque_minimo = ctk.CTkEntry(frame, placeholder_text="5")
        
        ctk.CTkLabel(frame, text="Nome do Produto:").pack(pady=(10, 5))
        self.nome_produto.pack(pady=5)
        
        ctk.CTkLabel(frame, text="Descrição:").pack(pady=(10, 5))
        self.desc_produto.pack(pady=5)
        
        ctk.CTkLabel(frame, text="Quantidade Inicial:").pack(pady=(10, 5))
        self.quant_produto.pack(pady=5)
        
        ctk.CTkLabel(frame, text="Estoque Mínimo:").pack(pady=(10, 5))
        self.estoque_minimo.pack(pady=5)
        
        cadastrar_btn = ctk.CTkButton(
            frame,
            text="Cadastrar (Enter)",
            command=lambda: self.cadastrar_produto(popup),
            fg_color=self.cor_principal
        )
        cadastrar_btn.pack(pady=20)
        
        self.botao_ativo = cadastrar_btn
        self.nome_produto.focus()
        popup.bind('<Return>', lambda e: cadastrar_btn.invoke())
    
    def cadastrar_produto(self, popup):
        nome = self.nome_produto.get()
        desc = self.desc_produto.get()
        quant = self.quant_produto.get()
        estoque_min = self.estoque_minimo.get()
        
        if not nome:
            messagebox.showwarning("Aviso", "Informe o nome do produto!")
            self.nome_produto.focus()
            return
        
        try:
            quantidade = int(quant)
            estoque_minimo = int(estoque_min) if estoque_min else 0
            if quantidade < 0 or estoque_minimo < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Quantidades devem ser números inteiros positivos!")
            self.quant_produto.focus()
            return
        
        adicionar_produto(nome, desc, quantidade, estoque_minimo)
        messagebox.showinfo("Sucesso", "Produto cadastrado com sucesso!")
        popup.destroy()

    def tela_consulta_estoque(self):
        frame, popup = self.criar_janela_popup("Consulta de Estoque", 800, 600)
        
        # Frame de pesquisa
        pesquisa_frame = ctk.CTkFrame(frame, fg_color="transparent")
        pesquisa_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(pesquisa_frame, text="Pesquisar:").pack(side="left", padx=5)
        pesquisa_entry = ctk.CTkEntry(pesquisa_frame, width=300)
        pesquisa_entry.pack(side="left", padx=5, fill="x", expand=True)
        pesquisa_entry.bind('<Return>', lambda e: self.filtrar_estoque(pesquisa_entry.get()))
        
        pesquisar_btn = ctk.CTkButton(
            pesquisa_frame,
            text="Filtrar (Enter)",
            width=100,
            command=lambda: self.filtrar_estoque(pesquisa_entry.get())
        )
        pesquisar_btn.pack(side="left", padx=5)
        
        # Treeview
        self.tree_estoque = ttk.Treeview(frame, columns=("ID", "Nome", "Descrição", "Quantidade", "Mínimo"), show="headings")
        
        # Configuração das colunas
        self.tree_estoque.heading("ID", text="ID")
        self.tree_estoque.column("ID", width=50, anchor="center")
        
        self.tree_estoque.heading("Nome", text="Nome")
        self.tree_estoque.column("Nome", width=200, anchor="w")
        
        self.tree_estoque.heading("Descrição", text="Descrição")
        self.tree_estoque.column("Descrição", width=250, anchor="w")
        
        self.tree_estoque.heading("Quantidade", text="Qtd.")
        self.tree_estoque.column("Quantidade", width=80, anchor="center")
        
        self.tree_estoque.heading("Mínimo", text="Mín.")
        self.tree_estoque.column("Mínimo", width=80, anchor="center")
        
        # Scrollbar
        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree_estoque.yview)
        self.tree_estoque.configure(yscrollcommand=scroll.set)
        
        self.tree_estoque.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        
        # Configura cores para itens com estoque baixo
        self.tree_estoque.tag_configure('estoque_baixo', background='#FFCCCB')
        
        # Carrega os dados
        self.carregar_dados_estoque()
    
    def carregar_dados_estoque(self, filtro=None):
        """Carrega os dados na treeview com destaque para estoque baixo"""
        for item in self.tree_estoque.get_children():
            self.tree_estoque.delete(item)
        
        produtos = obter_produtos(filtro)
        for prod in produtos:
            # Verifica se o estoque está abaixo do mínimo
            if prod[3] < prod[4]:  # quantidade < estoque_minimo
                self.tree_estoque.insert("", "end", values=prod, tags=('estoque_baixo',))
            else:
                self.tree_estoque.insert("", "end", values=prod)
    
    def filtrar_estoque(self, filtro):
        """Filtra os produtos na treeview"""
        self.carregar_dados_estoque(filtro)

    def tela_editar_quantidade(self):
        """Tela para editar a quantidade de um produto"""
        frame, popup = self.criar_janela_popup("Editar Quantidade")
        
        produtos = obter_produtos()
        nomes_produtos = [f"{p[0]} - {p[1]}" for p in produtos]
        
        ctk.CTkLabel(frame, text="Selecione o produto:").pack(pady=(10, 5))
        self.combo_produto_editar = ctk.CTkComboBox(frame, values=nomes_produtos)
        self.combo_produto_editar.pack(pady=5)
        
        ctk.CTkLabel(frame, text="Nova quantidade:").pack(pady=(10, 5))
        self.entry_nova_quantidade = ctk.CTkEntry(frame)
        self.entry_nova_quantidade.pack(pady=5)
        
        salvar_btn = ctk.CTkButton(
            frame,
            text="Salvar Alterações",
            command=lambda: self.salvar_edicao_quantidade(popup),
            fg_color=self.cor_principal
        )
        salvar_btn.pack(pady=20)
        
        self.botao_ativo = salvar_btn
        self.combo_produto_editar.focus()
        popup.bind('<Return>', lambda e: salvar_btn.invoke())
    
    def salvar_edicao_quantidade(self, popup):
        """Salva a nova quantidade do produto"""
        selecao = self.combo_produto_editar.get()
        nova_quant = self.entry_nova_quantidade.get()
        
        if not selecao:
            messagebox.showwarning("Aviso", "Selecione um produto!")
            return
        
        if not nova_quant:
            messagebox.showwarning("Aviso", "Informe a nova quantidade!")
            self.entry_nova_quantidade.focus()
            return
        
        try:
            produto_id = int(selecao.split(" - ")[0])
            nova_quantidade = int(nova_quant)
            if nova_quantidade < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Quantidade deve ser um número inteiro positivo!")
            self.entry_nova_quantidade.focus()
            return
        
        # Atualiza a quantidade no banco de dados
        if atualizar_quantidade_produto(produto_id, nova_quantidade):
            messagebox.showinfo("Sucesso", "Quantidade atualizada com sucesso!")
            popup.destroy()
            # Atualiza a tela de consulta se estiver aberta
            if hasattr(self, 'tree_estoque'):
                self.carregar_dados_estoque()
        else:
            messagebox.showerror("Erro", "Falha ao atualizar quantidade!")

    def tela_remover_produto(self):
        """Exibe a tela para remover produtos"""
        frame, popup = self.criar_janela_popup("Remover Produto")
        
        produtos = obter_produtos()
        nomes_produtos = [f"{p[0]} - {p[1]}" for p in produtos]
        
        ctk.CTkLabel(frame, text="Selecione o produto:").pack(pady=(10, 5))
        self.combo_produto = ctk.CTkComboBox(frame, values=nomes_produtos)
        self.combo_produto.pack(pady=5)
        
        remover_btn = ctk.CTkButton(
            frame,
            text="Remover Produto",
            command=lambda: self.remover_produto_selecionado(popup),
            fg_color="#FF6347",
            hover_color="#FF4500"
        )
        remover_btn.pack(pady=20)
        
        self.botao_ativo = remover_btn
        self.combo_produto.focus()
        popup.bind('<Return>', lambda e: remover_btn.invoke())

    def remover_produto_selecionado(self, popup):
        """Remove o produto selecionado"""
        selecao = self.combo_produto.get()
        if not selecao:
            messagebox.showwarning("Aviso", "Selecione um produto!")
            return
        
        produto_id = int(selecao.split(" - ")[0])
        
        confirmar = messagebox.askyesno(
            "Confirmar",
            f"Tem certeza que deseja remover este produto?",
            icon='warning'
        )
        
        if confirmar:
            if remover_produto(produto_id):
                messagebox.showinfo("Sucesso", "Produto removido com sucesso!")
                popup.destroy()
            else:
                messagebox.showerror("Erro", 
                    "Não foi possível remover o produto. Verifique se há movimentações relacionadas.")

    def exportar_csv(self):
        """Exporta dados para CSV"""
        caminho = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Arquivos CSV", "*.csv")],
            title="Exportar Estoque para CSV"
        )
        
        if caminho:
            try:
                if exportar_estoque_csv(caminho):
                    messagebox.showinfo("Sucesso", "Estoque exportado com sucesso!")
                else:
                    messagebox.showerror("Erro", "Falha ao exportar estoque")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao exportar:\n{e}")

    def importar_csv(self):
        """Importa produtos de CSV"""
        caminho = filedialog.askopenfilename(
            filetypes=[("Arquivos CSV", "*.csv")],
            title="Selecione o arquivo CSV para importar"
        )
        
        if caminho:
            try:
                if importar_produtos_csv(caminho):
                    messagebox.showinfo("Sucesso", "Produtos importados com sucesso!")
                else:
                    messagebox.showwarning("Aviso", "Alguns produtos não foram importados")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao importar:\n{e}")

    def tela_registrar_entrada(self):
        frame, popup = self.criar_janela_popup("Registrar Entrada")
        
        produtos = obter_produtos()
        nomes_produtos = [p[1] for p in produtos]
        
        self.produto_entrada = ctk.CTkComboBox(frame, values=nomes_produtos)
        self.quant_entrada = ctk.CTkEntry(frame)
        self.data_entrada = ctk.CTkEntry(frame, placeholder_text=datetime.now().strftime("%d/%m/%Y"))
        
        ctk.CTkLabel(frame, text="Produto:").pack(pady=(10, 5))
        self.produto_entrada.pack(pady=5)
        
        ctk.CTkLabel(frame, text="Quantidade:").pack(pady=(10, 5))
        self.quant_entrada.pack(pady=5)
        
        ctk.CTkLabel(frame, text="Data:").pack(pady=(10, 5))
        self.data_entrada.pack(pady=5)
        
        registrar_btn = ctk.CTkButton(
            frame,
            text="Registrar Entrada (Enter)",
            command=lambda: self.registrar_entrada(popup),
            fg_color=self.cor_principal
        )
        registrar_btn.pack(pady=20)
        
        self.botao_ativo = registrar_btn
        self.produto_entrada.focus()
        popup.bind('<Return>', lambda e: registrar_btn.invoke())
    
    def registrar_entrada(self, popup):
        produto_nome = self.produto_entrada.get()
        quant = self.quant_entrada.get()
        
        if not produto_nome:
            messagebox.showwarning("Aviso", "Selecione um produto!")
            self.produto_entrada.focus()
            return
        
        try:
            quantidade = int(quant)
            if quantidade <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Quantidade deve ser um número inteiro positivo!")
            self.quant_entrada.focus()
            return
        
        # Obtém o ID do produto
        produtos = obter_produtos()
        produto_id = next(p[0] for p in produtos if p[1] == produto_nome)
        
        registrar_movimentacao(
            produto_id=produto_id,
            tipo='entrada',
            quantidade=quantidade,
            responsavel=self.usuario_logado['nome']
        )
        
        messagebox.showinfo("Sucesso", "Entrada registrada com sucesso!")
        popup.destroy()

    def tela_registrar_saida(self):
        frame, popup = self.criar_janela_popup("Registrar Saída")
        
        produtos = obter_produtos()
        nomes_produtos = [p[1] for p in produtos]
        
        self.produto_saida = ctk.CTkComboBox(frame, values=nomes_produtos)
        self.quant_saida = ctk.CTkEntry(frame)
        self.motivo_saida = ctk.CTkEntry(frame, placeholder_text="Ex: Venda, Uso interno")
        
        ctk.CTkLabel(frame, text="Produto:").pack(pady=(10, 5))
        self.produto_saida.pack(pady=5)
        
        ctk.CTkLabel(frame, text="Quantidade:").pack(pady=(10, 5))
        self.quant_saida.pack(pady=5)
        
        ctk.CTkLabel(frame, text="Motivo:").pack(pady=(10, 5))
        self.motivo_saida.pack(pady=5)
        
        registrar_btn = ctk.CTkButton(
            frame,
            text="Registrar Saída (Enter)",
            command=lambda: self.registrar_saida(popup),
            fg_color="#FF6347",
            hover_color="#FF4500"
        )
        registrar_btn.pack(pady=20)
        
        self.botao_ativo = registrar_btn
        self.produto_saida.focus()
        popup.bind('<Return>', lambda e: registrar_btn.invoke())
    
    def registrar_saida(self, popup):
        produto_nome = self.produto_saida.get()
        quant = self.quant_saida.get()
        motivo = self.motivo_saida.get()
        
        if not produto_nome:
            messagebox.showwarning("Aviso", "Selecione um produto!")
            self.produto_saida.focus()
            return
        
        try:
            quantidade = int(quant)
            if quantidade <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Quantidade deve ser um número inteiro positivo!")
            self.quant_saida.focus()
            return
        
        # Obtém o ID do produto
        produtos = obter_produtos()
        produto_id = next(p[0] for p in produtos if p[1] == produto_nome)
        
        registrar_movimentacao(
            produto_id=produto_id,
            tipo='saida',
            quantidade=quantidade,
            responsavel=self.usuario_logado['nome'],
            motivo=motivo
        )
        
        messagebox.showinfo("Sucesso", "Saída registrada com sucesso!")
        popup.destroy()

    def tela_movimentacoes(self):
        frame, popup = self.criar_janela_popup("Histórico de Movimentações", 900, 600)
        
        # Treeview
        tree = ttk.Treeview(frame, columns=("ID", "Data", "Tipo", "Produto", "Quantidade", "Responsável", "Motivo"), show="headings")
        
        # Configuração das colunas
        tree.heading("ID", text="ID")
        tree.column("ID", width=50, anchor="center")
        
        tree.heading("Data", text="Data")
        tree.column("Data", width=120, anchor="center")
        
        tree.heading("Tipo", text="Tipo")
        tree.column("Tipo", width=80, anchor="center")
        
        tree.heading("Produto", text="Produto")
        tree.column("Produto", width=150, anchor="w")
        
        tree.heading("Quantidade", text="Qtd.")
        tree.column("Quantidade", width=80, anchor="center")
        
        tree.heading("Responsável", text="Responsável")
        tree.column("Responsável", width=120, anchor="w")
        
        tree.heading("Motivo", text="Motivo")
        tree.column("Motivo", width=200, anchor="w")
        
        # Scrollbar
        scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        
        # Carrega os dados
        movimentacoes = obter_movimentacoes()
        for mov in movimentacoes:
            tree.insert("", "end", values=mov)

if __name__ == "__main__":
    root = ctk.CTk()
    app = EstoqueApp(root)
    root.mainloop()