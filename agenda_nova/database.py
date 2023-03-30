from sqlalchemy import create_engine, text

db_connection_string = "mysql+pymysql://67g0tz6saj6gqpqpjsvm:pscale_pw_VZiIsmexTQc8jvh1LQ7OZVldeOwxv8G90o8Cmu1gkVl@aws.connect.psdb.cloud/agenda?charset=utf8mb4"
engine = create_engine(
    db_connection_string,
    connect_args={
        "ssl": {
            "ssl_ca": "/etc/ssl/cert.pem"
        }
    }
)


def register_user(user_nome, user_email, user_senha, user_status):
    with engine.connect() as conn:
        # Verifica se já existe um usuário com o mesmo email
        result = conn.execute(text("SELECT COUNT(*) FROM agenda_usuarios WHERE user_email = :user_email"),
                               user_email=user_email).scalar()
        if result > 0 and user_status != 2:
            print("Email já registrado!")
        else:
            conn.execute(text("INSERT INTO agenda_usuarios (user_nome, user_email, user_senha, user_status) VALUES (:user_nome, :user_email, :user_senha, :user_status)"),
                         user_nome=user_nome, user_email=user_email, user_senha=user_senha, user_status=user_status)
            print("Usuário registrado com sucesso!")


def login_user(user_email, user_senha):
    with engine.connect() as conn:
        # buscar usuário com o email fornecido e verificar a senha
        result = conn.execute(text("SELECT user_id, user_senha, user_status FROM agenda_usuarios WHERE user_email = :email"), {'email': user_email}).fetchone()

        if not result:
            return False

        user_id, senha_bd, user_status = result

        if user_status == 2:
            # usuário bloqueado, não permitir o login
            return False

        # atualizar o status de todos os usuários para 0, exceto o usuário atual
        conn.execute(text("UPDATE agenda_usuarios SET user_status = 0 WHERE user_id != :user_id AND user_status = 1"), {'user_id': user_id})

        # verificar se a senha fornecida corresponde à senha registrada no banco de dados
        if senha_bd == user_senha:
            # atualizar o status do usuário no banco de dados para ativo
            conn.execute(text("UPDATE agenda_usuarios SET user_status = 1 WHERE user_id = :user_id"), {'user_id': user_id})
            return True
        else:
            return False


def autenticacao_usuario():
    with engine.connect() as conn:
        # Verificar se há mais de um usuário logado
        result = conn.execute(text("SELECT COUNT(*) FROM agenda_usuarios WHERE user_status = 1")).fetchone()
        num_usuarios_logados = result[0]

        if num_usuarios_logados > 1:
            # Se houver mais de um usuário logado, atualizar o status de todos os usuários para 0
            conn.execute(text("UPDATE agenda_usuarios SET user_status = 0 WHERE user_status = 1"))
            return None
        elif num_usuarios_logados == 1:
            # Se houver apenas um usuário logado, recuperar o user_id dele
            result = conn.execute(text("SELECT user_id FROM agenda_usuarios WHERE user_status = 1")).fetchone()
            return result[0]
        else:
            # Se não houver usuários logados, retornar None
            return None


def recuperar_events(user_id, evento_id=None):
    with engine.connect() as conn:
        if evento_id is not None:
            result = conn.execute(text("SELECT * FROM agenda_eventos WHERE user_id = :user_id AND evento_status = 1 AND evento_id = :evento_id"), {'user_id': user_id, 'evento_id': evento_id})
        else:
            result = conn.execute(text("SELECT * FROM agenda_eventos WHERE user_id = :user_id AND evento_status = 1"), {'user_id': user_id})
        eventos = result.fetchall()

    return eventos


def criar_event(evento_titulo, evento_data_hora, evento_descricao, evento_status, user_id):
    with engine.connect() as conn:
        conn.execute(text("INSERT INTO agenda_eventos (evento_titulo, evento_data_hora, evento_descricao, evento_status, user_id) VALUES (:evento_titulo, :evento_data_hora, :evento_descricao, :evento_status, :user_id)"), {'evento_titulo': evento_titulo, 'evento_data_hora': evento_data_hora, 'evento_descricao': evento_descricao, 'evento_status': evento_status, 'user_id': user_id})


def recuperar_events_by_day(user_id, day, month, year):
    with engine.connect() as conn:
        # Construir a data em formato yyyy-mm-dd
        date_str = f"{year:04d}-{month:02d}-{day:02d}"
        # Fazer a consulta na tabela agenda_eventos filtrando pela data e pelo user_id
        result = conn.execute(
            text("SELECT evento_id, evento_titulo, evento_data_hora, evento_descricao "
                 "FROM agenda_eventos "
                 "WHERE user_id = :user_id "
                 "AND evento_status = 1 "
                 "AND DATE(evento_data_hora) = :date_str"),
            {'user_id': user_id, 'date_str': date_str}
        )
        eventos = result.fetchall()

    return eventos

def atualizar_evento(evento_id, evento_titulo, evento_data_hora, evento_descricao):
    with engine.connect() as conn:
        conn.execute(text("UPDATE agenda_eventos SET evento_titulo = :evento_titulo, evento_data_hora = :evento_data_hora, evento_descricao = :evento_descricao WHERE evento_id = :evento_id"), {'evento_id': evento_id, 'evento_titulo': evento_titulo, 'evento_data_hora': evento_data_hora, 'evento_descricao': evento_descricao})


def deletar_evento(evento_id):
    with engine.connect() as conn:
        conn.execute(text("UPDATE agenda_eventos SET evento_status = 0 WHERE evento_id = :evento_id"), {'evento_id': evento_id})


def recuperar_user(user_id):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM agenda_usuarios WHERE user_id = :user_id AND user_status = 1"),
            {"user_id": user_id}
        ).fetchone()

        if result:
            return dict(result)
        else:
            return None

def atualizar_user(user_id, user_nome, user_email, user_senha, user_status):
    with engine.connect() as conn:
        result = conn.execute(
            text("UPDATE agenda_usuarios SET user_nome=:user_nome, user_email=:user_email, user_senha=:user_senha, user_status=:user_status WHERE user_id=:user_id AND user_nome IS NOT NULL AND user_email IS NOT NULL AND user_senha IS NOT NULL"),
            user_nome=user_nome,
            user_email=user_email,
            user_senha=user_senha,
            user_status=user_status,
            user_id=user_id
        )
        return result.rowcount > 0

def deslogar_user(user_id):
    with engine.connect() as conn:
        result = conn.execute(
            text("UPDATE agenda_usuarios SET user_status=0 WHERE user_id=:user_id"),
            user_id=user_id
        )
        return result.rowcount > 0

def deletar_user(user_id):
    with engine.connect() as conn:
        result = conn.execute(
            text("UPDATE agenda_usuarios SET user_status=2 WHERE user_id=:user_id"),
            user_id=user_id
        )
        return result.rowcount > 0





