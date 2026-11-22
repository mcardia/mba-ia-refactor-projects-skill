# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo (ex.: `joao@email.com` / `123456`). As senhas são armazenadas com hash; um banco antigo com senhas em texto puro é convertido no boot.

## Configuração (variáveis de ambiente)

| Variável | Padrão | Uso |
|---|---|---|
| `SECRET_KEY` | aleatória a cada boot | chave de assinatura do Flask |
| `APP_HOST` / `APP_PORT` | `127.0.0.1` / `5000` | endereço do servidor (use `APP_HOST=0.0.0.0` para expor na rede) |
| `APP_DEBUG` | `0` | `1` ativa o modo debug (nunca em produção) |
| `APP_ENV` | `producao` | valor exibido em `/health` |
| `DATABASE_PATH` | `loja.db` | caminho do arquivo SQLite |
| `CORS_ORIGINS` | vazio | origens permitidas, separadas por vírgula |
| `ADMIN_TOKEN` | vazio | token exigido no header `X-Admin-Token` pelos endpoints `/admin/*`; vazio desativa esses endpoints (403) |
| `ALLOW_ADMIN_QUERY` | `0` | `1` habilita `/admin/query` (apenas um `SELECT`, conexão somente leitura) |

Veja `.env.example`.

## Estrutura

```
app.py                 # create_app() + execução
config/                # settings (ambiente) e constantes de negócio
database/connection.py # conexão por requisição, schema, seed
models/                # acesso a dados (SQL parametrizado)
services/              # regras de pedido, relatório e notificações
controllers/           # fluxo de cada endpoint + validação
views/routes.py        # tabela de rotas (Blueprint)
middlewares/           # tratamento de erros centralizado e guarda de admin
utils/errors.py        # exceções de domínio
```
