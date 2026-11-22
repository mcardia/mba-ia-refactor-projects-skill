# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
ADMIN_TOKEN=um-token-longo npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

Exemplos de requisições estão em `api.http`.

## Variáveis de ambiente

| Variável | Padrão | Uso |
|---|---|---|
| `PORT` | `3000` | Porta HTTP |
| `HOST` | (todas as interfaces) | Interface de escuta, ex. `127.0.0.1` |
| `DATABASE_PATH` | `:memory:` | Arquivo SQLite (ou memória) |
| `PAYMENT_GATEWAY_KEY` | vazio | Chave do gateway de pagamento (simulado) |
| `ADMIN_TOKEN` | vazio | Token exigido no header `X-Admin-Token` pelas rotas administrativas. Vazio = rotas desabilitadas (403) |
| `LOG_LEVEL` | `info` | `debug`, `info`, `warn`, `error` |

Veja `.env.example`.

## Rotas

| Método | Rota | Proteção |
|---|---|---|
| POST | `/api/checkout` | pública |
| GET | `/api/admin/financial-report` | `X-Admin-Token` |
| DELETE | `/api/users/:id` | `X-Admin-Token` |

Erros respondem em JSON: `{ "error": "<mensagem>" }`.

## Estrutura

```
src/
├── app.js            # composition root (npm start)
├── config/           # configuração via env + constantes de negócio
├── database/         # conexão SQLite, transações, schema e seed
├── models/           # acesso a dados por entidade
├── services/         # checkout, gateway de pagamento, relatório, exclusão de usuário
├── controllers/      # leitura/validação da requisição e resposta HTTP
├── routes/           # express.Router por recurso
├── middlewares/      # tratamento de erros, guarda de admin, async wrapper
└── utils/            # erro HTTP, logger, hash de senha
```
