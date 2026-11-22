"""Request-input parsing helpers. They raise ValidationError (400) instead of crashing."""
import re

from flask import request

from utils.errors import ValidationError

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def corpo_json():
    """Required JSON object body; missing, empty or malformed => 'Dados inválidos'."""
    dados = request.get_json(silent=True)
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")
    return dados


def corpo_json_opcional():
    """JSON object body or {} so field-level checks produce the error message."""
    dados = request.get_json(silent=True)
    return dados if isinstance(dados, dict) else {}


def numero(valor, mensagem):
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValidationError(mensagem)
    return valor


def texto(valor, mensagem):
    if not isinstance(valor, str):
        raise ValidationError(mensagem)
    return valor


def numero_query(nome_parametro):
    valor = request.args.get(nome_parametro, None)
    if not valor:
        return None
    try:
        return float(valor)
    except ValueError:
        raise ValidationError(nome_parametro + " inválido")


def email(valor):
    if not _EMAIL_RE.match(valor):
        raise ValidationError("Email inválido")
    return valor
