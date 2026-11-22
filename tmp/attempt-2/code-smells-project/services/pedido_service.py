"""Order use cases: placing an order and changing its status, with their notifications."""
import logging

from config.constants import STATUS_APROVADO, STATUS_CANCELADO, STATUS_PEDIDO
from models import pedido as pedido_model
from services import notification_service
from utils.errors import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


def criar_pedido(usuario_id, itens):
    resultado = pedido_model.criar(usuario_id, itens)
    logger.info("Pedido %s criado para usuário %s", resultado["pedido_id"], usuario_id)
    notification_service.pedido_criado(resultado["pedido_id"], usuario_id)
    return resultado


def atualizar_status(pedido_id, novo_status):
    if novo_status not in STATUS_PEDIDO:
        raise ValidationError("Status inválido")
    if not pedido_model.existe(pedido_id):
        raise NotFoundError("Pedido não encontrado")
    pedido_model.atualizar_status(pedido_id, novo_status)
    if novo_status == STATUS_APROVADO:
        notification_service.pedido_aprovado(pedido_id)
    elif novo_status == STATUS_CANCELADO:
        notification_service.pedido_cancelado(pedido_id)
