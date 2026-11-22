"""Notifications (simulated): e-mail, SMS and push are logged, not sent."""
import logging

logger = logging.getLogger(__name__)


def pedido_criado(pedido_id, usuario_id):
    logger.info("Notificação [email]: pedido %s criado para usuário %s", pedido_id, usuario_id)
    logger.info("Notificação [sms]: pedido %s recebido", pedido_id)
    logger.info("Notificação [push]: novo pedido %s recebido pelo sistema", pedido_id)


def pedido_aprovado(pedido_id):
    logger.info("Notificação: pedido %s foi aprovado, preparar envio", pedido_id)


def pedido_cancelado(pedido_id):
    logger.info("Notificação: pedido %s cancelado, devolver estoque", pedido_id)
