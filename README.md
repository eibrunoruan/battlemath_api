# BattleMath API

Este projeto implementa uma **API REST** para um jogo de perguntas e respostas matemáticas em tempo real. Ele foi desenvolvido para auxiliar no reforço escolar em matemática na cidade de Jaraguá do Sul.

## Tecnologias Utilizadas

- **Python 3.12**
- **Flask 3.1.0** – microframework web.
- **SQLAlchemy 2.0** + **Flask-SQLAlchemy 3.1.1** – ORM para manipulação do banco.
- **PostgreSQL** – banco de dados relacional (utilizado via Supabase).

---

## Configuração de Ambiente

Crie um arquivo `.env` na raiz do projeto com as variáveis de ambiente:

```ini
DATABASE_URL=postgresql://<usuario>:<senha>@<host>:<porta>/<database>?sslmode=require
SECRET_KEY=sua_chave_secreta_aqui
```

---

## Rotas da API REST

URL base: `http://127.0.0.1:5000`

### 🔐 Autenticação

#### `POST /auth/login`

Autentica um usuário e retorna o token JWT.

**Request:**

```json
{
  "username": "seu_usuario",
  "password": "sua_senha"
}
```

**Response:**

```json
{
  "token": "<JWT>"
}
```

---

### 👤 Usuários

#### `POST /clients/register`

Cria um novo usuário (não requer autenticação):

```json
{
  "username": "usuario",
  "password": "senha",
  "name": "Nome Completo",
  "email": "email@exemplo.com"
}
```

#### `GET /clients` (requer token)

Lista todos os usuários cadastrados.

#### `GET /clients?client_id=<id>`

Retorna os dados de um usuário específico.

#### `PUT /clients/<id>` (requer token)

Atualiza os dados do usuário autenticado.

#### `DELETE /clients/<id>` (requer token)

Remove a conta do usuário autenticado.

#### `GET /clients/<id>/history` (requer token)

Retorna o histórico de partidas do usuário.

---

### 🎮 Jogo

#### `POST /game/start` (requer token)

Cria uma nova partida (modo pareamento).

```json
{
  "categories": ["Álgebra", "Geometria"]
}
```

**Response:**

```json
{
  "message": "Game created. Waiting for another player.",
  "game_id": 5
}
```

#### `POST /game/end` (requer token)

Finaliza uma partida e salva os dados.

```json
{
  "game_id": 5,
  "total_time": 80,
  "winner_id": 2,
  "stats": [
    {
      "player_id": 1,
      "correct_answers": 4,
      "wrong_answers": 6,
      "time_played": 80,
      "result": "lose"
    },
    {
      "player_id": 2,
      "correct_answers": 7,
      "wrong_answers": 3,
      "time_played": 80,
      "result": "win"
    }
  ]
}
```

**Response:**

```json
{
  "message": "Game finished successfully"
}
```

---


---

### 🙋‍♂️ Interação do Jogador

#### `GET /game/question?game_id=<id>` (requer token)

Obtém uma nova pergunta para o jogador responder.

**Response:**

```json
{
  "question_id": 12,
  "question": "Quanto é 8 × 7?",
  "options": {
    "A": "54",
    "B": "56",
    "C": "64",
    "D": "58"
  }
}
```

#### `POST /game/submit_answer` (requer token)

Envia a resposta de uma pergunta.

**Request:**

```json
{
  "game_id": 5,
  "question_id": 12,
  "answer": "B"
}
```

**Response:**

```json
{
  "correct": true,
  "time_update": 2,
  "opponent_time_update": -2,
  "message": "Resposta correta!"
}
```


### 🏆 Ranking

#### `GET /ranking`

Retorna o top 10 jogadores:

```json
[
  {
    "username": "player1",
    "points": 320,
    "icon": "static/icons/player1.png"
  },
  ...
]
```

---