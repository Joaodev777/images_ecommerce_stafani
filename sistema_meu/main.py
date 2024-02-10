from flask import Flask, render_template, request, redirect, url_for, g, session, send_file, Response, jsonify, request
import sqlite3 as sql
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta
import pdfkit  # Import the pdfkit library
from weasyprint import HTML
import schedule
import pytz


from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)


# Function to get a database connection
def get_db_connection():
    return sql.connect('informações.db')

# Create the transactions table if it doesn't exist
with get_db_connection() as db:
    cursor = db.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transacoes(
        id INTEGER PRIMARY KEY,
            nome TEXT,
            tipo TEXT,
            valor REAL,
            data_lanc DATE,
            obs TEXT,
            referente TEXT,
            forma_pag TEXT,
            data_lanc_transacoes DATE
            
        )
    ''')
#     cursor = db.cursor()
#     cursor.execute(
#         '''
#         CREATE TABLE tarefas (
#         tarefa_id INTEGER PRIMARY KEY,
#         nome TEXT NOT NULL,
#         descricao TEXT,
#         data_limite DATETIME NOT NULL,
#         notificar INTEGER NOT NULL
# );
#         '''
#     )

    cursor = db.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cadastro_pessoas_empresas(
        pessoa_empresa_id INTEGER PRIMARY KEY,
        nome_pessoas_empresas TEXT,
        tipo_pessoas_empresas TEXT,
        nome_social TEXT,
        cpf_cnpj TEXT,
        classificacao_pessoas_empresas TEXT,
        numero_1 TEXT,
        numero_2 TEXT,
        numero_3 TEXT,
        email_pessoas_empresas TEXT,
        cep_pessoas_empresas TEXT,
        rua_pessoas_empresas TEXT,
        bairro_pessoas_empresas TEXT,
        observacao_pessoas_empresas TEXT,
        data_lanc_pessoas_empresas DATE
    )
    ''')
    

@app.route('/')
def index():
      # Use context manager for database connection
    with get_db_connection() as db:
        cursor = db.cursor()

        # Obter parâmetros do filtro
        tipo_transacao = request.args.get('tipo_transacao', 'all')
        referente_transacao = request.args.get('referente_transacao', '')
        nome_transacao = request.args.get('nome_transacao', '')
        valor_transacao = request.args.get('valor_transacao', '')
        dia_referente = request.args.get('data_lancamento', '')
        obs_transacao = request.args.get('observacao_transacao', '')
        forma_pagamento = request.args.get('form_pag', '')

        # Construir a query SQL base
        query = "SELECT * FROM transacoes WHERE 1=1"

        # Adicionar condições ao filtro
        if tipo_transacao != 'all':
            query += f" AND tipo = '{tipo_transacao}'"

        if referente_transacao:
            query += f" AND referente LIKE '%{referente_transacao}%'"
        if nome_transacao:
            query += f" AND nome LIKE '%{nome_transacao}%'"

        if valor_transacao:
            query += f" AND valor = {float(valor_transacao)}"
        if dia_referente:
            query += f" AND data_lanc = '{dia_referente}'"
        if obs_transacao:
            query += f" AND obs LIKE '%{obs_transacao}%'"
        # Add condition for payment method
        if forma_pagamento:
            query += f" AND forma_pag = '{forma_pagamento}'"

        # Executar a query no banco de dados
        cursor.execute(query)
        transacoes = cursor.fetchall()

        # Fetch all transactions and expenses from the database
        cursor.execute("SELECT * FROM transacoes WHERE tipo = 'despesa'")
        despesas = cursor.fetchall()

        cursor.execute("SELECT * FROM transacoes WHERE tipo = 'receita'")
        receitas = cursor.fetchall()

        # Calculate the sum of despesas
        total_despesas = sum(float(transacao[3]) for transacao in transacoes if transacao[2] == 'Despesa')
        total_receitas = sum(float(transacao[3]) for transacao in transacoes if transacao[2] == 'Receita')

        # Calculate the total (sum of receitas and despesas)
        total = total_receitas - total_despesas

    return render_template('dashboard.html',  despesas=despesas, receitas=receitas, total_despesas=total_despesas, total_receitas=total_receitas, total=total)


@app.route('/adicionar_transacao', methods=['POST'])
def adicionar_transacao():
    nome = request.form.get('nome_transacao')
    tipo = request.form.get('tipo_transacao')
    valor = request.form.get('valor_transacao')
    obs = request.form.get('observacao_transacao')
   # Formatando a data para o formato desejado (DD/MM/YYYY)
    data_str = request.form.get('data_lancamento')
    data = datetime.strptime(data_str, '%Y-%m-%d').strftime('%d/%m/%Y')
    referente = request.form.get('referente_transacao')
    form_pag = request.form.get('form_pag')
    
    # Dia que inseriu o cadastro no banco
    data_time_transacoes = datetime.now()
    data_lanc_transacoes = request.form.get(data_time_transacoes)

    # Use context manager for database connection
    with get_db_connection() as db:
        cursor = db.cursor()
        cursor.execute(
            '''
            INSERT INTO transacoes (nome, tipo, valor, data_lanc, obs, referente, forma_pag, data_lanc_transacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (nome, tipo, valor, data, obs, referente, form_pag, data_lanc_transacoes)
        )

        db.commit()

    return redirect('/transacoes')


