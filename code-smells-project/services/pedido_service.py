"""Order use cases: placing an order and changing its status (with notifications)."""
from models import pedido as pedido_model
from models import usuario as usuario_model
from services import notification_service
from utils.errors import NotFoundError, ValidationError


def criar_pedido(usuario_id, itens):
    if not usuario_model.existe(usuario_id):
        raise ValidationError("Usuário não encontrado")
    resultado = pedido_model.criar(usuario_id, itens)
    notification_service.pedido_criado(resultado["pedido_id"], usuario_id)
    return resultado


def atualizar_status(pedido_id, novo_status):
    if not pedido_model.atualizar_status(pedido_id, novo_status):
        raise NotFoundError("Pedido não encontrado")
    notification_service.status_alterado(pedido_id, novo_status)
