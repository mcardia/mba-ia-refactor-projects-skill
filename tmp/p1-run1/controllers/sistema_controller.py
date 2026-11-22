"""HTTP flow for / and /health."""
from flask import current_app, jsonify

from config.constants import VERSAO_API
from models import sistema as sistema_model


def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": VERSAO_API,
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    })


def health_check():
    return jsonify({
        "status": "ok",
        "database": "connected",
        "counts": sistema_model.contar_entidades(),
        "versao": VERSAO_API,
        "ambiente": current_app.config["APP_ENV"],
    }), 200
