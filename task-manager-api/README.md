# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`, organizada em MVC.

## Como rodar

```bash
pip install -r requirements.txt
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`instance/tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

## Configuração

Todas as variáveis são opcionais (veja `.env.example`; um arquivo `.env` local é carregado automaticamente):

| Variável | Padrão | Uso |
|---|---|---|
| `SECRET_KEY` | aleatória a cada boot | assina os tokens de login |
| `DATABASE_URL` | `sqlite:///tasks.db` | banco de dados |
| `APP_HOST` / `APP_PORT` | `127.0.0.1` / `5000` | endereço do servidor |
| `APP_DEBUG` | `0` | `1` liga o debugger do Flask (só em desenvolvimento) |
| `CORS_ORIGINS` | vazio (sem CORS) | origens permitidas, separadas por vírgula |
| `TOKEN_MAX_AGE_SECONDS` | `3600` | validade do token de login |
| `LOG_LEVEL` | `INFO` | nível de log |

## Autenticação

`POST /login` devolve um token assinado. As rotas privilegiadas exigem `Authorization: Bearer <token>` de um usuário com role `admin` (401 sem token válido, 403 sem a role):
`DELETE /tasks/<id>`, `DELETE /users/<id>`, `DELETE /categories/<id>`, `GET /reports/summary`, `GET /reports/user/<id>`, e a atribuição de role (`role` em `PUT /users/<id>`, ou role diferente de `user` em `POST /users`).

Usuário admin do seed: `joao@email.com` / `1234`.

## Estrutura

```
app.py              # create_app() + execução
config/             # settings (env) e constantes de negócio
database.py         # instância do SQLAlchemy + commit transacional
models/             # entidades, consultas e regras de domínio
controllers/        # fluxo de cada caso de uso + validação
routes/             # blueprints (views) + serializers
services/           # relatórios e estatísticas
middlewares/        # tratamento central de erros, guarda de autenticação
utils/              # erros de domínio, utc_now
```
