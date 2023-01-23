from calendar import monthrange

from flask import Flask, render_template, url_for, redirect, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
import sqlite3 as sql

app = Flask(__name__)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agenda.db'
app.config['SECRET_KEY'] = 'thisisasecretkey'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(80), nullable=False, unique=True)


class RegisterForm(FlaskForm):
    username = StringField(validators=[
        InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
        InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    email = StringField(validators=[
        InputRequired(), Length(min=8, max=500)], render_kw={"placeholder": "Email"})

    submit = SubmitField('Registrar')

    def validate_email(self, email):
        existing_user_email = User.query.filter_by(
            email=email.data).first()
        if existing_user_email:
            raise ValidationError(
                'That username already exists. Please choose a different one.')


class LoginForm(FlaskForm):

    password = PasswordField(validators=[
        InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Senha"})

    email = StringField(validators=[
        InputRequired(), Length(min=8, max=500)], render_kw={"placeholder": "Email"})

    submit = SubmitField('Logar')


class UpdateForm(FlaskForm):
    email = StringField(validators=[InputRequired()], render_kw={"placeholder": "Novo Email"})
    password = PasswordField(validators=[InputRequired()], render_kw={"placeholder": "Nova Senha"})
    submit = SubmitField('Atualizar')


def insert_event(titulo, data_hora, descricao):
    con = sql.connect("agenda.db")
    cur = con.cursor()
    cur.execute("INSERT INTO eventos (titulo,data_hora,descricao) VALUES (?,?,?)", (titulo, data_hora, descricao))
    con.commit()
    con.close()


def retrieve_events():
    con = sql.connect("agenda.db")
    cur = con.cursor()
    cur.execute("SELECT titulo,data_hora,descricao FROM eventos")
    eventos = cur.fetchall()
    con.close()
    return eventos


def delete_event_by_id(event_id):
    con = sql.connect("agenda.db")
    cur = con.cursor()
    cur.execute("DELETE FROM eventos WHERE id = ?", (event_id,))
    con.commit()
    con.close()


def update_ids():
    con = sql.connect("agenda.db")
    cur = con.cursor()
    cur.execute("SELECT id FROM eventos ORDER BY id")
    all_ids = cur.fetchall()
    for i in range(1, len(all_ids) + 1):
        cur.execute("UPDATE eventos SET id = ? WHERE id = ?", (i, all_ids[i-1][0]))
    con.commit()
    con.close()


class UpdateEventForm(FlaskForm):
    title = StringField(validators=[InputRequired()], render_kw={"placeholder": "Novo Título"})
    date_time = StringField(validators=[InputRequired()], render_kw={"placeholder": "Novo Data e Hora"})
    description = StringField(validators=[InputRequired()], render_kw={"placeholder": "Nova Descrição"})
    submit = SubmitField('Atualizar')


@app.route('/update_event/<int:event_id>', methods=['GET','POST'])
def update_event(event_id):
    form = UpdateEventForm()
    if form.validate_on_submit():
        titulo = form.title.data
        data_hora = form.date_time.data
        descricao = form.description.data
        update_event_by_id(event_id,titulo,data_hora,descricao)
        return redirect(url_for('start'))
    event = retrieve_event_by_id(event_id)
    form.title.data = event[0]
    form.date_time.data = event[1]
    form.description.data = event[2]
    return render_template('update_event.html', form=form, event_id=event_id)


def update_event_by_id(event_id,titulo,data_hora,descricao):
    con = sql.connect("agenda.db")
    cur = con.cursor()
    cur.execute("UPDATE eventos SET titulo=?, data_hora=?, descricao=? WHERE id=?", (titulo,data_hora,descricao,event_id))
    con.commit()
    con.close()


def retrieve_event_by_id(event_id):
    con = sql.connect("agenda.db")
    cur = con.cursor()
    cur.execute("SELECT titulo,data_hora,descricao FROM eventos WHERE id=?", (event_id,))
    event = cur.fetchone()
    con.close()
    return event


@app.route('/remove/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    delete_event_by_id(event_id)
    update_ids()
    return redirect(url_for('start'))


@app.route('/')
def home():
    # return render_template('home.html')
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('start'))
    return render_template('login.html', form=form)


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = UpdateForm()
    if form.validate_on_submit():
        current_user.email = form.email.data
        current_user.password = bcrypt.generate_password_hash(form.password.data)
        db.session.commit()
        return redirect(url_for('start'))
    return render_template('settings.html', form=form)


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/delete', methods=['GET', 'POST'])
@login_required
def delete():
    db.session.delete(current_user)
    db.session.commit()
    logout_user()
    return redirect(url_for('login'))


@app.route('/start', methods=['GET', 'POST'])
@login_required
def start():
    eventos = retrieve_events()
    return render_template('start.html', eventos=eventos)


@app.route('/insert', methods=['GET', 'POST'])
@login_required
def insert():
    if request.method == 'POST':
        titulo = request.form['titulo']
        data_hora = request.form['data_hora']
        descricao = request.form['descricao']
        insert_event(titulo, data_hora, descricao)
        eventos = retrieve_events()
        update_ids()
        return render_template('insert.html', eventos=eventos)
    else:
        return render_template('insert.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password, email=form.email.data)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


def retrieve_events_by_date(day, month, year):
    con = sql.connect("agenda.db")
    cur = con.cursor()
    cur.execute("SELECT titulo, data_hora, descricao FROM eventos WHERE strftime('%d-%m-%Y', data_hora) = ?", (f"{day:02d}-{month:02d}-{year}",))
    events = cur.fetchall()
    con.close()
    return events


@app.route('/date/<int:day>/<int:month>/<int:year>', methods=['GET'])
def events_by_date(day, month, year):
    events_db = retrieve_events_by_date(day, month, year)
    next_month = month + 1 if month < 12 else 1
    next_year = year + 1
    prev_month = month - 1 if month > 1 else 12
    prev_year = year - 1
    next_day = day + 1 if (day < monthrange(year, month)[1]) else 1
    prev_day = day - 1 if (day > 1) else monthrange(year, month)[1]
    return render_template('date.html', eventos=events_db, day=f"{day:02d}", month=f"{month:02d}", year=f"{year}", next_month=f"{next_month:02d}", next_year=f"{next_year}", prev_month=f"{prev_month:02d}", prev_year=f"{prev_year}", next_day=f"{next_day:02d}", prev_day=f"{prev_day:02d}")


@app.route('/get-events')
def get_events():
    events = retrieve_events()
    return jsonify(events)


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
