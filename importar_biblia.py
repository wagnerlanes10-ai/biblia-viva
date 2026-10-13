"""
Bíblia Viva — Importador de Bíblia em JSON

Lê os arquivos JSON (um por livro) e insere os versículos no banco.

Formato esperado do JSON:
{
  "id": 1,
  "code": "GEN",
  "name": "Gênesis",
  "abbrev": "Gn",
  "chapters": [
    {"number": 1, "verses": [{"number": 1, "text": "..."}]},
    ...
  ]
}

Uso:
    python importar_biblia.py <translation_id> <pasta_json>

Exemplo:
    python importar_biblia.py 3 ~/biblia_viva/dados
"""

import json
import sys
from pathlib import Path

from database import SessionLocal
from models import Book, Verse


# Lista dos 66 códigos, na ordem canônica
CODIGOS = [
    "GEN", "EXO", "LEV", "NUM", "DEU", "JOS", "JDG", "RUT",
    "1SA", "2SA", "1KI", "2KI", "1CH", "2CH", "EZR", "NEH",
    "EST", "JOB", "PSA", "PRO", "ECC", "SNG", "ISA", "JER",
    "LAM", "EZK", "DAN", "HOS", "JOL", "AMO", "OBA", "JON",
    "MIC", "NAM", "HAB", "ZEP", "HAG", "ZEC", "MAL",
    "MAT", "MRK", "LUK", "JHN", "ACT", "ROM", "1CO", "2CO",
    "GAL", "EPH", "PHP", "COL", "1TH", "2TH", "1TI", "2TI",
    "TIT", "PHM", "HEB", "JAS", "1PE", "2PE", "1JN", "2JN",
    "3JN", "JUD", "REV",
]


def importar(translation_id: int, pasta: Path):
    db = SessionLocal()
    try:
        total_versiculos = 0
        total_livros = 0

        for ordem, codigo in enumerate(CODIGOS, start=1):
            arquivo = pasta / f"{codigo}.json"
            if not arquivo.exists():
                print(f"⚠  Faltando: {codigo}.json")
                continue

            with open(arquivo, "r", encoding="utf-8") as f:
                dados = json.load(f)

            book_id = ordem  # 1 = Gênesis, 2 = Êxodo, etc.

            # Verifica se o livro existe no banco
            livro = db.query(Book).filter(Book.id == book_id).first()
            if not livro:
                print(f"⚠  Livro id={book_id} ({codigo}) não está no banco. Pule.")
                continue

            # Evita duplicação: apaga versículos dessa tradução+livro
            db.query(Verse).filter(
                Verse.translation_id == translation_id,
                Verse.book_id == book_id,
            ).delete()

            # Insere os versículos
            for capitulo in dados.get("chapters", []):
                num_cap = capitulo.get("number")
                for vers in capitulo.get("verses", []):
                    db.add(Verse(
                        translation_id=translation_id,
                        book_id=book_id,
                        chapter=num_cap,
                        verse=vers.get("number"),
                        text=vers.get("text", ""),
                    ))
                    total_versiculos += 1

            db.commit()
            total_livros += 1
            print(f"✓ {codigo:5} ({livro.name:20}) — {total_versiculos} versículos acumulados")

        print()
        print("=== Importação concluída ===")
        print(f"Livros importados: {total_livros}/66")
        print(f"Versículos inseridos: {total_versiculos}")

    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python importar_biblia.py <translation_id> <pasta_json>")
        print("Exemplo: python importar_biblia.py 3 ~/biblia_viva/dados")
        sys.exit(1)

    t_id = int(sys.argv[1])
    pasta = Path(sys.argv[2]).expanduser()

    if not pasta.exists():
        print(f"Pasta não encontrada: {pasta}")
        sys.exit(1)

    print(f"Importando tradução {t_id} de {pasta}")
    print()
    importar(t_id, pasta)
