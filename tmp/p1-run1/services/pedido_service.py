"""Order use cases: placing an order and changing its status (with notifications)."""
import logging

from config.constants import STATUS_VALIDOS
from models import pedido as pedido_model
from models import usuario as usuario_model
from services import notification_service
from utils.errors import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


def _inteiro_positivo(valor):
    return isinstance(valor, int) and not isinstance(valor, bool) and valor > 0


def _normalizar_itens(itens):
    if not isinstance(itens, list) or len(itens) == 0:
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    normalizados = []
    for item in itens:
        if not isinstance(item, dict) or not _inteiro_positivo(item.get("produto_id")):
            raise ValidationError("Cada item deve ter um produto_id válido")
        if not _inteiro_positivo(item.get("quantidade")):
            raise ValidationError("Quantidade deve ser um inteiro maior que zero")
        normalizados.append({"produto_id": item["produto_id"], "quantidade": item["quantidade"]})
    return normalizados


def criar_pedido(usuario_id, itens):
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not itens:
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    if not _inteiro_positivo(usuario_id):
        raise ValidationError("Usuario ID inválido")
    itens = _normalizar_itens(itens)
    if not usuario_model.existe(usuario_id):
        raise ValidationError("Usuário " + str(usuario_id) + " não encontrado")

    resultado = pedido_model.criar(usuario_id, itens)
    logger.info("Pedido %s criado para usuário %s", resultado["pedido_id"], usuario_id)
    notification_service.pedido_criado(resultado["pedido_id"], usuario_id)
    return resultado


def atualizar_status(pedido_id, novo_status):
    if novo_status not in STATUS_VALIDOS:
        raise ValidationError("Status inválido")
    if not pedido_model.existe(pedido_id):
        raise NotFoundError("Pedido não encontrado")
    pedido_model.atualizar_status(pedido_id, novo_status)
    notification_service.status_alterado(pedido_id, novo_status)
