from flask import Flask, request, jsonify, render_template
from flask_bcrypt import Bcrypt
import jwt
import uuid
import datetime
import sqlite3
from uuid import uuid4  
import qrcode
import io
import os
import mercadopago
from functools import wraps
from apscheduler.schedulers.background import BackgroundScheduler
from flask import send_from_directory
import smtplib
from email.message import EmailMessage

EMAIL_EMISSOR = 'seuemail@gmail.com' #email da academia 
SENHA_EMAIL = 'senha_de_app'  # use senha de app se for Gmail

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SECRET_KEY'] = 'Creator_russian_1945@_sins_dav1d_2026'
DB = 'alunos.db'

# Atualização de status automática
def verificar_vencimentos():
    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        hoje = datetime.date.today()

        cur.execute("""
            SELECT p.id, a.email, a.nome, p.vencimento, p.status
            FROM pagamentos p
            JOIN alunos a ON a.id = p.aluno_id
        """)
        pagamentos = cur.fetchall()

        for pid, email, nome, venc_str, status in pagamentos:
            vencimento = datetime.datetime.strptime(venc_str, "%Y-%m-%d").date()
            dias = (vencimento - hoje).days

            if status == 'ativo' and dias == 3:
                enviar_email(email, "Plano quase vencendo", f"Ol� {nome}, seu plano vence em 3 dias.")
                enviar_whatsapp(usuario.telefone, "seu plano ira vencer em 3 dias, renove agora!")
            elif status == 'ativo' and dias == 0:
                enviar_email(email, "Hoje � o vencimento!", f"Ol� {nome}, hoje � o �ltimo dia do seu plano.")
                enviar_whatsapp(usuario.telefone, "Seu plano est� vencendo! Renove imediatamente.")
            elif status == 'ativo' and dias < 0:
                cur.execute("UPDATE pagamentos SET status = 'inativo' WHERE id = ?", (pid,))
                con.commit()
                enviar_email(email, "Plano vencido", f"{nome}, seu plano venceu. Renove para continuar o acesso.")
                enviar_whatsapp(usuario.telefone, "Seu plano est� inativo  Renove ele imediatamente.")

scheduler = BackgroundScheduler()
scheduler.add_job(verificar_vencimentos, 'interval', hours=24)
scheduler.start()

# Criação de tabelas
def criar_tabela_alunos():
    with sqlite3.connect(DB) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS alunos (
                id TEXT PRIMARY KEY,
                nome TEXT,
                email TEXT UNIQUE,
                senha TEXT,
                cpf TEXT,
                telefone TEXT
            )
        """)

def criar_tabela_pagamentos():
    with sqlite3.connect(DB) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS pagamentos (
                id TEXT PRIMARY KEY,
                aluno_id TEXT,
                plano TEXT,
                vencimento TEXT,
                status TEXT
            )
        """)

criar_tabela_alunos()
criar_tabela_pagamentos()

