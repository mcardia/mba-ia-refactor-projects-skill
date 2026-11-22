# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`, organizada em camadas MVC.

## Como rodar

```bash
pip install -r requirements.txt
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

## Configuração

Todas as variáveis são opcionais e podem ficar num arquivo `.env` (veja `.env.example`):

| Variável | Padrão | Uso |
|---|---|---|
| `SECRET_KEY` | aleatória a cada boot | assina os tokens de login (defina em produção, senão os tokens expiram a cada restart) |
| `DATABASE_URL` | `sqlite:///tasks.db` | banco de dados |
| `APP_HOST` / `APP_PORT` | `127.0.0.1` / `5000` | endereço do servidor |
| `APP_DEBUG` | `0` | `1` liga o modo debug (somente desenvolvimento) |
| `CORS_ORIGINS` | vazio (sem CORS) | origens permitidas, separadas por vírgula |
| `TOKEN_MAX_AGE_SECONDS` | `28800` | validade do token |
| `LOG_LEVEL` | `INFO` | nível de log |

## Autenticação

`POST /login` devolve um token assinado. Envie-o como `Authorization: Bearer <token>`.

- Exigem usuário **admin**: `DELETE /tasks/<id>`, `DELETE /users/<id>`, `DELETE /categories/<id>`, `GET /reports/summary`, e criar/promover usuários com `role` diferente de `user`.
- `PUT /users/<id>` exige estar autenticado como o próprio usuário ou como admin.

Usuário admin do seed: `joao@email.com` / `1234`.

## Estrutura

```
app.py            create_app() + execução
config/           settings (variáveis de ambiente) e constantes de negócio
database.py       instância SQLAlchemy, foreign keys do SQLite, commit transacional
models/           entidades, consultas e regras de domínio
services/         tokens de acesso e relatórios/estatísticas
controllers/      fluxo de cada caso de uso + validação de entrada
routes/           blueprints (URL -> controller)
middlewares/      tratamento centralizado de erros e guarda de autenticação
utils/            exceções de domínio e utc_now()
```
