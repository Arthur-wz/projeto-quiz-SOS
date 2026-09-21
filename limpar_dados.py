import json

ARQUIVO_ENTRADA = "backups/dados.json"
ARQUIVO_SAIDA = "backups/dados_limpos.json"

MODELOS_REMOVER = {
    "quiz.pergunta",
    "contenttypes.contenttype",
    "auth.permission",
    "admin.logentry",
    "sessions.session",
}

with open(ARQUIVO_ENTRADA, "r", encoding="utf-8") as arquivo:
    dados = json.load(arquivo)

dados_limpos = [
    item
    for item in dados
    if item.get("model") not in MODELOS_REMOVER
]

with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as arquivo:
    json.dump(
        dados_limpos,
        arquivo,
        ensure_ascii=False,
        indent=2
    )

print("Backup limpo criado com sucesso!")
print(f"Registros originais: {len(dados)}")
print(f"Registros mantidos: {len(dados_limpos)}")