@app.route('/transacoes')
def tabela():
    # Use context manager for database connection
    with get_db_connection() as db:
        cursor = db.cursor()

        # Obter parâmetros do filtro
        tipo_transacao = request.args.get('tipo_transacao', 'all')
        referente_transacao = request.args.get('referente_transacao', '')
        nome_transacao = request.args.get('nome_transacao', '')
        valor_transacao = request.args.get('valor_transacao', '')
        dia_referente = request.args.get('data_lancamento', '')
        obs_transacao = request.args.get('observacao_transacao', '')
        forma_pagamento = request.args.get('form_pag', '')

        # Construir a query SQL base
        query = "SELECT * FROM transacoes WHERE 1=1"

        # Adicionar condições ao filtro
        if tipo_transacao != 'all':
            query += f" AND tipo = '{tipo_transacao}'"

        if referente_transacao:
            query += f" AND referente LIKE '%{referente_transacao}%'"
        if nome_transacao:
            query += f" AND nome LIKE '%{nome_transacao}%'"

        if valor_transacao:
            query += f" AND valor = {float(valor_transacao)}"
        if dia_referente:
            query += f" AND data_lanc = '{dia_referente}'"
        if obs_transacao:
            query += f" AND obs LIKE '%{obs_transacao}%'"
        # Add condition for payment method
        if forma_pagamento:
            query += f" AND forma_pag = '{forma_pagamento}'"

        # Executar a query no banco de dados
        cursor.execute(query)
        transacoes = cursor.fetchall()

        # Fetch all transactions and expenses from the database
        cursor.execute("SELECT * FROM transacoes WHERE tipo = 'despesa'")
        despesas = cursor.fetchall()

        cursor.execute("SELECT * FROM transacoes WHERE tipo = 'receita'")
        receitas = cursor.fetchall()

        # Calculate the sum of despesas
        total_despesas = sum(float(transacao[3]) for transacao in transacoes if transacao[2] == 'Despesa')
        total_receitas = sum(float(transacao[3]) for transacao in transacoes if transacao[2] == 'Receita')

        # Calculate the total (sum of receitas and despesas)
        total = total_receitas - total_despesas

    return render_template('transacoes.html', transacoes=transacoes, despesas=despesas, receitas=receitas, total_despesas=total_despesas, total_receitas=total_receitas, total=total)

# APAGAR TRANSACAO

