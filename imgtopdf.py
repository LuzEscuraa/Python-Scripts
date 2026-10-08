"""
Conversor de imagens para PDF (um PDF por imagem)
------------------------------------------------
Converte todas as imagens da PASTA ATUAL (onde o script está sendo
executado) em arquivos PDF separados — um PDF para cada imagem.
Suporta PNG, JPG/JPEG, BMP, GIF, TIFF, WEBP, ICO e outros formatos
que o Pillow consegue abrir.

A página do PDF é criada com o tamanho EXATO da imagem (não usa A4 nem
nenhum tamanho padrão). Isso garante que a imagem sempre cabe inteira
numa única página, sem cortar nada e sem sobrar borda — e a orientação
(retrato ou paisagem) é definida automaticamente pela própria imagem.

Os arquivos de imagem originais são enviados para a lixeira do sistema
após a conversão.

Requisitos:
    pip install Pillow send2trash

Uso:
    Coloque este arquivo dentro da pasta com as imagens e execute:
        python png-to-pdf.py

    Se quiser manter os arquivos originais (não enviar para a lixeira):
        python png-to-pdf.py --manter-original
"""

import argparse
import sys
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


DPI = 96

EXTENSOES_VALIDAS = {
    ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".tif",
    ".webp", ".ico", ".ppm", ".pgm", ".pbm",
}


def converter_png_para_pdf(arquivo: Path, destino: Path):
    
    with Image.open(arquivo) as img:
        # Como PDFs não suportam transparência (canal alfa); converte pra RGB
        # com fundo branco quando necessário.
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            fundo = Image.new("RGB", img.size, (255, 255, 255))
            img_rgba = img.convert("RGBA")
            fundo.paste(img_rgba, mask=img_rgba.split()[-1])
            img_final = fundo
        elif img.mode != "RGB":
            img_final = img.convert("RGB")
        else:
            img_final = img.copy()

      
        img_final.save(destino, "PDF", resolution=DPI)


def converter_pasta_atual(manter_original: bool = False):
    pasta = Path.cwd()

    arquivos = [
        f for f in pasta.iterdir()
        if f.is_file() and f.suffix.lower() in EXTENSOES_VALIDAS
    ]

    if not arquivos:
        print("Nenhuma imagem encontrada.")
        return

    total = len(arquivos)
    convertidos = 0
    erros = 0

    print(f"Pasta: {pasta}")
    print(f"Encontrado(s) {total} imagem(ns). Iniciando conversão para PDF...\n")

    for arquivo in arquivos:
        destino = pasta / (arquivo.stem + ".pdf")
        try:
            converter_png_para_pdf(arquivo, destino)

            tamanho_mb = destino.stat().st_size / (1024 * 1024)
            convertidos += 1
            print(f"[OK] {arquivo.name} -> {destino.name} ({tamanho_mb:.2f} MB)")

            if not manter_original:
                try:
                    send2trash(str(arquivo))
                    print("      (original enviado para a lixeira)")
                except Exception as e_lixeira:
                    print(f"      [AVISO] não foi possível enviar '{arquivo.name}' para a lixeira: {e_lixeira}")

        except Exception as e:
            erros += 1
            print(f"[ERRO] Falha ao converter '{arquivo.name}': {e}")

    print(f"\nConcluído: {convertidos} convertido(s), {erros} erro(s), de {total} arquivo(s).")


def main():
    parser = argparse.ArgumentParser(
        description="Converte as imagens da pasta atual em PDFs individuais (página do tamanho exato da imagem)."
    )
    parser.add_argument(
        "--manter-original",
        action="store_true",
        help="Mantém os arquivos de imagem originais (por padrão, são enviados para a lixeira após a conversão).",
    )

    args = parser.parse_args()
    converter_pasta_atual(args.manter_original)


if __name__ == "__main__":
    main()
