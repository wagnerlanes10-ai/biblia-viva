"""Bíblia Viva — Importador da WEB do repositório TehShrike"""

import json
from pathlib import Path
from database import SessionLocal
from models import Book, Verse

LIVROS_WEB = {
    1: "genesis", 2: "exodus", 3: "leviticus", 4: "numbers", 5: "deuteronomy",
    6: "joshua", 7: "judges", 8: "ruth", 9: "1samuel", 10: "2samuel",
    11: "1kings", 12: "2kings", 13: "1chronicles", 14: "2chronicles",
    15: "ezra", 16: "nehemiah", 17: "esther", 18: "job", 19: "psalms",
    20: "proverbs", 21: "ecclesiastes", 22: "songofsolomon", 23: "isaiah",
    24: "jeremiah", 25: "lamentations", 26: "ezekiel", 27: "daniel",
    28: "hosea", 29: "joel", 30: "amos", 31: "obadiah", 32: "jonah",
    33: "micah", 34: "nahum", 35: "habakkuk", 36: "zephaniah", 37: "haggai",
    38: "zechariah", 39: "malachi",
    40: "matthew", 41: "mark", 42: "luke", 43: "john", 44: "acts",
    45: "romans", 46: "1corinthians", 47: "2corinthians", 48: "galatians",
    49: "ephesians", 50: "philippians", 51: "colossians",
    52: "1thessalonians", 53: "2thessalonians", 54: "1timothy",
    55: "2timothy", 56: "titus", 57: "philemon", 58: "hebrews",
    59: "james", 60: "1peter", 61: "2peter", 62: "1john", 63: "2john",
    64: "3john", 65: "jude", 66: "revelation",
}


def importar_web(translation_id, pasta):
    db = SessionLocal()
    try:
        total = 0
        for book_id, nome_arquivo in LIVROS_WEB.items():
            arquivo = pasta / f"{nome_arquivo}.json"
            if not arquivo.exists():
                print(f"AVISO: {nome_arquivo}.json nao existe")
                continue

            with open(arquivo, "r", encoding="utf-8") as f:
                dados = json.load(f)

            livro = db.query(Book).filter(Book.id == book_id).first()
            if not livro:
                print(f"AVISO: livro id={book_id} nao esta no banco")
                continue

            db.query(Verse).filter(
                Verse.translation_id == translation_id,
                Verse.book_id == book_id,
            ).delete()

            inseridos = 0
            vistos = set()  # (chapter, verse) já inseridos
            for item in dados:
                tipo = item.get("type")
                if tipo not in ("paragraph text", "line text"):
                    continue
                texto = item.get("value", "").strip()
                if not texto:
                    continue

                chave = (item.get("chapterNumber"), item.get("verseNumber"))
                if chave in vistos:
                    continue  # pula duplicata
                vistos.add(chave)

                db.add(Verse(
                    translation_id=translation_id,
                    book_id=book_id,
                    chapter=item.get("chapterNumber"),
                    verse=item.get("verseNumber"),
                    text=texto,
                ))
                inseridos += 1
                total += 1

            db.commit()
            print(f"OK - {livro.name} ({inseridos} versiculos)")

        print()
        print("=== Importacao WEB concluida ===")
        print(f"Total de versiculos: {total}")

    finally:
        db.close()


if __name__ == "__main__":
    importar_web(2, Path.home() / "biblia_viva" / "dados" / "web")
