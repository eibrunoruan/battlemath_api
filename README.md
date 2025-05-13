# BattleMath API

Este projeto implementa uma API REST e WebSocket para um jogo de perguntas e respostas matemáticas em tempo real. Este projeto foi realizado para auxiliar o reforço matemático em Jaraguá do Sul.

## Tecnologias

* **Python 3.12**
* **Flask 3.1.0**: microframework web para construir a API REST.
* **SQLAlchemy 2.0** + **Flask-SQLAlchemy 3.1.1**: ORM para interagir com o banco.
* **PostgreSQL**: banco de dados relacional (via Supabase).

---

## Configuração de Ambiente

Crie um arquivo `.env` na raiz do projeto com as variáveis:

```ini
DATABASE_URL=postgresql://<usuário>:<senha>@<host>:<porta>/<db>?sslmode=require
REDIS_URL=redis://redis:6379/0
SECRET_KEY=sua_chave_secreta_aqui
```

No `.env`, inclua:

```yaml

  DATABASE_URL='URL do Database'
  SECRET_KEY='Sua-chave-Secreta'
```


---

## Rotas da API REST

Base: `http://127.0.0.1:5000`

### Autenticação

#### `POST /auth/login`

Request:

```json
{
  "username": "seu_usuario",
  "password": "sua_senha"
}
```

Response (200):

```json
{
  "token": "<JWT>"
}
```

---

### Clientes

#### `POST /clients/register`

Cadastro de usuário (não requer token):

Request:

```json
{
  "username": "novo_usuario",
  "password": "senha",
  "name": "Nome Completo",
  "email": "email@exemplo.com"
}
```

Response (201):

```json
{
  "id": 1,
  "username": "novo_usuario",
  "name": "Nome Completo",
  "email": "email@exemplo.com",
  "icon": "static/icons/default.png",
  "points": 0,
  "created_at": "2025-05-05T12:34:56.789012",
  "badges": []
}
```

#### `GET /clients`  (token obrigatório)

Listar todos os usuários:

Headers:

```
Authorization: Bearer <JWT>
```

Response (200):

```json
[
  {...},
  {...}
]
```

#### `GET /clients?client_id=<id>`

Detalhes de um cliente:

Response (200):

```json
{ ... }
```

#### `PUT /clients/<id>`  (token)

Atualizar dados próprios:

Request:

```json
{
  "name": "Novo Nome",
  "email": "novo@exemplo.com"
}
```

#### `DELETE /clients/<id>`  (token)

Deletar conta própria.

#### `GET /clients/<id>/history`  (token)

Histórico de jogos do usuário:

Response:

```json
[
  {
    "game_id": 10,
    "correct_answers": 7,
    "wrong_answers": 3,
    "time_played": 45,
    "result": "win"
  }
]
```

---

### Jogo

#### `POST /game/start`  (token)

Inicia um jogo.

Request:

```json
{
  "categories": ["Álgebra", "Geometria"]
}
```

Response (201):

```json
{
  "message": "Game created. Waiting for another player.",
  "game_id": 5
}
```

#### `POST /game/end`  (token)

Encerra um jogo por REST (usual no backend ou admin).

Request:

```json
{
  "game_id": 5,
  "total_time": 80,
  "winner_id": 2,
  "stats": [
    {"player_id":1, "correct_answers":4, "wrong_answers":6, "time_played":80, "result":"lose"},
    {"player_id":2, "correct_answers":7, "wrong_answers":3, "time_played":80, "result":"win"}
  ]
}
```

Response (200): `{ "message": "Game finished successfully" }`

#### `GET /ranking`

Ranking top 10 jogadores:

Response:

```json
[
  {"username":"player1","points":320,"icon":"..."},
  {...}
]
```

---

## WebSocket

Endpoint: `ws://127.0.0.1:5000/ws/game?token=<JWT>`

Eventos:

1. **on\_connect**: autentica via JWT no query param ou header.
2. **on\_join**: `{ "game_id": 5 }` → entra na sala.
3. **on\_ready**: `{ "game_id": 5, "categories": [ ... ] }` → começa o jogo.
4. **on\_request\_question**: `{ "game_id": 5 }` → recebe `new_question`.
5. **on\_answer**: `{ "game_id":5, "question_id":12, "answer":"A" }` → recebe `state_update`.
6. **game\_over**: broadcast quando alguém perde.

