# Projeto Quiz SOS

Projeto web em `Django` inspirado no Show do Milhao, mas com foco em perguntas educacionais.

Hoje o sistema possui:
- login local com usuario e senha
- login com Google
- quiz com 20 perguntas por partida
- pontuacao, acertos, erros e ajudas
- historico de partidas e respostas
- ranking semanal e mensal
- temas visuais por usuario
- backup e compartilhamento de dados em JSON


## Estrutura do projeto

Pastas e arquivos mais importantes:

- `config/`
  Configuracao global do projeto Django.

- `quiz/`
  App principal com models, views, urls, templates, admin e comandos customizados.

- `backups/`
  Pasta usada para exportar e compartilhar dados do projeto.

- `db.sqlite3`
  Banco local SQLite da maquina atual.

- `manage.py`
  Arquivo usado para rodar comandos do Django.


## Tecnologias usadas

- `Python`
- `Django 6`
- `SQLite`
- `django-allauth`


## Como rodar o projeto

### 1. Criar e ativar ambiente virtual

No Windows:

```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 2. Instalar dependencias

```powershell
pip install -r requirements.txt
```

### 3. Aplicar migrations

```powershell
python manage.py migrate
```

### 4. Rodar o servidor

```powershell
python manage.py runserver
```

Depois abra:

- `http://127.0.0.1:8000/`


## Login com Google

O projeto ainda esta com a estrutura de login com Google ativa.

Para funcionar, configure estas variaveis de ambiente:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`

Exemplo no PowerShell:

```powershell
$env:GOOGLE_CLIENT_ID="seu-client-id"
$env:GOOGLE_CLIENT_SECRET="seu-client-secret"
python manage.py runserver
```

No Google Cloud Console, use uma destas URLs de callback:

- `http://127.0.0.1:8000/accounts/google/login/callback/`
- `http://localhost:8000/accounts/google/login/callback/`

Importante:
- se voce cadastrar `127.0.0.1`, abra o projeto usando `127.0.0.1`
- se voce cadastrar `localhost`, abra usando `localhost`
- nao misture os dois no teste


## Banco de dados atual

O projeto usa `SQLite`.

Isso significa:
- o banco fica em um arquivo local chamado `db.sqlite3`
- cada maquina pode ter seu proprio banco local
- para trabalho em grupo, o ideal nao e compartilhar o `db.sqlite3`
- o ideal e compartilhar os dados em arquivos JSON dentro da pasta `backups/`


## Como criar o banco local

Se a pessoa acabou de clonar o projeto:

```powershell
python manage.py migrate
```

Esse comando cria a estrutura do banco local com base nas migrations.


## Como fazer backup dos dados

O projeto tem um comando customizado de backup em:

- `quiz/management/commands/backup.py`

### Backup automatico completo

```powershell
python manage.py backup
```

Esse comando:
- cria a pasta `backups/` se ela nao existir
- gera um arquivo JSON com data e hora
- exporta os dados do banco para esse arquivo

Exemplo de nome gerado:

- `backups/backup_2026-08-10_14-30.json`

### Backup completo com nome definido por voce

```powershell
python manage.py backup --output backups\meu_backup.json
```


## Como exportar dados manualmente

### Exportar so as perguntas

Mais recomendado para trabalho em grupo quando o foco e compartilhar o conteudo do quiz:

```powershell
python manage.py dumpdata quiz.Pergunta --indent 2 > backups\perguntas.json
```

### Exportar o banco inteiro em JSON

```powershell
python manage.py dumpdata --indent 2 > backups\dados.json
```


## Como importar dados

Antes de importar, monte a estrutura do banco:

```powershell
python manage.py migrate
```

### Importar so as perguntas

```powershell
python manage.py loaddata backups\perguntas.json
```

### Importar um dump maior

```powershell
python manage.py loaddata backups\dados.json
```


## Jeito certo de compartilhar o banco em grupo

### Opcao recomendada

Cada pessoa:
- cria seu proprio `db.sqlite3` com `migrate`
- recebe os mesmos dados por `JSON`

Fluxo:

1. Uma pessoa atualiza as perguntas.
2. Essa pessoa roda:

```powershell
python manage.py dumpdata quiz.Pergunta --indent 2 > backups\perguntas.json
```

3. Ela sobe `backups\perguntas.json` para o GitHub.
4. Quem puxar o projeto roda:

```powershell
python manage.py migrate
python manage.py loaddata backups\perguntas.json
```

### Quando faz sentido enviar o `db.sqlite3`

So faz sentido quando:
- voce quer copiar exatamente o banco da sua maquina para outra
- e nao se importa em sobrescrever o banco local da outra pessoa

Mesmo assim, isso nao e o ideal para equipe, porque:
- pode causar conflito
- o arquivo muda toda hora
- e mais dificil de versionar no Git


## O que vai e o que nao vai para o GitHub

### Pode ir

- codigo-fonte
- migrations
- `requirements.txt`
- `backups\perguntas.json`
- `backups\dados.json`

### Nao deve ir

- `db.sqlite3`
- `venv/`
- `__pycache__/`


## Comandos mais usados

### Rodar projeto

```powershell
python manage.py runserver
```

### Aplicar migrations

```powershell
python manage.py migrate
```

### Criar novas migrations

```powershell
python manage.py makemigrations
```

### Rodar testes

```powershell
python manage.py test
```

### Verificar projeto

```powershell
python manage.py check
```

### Backup completo

```powershell
python manage.py backup
```


## Resumo curto

Se a ideia for so usar o projeto normalmente:

```powershell
python manage.py migrate
python manage.py runserver
```

Se a ideia for compartilhar dados com outra pessoa:

```powershell
python manage.py dumpdata quiz.Pergunta --indent 2 > backups\perguntas.json
```

E na outra maquina:

```powershell
python manage.py migrate
python manage.py loaddata backups\perguntas.json
```