@app.route('/apagar_transacao/<int:id>', methods=['POST'])
def apagar_transacao(id):
    with get_db_connection() as db:
        cursor = db.cursor()
        
        # Excluir transação da tabela principal
        cursor.execute("DELETE FROM transacoes WHERE id = ?", (id,))
        db.commit()

    return redirect('/transacoes')



# Exportar informações



@app.route('/exportar_pdf', methods=['GET'])
def exportar_pdf():
    with get_db_connection() as db:
        cursor = db.cursor()

        # Obtain filter parameters
        tipo_transacao = request.args.get('tipo_transacao', 'all')
        referente_transacao = request.args.get('referente_transacao', '')
        nome_transacao = request.args.get('nome_transacao', '')
        valor_transacao = request.args.get('valor_transacao', '')
        dia_referente = request.args.get('data_lancamento', '')
        obs_transacao = request.args.get('observacao_transacao', '')
        forma_pagamento = request.args.get('form_pag', '')

        # Construct the base SQL query
        query_conditions = ["SELECT * FROM transacoes WHERE 1=1"]

        # Add conditions to the filter
        if tipo_transacao != 'all':
            query_conditions.append(f"tipo = '{tipo_transacao}'")
        if referente_transacao:
            query_conditions.append(f"referente LIKE '%{referente_transacao}%'")
        if nome_transacao:
            query_conditions.append(f"nome LIKE '%{nome_transacao}%'")
        if valor_transacao:
            query_conditions.append(f"valor = {float(valor_transacao)}")
        if dia_referente:
            query_conditions.append(f"data_lanc = '{dia_referente}'")
        if obs_transacao:
            query_conditions.append(f"obs LIKE '%{obs_transacao}%'")
        if forma_pagamento:
            query_conditions.append(f"forma_pag = '{forma_pagamento}'")

        # Join the conditions to form the final query
        query = " AND ".join(query_conditions)

        # Execute the query on the database
        cursor.execute(query)
        transacoes = cursor.fetchall()

        # Convert the transactions to a Pandas DataFrame
        df = pd.DataFrame(transacoes, columns=['id', 'nome', 'tipo', 'valor', 'data_lanc', 'obs', 'referente', 'forma_pag'])  # Adjusted column names

        # Create an HTML string from the DataFrame
        html_string = df.to_html(index=False)

        # Create an HTML string from the DataFrame with styles
        html_string = """
<html>
    <head>
        <link href='https://unpkg.com/boxicons@2.1.4/css/boxicons.min.css' rel='stylesheet'>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"
            integrity="sha384-C6RzsynM9kWDrMNeT87bh95OGNyZPhcTNXj1NW7RuBCsyN/o0jlpcV8Qyq46cDfL"
            crossorigin="anonymous"></script>
    
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Lilita+One&display=swap" rel="stylesheet">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Black+Ops+One&display=swap" rel="stylesheet">
        <style>
                      @page {
                    size: landscape;
                }
            body {
                font-family: 'Arial', sans-serif;
                color: #ffffff;
                background-color: #050022;
                text-align: center;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }
            th, td {
                border-bottom: 1px solid #00d79e;
                padding: 10px;
                text-align: left;
            }
            th {
                background-color: #8000ff;
                color: #fff;
            }
            td {
                background-color: #050022;
            }
        </style>
    </head>
    <body>
        <h1 style="    font-family: 'Black Ops One', system-ui;
        font-size: 50px;
    
        color: #00ff91;border-bottom:1px solid #00ff91   ">Transaction Report JGByte</h1>
        """ + df.to_html(index=False) + """
    </body>
    </html>
        
        """

        # Generate PDF from HTML using WeasyPrint
        pdf_bytes = HTML(string=html_string).write_pdf()

    # Create a BytesIO buffer and write PDF bytes to it
    pdf_buffer = BytesIO(pdf_bytes)

    return send_file(pdf_buffer, download_name='JGByte_transactions.pdf', as_attachment=True, mimetype='application/pdf')


