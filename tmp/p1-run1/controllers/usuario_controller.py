"""HTTP flow for /usuarios and /login."""
import logging

from flask import jsonify

from controllers import validators
from models import usuario as usuario_model
from utils.errors import ConflictError, NotFoundError, UnauthorizedError, ValidationError

logger = logging.getLogger(__name__)


def listar_usuarios():
    return jsonify({"dados": usuario_model.listar(), "sucesso": True}), 200


def buscar_usuario(usuario_id):
    usuario = usuario_model.buscar_por_id(usuario_id)
    if not usuario:
        raise NotFoundError("Usuário não encontrado")
    return jsonify({"dados": usuario, "sucesso": True}), 200


def criar_usuario():
    dados = validators.corpo_json()
    nome, email, senha = dados.get("nome", ""), dados.get("email", ""), dados.get("senha", "")
    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")
    for valor in (nome, email, senha):
        validators.texto(valor, "Nome, email e senha devem ser texto")
    validators.email(email)
    if usuario_model.email_cadastrado(email):
        raise ConflictError("Email já cadastrado")

    usuario_id = usuario_model.criar(nome, email, senha)
    logger.info("Usuário criado com ID %s", usuario_id)
    return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201


def login():
    dados = validators.corpo_json_opcional()
    email, senha = dados.get("email", ""), dados.get("senha", "")
    if not email or not senha or not isinstance(email, str) or not isinstance(senha, str):
        raise ValidationError("Email e senha são obrigatórios")

    usuario = usuario_model.autenticar(email, senha)
    if not usuario:
        logger.info("Tentativa de login falhou")
        raise UnauthorizedError("Email ou senha inválidos")
    logger.info("Login bem-sucedido para usuário %s", usuario["id"])
    return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
