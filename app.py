from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from datetime import datetime
import json
import os
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import random
import string

def gerar_codigo_verificacao(tamanho=20):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=tamanho))

app = Flask(__name__)
app.secret_key = 'minha_chave_secreta'
s = URLSafeTimedSerializer(app.secret_key)


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'emaildealgoritmoalgoritmo@gmail.com'
app.config['MAIL_PASSWORD'] = 'acov lcsx dugo sufo '
app.config['MAIL_DEFAULT_SENDER'] = 'emaildealgoritmoalgoritmo@gmail.com'
app.config['SERVER_NAME'] = 'lucasrrr.pythonanywhere.com'
mail = Mail(app)

def enviar_email_verificacao(email, usuario):
    s = URLSafeTimedSerializer(app.secret_key)
    token = s.dumps(usuario, salt='email-verification')
    link = url_for('confirmar_email', token=token, _external=True)

    msg = Message('Confirme seu e-mail',
              sender='seuemail@gmail.com',
              recipients=[usuario['email']])
    msg.body = f"Clique no link para verificar: {url_for('verificar_email', token=token, _external=True)}"
    mail.send(msg)

@app.route('/verificar_email/<token>')
def verificar_email(token):
    try:
        email = s.loads(token, max_age=3600)  # 1 hora de validade
    except SignatureExpired:
        flash("Link expirado.", "danger")
        return redirect(url_for('login'))
    except BadTimeSignature:
        flash("Link inválido.", "danger")
        return redirect(url_for('login'))

    usuarios = carregar_usuarios()
    for login, user in usuarios.items():
        if user.get('email') == email:
            # marca no JSON
            user['verificado'] = True
            salvar_usuarios(usuarios)

            # atualiza/auto‐login na sessão
            session['usuario'] = {
                'login': login,
                'nome': user.get('nome'),
                'foto': user.get('foto'),
                'is_admin': user.get('is_admin', False),
                'curso': user.get('curso', ''),
                'turno': user.get('turno', ''),
                'email': user.get('email', ''),
                'verificado': True
            }

            flash("E-mail verificado com sucesso!", "success")
            return redirect(url_for('perfil'))

    flash("Usuário não encontrado.", "danger")
    return redirect(url_for('login'))


# Funções para Usuários
def carregar_usuarios():
    try:
        with open('usuarios.json', 'r') as file:
            usuarios = json.load(file)
            # Se o conteúdo estiver em formato lista, converte para dicionário
            if isinstance(usuarios, list):
                usuarios_dict = {}
                for usuario in usuarios:
                    usuarios_dict[usuario['login']] = usuario
                return usuarios_dict
            return usuarios
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def salvar_usuarios(usuarios):
    with open('usuarios.json', 'w') as file:
        json.dump(usuarios, file, indent=4)

