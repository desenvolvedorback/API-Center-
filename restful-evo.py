from flask import Flask, request, jsonify from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity import sqlite3 import datetime

app = Flask(name) app.config['JWT_SECRET_KEY'] = 'sua_chave_secreta' jwt = JWTManager(app)

Banco de dados

conn = sqlite3.connect('banco.db', check_same_thread=False) c = conn.cursor() c.execute('''CREATE TABLE IF NOT EXISTS alunos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, cpf TEXT UNIQUE, status TEXT DEFAULT 'inativo')''') c.execute('''CREATE TABLE IF NOT EXISTS pagamentos (id INTEGER PRIMARY KEY AUTOINCREMENT, cpf TEXT, plano TEXT, data TEXT, status TEXT DEFAULT 'pendente')''') conn.commit()

Rotas RESTful para alunos

@app.route('/alunos', methods=['POST']) def cadastrar_aluno(): dados = request.json try: c.execute('INSERT INTO alunos (nome, cpf) VALUES (?, ?)', (dados['nome'], dados['cpf'])) conn.commit() return jsonify({'mensagem': 'Aluno cadastrado com sucesso'}), 201 except sqlite3.IntegrityError: return jsonify({'erro': 'CPF já cadastrado'}), 400

@app.route('/alunos', methods=['GET']) @jwt_required() def listar_alunos(): c.execute('SELECT * FROM alunos') alunos = c.fetchall() return jsonify(alunos)

@app.route('/alunos/int:id', methods=['GET']) @jwt_required() def obter_aluno(id): c.execute('SELECT * FROM alunos WHERE id=?', (id,)) aluno = c.fetchone() if aluno: return jsonify(aluno) return jsonify({'erro': 'Aluno não encontrado'}), 404

@app.route('/alunos/int:id', methods=['PUT']) @jwt_required() def atualizar_aluno(id): dados = request.json c.execute('UPDATE alunos SET nome=?, cpf=?, status=? WHERE id=?', (dados['nome'], dados['cpf'], dados['status'], id)) conn.commit() return jsonify({'mensagem': 'Aluno atualizado'})

@app.route('/alunos/int:id', methods=['DELETE']) @jwt_required() def deletar_aluno(id): c.execute('DELETE FROM alunos WHERE id=?', (id,)) conn.commit() return jsonify({'mensagem': 'Aluno deletado'})

Autenticação

@app.route('/auth/login', methods=['POST']) def login(): dados = request.json c.execute('SELECT * FROM alunos WHERE cpf=?', (dados['cpf'],)) aluno = c.fetchone() if aluno: token = create_access_token(identity=aluno[2]) return jsonify({'token': token}) return jsonify({'erro': 'CPF não encontrado'}), 401

@app.route('/auth/painel', methods=['GET']) @jwt_required() def painel(): cpf = get_jwt_identity() c.execute('SELECT * FROM alunos WHERE cpf=?', (cpf,)) aluno = c.fetchone() return jsonify({'aluno': aluno})

Pagamentos

@app.route('/pagamentos', methods=['POST']) @jwt_required() def criar_pagamento(): dados = request.json cpf = get_jwt_identity() data = datetime.date.today().isoformat() c.execute('INSERT INTO pagamentos (cpf, plano, data) VALUES (?, ?, ?)', (cpf, dados['plano'], data)) conn.commit() return jsonify({'mensagem': 'Pagamento registrado'})

@app.route('/pagamentos', methods=['GET']) @jwt_required() def listar_pagamentos(): cpf = get_jwt_identity() c.execute('SELECT * FROM pagamentos WHERE cpf=?', (cpf,)) pagamentos = c.fetchall() return jsonify(pagamentos)

@app.route('/pagamentos/int:id', methods=['PUT']) @jwt_required() def confirmar_pagamento(id): c.execute('UPDATE pagamentos SET status="ativo" WHERE id=?', (id,)) conn.commit() return jsonify({'mensagem': 'Pagamento confirmado'})

Funcionário ativa pagamento por CPF

@app.route('/pagamentos/funcionario', methods=['POST']) def pagamento_funcionario(): dados = request.json c.execute('UPDATE alunos SET status="ativo" WHERE cpf=?', (dados['cpf'],)) conn.commit() return jsonify({'mensagem': 'Aluno ativado'})

Verificação de acesso (catraca)

@app.route('/acesso', methods=['GET']) def verificar_acesso(): cpf = request.args.get('cpf') c.execute('SELECT status FROM alunos WHERE cpf=?', (cpf,)) status = c.fetchone() if status and status[0] == 'ativo': return jsonify({'acesso': 'liberado'}) return jsonify({'acesso': 'negado'})

if name == 'main': app.run(debug=True)