# ==================================================================
#                          PESSOAS OU EMPRESAS
# ==================================================================

@app.route('/pessoas_ou_empresas')
def pessoas_ou_empresas():
    # Use context manager for database connection
    with get_db_connection() as db:
        cursor = db.cursor()

        # Obter parâmetros do filtro
        tipo_transacao = request.args.get('tipo_transacao', 'all')
        referente_transacao = request.args.get('referente_transacao', '')
        nome_transacao = request.args.get('nome_transacao', '')
        valor_transacao = request.args.get('valor_transacao', '')
        dia_referente = request.args.get('data_lancamento', '')
        obs_transacao = request.args.get('observacao_transacao', '')
        forma_pagamento = request.args.get('form_pag', '')

        # Construir a query SQL base
        query = "SELECT * FROM transacoes WHERE 1=1"

        # Adicionar condições ao filtro
        if tipo_transacao != 'all':
            query += f" AND tipo = '{tipo_transacao}'"

        if referente_transacao:
            query += f" AND referente LIKE '%{referente_transacao}%'"
        if nome_transacao:
            query += f" AND nome LIKE '%{nome_transacao}%'"

        if valor_transacao:
            query += f" AND valor = {float(valor_transacao)}"
        if dia_referente:
            query += f" AND data_lanc = '{dia_referente}'"
        if obs_transacao:
            query += f" AND obs LIKE '%{obs_transacao}%'"
        # Add condition for payment method
        if forma_pagamento:
            query += f" AND forma_pag = '{forma_pagamento}'"

        # Executar a query no banco de dados
        cursor.execute(query)
        transacoes = cursor.fetchall()

     # Fetch all transactions and expenses from the database
    cursor.execute("SELECT * FROM transacoes WHERE tipo = 'despesa'")
    despesas = cursor.fetchall()

    cursor.execute("SELECT * FROM transacoes WHERE tipo = 'receita'")
    receitas = cursor.fetchall()

    # Calculate the sum of despesas
    total_despesas = sum(float(transacao[3]) for transacao in transacoes if transacao[2] == 'Despesa')
    total_receitas = sum(float(transacao[3]) for transacao in transacoes if transacao[2] == 'Receita')

    # Calculate the total (sum of receitas and despesas)
    total = total_receitas - total_despesas
    
    
        # Fetch all people or companies from the database
    cursor.execute("SELECT * FROM cadastro_pessoas_empresas")
    pessoas_empresas = cursor.fetchall()

    return render_template('pessoas_ou_empresas.html', despesas=despesas, receitas=receitas, total_despesas=total_despesas, total_receitas=total_receitas, total=total, pessoas_empresas=pessoas_empresas)


