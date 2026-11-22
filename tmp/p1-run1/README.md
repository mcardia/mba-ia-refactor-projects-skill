# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000` (por padrão escuta apenas em `127.0.0.1`). O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo (`admin@loja.com` / `admin123`, `joao@email.com` / `123456`, `maria@email.com` / `senha123`; as senhas são gravadas como hash).

## Configuração (variáveis de ambiente)

Veja `.env.example`. Todas são opcionais:

| Variável | Padrão | Uso |
|---|---|---|
| `SECRET_KEY` | aleatória a cada boot | chave de assinatura do Flask |
| `APP_DEBUG` | `0` | `1` ativa o modo debug (nunca em produção) |
| `APP_HOST` / `APP_PORT` | `127.0.0.1` / `5000` | endereço de escuta (`0.0.0.0` para expor na rede) |
| `APP_ENV` | `producao` | nome do ambiente exibido em `/health` |
| `LOG_LEVEL` | `INFO` | nível de log |
| `DATABASE_PATH` | `loja.db` | caminho do arquivo SQLite |
| `CORS_ORIGINS` | `http://localhost:5000,http://127.0.0.1:5000` | origens permitidas, separadas por vírgula (`*` libera todas) |
| `ADMIN_TOKEN` | vazio | token exigido no header `X-Admin-Token` pelas rotas `/admin/*`; vazio = rotas desabilitadas (403) |
| `ADMIN_RAW_QUERY_ENABLED` | `0` | `1` habilita `/admin/query` (somente um `SELECT`, em conexão somente-leitura) |

## Estrutura

```
app.py              # composition root: create_app() + app.run
config/             # settings (env) e constantes de domínio
database/           # conexão por request, schema e seed
models/             # acesso a dados (SQL parametrizado) e regras de entidade
services/           # pedidos, relatório de vendas, notificações
controllers/        # fluxo HTTP por recurso + validação de entrada
views/routes.py     # mapeamento URL -> controller (Blueprint)
middlewares/        # tratamento de erros centralizado, guarda de admin
utils/errors.py     # exceções de domínio
```
