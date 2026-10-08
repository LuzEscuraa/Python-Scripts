import os
#Script criado pra enumerar imagens de whatsapp em uma pasta seguindo a ordem de data/hora no nome do arquivo

PASTA = r#"c:insira o caminho da pasta aqui"

EXTENSOES_PERMITIDAS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif"
}



if not os.path.isdir(PASTA):
    print("ERRO: A pasta informada não existe.")
    input("\nPressione ENTER para sair...")
    exit()



arquivos = []

for arquivo in os.listdir(PASTA):
    caminho = os.path.join(PASTA, arquivo)

    # Ignora pastas
    if not os.path.isfile(caminho):
        continue

    # Verifica a extensão
    extensao = os.path.splitext(arquivo)[1].lower()

    if extensao in EXTENSOES_PERMITIDAS:
        arquivos.append(arquivo)


arquivos.sort(
    key=lambda arquivo: os.path.getctime(
        os.path.join(PASTA, arquivo)
    )
)

if not arquivos:
    print("Nenhuma imagem encontrada na pasta.")
    input("\nPressione ENTER para sair...")
    exit()



print("=" * 60)
print("ARQUIVOS ENCONTRADOS")
print("=" * 60)

for numero, arquivo in enumerate(arquivos, start=1):
    extensao = os.path.splitext(arquivo)[1]
    novo_nome = f"print{numero}{extensao}"

    print(f"{numero:03} | {arquivo} -> {novo_nome}")

print("=" * 60)


conflitos = []

for numero, arquivo in enumerate(arquivos, start=1):
    extensao = os.path.splitext(arquivo)[1]
    novo_nome = f"print{numero}{extensao}" #Você pode alterar o prefixo "print" para outro nome, se desejar.

    caminho_novo = os.path.join(PASTA, novo_nome)
    caminho_antigo = os.path.join(PASTA, arquivo)

    if (
        os.path.exists(caminho_novo)
        and os.path.abspath(caminho_novo)
        != os.path.abspath(caminho_antigo)
    ):
        conflitos.append(novo_nome)

if conflitos:
    print("\nERRO: Existem arquivos que já possuem os nomes:")
    
    for arquivo in conflitos:
        print(f" - {arquivo}")

    print("\nNenhuma alteração foi realizada.")
    input("\nPressione ENTER para sair...")
    exit()



print(f"\nSerão renomeados {len(arquivos)} arquivos.")
print("A ordem será baseada na data de criação dos arquivos.")

confirmacao = input("\nDeseja continuar? [S/N]: ").strip().lower()

if confirmacao != "s":
    print("\nOperação cancelada. Nenhum arquivo foi alterado.")
    input("\nPressione ENTER para sair...")
    exit()



print("\nRenomeando arquivos...\n")

for numero, arquivo in enumerate(arquivos, start=1):

    caminho_antigo = os.path.join(PASTA, arquivo)

    extensao = os.path.splitext(arquivo)[1]
    novo_nome = f"print{numero}{extensao}"

    caminho_novo = os.path.join(PASTA, novo_nome)

    try:
        os.rename(caminho_antigo, caminho_novo)

        print(f"[OK] {arquivo} -> {novo_nome}")

    except Exception as erro:
        print(f"[ERRO] Não foi possível renomear {arquivo}")
        print(f"       Motivo: {erro}")

print("\n" + "=" * 60)
print("RENOMEAÇÃO CONCLUÍDA!")
print("=" * 60)

input("\nPressione ENTER para sair...")
