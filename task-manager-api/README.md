# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`, refatorada para o padrão MVC.

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env   # opcional: ajuste as variáveis
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias. Usuários do seed: `joao@email.com / 1234`, `maria@email.com / abcd`, `pedro@email.com / pass`.

## Configuração (variáveis de ambiente / `.env`)

| Variável | Padrão | Descrição |
|---|---|---|
| `SECRET_KEY` | aleatória a cada boot | Chave usada para assinar os tokens de login |
| `DATABASE_URL` | `sqlite:///tasks.db` | URI do banco (SQLAlchemy) |
| `APP_HOST` | `127.0.0.1` | Interface de escuta |
| `APP_PORT` | `5000` | Porta |
| `APP_DEBUG` | `0` | `1` habilita o modo debug (nunca em produção) |
| `CORS_ORIGINS` | vazio | Origens permitidas, separadas por vírgula (vazio = sem CORS) |
| `ADMIN_TOKEN` | vazio | Token exigido no header `X-Admin-Token` nas rotas privilegiadas (vazio = rotas desabilitadas, 403) |

Rotas privilegiadas (exigem `X-Admin-Token`): `DELETE /tasks/<id>`, `DELETE /users/<id>`, `DELETE /categories/<id>`, alteração de `role` em `PUT /users/<id>` e criação de usuários com `role` diferente de `user` em `POST /users`.

## Estrutura

```
app.py                  ponto de entrada: create_app() + app.run
config/                 settings.py (env) e constants.py (regras de negócio)
database.py             instância do SQLAlchemy e helper de commit
models/                 entidades, consultas e regras de cada entidade
services/               report_service.py (estatísticas e relatórios)
controllers/            casos de uso por recurso + validators.py
routes/                 blueprints (URL -> controller) + serializers.py
middlewares/            tratamento centralizado de erros e guard de admin
utils/                  errors.py (exceções de domínio), time.py (utc_now)
seed.py                 dados iniciais
```
