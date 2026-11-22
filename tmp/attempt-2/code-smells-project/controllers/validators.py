"""Input validation shared by the controllers. Raises ValidationError (400)."""
import re

from flask import request

from config.constants import (
    CATEGORIA_PADRAO,
    CATEGORIAS_VALIDAS,
    NOME_PRODUTO_MAX,
    NOME_PRODUTO_MIN,
)
from utils.errors import ValidationError

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _e_numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def _e_inteiro(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


def corpo_json(exigir_conteudo=True):
    """Return the JSON body as a dict. Missing/malformed body => 400 'Dados inválidos'."""
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict) or (exigir_conteudo and not dados):
        raise ValidationError("Dados inválidos")
    return dados


def validar_produto(dados):
    """Validation chain shared by create and update."""
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
    if not _e_numero(preco):
        raise ValidationError("Preço deve ser numérico")
    if not _e_inteiro(estoque):
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

    return {"nome": nome, "descricao": descricao, "preco": preco,
            "estoque": estoque, "categoria": categoria}


def preco_opcional(valor, nome_parametro):
    if not valor:
        return None
    try:
        return float(valor)
    except ValueError as erro:
        raise ValidationError(f"Parâmetro {nome_parametro} inválido") from erro


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
    if not itens:
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    if not _e_inteiro(usuario_id):
        raise ValidationError("Usuario ID inválido")
    if not isinstance(itens, list):
        raise ValidationError("Itens do pedido inválidos")
    for item in itens:
        if (not isinstance(item, dict)
                or not _e_inteiro(item.get("produto_id"))
                or not _e_inteiro(item.get("quantidade"))
                or item["quantidade"] <= 0):
            raise ValidationError(
                "Item de pedido inválido: produto_id e quantidade (inteiro positivo) são obrigatórios"
            )
    return usuario_id, itens
