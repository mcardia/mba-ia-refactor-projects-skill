"""Usuario and login endpoints."""
import logging

from flask import jsonify

from controllers import validators
from models import usuario as usuario_model
from utils.errors import NotFoundError, UnauthorizedError

logger = logging.getLogger(__name__)


def listar_usuarios():
    return jsonify({"dados": usuario_model.listar(), "sucesso": True}), 200


def buscar_usuario(usuario_id):
    usuario = usuario_model.buscar_por_id(usuario_id)
    if not usuario:
        raise NotFoundError("Usuário não encontrado")
    return jsonify({"dados": usuario, "sucesso": True}), 200


def criar_usuario():
    usuario = validators.validar_usuario(validators.corpo_json())
    usuario_id = usuario_model.criar(**usuario)
    logger.info("Usuário criado: id %s", usuario_id)
    return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201


def login():
    email, senha = validators.validar_login(validators.corpo_json())
    usuario = usuario_model.autenticar(email, senha)
    if not usuario:
        logger.info("Login falhou")
        raise UnauthorizedError("Email ou senha inválidos")
    logger.info("Login bem-sucedido: usuário %s", usuario["id"])
    return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
