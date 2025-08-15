import sqlite3
from datetime import datetime
import csv

def conectar():
    """Conecta ao banco de dados SQLite"""
    conn = sqlite3.connect('estoque.db')
    return conn

def criar_tabelas():
    """Cria as tabelas necessárias no banco de dados"""
    conn = conectar()
    cursor = conn.cursor()
    
    # Tabela de usuários
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        senha TEXT NOT NULL,
        tipo TEXT NOT NULL
    )''')
    
    # Tabela de produtos (ATUALIZADA com estoque_minimo)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        descricao TEXT,
        quantidade INTEGER NOT NULL,
        estoque_minimo INTEGER DEFAULT 0
    )''')
    
    # Tabela de movimentações
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS movimentacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produto_id INTEGER NOT NULL,
        tipo TEXT NOT NULL,  -- 'entrada' ou 'saida'
        quantidade INTEGER NOT NULL,
        data TEXT NOT NULL,
        responsavel TEXT NOT NULL,
        motivo TEXT,
        FOREIGN KEY (produto_id) REFERENCES produtos (id)
    )''')
    
    conn.commit()
    conn.close()

def validar_login(nome, senha):
    """Valida as credenciais do usuário"""
    conn = conectar()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, nome, tipo FROM usuarios WHERE nome = ? AND senha = ?', 
                  (nome, senha))
    usuario = cursor.fetchone()
    conn.close()
    
    if usuario:
        return {'id': usuario[0], 'nome': usuario[1], 'tipo': usuario[2]}
    return None

def cadastrar_usuario(nome, senha, tipo):
    """Cadastra um novo usuário"""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        cursor.execute('INSERT INTO usuarios (nome, senha, tipo) VALUES (?, ?, ?)', 
                      (nome, senha, tipo))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def adicionar_produto(nome, descricao, quantidade, estoque_minimo=0):
    """Adiciona um novo produto ao estoque (ATUALIZADA com estoque_minimo)"""
    conn = conectar()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO produtos (nome, descricao, quantidade, estoque_minimo) 
        VALUES (?, ?, ?, ?)
    ''', (nome, descricao, quantidade, estoque_minimo))
    conn.commit()
    conn.close()

def obter_produtos(filtro=None):
    """Obtém todos os produtos, opcionalmente filtrados (ATUALIZADA com estoque_minimo)"""
    conn = conectar()
    cursor = conn.cursor()
    
    if filtro:
        cursor.execute('''
            SELECT id, nome, descricao, quantidade, estoque_minimo 
            FROM produtos 
            WHERE nome LIKE ?
        ''', (f'%{filtro}%',))
    else:
        cursor.execute('''
            SELECT id, nome, descricao, quantidade, estoque_minimo 
            FROM produtos
        ''')
    
    produtos = cursor.fetchall()
    conn.close()
    return produtos

def registrar_movimentacao(produto_id, tipo, quantidade, responsavel, motivo=None):
    """Registra uma movimentação (entrada ou saída)"""
    conn = conectar()
    cursor = conn.cursor()
    
    # Atualiza o estoque
    if tipo == 'entrada':
        cursor.execute('UPDATE produtos SET quantidade = quantidade + ? WHERE id = ?', 
                      (quantidade, produto_id))
    else:  # saída
        cursor.execute('UPDATE produtos SET quantidade = quantidade - ? WHERE id = ?', 
                      (quantidade, produto_id))
    
    # Registra a movimentação
    data = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO movimentacoes 
        (produto_id, tipo, quantidade, data, responsavel, motivo) 
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (produto_id, tipo, quantidade, data, responsavel, motivo))
    
    conn.commit()
    conn.close()

def obter_movimentacoes():
    """Obtém todas as movimentações"""
    conn = conectar()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT m.id, m.data, m.tipo, p.nome, m.quantidade, m.responsavel, m.motivo
        FROM movimentacoes m
        JOIN produtos p ON m.produto_id = p.id
        ORDER BY m.data DESC
    ''')
    
    movimentacoes = cursor.fetchall()
    conn.close()
    return movimentacoes

def produtos_estoque_baixo():
    """Obtém produtos com estoque abaixo do mínimo (ATUALIZADA para usar estoque_minimo)"""
    conn = conectar()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, nome, descricao, quantidade, estoque_minimo 
        FROM produtos 
        WHERE quantidade < estoque_minimo
    ''')
    
    produtos = cursor.fetchall()
    conn.close()
    return produtos

def exportar_estoque_csv(caminho_arquivo):
    """Exporta todos os produtos para um arquivo CSV (ATUALIZADA com estoque_minimo)"""
    conn = conectar()
    cursor = conn.cursor()
    
    cursor.execute('SELECT nome, descricao, quantidade, estoque_minimo FROM produtos')
    produtos = cursor.fetchall()
    
    with open(caminho_arquivo, 'w', newline='', encoding='utf-8') as arquivo:
        writer = csv.writer(arquivo)
        writer.writerow(['Nome', 'Descrição', 'Quantidade', 'Estoque_Mínimo'])
        writer.writerows(produtos)
    
    conn.close()
    return True

def importar_produtos_csv(caminho_arquivo):
    """Importa produtos de um arquivo CSV (ATUALIZADA com estoque_minimo)"""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        with open(caminho_arquivo, 'r', newline='', encoding='utf-8') as arquivo:
            reader = csv.DictReader(arquivo)
            for linha in reader:
                nome = linha.get('Nome') or linha.get('nome')
                descricao = linha.get('Descrição') or linha.get('descricao') or ''
                quantidade = linha.get('Quantidade') or linha.get('quantidade') or '0'
                estoque_minimo = linha.get('Estoque_Mínimo') or linha.get('estoque_minimo') or '0'
                
                if nome and quantidade.isdigit() and estoque_minimo.isdigit():
                    try:
                        cursor.execute('''
                            INSERT INTO produtos (nome, descricao, quantidade, estoque_minimo) 
                            VALUES (?, ?, ?, ?)
                        ''', (nome, descricao, int(quantidade), int(estoque_minimo)))
                    except sqlite3.IntegrityError:
                        continue
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro ao importar CSV: {e}")
        return False
    finally:
        conn.close()

def remover_produto(produto_id):
    """Remove um produto do banco de dados"""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        # Verifica se há movimentações para este produto
        cursor.execute('SELECT COUNT(*) FROM movimentacoes WHERE produto_id = ?', (produto_id,))
        if cursor.fetchone()[0] > 0:
            return False  # Não permite remover produtos com histórico
        
        cursor.execute('DELETE FROM produtos WHERE id = ?', (produto_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Erro ao remover produto: {e}")
        return False
    finally:
        conn.close()

def atualizar_quantidade_produto(produto_id, nova_quantidade):
    """Atualiza a quantidade de um produto no estoque (NOVA FUNÇÃO)"""
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE produtos SET quantidade = ? WHERE id = ?",
            (nova_quantidade, produto_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Erro ao atualizar quantidade: {e}")
        return False
    finally:
        conn.close()

# Cria as tabelas ao importar o módulo
criar_tabelas()

