Projeto: API Center – Sistema completo para academias

> Desenvolvi sozinho, em apenas 5 dias, um sistema completo e funcional para academias, inspirado e expandido a partir de modelos comerciais como o da ABC Evo.

Este projeto integra:

API RESTful com mais de 830 linhas de código, desenvolvida em Flask

Interface web profissional com mais de 760 linhas, com templates, rotas públicas e protegidas

Integração com Mercado Pago para cobranças online

Geração de QR Code dinâmico para liberação de acesso

Sistema de login com autenticação via JWT e criptografia com Bcrypt

Notificações automáticas via e-mail e WhatsApp

Agendamentos automáticos com APScheduler

Banco de dados SQLite otimizado

Painel administrativo para funcionários

Site principal com área institucional, pagamento e localização


Toda a infraestrutura foi planejada para ser modular, segura e escalável. Este projeto, se encomendado comercialmente, teria custo estimado superior a R$10.000. Foi feito com fins educacionais, demonstrando minha capacidade técnica, organização e produtividade — com foco em resultados reais.

📘 Documentação Técnica – API Center (Sistema de Academia)

Índice

1. Visão Geral


2. Tecnologias Utilizadas


3. Estrutura de Diretórios


4. Rotas da API


5. Interface Web


6. Funcionalidades Principais


7. Banco de Dados


8. Segurança e Criptografia


9. Integrações


10. Deploy e Execução




---

📌 Visão Geral

O API Center é um sistema completo para academias, inspirado na estrutura da ABC Evo, mas com maior liberdade e integração. Ele oferece:

Painel administrativo via web

Sistema de planos e pagamentos integrados

Liberação por QR Code, token ou catraca

Integração com WhatsApp e e-mail

API RESTful

Frontend leve, moderno e funcional



---

⚙️ Tecnologias Utilizadas

Backend: Python (Flask)

Frontend: HTML5, CSS3, JavaScript

Banco de Dados: SQLite

Notificações: Email e WhatsApp (via API de terceiros)

Segurança: Hash de senhas (bcrypt), verificação de login e permissões



---

🗂 Estrutura de Diretórios

📁 api_center/
├── app.py
│   ├── site_principal.html
│   ├── preco.html
│   ├── painel_funcionario.html
│   └── login.html
│   └── dados.db
│   ├── criptografia.py
│   └── notificacoes.py
    └── README.md


---

🌐 Rotas da API

Rotas Públicas

GET /site – Redireciona para /siteP1

GET /siteP1 – Página principal da academia

GET /recursos – Redireciona para preco.html

POST /pagar – Processa pagamento do plano

GET /status_usuario/<id> – Verifica status de plano de um cliente


Rotas Protegidas (Login obrigatório)

GET /painel_funcionario – Painel interno para liberação manual

POST /liberar_plano – Libera plano manualmente

POST /login – Autentica o funcionário

GET /logout – Finaliza sessão



---

🖥 Interface Web

/siteP1 – Página principal da academia

Contém:

Logo e navbar estilizados (vermelho neon + preto)

Seções: Sobre a academia, Localização, Contato

Galeria com imagens reais da academia

Botão “Pagar Plano” que redireciona para /recursos


/recursos → preco.html

Contém os planos disponíveis (mensal, trimestral, anual) com integração a pagamento.

/painel_funcionario

Acesso protegido com login. O funcionário pode:

Consultar status de alunos

Liberar planos manualmente



---

🔑 Funcionalidades Principais

✔️ Sistema completo de planos

✔️ Envio automático de e-mail e WhatsApp sobre status e vencimento

✔️ Liberação de acesso por token, QR Code ou sistema de catraca

✔️ Criptografia de senhas

✔️ Interface responsiva e leve



---

🧠 Banco de Dados

Tabelas principais

usuarios (id, nome, email, plano, status, vencimento)

logins (id_funcionario, nome, senha_hash)

pagamentos (id_pagamento, id_usuario, plano, data_pagamento, status)


Armazenado em: database/dados.db


---

🔐 Segurança e Criptografia

As senhas dos funcionários são criptografadas com bcrypt.

As permissões são controladas por sessão (Flask session).

A API realiza validações antes de qualquer operação sensível.

IP do cliente pode ser logado (opcional).



---

📡 Integrações

WhatsApp: envio via API externa (Twilio, WppConnect etc.)

Email: envio via SMTP seguro

QR Code/token: Geração dinâmica com base no status do plano



---

## 📜 Licença

Este projeto está licenciado sob os termos da **Creative Commons Atribuição - Sem Derivações 4.0 Internacional (CC BY-ND 4.0)**.

Você pode:
- Compartilhar, copiar e redistribuir o material em qualquer meio ou formato.
- Usar para fins educacionais e pessoais.

Você **não pode**:
- Usar o projeto para fins comerciais.
- Modificar, adaptar ou criar derivados a partir deste projeto.

**Créditos obrigatórios ao autor original.**

Mais informações: [https://creativecommons.org/licenses/by-nd/4.0/deed.pt-br](https://creativecommons.org/licenses/by-nd/4.0/deed.pt-br)

🚀 Deploy e Execução

Requisitos

Python 3.10+

Flask

SQLite

Bibliotecas:

flask

bcrypt

requests

smtplib (built-in)



Rodar localmente

pip install -r requirements.txt
python app.py

Acesse:

http://localhost:5000/siteP1