# JWT Middleware
def token_requerido(f):
    @wraps(f)
    def decorada(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"mensagem": "Token ausente!"}), 401
        try:
            token_limpo = token.replace("Bearer ", "")
            dados = jwt.decode(token_limpo, app.config['SECRET_KEY'], algorithms=['HS256'])
            aluno_id = dados['id']
        except jwt.ExpiredSignatureError:
            return jsonify({"mensagem": "Token expirado!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"mensagem": "Token inválido!"}), 401
        return f(aluno_id, *args, **kwargs)
    return decorada

@app.route('/')
def home():
    return "API Center com SQLite feito por Davi Leonardo 😁"

@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    dados = request.get_json()
    senha_criptografada = bcrypt.generate_password_hash(dados.get("senha", "")).decode('utf-8')
    novo_id = str(uuid.uuid4())

    try:
        with sqlite3.connect(DB) as con:
            con.execute("""
                INSERT INTO alunos (id, nome, email, senha, cpf, telefone)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (novo_id, dados.get("nome"), dados.get("email"), senha_criptografada, dados.get("cpf"), dados.get("telefone")))
        return jsonify({"mensagem": "Aluno cadastrado com sucesso!"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"mensagem": "Email já cadastrado!"}), 400

@app.route('/login', methods=['POST'])
def login():
    dados = request.get_json()
    email = dados.get("email")
    senha = dados.get("senha")

    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        cur.execute("SELECT id, nome, senha FROM alunos WHERE email = ?", (email,))
        resultado = cur.fetchone()

    if resultado and bcrypt.check_password_hash(resultado[2], senha):
        token = jwt.encode({
            'id': resultado[0],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({"mensagem": "Acesso liberado", "token": token, "nome": resultado[1]})
    
    return jsonify({"mensagem": "Acesso negado"}), 401

@app.route('/painel', methods=['GET'])
@token_requerido
def painel(aluno_id):
    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        cur.execute("SELECT nome, email FROM alunos WHERE id = ?", (aluno_id,))
        aluno = cur.fetchone()

    if aluno:
        return jsonify({"mensagem": f"Bem-vindo ao painel, {aluno[0]}!", "seu_email": aluno[1]})
    return jsonify({"mensagem": "Aluno não encontrado!"}), 404

@app.route('/planos', methods=['GET'])
def planos():
    planos_academia = {
        "1mes": "R$64",
        "2mes": "R$94",
        "3mes": "R$124",
        "8mes": "R$754",
        "12mes": "R$500"
    }
    return jsonify(planos_academia)

@app.route('/pagamento', methods=['POST'])
@token_requerido
def pagamento(aluno_id):
    dados = request.get_json()
    plano = dados.get("plano")

    valores = {
        "1mes": 64,
        "2mes": 94,
        "3mes": 124,
        "8mes": 754,
        "12mes": 500
    }

    if plano not in valores:
        return jsonify({"mensagem": "Plano inválido!"}), 400

    vencimento = (datetime.datetime.utcnow() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    pagamento_id = str(uuid.uuid4())

    with sqlite3.connect(DB) as con:
        con.execute("""
            INSERT INTO pagamentos (id, aluno_id, plano, vencimento, status)
            VALUES (?, ?, ?, ?, ?)
        """, (pagamento_id, aluno_id, plano, vencimento, "pendente"))

    return jsonify({
        "mensagem": "Pagamento pendente",
        "plano": plano,
        "valor": valores[plano],
        "qrcode_simulado": f"https://pix.simulador/evoacademy/{aluno_id}/{plano}/{valores[plano]}"
    })

@app.route('/catraca', methods=['GET'])
@token_requerido
def catraca(aluno_id):
    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        cur.execute("""
            SELECT vencimento, status FROM pagamentos
            WHERE aluno_id = ? ORDER BY vencimento DESC LIMIT 1
        """, (aluno_id,))
        resultado = cur.fetchone()

        if resultado:
            vencimento_str, status = resultado
            vencimento = datetime.datetime.strptime(vencimento_str, "%Y-%m-%d").date()
            hoje = datetime.date.today()

            if hoje > vencimento and status == "ativo":
                cur.execute("UPDATE pagamentos SET status = ? WHERE aluno_id = ?", ("inativo", aluno_id))
                con.commit()
                status = "inativo"

            if status == "ativo":
                return jsonify({
                    "status": "online",
                    "acesso": "liberado",
                    "mensagem": "Entrada autorizada. Bem-vindo à academia!"
                })

    return jsonify({
        "status": "bloqueado",
        "acesso": "negado",
        "mensagem": "Pagamento vencido. Regularize seu plano."
    }), 403

@app.route('/registrar_pagamento', methods=['POST'])
@token_requerido
def registrar_pagamento(aluno_id):
    dados = request.get_json()
    plano = dados.get("plano")

    valores = {
        "1mes": 64,
        "2mes": 94,
        "3mes": 124,
        "8mes": 754,
        "12mes": 500
    }

    if plano not in valores:
        return jsonify({"mensagem": "Plano inválido"}), 400

    vencimento = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime('%Y-%m-%d')
    pagamento_id = str(uuid.uuid4())

    with sqlite3.connect(DB) as con:
        con.execute("""
            INSERT INTO pagamentos (id, aluno_id, plano, vencimento, status)
            VALUES (?, ?, ?, ?, 'pendente')
        """, (pagamento_id, aluno_id, plano, vencimento))

    return jsonify({
        "mensagem": "Pagamento registrado como pendente.",
        "valor": valores[plano]
    })

@app.route('/confirmar_pagamento_funcionario', methods=['POST'])
def confirmar_pagamento_funcionario():
    dados = request.get_json()
    cpf = dados.get("cpf")
    plano = dados.get("plano")

    if not cpf or not plano:
        return jsonify({"mensagem": "Dados incompletos!"}), 400

    vencimento = (datetime.datetime.utcnow() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    pagamento_id = str(uuid.uuid4())

    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        cur.execute("SELECT id FROM alunos WHERE cpf = ?", (cpf,))
        aluno = cur.fetchone()
        if not aluno:
            return jsonify({"mensagem": "Aluno não encontrado!"}), 404

        aluno_id = aluno[0]

        cur.execute("""
            INSERT INTO pagamentos (id, aluno_id, plano, vencimento, status)
            VALUES (?, ?, ?, ?, 'ativo')
        """, (pagamento_id, aluno_id, plano, vencimento))

    return jsonify({"mensagem": "Pagamento confirmado e acesso liberado!"})

@app.route('/painel-funcionario')
def painel_funcionario():
    return render_template('painel_funcionario.html')

@app.route('/listar_alunos', methods=['GET'])
def listar_alunos():
    status = request.args.get("status", "ativo")
    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        cur.execute("""
            SELECT a.nome, a.email, a.cpf, a.telefone, p.status
            FROM alunos a
            JOIN pagamentos p ON a.id = p.aluno_id
            WHERE p.status = ?
        """, (status,))
        alunos = cur.fetchall()

    lista = []
    for a in alunos:
        lista.append({
            "nome": a[0],
            "email": a[1],
            "cpf": a[2],
            "telefone": a[3],
            "status": a[4]
        })
    return jsonify(lista)

@app.route('/atualizar_status', methods=['POST'])
def atualizar_status():
    dados = request.get_json()
    cpf = dados.get("cpf")
    novo_status = dados.get("status")

    if not cpf or not novo_status:
        return jsonify({"mensagem": "CPF e status são obrigatórios!"}), 400

    with sqlite3.connect(DB) as con:
     cur = con.cursor()
     cur.execute("SELECT id FROM alunos WHERE cpf = ?", (cpf,))
     aluno = cur.fetchone()
     if not aluno:
         return jsonify({"mensagem": "Aluno não encontrado!"}), 404

     aluno_id = aluno[0]
     cur.execute("""
         UPDATE pagamentos SET status = ?
         WHERE aluno_id = ? AND status != ?
     """, (novo_status, aluno_id, novo_status))
     con.commit()

 return jsonify({"mensagem": f"Status atualizado para {novo_status} com sucesso."})
    
@app.route("/site")
def site():
    return send_from_directory(".", "index.html")
    
@app.route("/recursos.html")
def recursos():
    return send_from_directory(".", "recursos.html")
    
@app.route("/preco.html")
def preco():
    return send_from_directory(os.getcwd(), "preco.html")
    
sdk = mercadopago.SDK("SEU_ACCESS_TOKEN_AQUI")

conn = sqlite3.connect('pix_db.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS pagamentos (
    id TEXT PRIMARY KEY,
    plano TEXT,
    valor REAL,
    preference_id TEXT,
    status TEXT
)
''')
conn.commit()

precos = {
    'basico': 10.00,
    'pro': 25.00,
    'premium': 50.00
}

@app.route('/gerar_pagamento', methods=['POST'])
def gerar_pagamento():
    data = request.get_json()
    plano = data.get('plano')

    if plano not in precos:
        return jsonify({'erro': 'Plano inválido'}), 400

    valor = precos[plano]
    pagamento_id = str(uuid.uuid4())

    preference_data = {
        "items": [
            {
                "title": f"Plano {plano}",
                "quantity": 1,
                "unit_price": valor
            }
        ],
        "external_reference": pagamento_id,
        "notification_url": "https://seu_dominio.com/webhook_mercadopago"
    }

    preference_response = sdk.preference().create(preference_data)
    preference = preference_response["response"]

    cursor.execute("INSERT INTO pagamentos VALUES (?, ?, ?, ?, ?)",
                   (pagamento_id, plano, valor, preference["id"], "pendente"))
    conn.commit()

    return jsonify({
        "id": pagamento_id,
        "plano": plano,
        "valor": valor,
        "preference_id": preference["id"],
        "init_point": preference["init_point"]
    })

@app.route('/webhook_mercadopago', methods=['POST'])
def webhook_mercadopago():
    data = request.json
    if data['type'] == 'payment':
        payment_id = data['data']['id']
        payment = sdk.payment().get(payment_id)
        payment_data = payment["response"]
        external_ref = payment_data['external_reference']
        status = payment_data['status']

        if status == "approved":
            cursor.execute("UPDATE pagamentos SET status = 'pago' WHERE id = ?", (external_ref,))
            conn.commit()
            
            # Buscar e-mail do aluno
            cur = sqlite3.connect(DB).cursor()
            cur.execute("""
                SELECT a.email, a.nome
                FROM alunos a
                JOIN pagamentos p ON a.id = p.aluno_id
                WHERE p.id = ?
            """, (external_ref,))
            aluno = cur.fetchone()

            if aluno:
                email, nome = aluno
                enviar_email(
                    email,
                    "Pagamento aprovado!",
                    f"Ol� {nome}, seu pagamento foi confirmado. Acesso liberado!"
                )
                enviar_whatsapp(usuario.telefone, "Seu plano foi ativado com sucesso! Obrigado por renovar.")

@app.route('/status/<pagamento_id>')
def status_pagamento(pagamento_id):
    cursor.execute("SELECT status FROM pagamentos WHERE id = ?", (pagamento_id,))
    row = cursor.fetchone()
    if not row:
        return jsonify({'status': 'erro'})
    return jsonify({'status': row[0]})

# Rota para gerar QR code do init_point (opcional)
@app.route('/qrcode/<pagamento_id>')
def gerar_qrcode(pagamento_id):
    cursor.execute("SELECT preference_id FROM pagamentos WHERE id = ?", (pagamento_id,))
    row = cursor.fetchone()
    if not row:
        return "Pagamento não encontrado", 404

    preference_id = row[0]
    # Busca URL para pagamento
    preference_response = sdk.preference().get(preference_id)
    init_point = preference_response['response']['init_point']

    img = qrcode.make(init_point)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')
    
    #criando uma rota para deletar alunos inativos a mais de 3 meses 
    @app.route('/deletar_inativos', methods=['DELETE'])
def deletar_inativos():
    hoje = datetime.date.today()
    limite = hoje - datetime.timedelta(days=90)

    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        
        # Buscar alunos com último pagamento inativo há mais de 3 meses
        cur.execute("""
            SELECT a.id FROM alunos a
            JOIN pagamentos p ON a.id = p.aluno_id
            WHERE p.status = 'inativo' AND p.vencimento <= ?
            GROUP BY a.id
        """, (limite.strftime("%Y-%m-%d"),))
        alunos_inativos = cur.fetchall()

        deletados = 0
        for (aluno_id,) in alunos_inativos:
            # Deleta os pagamentos
            cur.execute("DELETE FROM pagamentos WHERE aluno_id = ?", (aluno_id,))
            # Deleta o aluno
            cur.execute("DELETE FROM alunos WHERE id = ?", (aluno_id,))
            deletados += 1

        con.commit()

    return jsonify({"mensagem": f"{deletados} aluno(s) inativo(s) deletado(s) com sucesso!"})
    
    @app.route('/alunos_ativos', methods=['GET'])
def alunos_ativos():
    with sqlite3.connect(DB) as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        cur.execute("""
            SELECT a.id, a.nome, a.email, p.vencimento, p.valor
            FROM alunos a
            JOIN pagamentos p ON a.id = p.aluno_id
            WHERE p.status = 'ativo'
        """)
        alunos = [dict(row) for row in cur.fetchall()]

    return jsonify(alunos)
    
    @app.route('/alunos_ativos', methods=['GET'])
def alunos_ativos():
    mes = request.args.get('mes')  # Pega ?mes=05 da URL

    with sqlite3.connect(DB) as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        if mes:
            cur.execute("""
                SELECT a.id, a.nome, a.email, p.vencimento, p.valor
                FROM alunos a
                JOIN pagamentos p ON a.id = p.aluno_id
                WHERE p.status = 'ativo'
                AND strftime('%m', p.vencimento) = ?
            """, (mes,))
        else:
            cur.execute("""
                SELECT a.id, a.nome, a.email, p.vencimento, p.valor
                FROM alunos a
                JOIN pagamentos p ON a.id = p.aluno_id
                WHERE p.status = 'ativo'
            """)

        alunos = [dict(row) for row in cur.fetchall()]
        total_pago = sum(float(aluno['valor']) for aluno in alunos)

    return jsonify({
        'alunos_ativos': alunos,
        'total_pago': total_pago
    })
    
DB = 'academia.db'

# Inicializa o banco e as tabelas
def init_db():
    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        
        # Tabela de alunos
        cur.execute('''
            CREATE TABLE IF NOT EXISTS alunos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                pontos INTEGER DEFAULT 0
            )
        ''')
        
        # Tabela de acessos
        cur.execute('''
            CREATE TABLE IF NOT EXISTS acessos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                aluno_id INTEGER,
                data_hora TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (aluno_id) REFERENCES alunos(id)
            )
        ''')

# Rota para registrar acesso e adicionar pontos
@app.route('/registrar_acesso', methods=['POST'])
def registrar_acesso():
    dados = request.json
    aluno_id = dados.get('aluno_id')

    if not aluno_id:
        return jsonify({'erro': 'ID do aluno é obrigatório'}), 400

    with sqlite3.connect(DB) as con:
        cur = con.cursor()

        # Verifica se aluno existe
        cur.execute("SELECT id FROM alunos WHERE id = ?", (aluno_id,))
        aluno = cur.fetchone()
        if not aluno:
            return jsonify({'erro': 'Aluno não encontrado'}), 404

        # Registra o acesso
        cur.execute("INSERT INTO acessos (aluno_id) VALUES (?)", (aluno_id,))

        # Adiciona 10 pontos
        cur.execute("UPDATE alunos SET pontos = pontos + 10 WHERE id = ?", (aluno_id,))
        con.commit()

    return jsonify({'mensagem': 'Acesso registrado e 10 pontos adicionados'}), 201
    
       #desenvolvedor 
    @app.route('/credito')
def creditos():
    return jsonify({
        'criador': 'Davi',
        'banco': 'sqlite',
        'criado-inicio': '23/05/2025',
        'termino': '01/06/2025',
        'deploy': 'sem_previsao',
        'contato': '55999999999',
        'email': 'desenvolvedorback-end@gmail.com',
        'status': 'online'
    }), 201

# Rota para descontar pontos
@app.route('/descontar_pontos', methods=['POST'])
def descontar_pontos():
    dados = request.json
    aluno_id = dados.get('aluno_id')
    pontos_descontar = dados.get('pontos')

    if not aluno_id or not pontos_descontar:
        return jsonify({'erro': 'ID do aluno e pontos são obrigatórios'}), 400

    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        cur.execute("SELECT pontos FROM alunos WHERE id = ?", (aluno_id,))
        resultado = cur.fetchone()

        if not resultado:
            return jsonify({'erro': 'Aluno não encontrado'}), 404

        pontos_atuais = resultado[0]

        if pontos_atuais < pontos_descontar:
            return jsonify({'erro': 'Pontos insuficientes'}), 400

        cur.execute("UPDATE alunos SET pontos = pontos - ? WHERE id = ?", (pontos_descontar, aluno_id))
        con.commit()

    return jsonify({'mensagem': f'{pontos_descontar} pontos descontados com sucesso'}), 200

    init_db()
    
    #editar perfil do aluno 
 @app.route('/editar_perfil', methods=['PUT'])
@token_requerido
def editar_perfil(aluno_id):
    dados = request.get_json()
    campos = ['nome', 'email', 'telefone']
    
    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        for campo in campos:
            if campo in dados:
                cur.execute(f"UPDATE alunos SET {campo} = ? WHERE id = ?", (dados[campo], aluno_id))
        con.commit()
    return jsonify({"mensagem": "Perfil atualizado com sucesso!"})
    
    #historico de pagamento 
    @app.route('/historico_pagamentos', methods=['GET'])
@token_requerido
def historico_pagamentos(aluno_id):
    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        cur.execute("""
            SELECT plano, vencimento, status
            FROM pagamentos
            WHERE aluno_id = ?
            ORDER BY vencimento DESC
        """, (aluno_id,))
        historico = cur.fetchall()

    return jsonify([
        {"plano": h[0], "vencimento": h[1], "status": h[2]}
        for h in historico
    ])

#excluir conta do aluno
@app.route('/excluir_conta', methods=['DELETE'])
@token_requerido
def excluir_conta(aluno_id):
    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        cur.execute("DELETE FROM pagamentos WHERE aluno_id = ?", (aluno_id,))
        cur.execute("DELETE FROM alunos WHERE id = ?", (aluno_id,))
        con.commit()
    return jsonify({"mensagem": "Conta exclu�da com sucesso!"})
    
#resetar senha pelo cpf do aluno 
    @app.route('/resetar_senha', methods=['POST'])
def resetar_senha():
    dados = request.get_json()
    identificador = dados.get("email") or dados.get("cpf")
    nova_senha = bcrypt.generate_password_hash(dados.get("nova_senha")).decode('utf-8')

    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        cur.execute("""
            UPDATE alunos SET senha = ?
            WHERE email = ? OR cpf = ?
        """, (nova_senha, identificador, identificador))
        con.commit()

        if cur.rowcount == 0:
            return jsonify({"mensagem": "Usu�rio n�o encontrado!"}), 404

    return jsonify({"mensagem": "Senha redefinida com sucesso!"})
    
    #enviar email
    def enviar_email(destinatario, assunto, corpo):
    msg = EmailMessage()
    msg['Subject'] = assunto
    msg['From'] = EMAIL_EMISSOR
    msg['To'] = destinatario
    msg.set_content(corpo)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_EMISSOR, SENHA_EMAIL)
            smtp.send_message(msg)
    except Exception as e:
        print("Erro ao enviar e-mail:", e)
        
        #enviar mensagem bot whatsapp 
        def enviar_whatsapp(numero, mensagem):
    url = 'http://localhost:3001/enviar'
    payload = {"numero": numero, "mensagem": mensagem}
    try:
        r = requests.post(url, json=payload)
        print("WhatsApp enviado:", r.text)
    except Exception as e:
        print("Erro:", e)
        

# Mensagem de retorno para rotas falsas
falsa_resposta = {"mensagem": "rota falsa kkkk"}

# Rotas falsas
@app.route('/admin')
def admin():
    return jsonify(falsa_resposta)

@app.route('/root')
def root():
    return jsonify(falsa_resposta)

@app.route('/dev')
def dev():
    return jsonify(falsa_resposta)
    
    app.route('/rotas')
def rotas():
    return jsonify(falsa_resposta)
    
    app.route('/liberar')
def liberar():
    return jsonify(falsa_resposta)

@app.route('/adm')
def adm():
    return jsonify(falsa_resposta)

@app.route('/log')
def log():
    return jsonify(falsa_resposta)
    
    app.route('/developer')
def deveveloper():
    return jsonify(falsa_resposta)
    
    
    from flask import Flask, render_template, request, jsonify, redirect, url_for, session # type: ignore
import json
import requests # type: ignore
from consultas import fazer_consulta # type: ignore

app = Flask(__name__)
app.secret_key = "chave_secreta"

# Carregar usu�rios do JSON
with open("auth_config.json", "r") as file:
    AUTH_CONFIG = json.load(file)

@app.route("/site", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        for user in AUTH_CONFIG["users"]:
            if user["username"] == username and user["password"] == password:
                session["username"] = username
                session["role"] = user["role"]
                return redirect(url_for("adim"))
        
        return render_template("login.html", error="Credenciais inv�lidas")

    return render_template("login.html")

    
    return render_template("adim.html", user_type=session["role"])



@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))
    
    
    @app.route('/siteP1')
def painel_funcionario():
    return render_template('site_principal.html')

if __name__ == "__main__":
    app.run(debug=True)


if __name__ == '__main__':
    app.run(debug=True)