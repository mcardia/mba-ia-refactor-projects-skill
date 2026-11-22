# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo (senhas armazenadas como hash):

| Email | Senha |
|---|---|
| admin@loja.com | admin123 |
| joao@email.com | 123456 |
| maria@email.com | senha123 |

## Configuração (variáveis de ambiente)

Todas são opcionais; veja `.env.example`.

| Variável | Padrão | Descrição |
|---|---|---|
| `SECRET_KEY` | aleatória a cada boot | Chave de assinatura do Flask |
| `APP_DEBUG` | `0` | `1` liga o modo debug (nunca em produção) |
| `APP_HOST` | `127.0.0.1` | Interface de escuta (`0.0.0.0` para expor na rede) |
| `APP_PORT` | `5000` | Porta HTTP |
| `APP_ENV` | `producao` | Nome do ambiente exibido em `/health` |
| `DATABASE_PATH` | `loja.db` | Caminho do arquivo SQLite |
| `CORS_ORIGINS` | vazio | Origens permitidas, separadas por vírgula (vazio = sem CORS) |
| `ADMIN_TOKEN` | vazio | Token exigido no header `X-Admin-Token` pelas rotas `/admin/*`; vazio = rotas desabilitadas (403) |
| `ADMIN_SQL_QUERY_ENABLED` | `0` | `1` habilita `POST /admin/query` (somente uma instrução `SELECT`, conexão somente leitura) |

Exemplo: `ADMIN_TOKEN=troque-me python app.py` e então
`curl -X POST -H "X-Admin-Token: troque-me" http://localhost:5000/admin/reset-db`.

## Estrutura (MVC)

```
app.py                 # ponto de entrada: create_app() + app.run
config/                # settings (env) e constantes de negócio
database/connection.py # conexão por requisição, schema e seed
models/                # acesso a dados (SQL parametrizado) por entidade
services/              # pedidos, relatório de vendas, notificações
controllers/           # fluxo HTTP por recurso + validação de entrada
views/routes.py        # registro das rotas (Blueprint)
middlewares/           # tratamento centralizado de erros e guarda de admin
utils/errors.py        # exceções de domínio
```
