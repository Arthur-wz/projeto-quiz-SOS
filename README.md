# projeto-quiz-SOS
um projeto baseado no show do milhao onde ao inves de perguntas de curiosidades teremos perguntas educacionais

## Login com Google

Para ativar o login com Google, configure estas variaveis de ambiente antes de subir o servidor:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`

No Google Cloud Console, use uma destas URLs de callback no OAuth:

- `http://127.0.0.1:8000/accounts/google/login/callback/`
- `http://localhost:8000/accounts/google/login/callback/`

Depois rode:

```bash
python manage.py migrate
python manage.py runserver
```
