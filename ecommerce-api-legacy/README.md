# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000` (ou na porta de `PORT`). O banco SQLite é em memória por padrão e já carrega seeds automaticamente no boot.

Exemplos de requisições estão em `api.http`.

## Variáveis de ambiente

Veja `.env.example`.

| Variável | Padrão | Uso |
|---|---|---|
| `PORT` | `3000` | Porta HTTP |
| `DATABASE_PATH` | `:memory:` | Arquivo SQLite (ou memória) |
| `PAYMENT_GATEWAY_KEY` | vazio | Chave do gateway de pagamento |
| `ADMIN_TOKEN` | vazio | Token exigido no header `X-Admin-Token` pelas rotas administrativas. Vazio = rotas desabilitadas (403) |
| `LOG_LEVEL` | `info` | `error`, `warn`, `info` ou `debug` |

Rotas protegidas por `X-Admin-Token`: `GET /api/admin/financial-report` e `DELETE /api/users/:id`.

## Estrutura

```
src/
├── app.js            # composição: config, banco, camadas, servidor
├── config/           # configuração (env) e constantes de negócio
├── database/         # conexão, schema, seed, helpers async e transações
├── models/           # acesso a dados por entidade
├── services/         # checkout, gateway de pagamento, relatório, remoção de usuário
├── controllers/      # leitura/validação da requisição e resposta HTTP
├── routes/           # mapeamento URL -> controller
├── middlewares/      # tratamento de erros, guarda admin, wrapper async
└── utils/            # logger, hash de senha, HttpError
```
