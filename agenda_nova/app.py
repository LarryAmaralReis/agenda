from datetime import datetime

import connexion
from flask import render_template, jsonify, redirect, url_for, request, abort  # Remove: import Flask
from database import *

app = connexion.App(__name__, specification_dir="./")
app.add_api("swagger.yml")


@app.route("/")
def homes():
    return redirect(url_for('login'))


@app.route("/register", methods=['GET','POST'])
def register():
    if request.method == 'POST':
        user_nome = request.form['user_nome']
        user_email = request.form['user_email']
        user_senha = request.form['user_senha']
        user_status = 0
        register_user(user_nome, user_email, user_senha, user_status)

        return redirect(url_for('login'))
    else:
        return render_template('register.html')


@app.route("/login", methods=['GET','POST'])
def login():
    if request.method == 'POST':
        # obter as informações de login do usuário a partir do request
        user_email = request.form['user_email']
        user_senha = request.form['user_senha']

        # verificar se as credenciais são válidas (por exemplo, comparando com os registros no banco de dados)
        if login_user(user_email, user_senha):
            # se as credenciais forem válidas, retornar um token de autenticação
            return redirect(url_for('home'))
        else:
            # se as credenciais forem inválidas, retornar um erro
            return {'erro': 'Credenciais invalidas.'}, 401
    else:
        return render_template('login.html')


@app.route('/home', methods=['GET', 'POST'])
def home():
    # Verificar se há apenas um usuário logado
    user_id = autenticacao_usuario()

    # Se não houver usuários logados, redirecionar para a página de login
    if user_id is None:
        return redirect(url_for('login'))

    # Recuperar os eventos correspondentes ao usuário logado
    eventos = recuperar_events(user_id)

    return render_template('home.html', eventos=eventos)



@app.route("/event/create", methods=['GET', 'POST'])
def event_create():
    # Verificar se há apenas um usuário logado
    user_id = autenticacao_usuario()

    # Se não houver usuários logados, redirecionar para a página de login
    if user_id is None:
        return redirect(url_for('login'))

    if request.method == 'POST':
        evento_titulo = request.form['evento_titulo']
        evento_data_hora = request.form['evento_data_hora']
        evento_descricao = request.form['evento_descricao']
        evento_status = 1
        data_hora = datetime.strptime(evento_data_hora, '%Y-%m-%dT%H:%M')
        evento_data_hora = datetime.strftime(data_hora, '%Y-%m-%d %H:%M:%S')
        criar_event(evento_titulo, evento_data_hora, evento_descricao, evento_status, user_id)

        return redirect(url_for('home'))
    else:
        return render_template('create.html')



@app.route("/event/<int:day>/<int:month>/<int:year>")
def event_read(day, month, year):
    # Verificar se há apenas um usuário logado
    user_id = autenticacao_usuario()

    # Se não houver usuários logados, redirecionar para a página de login
    if user_id is None:
        return redirect(url_for('login'))

    # Recuperar os eventos correspondentes ao usuário logado e ao dia específico
    eventos = recuperar_events_by_day(user_id, day, month, year)

    return render_template('read.html', eventos=eventos)



@app.route("/event/update/<int:evento_id>", methods=['GET', 'POST'])
def event_update(evento_id):
    # Check if there is only one logged-in user
    user_id = autenticacao_usuario()

    # Redirect to login page if there are no logged-in users
    if user_id is None:
        return redirect(url_for('login'))

    # Retrieve the event corresponding to the provided ID
    evento = recuperar_events(user_id, evento_id=evento_id)

    # Redirect to home page if there is no corresponding event
    if not evento:
        return redirect(url_for('home'))

    # Update the event in the database if the request method is POST
    if request.method == 'POST':
        evento_titulo = request.form.get('evento_titulo')
        evento_data_hora = request.form.get('evento_data_hora')
        evento_descricao = request.form.get('evento_descricao')

        # Convert the date/time string to a datetime object
        data_hora = datetime.strptime(evento_data_hora, '%Y-%m-%dT%H:%M')
        evento_data_hora = datetime.strftime(data_hora, '%Y-%m-%d %H:%M:%S')

        # Update the event in the database
        atualizar_evento(evento_id, evento_titulo, evento_data_hora, evento_descricao)

        return redirect(url_for('home'))

    # Render the update form with the event information filled in
    return render_template('update.html', evento=evento[0])


@app.route("/event/delete/<int:evento_id>", methods=['GET', 'POST'])
def event_delete(evento_id):
    # Check if there is only one logged-in user
    user_id = autenticacao_usuario()

    # Redirect to login page if there are no logged-in users
    if user_id is None:
        abort(401)

    # Retrieve the event corresponding to the provided ID
    evento = recuperar_events(user_id, evento_id=evento_id)

    # Return error 404 if there is no corresponding event
    if not evento or len(evento) == 0:
        abort(404)

    # Delete the event if it belongs to the user
    if evento[0].user_id == user_id:
        deletar_evento(evento_id)
        return redirect(url_for('home'))

    # Return error 403 if the user does not have permission to delete the event
    abort(403)



@app.route("/settings", methods=['GET', 'POST'])
def settings():
    # Check if there is only one logged-in user
    user_id = autenticacao_usuario()

    # Redirect to login page if there are no logged-in users
    if user_id is None:
        return redirect(url_for('login'))

    # Retrieve the event corresponding to the provided ID
    usuario = recuperar_user(user_id)

    # Redirect to home page if there is no corresponding event
    if not usuario:
        return redirect(url_for('login'))

    # Update the event in the database if the request method is POST
    if request.method == 'POST':
        user_nome = request.form.get('user_nome')
        user_email = request.form.get('user_email')
        user_senha = request.form.get('user_senha')
        user_status = 1
        # Update the event in the database
        atualizar_user(user_id, user_nome, user_email , user_senha, user_status)

        return redirect(url_for('home'))

    # Render the update form with the event information filled in
    return render_template('settings.html', usuario=usuario)


@app.route("/settings/logout")
def user_logout():
    # Check if there is only one logged-in user
    user_id = autenticacao_usuario()

    # Redirect to login page if there are no logged-in users
    if user_id is None:
        return redirect(url_for('login'))

    # Update the user status to 0 in the database
    deslogar_user(user_id)

    # Clear the session and redirect to login page
    return redirect(url_for('login'))



@app.route("/settings/delete")
def user_delete():
    # Check if there is only one logged-in user
    user_id = autenticacao_usuario()

    # Redirect to login page if there are no logged-in users
    if user_id is None:
        return redirect(url_for('login'))

    # Update the user status to 0 in the database
    deletar_user(user_id)

    # Clear the session and redirect to login page
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
