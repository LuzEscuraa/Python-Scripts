"""
Conversor de imagens para PNG (versão 3)
------------------------------------------------------
Converte todas as imagens da PASTA ATUAL (onde o script está sendo executado)
para o formato PNG. Não precisa informar caminho nenhum.

Os arquivos originais são enviados para a lixeira do sistema após a conversão.

Se o PNG resultante (seja de uma conversão, seja um PNG que JÁ EXISTIA na
pasta) ultrapassar 4,15 MB, o script tenta reduzir o tamanho em etapas,
da menos agressiva para a mais agressiva:
    1. Compressão PNG máxima (sem perda nenhuma de qualidade)
    2. Redução de paleta de cores (perda mínima, quase imperceptível)
    3. Redimensionamento gradual (só como último recurso)

Novidade desta versão: arquivos que já estão em .png e ultrapassam o
limite também são verificados e comprimidos no lugar, mesmo que não
precisem passar por conversão de formato.

Requisitos:
    pip install Pillow send2trash

Uso:
    Coloque este arquivo dentro da pasta com as imagens e execute:
        python png-convert-3.py

    Se quiser manter os arquivos originais (não enviar para a lixeira):
        python png-convert-3.py --manter-original
"""

import argparse
import io
import os
import sys
import time
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("A biblioteca Pillow não está instalada.")
    print("Instale com: pip install Pillow")
    sys.exit(1)

try:
    from send2trash import send2trash
except ImportError:
    print("A biblioteca send2trash não está instalada.")
    print("Instale com: pip install send2trash")
    sys.exit(1)

# Extensões de imagem que serão consideradas para conversão
EXTENSOES_VALIDAS = {
    ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".tif",
    ".webp", ".ico", ".ppm", ".pgm", ".pbm",
}

# Limite máximo de tamanho do arquivo PNG final
LIMITE_MB = 4.15
LIMITE_BYTES = int(LIMITE_MB * 1024 * 1024)


def _tamanho_em_bytes(img: Image.Image) -> bytes:
    """Salva a imagem em memória com compressão máxima e retorna os bytes."""
    buffer = io.BytesIO()
    img.save(buffer, "PNG", optimize=True, compress_level=9)
    return buffer.getvalue()


def salvar_png_respeitando_limite(img: Image.Image, destino: Path) -> str:
    """
    Salva a imagem como PNG tentando ficar abaixo de LIMITE_BYTES,
    aplicando reduções progressivas somente se necessário.
    Retorna uma string descrevendo o que foi feito.
    """
    # Etapa 1: compressão PNG máxima, sem nenhuma perda de qualidade
    dados = _tamanho_em_bytes(img)
    if len(dados) <= LIMITE_BYTES:
        destino.write_bytes(dados)
        return "sem necessidade de compressão adicional"

    # Etapa 2: redução de paleta de cores (quantização adaptativa)
    # Perda mínima, geralmente imperceptível a olho nu.
    img_paleta = img.convert("RGBA") if img.mode != "RGBA" else img
    img_quantizada = img_paleta.convert(
        "P", palette=Image.ADAPTIVE, colors=256
    )
    dados = _tamanho_em_bytes(img_quantizada)
    if len(dados) <= LIMITE_BYTES:
        destino.write_bytes(dados)
        return "reduzida a paleta de cores (qualidade praticamente igual)"

    # Etapa 3: redimensionamento gradual (último recurso)
    # Reduz a resolução em passos de 10% até atingir o limite.
    img_atual = img
    escala = 1.0
    while len(dados) > LIMITE_BYTES and escala > 0.2:
        escala -= 0.1
        nova_largura = max(1, int(img.width * escala))
        nova_altura = max(1, int(img.height * escala))
        img_atual = img.resize((nova_largura, nova_altura), Image.LANCZOS)
        dados = _tamanho_em_bytes(img_atual)

    destino.write_bytes(dados)
    if escala <= 0.2:
        return (
            f"AVISO: mesmo reduzida para {int(escala*100)}% do tamanho original, "
            f"o arquivo ainda pode estar próximo do limite de {LIMITE_MB} MB"
        )
    return f"imagem redimensionada para {int(escala*100)}% do tamanho original para caber no limite"


