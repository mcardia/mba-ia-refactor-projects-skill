"""Input validation shared by the controllers. Raises ValidationError (HTTP 400)."""
import re

from flask import request

from config.constants import (
    CATEGORIA_PADRAO,
    CATEGORIAS_VALIDAS,
    NOME_PRODUTO_MAX,
    NOME_PRODUTO_MIN,
    STATUS_PEDIDO_VALIDOS,
)
from utils.errors import ValidationError

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def corpo_json(obrigatorio=True):
    """JSON object of the request body; missing, malformed or empty => 400."""
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict) or (obrigatorio and not dados):
        raise ValidationError("Dados inválidos")
    return dados


def validar_produto(dados):
    for campo, mensagem in (("nome", "Nome é obrigatório"),
                            ("preco", "Preço é obrigatório"),
                            ("estoque", "Estoque é obrigatório")):
        if campo not in dados:
            raise ValidationError(mensagem)

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if not isinstance(nome, str):
        raise ValidationError("Nome deve ser texto")
    if not isinstance(descricao, str):
        raise ValidationError("Descrição deve ser texto")
    if not _is_number(preco):
        raise ValidationError("Preço deve ser numérico")
    if not _is_integer(estoque):
        raise ValidationError("Estoque deve ser um número inteiro")
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if len(nome) < NOME_PRODUTO_MIN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_PRODUTO_MAX:
        raise ValidationError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))

    return {"nome": nome, "descricao": descricao, "preco": preco, "estoque": estoque, "categoria": categoria}


def parametro_numerico(nome):
    valor = request.args.get(nome)
    if not valor:
        return None
    try:
        return float(valor)
    except ValueError:
        raise ValidationError(nome + " deve ser numérico")


def validar_usuario(dados):
    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")
    if not all(isinstance(valor, str) for valor in (nome, email, senha)):
        raise ValidationError("Nome, email e senha devem ser texto")
    if not _EMAIL_RE.match(email):
        raise ValidationError("Email inválido")
    return {"nome": nome, "email": email, "senha": senha}


def validar_login(dados):
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not email or not senha:
        raise ValidationError("Email e senha são obrigatórios")
    if not isinstance(email, str) or not isinstance(senha, str):
        raise ValidationError("Email e senha devem ser texto")
    return email, senha


def validar_pedido(dados):
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not _is_integer(usuario_id):
        raise ValidationError("Usuario ID inválido")
    if not itens or not isinstance(itens, list):
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    for item in itens:
        if not isinstance(item, dict) or not _is_integer(item.get("produto_id")) \
                or not _is_integer(item.get("quantidade")) or item["quantidade"] <= 0:
            raise ValidationError("Item inválido: produto_id e quantidade (inteiro positivo) são obrigatórios")
    return usuario_id, itens


def validar_status(dados):
    novo_status = dados.get("status", "")
    if novo_status not in STATUS_PEDIDO_VALIDOS:
        raise ValidationError("Status inválido")
    return novo_status