# ===============================================================================
#                        ADIONANDO PESSOAS E EMPRESAS
#===============================================================================
@app.route('/adicionar_pessoas_empresas', methods=['POST'])
def adicionar_empresas():
    nome = request.form.get('nome_pessoas_empresas')
    tipo = request.form.get('tipo_pessoas_empresas')
    nome_social = request.form.get('nome_social')
    cpf_cnpj = request.form.get('cpf_cnpj')
    classificacao_pessoas_empresas = request.form.get('classificacao_pessoas_empresas')
    numero_1 = request.form.get('numero_1')
    numero_2 = request.form.get('numero_2')
    numero_3 = request.form.get('numero_3')
    email_pessoas_empresas = request.form.get('email_pessoas_empresas')
    cep_pessoas_empresas = request.form.get('cep_pessoas_empresas')
    rua_pessoas_empresas = request.form.get('rua_pessoas_empresas')
    bairro_pessoas_empresas = request.form.get('bairro_pessoas_empresas')
    observacao_pessoas_empresas = request.form.get('observacao_pessoas_empresas')
    
    data_time_pessoas_empresas = datetime.now()
    data_lanc_pessoas_empresas = request.form.get(data_time_pessoas_empresas)
    
    # Use context manager for database connection
    with get_db_connection() as db:
        cursor = db.cursor()
        cursor.execute(
            '''
            INSERT INTO cadastro_pessoas_empresas (nome_pessoas_empresas, tipo_pessoas_empresas, nome_social, cpf_cnpj,
            classificacao_pessoas_empresas, numero_1, numero_2, numero_3, email_pessoas_empresas, cep_pessoas_empresas,
            rua_pessoas_empresas, bairro_pessoas_empresas, observacao_pessoas_empresas, data_lanc_pessoas_empresas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (nome, tipo, nome_social, cpf_cnpj, classificacao_pessoas_empresas, numero_1, numero_2, numero_3,
            email_pessoas_empresas, cep_pessoas_empresas, rua_pessoas_empresas, bairro_pessoas_empresas,
            observacao_pessoas_empresas, data_lanc_pessoas_empresas)
        )

        db.commit()

    return redirect('/pessoas_ou_empresas')

# ================================================
#                       editar
# ================================================

@app.route('/editar_pessoa_empresa/<int:pessoa_empresa_id>', methods=['GET', 'POST'])
def editar_pessoa_empresa(pessoa_empresa_id):
    # Recupere as informações existentes do banco de dados com base no ID
    with get_db_connection() as db:
        cursor = db.cursor()
        cursor.execute('SELECT * FROM cadastro_pessoas_empresas WHERE pessoa_empresa_id = ?', (pessoa_empresa_id,))
        pessoa_empresa = cursor.fetchone()

    if request.method == 'POST':
        # Processar os dados enviados pelo formulário de edição
        nome = request.form.get('nome_pessoas_empresas')
        tipo = request.form.get('tipo_pessoas_empresas')
        nome_social = request.form.get('nome_social')
        cpf_cnpj = request.form.get('cpf_cnpj')
        classificacao_pessoas_empresas = request.form.get('classificacao_pessoas_empresas')
        numero_1 = request.form.get('numero_1')
        numero_2 = request.form.get('numero_2')
        numero_3 = request.form.get('numero_3')
        email_pessoas_empresas = request.form.get('email_pessoas_empresas')
        cep_pessoas_empresas = request.form.get('cep_pessoas_empresas')
        rua_pessoas_empresas = request.form.get('rua_pessoas_empresas')
        bairro_pessoas_empresas = request.form.get('bairro_pessoas_empresas')
        observacao_pessoas_empresas = request.form.get('observacao_pessoas_empresas')
        # Adicione aqui os outros campos que precisam ser atualizados

        # Atualize as informações no banco de dados
        with get_db_connection() as db:
            cursor = db.cursor()
            cursor.execute(
                '''
                UPDATE cadastro_pessoas_empresas
                SET nome_pessoas_empresas=?, tipo_pessoas_empresas=?, nome_social=?, cpf_cnpj=?,
                classificacao_pessoas_empresas=?, numero_1=?, numero_2=?, numero_3=?, email_pessoas_empresas=?,
                cep_pessoas_empresas=?, rua_pessoas_empresas=?, bairro_pessoas_empresas=?,
                observacao_pessoas_empresas=?
                WHERE pessoa_empresa_id=?
                ''',
                (nome, tipo, nome_social, cpf_cnpj, classificacao_pessoas_empresas, numero_1, numero_2, numero_3,
                email_pessoas_empresas, cep_pessoas_empresas, rua_pessoas_empresas, bairro_pessoas_empresas,
                observacao_pessoas_empresas, pessoa_empresa_id)
            )
            db.commit()

        # Redirecione para a página principal ou outra página desejada após a edição
        return redirect('/pessoas_ou_empresas')

    # Renderize a página de edição com as informações existentes
    return render_template('editar_pessoa_empresa.html', pessoa_empresa=pessoa_empresa)


# Relatorios

@app.route('/relatorios')
def relatorio():
    return render_template('relatorios.html')




if __name__ == '__main__':
    app.run(debug=True)