# Funções para Itens Perdidos
def carregar_itens():
    try:
        with open('itens.json', 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def salvar_itens(itens):
    with open('itens.json', 'w') as file:
        json.dump(itens, file, indent=4)

# Rota inicial - Página Inicial com listagem de itens e busca
@app.route('/')
def index():
    usuario = session.get('usuario')
    query = request.args.get('q', '').lower()
    itens = carregar_itens()
    itens = list(reversed(itens))
    if query:
        itens = [item for item in itens if query in item['nome'].lower()]
    return render_template('index.html', usuario=usuario, itens=itens, query=query)

# Rota de cadastro de usuários
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        login = request.form['login']
        senha = request.form['senha']
        curso = request.form.get('curso')
        turno = request.form.get('turno')
        email = request.form.get('email') 

        foto_arquivo = request.files.get('foto')
        if foto_arquivo and foto_arquivo.filename != '':
            filename = secure_filename(foto_arquivo.filename)
            caminho = os.path.join('static', 'imagens', filename)
            foto_arquivo.save(caminho)
        else:
            filename = 'login_padrao.png'

        usuarios = carregar_usuarios()
        if login in usuarios:
            flash("Usuário já existe!")
            return redirect(url_for('cadastro'))

        usuarios[login] = {
            'nome': nome,
            'senha': senha,
            'login': login,
            'foto': filename,
            'is_admin': False,
            'curso': curso,
            'turno': turno,
            'email': email
        }
        salvar_usuarios(usuarios)
        flash("Cadastro realizado com sucesso. Faça login!")
        return redirect(url_for('login'))

    return render_template('cadastro.html')


# Rota de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_digitado = request.form['login']
        senha_digitada = request.form['senha']
        usuarios = carregar_usuarios()

        if login_digitado in usuarios and usuarios[login_digitado]['senha'] == senha_digitada:
            user = usuarios[login_digitado]
            session['usuario'] = {
                'login': login_digitado,
                'nome': user.get('nome'),
                'foto': user.get('foto'),
                'is_admin': user.get('is_admin', False),
                'curso': user.get('curso', ''),
                'turno': user.get('turno', ''),
                'email': user.get('email', ''),
                'verificado': user.get('verificado', False)
            }
            return redirect(url_for('index'))
        else:
            flash("Login ou senha incorretos.", "error")
    return render_template('login.html')

# Rota de perfil (exibição e atualização dos dados do usuário)
@app.route('/perfil', methods=['GET', 'POST'])
def perfil():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    login_usuario = session['usuario']['login']
    usuarios = carregar_usuarios()
    usuario = usuarios.get(login_usuario)

    if request.method == 'POST':
        # Atualize os campos editáveis
        usuario['nome'] = request.form.get('nome', usuario['nome'])
        usuario['email'] = request.form.get('email', usuario.get('email', ''))
        usuario['curso'] = request.form.get('curso', usuario.get('curso', ''))
        usuario['turno'] = request.form.get('turno', usuario.get('turno', ''))

        nova_senha = request.form.get('senha')
        if nova_senha:
            usuario['senha'] = nova_senha

        # Verifica se o usuário trocou a foto
        if 'foto' in request.files:
            foto = request.files['foto']
            if foto.filename:
                caminho = os.path.join('static/imagens', foto.filename)
                foto.save(caminho)
                usuario['foto'] = foto.filename

        # Garante que esses campos não sejam perdidos
        usuario['is_admin'] = usuarios[login_usuario].get('is_admin', False)
        usuario['verificado'] = usuarios[login_usuario].get('verificado', False)
        usuario['codigo_verificacao'] = usuarios[login_usuario].get('codigo_verificacao', None)

        # Gera código de verificação se ainda não tiver e o e-mail for preenchido
        if usuario.get('email') and not usuario.get('verificado'):

         token = s.dumps(usuario['email'])
         link = url_for('verificar_email', token=token, _external=True)
         msg = Message("Verifique seu e-mail", recipients=[usuario['email']])
         msg.body = f"Olá {usuario['nome']}, clique no link para verificar seu e-mail: {link}"
         mail.send(msg)
         flash("E-mail de verificação enviado!", "info")


        # Salva de volta no dicionário e no arquivo
        usuarios[login_usuario] = usuario
        salvar_usuarios(usuarios)

        # Atualiza a sessão
        session['usuario'] = {
            'login': login_usuario,
            'nome': usuario['nome'],
            'foto': usuario.get('foto'),
            'is_admin': usuario.get('is_admin', False),
            'curso': usuario.get('curso', ''),
            'turno': usuario.get('turno', ''),
            'email': usuario.get('email', ''),
            'verificado': usuario.get('verificado', False)
        }

        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('perfil'))

    return render_template('perfil.html', usuario=usuario)


# Rota para cadastrar um novo item perdido
@app.route('/novo_item', methods=['GET', 'POST'])
def novo_item():
    if request.method == 'POST':
        nome_item = request.form['nome_item']
        descricao = request.form['descricao']
        local_encontrado = request.form.get('local_encontrado')
        local_guardado = request.form.get('local_guardado')

        contato = request.form.get('contato')  # novo, opcional

        imagens = request.files.getlist('imagens')
        imagem_nomes = []
        for imagem_file in imagens[:3]:
            if imagem_file and imagem_file.filename != '':
                filename = secure_filename(imagem_file.filename)
                caminho = os.path.join('static', 'imagens', filename)
                imagem_file.save(caminho)
                imagem_nomes.append(filename)

        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        item_id = f"{session['usuario']['login']}_{int(datetime.now().timestamp())}"

        novo_item = {
            "id": item_id,
            "nome": nome_item,
            "descricao": descricao,
            "local_encontrado": local_encontrado,
            "local_guardado": local_guardado,

            "imagens": imagem_nomes,
            "data_cadastro": timestamp,
            "usuario": {
                "login": session['usuario']['login'],
                "foto": session['usuario']['foto'],
                "nome": session['usuario']['nome'],
                "verificado": session['usuario']['verificado']
            },
            "contato": contato,
            "estado": "Ainda não entregue"
        }

        itens = carregar_itens()
        itens.append(novo_item)
        salvar_itens(itens)

        flash("Item cadastrado com sucesso!")
        return redirect(url_for('index'))


    return render_template('novo_item.html')

# Rota para alterar o estado do item (só o dono pode alterar)
@app.route('/alterar_estado/<item_id>', methods=['POST'])
def alterar_estado(item_id):
    if 'usuario' not in session:
        flash("Você precisa estar logado para alterar o estado.")
        return redirect(url_for('login'))

    itens = carregar_itens()
    for item in itens:
        if item['id'] == item_id:
            if item['usuario']['login'] == session['usuario']['login']:
                item['estado'] = "Entregue" if item['estado'] == "Ainda não entregue" else "Ainda não entregue"
                salvar_itens(itens)
                flash("Estado do item atualizado!")
            else:
                flash("Você não tem permissão para alterar este item.")
            break
    return redirect(url_for('index'))

# Função de denunciar item

