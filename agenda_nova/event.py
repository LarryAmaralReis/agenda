from datetime import datetime
from flask import abort, make_response


def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


EVENTS = {
    "1": {
        'evento_id': 1,
        'evento_titulo': 'Assistir Aula',
        'evento_data_hora': '00/00/0000 34:34:34',
        'evento_descricao': 'Aula de MPS',
        'evento_status': 1,
        'user_id': 1,
    },
    "2": {
        'evento_id': 2,
        'evento_titulo': 'Assistir Aula',
        'evento_data_hora': '00/00/0000 34:34:34',
        'evento_descricao': 'Aula de Empreendedorismo',
        'evento_status': 1,
        'user_id': 1,
    }
}


def read_all():
    return list(EVENTS.values())


def create(event):
    evento_id = event.get("evento_id")
    evento_titulo = event.get("evento_titulo", "")
    evento_data_hora = event.get("evento_data_hora", "")
    evento_descricao = event.get("evento_descricao", "")
    evento_status = event.get("evento_status", "")
    user_id = event.get("user_id", "")

    if evento_id and evento_id not in EVENTS:
        EVENTS[evento_id] = {
            "evento_id": evento_id,
            "evento_titulo": evento_titulo,
            "evento_data_hora": evento_data_hora,
            "evento_descricao": evento_descricao,
            "evento_status": evento_status,
            "user_id": user_id,
        }
        return EVENTS[evento_id], 201
    else:
        abort(
            406,
            f"User with last name {evento_id} already exists",
        )


def read_one(evento_id):
    if evento_id in EVENTS:
        return EVENTS[evento_id]
    else:
        abort(
            404, f"Event with ID {evento_id} not found"
        )


def update(evento_id, event):
    if evento_id in EVENTS:
        EVENTS[evento_id]["evento_titulo"] = event.get("evento_titulo", EVENTS[evento_id]["evento_titulo"])
        EVENTS[evento_id]["evento_data_hora"] = event.get("evento_data_hora", EVENTS[evento_id]["evento_data_hora"])
        EVENTS[evento_id]["evento_descricao"] = event.get("evento_descricao", EVENTS[evento_id]["evento_descricao"])
        return EVENTS[evento_id]
    else:
        abort(
            404,
            f"Event with ID {evento_id} not found"
        )


def delete(evento_id):
    if evento_id in EVENTS:
        del EVENTS[evento_id]
        return make_response(
            f"{evento_id} successfully deleted", 200
        )
    else:
        abort(
            404,
            f"Person with ID {evento_id} not found"
        )