def comprimir_png_existente(arquivo: Path) -> str:
    """
    Verifica se um PNG já existente ultrapassa o limite de tamanho e,
    se sim, tenta comprimi-lo no lugar usando as mesmas etapas
    (compressão máxima -> paleta de cores -> redimensionamento).
    Retorna uma string descrevendo o que foi feito, ou None se não precisou mexer.
    """
    tamanho_original = arquivo.stat().st_size
    if tamanho_original <= LIMITE_BYTES:
        return None

    with Image.open(arquivo) as img:
        img = img.convert("RGBA") if img.mode not in ("RGB", "RGBA", "P") else img.copy()

        # Etapa 1: recomprimir com compressão máxima (sem perda)
        dados = _tamanho_em_bytes(img)

        # Etapa 2: paleta de cores, se a etapa 1 não foi suficiente
        if len(dados) > LIMITE_BYTES:
            img_paleta = img.convert("RGBA") if img.mode != "RGBA" else img
            img_quantizada = img_paleta.convert("P", palette=Image.ADAPTIVE, colors=256)
            dados_quant = _tamanho_em_bytes(img_quantizada)
            if len(dados_quant) < len(dados):
                dados = dados_quant
                img = img_quantizada

        # Etapa 3: redimensionamento gradual, se ainda necessário
        escala = 1.0
        img_base = img
        while len(dados) > LIMITE_BYTES and escala > 0.2:
            escala -= 0.1
            nova_largura = max(1, int(img_base.width * escala))
            nova_altura = max(1, int(img_base.height * escala))
            img_redimensionada = img_base.resize((nova_largura, nova_altura), Image.LANCZOS)
            dados = _tamanho_em_bytes(img_redimensionada)

    # Só sobrescreve se o resultado for realmente menor que o original.
    # Escreve primeiro em um arquivo temporário e só então substitui o
    # original de forma atômica (os.replace) — evita erros de acesso no
    # Windows ao tentar escrever no mesmo arquivo que acabou de ser lido.
    if len(dados) < tamanho_original:
        arquivo_temp = arquivo.with_name(arquivo.stem + ".tmp_compress.png")
        arquivo_temp.write_bytes(dados)
        os.replace(arquivo_temp, arquivo)
        tamanho_final_mb = len(dados) / (1024 * 1024)
        if escala < 1.0:
            return f"PNG já existente comprimido para {tamanho_final_mb:.2f} MB (redimensionado para {int(escala*100)}%)"
        return f"PNG já existente comprimido para {tamanho_final_mb:.2f} MB"

    return "AVISO: não foi possível reduzir o PNG abaixo do tamanho original"


def converter_pasta_atual(manter_original: bool = False):
    pasta = Path.cwd()

    arquivos_para_converter = [
        f for f in pasta.iterdir()
        if f.is_file() and f.suffix.lower() in EXTENSOES_VALIDAS
    ]
    arquivos_png_existentes = [
        f for f in pasta.iterdir()
        if f.is_file() and f.suffix.lower() == ".png"
    ]

    if not arquivos_para_converter and not arquivos_png_existentes:
        print("Nenhuma imagem encontrada nesta pasta.")
        return

    total = len(arquivos_para_converter)
    convertidos = 0
    erros = 0

    print(f"Pasta: {pasta}\n")

    # Etapa 0: comprimir PNGs que já existem e estão acima do limite
    pngs_grandes = [f for f in arquivos_png_existentes if f.stat().st_size > LIMITE_BYTES]
    if pngs_grandes:
        print(f"Encontrado(s) {len(pngs_grandes)} PNG(s) já existente(s) acima de {LIMITE_MB} MB. Comprimindo...\n")
        for png in pngs_grandes:
            # Tenta até 3 vezes: em alguns sistemas (principalmente Windows),
            # o arquivo pode estar momentaneamente bloqueado por outro
            # processo (antivírus, explorer, etc.) logo após ser lido.
            ultimo_erro = None
            for tentativa in range(1, 4):
                try:
                    resultado = comprimir_png_existente(png)
                    if resultado:
                        print(f"[PNG] {png.name}: {resultado}")
                    ultimo_erro = None
                    break
                except Exception as e:
                    ultimo_erro = e
                    time.sleep(0.5)
            if ultimo_erro is not None:
                print(f"[ERRO] Falha ao comprimir '{png.name}': {ultimo_erro}")
        print()

    if not arquivos_para_converter:
        print("Nenhuma outra imagem para converter.")
        return

    print(f"Encontradas {total} imagem(ns) para converter. Iniciando conversão...\n")

    for arquivo in arquivos_para_converter:
        destino = pasta / (arquivo.stem + ".png")
        try:
            with Image.open(arquivo) as img:
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGBA")
                resultado = salvar_png_respeitando_limite(img, destino)

            tamanho_final_mb = destino.stat().st_size / (1024 * 1024)
            convertidos += 1
            print(f"[OK] {arquivo.name} -> {destino.name} ({tamanho_final_mb:.2f} MB — {resultado})")

            if not manter_original:
                try:
                    send2trash(str(arquivo))
                    print("      (original enviado para a lixeira)")
                except Exception as e_lixeira:
                    print(f"      [AVISO] não foi possível enviar '{arquivo.name}' para a lixeira: {e_lixeira}")

        except Exception as e:
            erros += 1
            print(f"[ERRO] Falha ao converter '{arquivo.name}': {e}")

    print(f"\nConcluído: {convertidos} convertida(s), {erros} erro(s), de {total} arquivo(s).")


def main():
    parser = argparse.ArgumentParser(
        description="Converte as imagens da pasta atual para PNG e comprime PNGs acima de 4,15 MB."
    )
    parser.add_argument(
        "--manter-original",
        action="store_true",
        help="Mantém o arquivo original (por padrão, ele é enviado para a lixeira após a conversão).",
    )

    args = parser.parse_args()
    converter_pasta_atual(args.manter_original)


if __name__ == "__main__":
    main()