@app.route('/denunciar/<item_id>', methods=['POST'])
def denunciar_item(item_id):
    # Verifica se o usuário está logado
    if 'usuario' not in session:
        flash("Você precisa estar logado para denunciar um item.")
        return redirect(url_for('login'))

    usuario = session['usuario']
    login_usuario = usuario['login']

    # Carrega os itens do arquivo itens.json (que está na mesma pasta do app.py)
    with open('itens.json', 'r', encoding='utf-8') as f:
        itens = json.load(f)

    # Procura o item cujo 'id' corresponde ao parâmetro
    item_encontrado = False
    for index, item in enumerate(itens):
        if item.get('id') == item_id:
            item_encontrado = True
            # Garante que o campo "denuncias" existe
            if 'denuncias' not in item:
                item['denuncias'] = []

            # Verifica se este usuário já denunciou o item
            ja_denunciou = any(denuncia.get("login") == login_usuario for denuncia in item['denuncias'])
            if ja_denunciou:
                flash("Você já denunciou este item.")
            else:
                # Registra a denúncia adicionando somente o login (pode incluir outros dados se desejar)
                item['denuncias'].append({"login": login_usuario})
                flash("Denúncia registrada com sucesso.")

                # Se o número de denúncias for igual ou superior a 5, remove o item
                if len(item['denuncias']) >= 5:
                    # Remove o item da lista
                    del itens[index]
                    flash("Item removido após denúncias.")

            break  # Item encontrado, não precisa continuar o loop

    if not item_encontrado:
        flash("Item não encontrado.")

    # Salva os itens atualizados de volta no arquivo JSON
    with open('itens.json', 'w', encoding='utf-8') as f:
        json.dump(itens, f, indent=4, ensure_ascii=False)

    return redirect(url_for('index'))

# Função para deletar item (Proprietário ou admin)

@app.route('/delete_item/<item_id>', methods=['POST'])
def delete_item(item_id):
    # Verifica se o usuário está logado
    if 'usuario' not in session:
        flash("Você precisa estar logado para realizar essa ação.", "error")
        return redirect(url_for('login'))

    usuario_logado = session['usuario']

    # Carrega os itens do arquivo JSON (assumindo que "itens.json" está na mesma pasta do app.py)
    with open('itens.json', 'r', encoding='utf-8') as f:
        itens = json.load(f)

    # Procura o item com o id passado
    item_index = None
    for idx, item in enumerate(itens):
        if item.get('id') == item_id:
            item_index = idx
            break

    if item_index is None:
        flash("Item não encontrado.", "error")
        return redirect(url_for('index'))

    item = itens[item_index]

    # Verifica se o usuário logado é o proprietário ou é administrador
    if usuario_logado['login'] != item['usuario']['login'] and not usuario_logado.get('is_admin', False):
        flash("Você não tem permissão para excluir este item.", "error")
        return redirect(url_for('index'))

    # Remove o item e salva o arquivo atualizado
    itens.pop(item_index)
    with open('itens.json', 'w', encoding='utf-8') as f:
        json.dump(itens, f, indent=4, ensure_ascii=False)

    flash("Item excluído com sucesso!")
    return redirect(url_for('index'))

# Rota para exibir regras do site

@app.route('/regras')
def regras():
    return render_template('regras.html')

# Rota para exibir informações de cada usuário (apenas para administradores)

@app.route('/admin/usuarios')
def listar_usuarios():
    user = session.get('usuario')
    if not user:
        flash("Faça login primeiro.")
        return redirect(url_for('login'))
    # aqui usamos .get para não KeyError
    if not user.get('is_admin', False):
        flash("Acesso negado: somente administradores.", "error")
        return redirect(url_for('index'))

    usuarios = carregar_usuarios()
    lista = list(usuarios.values())
    return render_template('usuarios.html', lista_usuarios=lista)

@app.route('/admin/delete_user/<login>', methods=['POST'])
def delete_user(login):
    # Verifica se o usuário logado é administrador.
    if 'usuario' not in session or not session['usuario'].get('is_admin', False):
        flash("Acesso negado: somente administradores podem realizar essa ação.")
        return redirect(url_for('index'))

    usuarios = carregar_usuarios()
    if login in usuarios:
        # Remove o usuário do dicionário.
        usuarios.pop(login)
        salvar_usuarios(usuarios)
        flash(f"Usuário '{login}' excluído com sucesso.")
    else:
        flash("Usuário não encontrado.")

    return redirect(url_for('listar_usuarios'))

@app.route('/user/<login>')
def user_profile(login):
    # Carrega todos os usuários (do seu JSON ou base de dados)
    usuarios = carregar_usuarios()  
    user = usuarios.get(login)
    if not user:
        flash("Usuário não encontrado.")
        return redirect(url_for('index'))

    # Renderiza um template específico para mostrar o perfil dele
    return render_template('perfil_usuario.html', usuario=user)




# Rota de logout
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    flash("Você saiu com sucesso!")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)




