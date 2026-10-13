"""Bíblia Viva — Seed dos 66 livros"""

from database import SessionLocal, criar_tabelas
from models import Book

LIVROS = [
    (1, "Gênesis", "Gn", "AT", 50), (2, "Êxodo", "Ex", "AT", 40),
    (3, "Levítico", "Lv", "AT", 27), (4, "Números", "Nm", "AT", 36),
    (5, "Deuteronômio", "Dt", "AT", 34), (6, "Josué", "Js", "AT", 24),
    (7, "Juízes", "Jz", "AT", 21), (8, "Rute", "Rt", "AT", 4),
    (9, "1 Samuel", "1Sm", "AT", 31), (10, "2 Samuel", "2Sm", "AT", 24),
    (11, "1 Reis", "1Rs", "AT", 22), (12, "2 Reis", "2Rs", "AT", 25),
    (13, "1 Crônicas", "1Cr", "AT", 29), (14, "2 Crônicas", "2Cr", "AT", 36),
    (15, "Esdras", "Ed", "AT", 10), (16, "Neemias", "Ne", "AT", 13),
    (17, "Ester", "Et", "AT", 10), (18, "Jó", "Jó", "AT", 42),
    (19, "Salmos", "Sl", "AT", 150), (20, "Provérbios", "Pv", "AT", 31),
    (21, "Eclesiastes", "Ec", "AT", 12), (22, "Cantares", "Ct", "AT", 8),
    (23, "Isaías", "Is", "AT", 66), (24, "Jeremias", "Jr", "AT", 52),
    (25, "Lamentações", "Lm", "AT", 5), (26, "Ezequiel", "Ez", "AT", 48),
    (27, "Daniel", "Dn", "AT", 12), (28, "Oseias", "Os", "AT", 14),
    (29, "Joel", "Jl", "AT", 3), (30, "Amós", "Am", "AT", 9),
    (31, "Obadias", "Ob", "AT", 1), (32, "Jonas", "Jn", "AT", 4),
    (33, "Miqueias", "Mq", "AT", 7), (34, "Naum", "Na", "AT", 3),
    (35, "Habacuque", "Hc", "AT", 3), (36, "Sofonias", "Sf", "AT", 3),
    (37, "Ageu", "Ag", "AT", 2), (38, "Zacarias", "Zc", "AT", 14),
    (39, "Malaquias", "Ml", "AT", 4),
    (40, "Mateus", "Mt", "NT", 28), (41, "Marcos", "Mc", "NT", 16),
    (42, "Lucas", "Lc", "NT", 24), (43, "João", "Jo", "NT", 21),
    (44, "Atos", "At", "NT", 28), (45, "Romanos", "Rm", "NT", 16),
    (46, "1 Coríntios", "1Co", "NT", 16), (47, "2 Coríntios", "2Co", "NT", 13),
    (48, "Gálatas", "Gl", "NT", 6), (49, "Efésios", "Ef", "NT", 6),
    (50, "Filipenses", "Fp", "NT", 4), (51, "Colossenses", "Cl", "NT", 4),
    (52, "1 Tessalonicenses", "1Ts", "NT", 5), (53, "2 Tessalonicenses", "2Ts", "NT", 3),
    (54, "1 Timóteo", "1Tm", "NT", 6), (55, "2 Timóteo", "2Tm", "NT", 4),
    (56, "Tito", "Tt", "NT", 3), (57, "Filemom", "Fm", "NT", 1),
    (58, "Hebreus", "Hb", "NT", 13), (59, "Tiago", "Tg", "NT", 5),
    (60, "1 Pedro", "1Pe", "NT", 5), (61, "2 Pedro", "2Pe", "NT", 3),
    (62, "1 João", "1Jo", "NT", 5), (63, "2 João", "2Jo", "NT", 1),
    (64, "3 João", "3Jo", "NT", 1), (65, "Judas", "Jd", "NT", 1),
    (66, "Apocalipse", "Ap", "NT", 22),
]


def popular():
    criar_tabelas()
    db = SessionLocal()
    try:
        existentes = {b.id for b in db.query(Book).all()}
        inseridos = 0
        for ordem, nome, abbrev, test, caps in LIVROS:
            if ordem in existentes:
                continue
            db.add(Book(id=ordem, name=nome, abbrev=abbrev,
                        testament=test, order_num=ordem, chapters=caps))
            inseridos += 1
        db.commit()

        total = db.query(Book).count()
        at = db.query(Book).filter(Book.testament == "AT").count()
        nt = db.query(Book).filter(Book.testament == "NT").count()
        print(f"OK — {inseridos} livros inseridos")
        print(f"Total: {total}  (AT: {at}  NT: {nt})")
    finally:
        db.close()


if __name__ == "__main__":
    popular()
