"""
Bíblia Viva — Backend FastAPI
Versão 0.3.0 — Integração com banco de dados SQLite

Esta versão migra o backend de dicionários em memória para o banco
SQLite definido em database.py e models.py.
"""

from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from database import get_db, criar_tabelas
from models import Translation, Book, Verse, Passage, Favorite, Note


app = FastAPI(
    title="Bíblia Viva API",
    description="API do projeto Bíblia Viva — A Palavra que ganha vida",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    criar_tabelas()


def gerar_passage_id() -> str:
    return f"PASSAGE-{uuid.uuid4().hex[:8].upper()}"


def verse_existe(db: Session, translation_id: int, book_id: int, chapter: int, verse: int) -> bool:
    return db.query(Verse).filter(
        Verse.translation_id == translation_id,
        Verse.book_id == book_id,
        Verse.chapter == chapter,
        Verse.verse == verse,
    ).first() is not None


def validar_passagem(db: Session, dados: dict) -> Optional[str]:
    if not db.query(Translation).filter(Translation.id == dados["translation_id"]).first():
        return f"Tradução {dados['translation_id']} não encontrada."

    if not db.query(Book).filter(Book.id == dados["start_book_id"]).first():
        return f"Livro inicial {dados['start_book_id']} não encontrado."
    if not db.query(Book).filter(Book.id == dados["end_book_id"]).first():
        return f"Livro final {dados['end_book_id']} não encontrado."

    if not verse_existe(db, dados["translation_id"], dados["start_book_id"], dados["start_chapter"], dados["start_verse"]):
        return (
            f"Versículo inicial inválido: "
            f"livro {dados['start_book_id']}, "
            f"capítulo {dados['start_chapter']}, "
            f"versículo {dados['start_verse']}."
        )
    if not verse_existe(db, dados["translation_id"], dados["end_book_id"], dados["end_chapter"], dados["end_verse"]):
        return (
            f"Versículo final inválido: "
            f"livro {dados['end_book_id']}, "
            f"capítulo {dados['end_chapter']}, "
            f"versículo {dados['end_verse']}."
        )

    inicio = (dados["start_book_id"], dados["start_chapter"], dados["start_verse"])
    fim = (dados["end_book_id"], dados["end_chapter"], dados["end_verse"])
    if inicio > fim:
        return "Intervalo inválido: o versículo inicial não pode vir depois do versículo final."

    return None


@app.get("/", tags=["health"])
def raiz():
    return {
        "app": "Bíblia Viva",
        "slogan": "A Palavra que ganha vida",
        "versao": "0.3.0",
        "status": "online",
    }


@app.get("/api/v1/health", tags=["health"])
def health(db: Session = Depends(get_db)):
    return {
        "status": "ok",
        "traducoes": db.query(Translation).count(),
        "livros": db.query(Book).count(),
        "versiculos": db.query(Verse).count(),
        "passagens_criadas": db.query(Passage).count(),
    }


@app.get("/api/v1/translations", tags=["biblia"])
def listar_traducoes(db: Session = Depends(get_db)):
    """
    Lista todas as traduções cadastradas, com o total de versículos de cada uma.
    """
    traducoes = db.query(Translation).order_by(Translation.id).all()
    resultado = []
    for t in traducoes:
        n = db.query(Verse).filter(Verse.translation_id == t.id).count()
        resultado.append({
            "id": t.id,
            "code": t.code,
            "name": t.name,
            "language": t.language,
            "total_versiculos": n,
        })
    return resultado


@app.get("/api/v1/books", tags=["biblia"])
def listar_livros(db: Session = Depends(get_db)):
    livros = db.query(Book).order_by(Book.order_num).all()
    return [
        {
            "id": b.id,
            "name": b.name,
            "abbrev": b.abbrev,
            "testament": b.testament,
            "order_num": b.order_num,
            "chapters": b.chapters,
        }
        for b in livros
    ]


@app.get("/api/v1/books/{book_id}", tags=["biblia"])
def obter_livro(book_id: int, db: Session = Depends(get_db)):
    """
    Retorna os detalhes de um livro específico, incluindo:
    - Metadados (nome, abreviação, testamento, ordem, capítulos)
    - Total de versículos por tradução disponível
    """
    livro = db.query(Book).filter(Book.id == book_id).first()
    if not livro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Livro {book_id} não encontrado.",
        )

    # Conta versículos por tradução
    traducoes = db.query(Translation).order_by(Translation.id).all()
    contagem = []
    for t in traducoes:
        n = db.query(Verse).filter(
            Verse.book_id == book_id,
            Verse.translation_id == t.id,
        ).count()
        if n > 0:
            contagem.append({
                "translation_id": t.id,
                "translation_name": t.name,
                "total_versiculos": n,
            })

    return {
        "id": livro.id,
        "name": livro.name,
        "abbrev": livro.abbrev,
        "testament": livro.testament,
        "order_num": livro.order_num,
        "chapters": livro.chapters,
        "traducoes_disponiveis": contagem,
    }


@app.get("/api/v1/verses/{book_id}/{chapter}", tags=["biblia"])
def listar_versiculos(
    book_id: int,
    chapter: int,
    translation_id: int = 3,
    db: Session = Depends(get_db),
):
    """
    Retorna os versículos de um capítulo em uma tradução específica,
    com metadados do livro e da tradução.

    Parâmetro opcional:
      translation_id: 1 = Almeida 1911, 3 = Bíblia Livre (padrão)
    """
    # Busca a tradução
    traducao = db.query(Translation).filter(Translation.id == translation_id).first()
    if not traducao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tradução {translation_id} não encontrada.",
        )

    # Busca o livro
    livro = db.query(Book).filter(Book.id == book_id).first()
    if not livro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Livro {book_id} não encontrado.",
        )

    # Busca os versículos
    versiculos = db.query(Verse).filter(
        Verse.book_id == book_id,
        Verse.chapter == chapter,
        Verse.translation_id == translation_id,
    ).order_by(Verse.verse).all()

    if not versiculos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nenhum versículo encontrado para {livro.name} {chapter}, tradução {traducao.name}.",
        )

    return {
        "translation_id": traducao.id,
        "translation_name": traducao.name,
        "translation_code": traducao.code,
        "book_id": livro.id,
        "book_name": livro.name,
        "book_abbrev": livro.abbrev,
        "chapter": chapter,
        "total": len(versiculos),
        "versiculos": [{"verse": v.verse, "text": v.text} for v in versiculos],
    }


@app.post("/api/v1/passages", status_code=status.HTTP_201_CREATED, tags=["passages"])
def criar_passagem(dados: dict, db: Session = Depends(get_db)):
    campos = [
        "translation_id",
        "start_book_id", "start_chapter", "start_verse",
        "end_book_id",   "end_chapter",   "end_verse",
    ]
    faltando = [c for c in campos if c not in dados]
    if faltando:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Campos obrigatórios ausentes: {', '.join(faltando)}",
        )

    erro = validar_passagem(db, dados)
    if erro:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=erro,
        )

    passage_id = gerar_passage_id()

    passagem = Passage(
        passage_id=passage_id,
        translation_id=dados["translation_id"],
        start_book_id=dados["start_book_id"],
        start_chapter=dados["start_chapter"],
        start_verse=dados["start_verse"],
        end_book_id=dados["end_book_id"],
        end_chapter=dados["end_chapter"],
        end_verse=dados["end_verse"],
    )
    db.add(passagem)
    db.commit()
    db.refresh(passagem)

    return {
        "passage_id": passagem.passage_id,
        "translation_id": passagem.translation_id,
        "start_book_id": passagem.start_book_id,
        "start_chapter": passagem.start_chapter,
        "start_verse": passagem.start_verse,
        "end_book_id": passagem.end_book_id,
        "end_chapter": passagem.end_chapter,
        "end_verse": passagem.end_verse,
        "created_at": passagem.created_at.isoformat() if passagem.created_at else None,
    }


@app.get("/api/v1/passages/{passage_id}", tags=["passages"])
def obter_passagem(passage_id: str, db: Session = Depends(get_db)):
    p = db.query(Passage).filter(Passage.passage_id == passage_id).first()
    if not p:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Passagem {passage_id} não encontrada.",
        )
    return {
        "passage_id": p.passage_id,
        "translation_id": p.translation_id,
        "start_book_id": p.start_book_id,
        "start_chapter": p.start_chapter,
        "start_verse": p.start_verse,
        "end_book_id": p.end_book_id,
        "end_chapter": p.end_chapter,
        "end_verse": p.end_verse,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


@app.get("/api/v1/passages", tags=["passages"])
def listar_passagens(db: Session = Depends(get_db)):
    passagens = db.query(Passage).order_by(Passage.id).all()
    return [
        {
            "passage_id": p.passage_id,
            "translation_id": p.translation_id,
            "start_book_id": p.start_book_id,
            "start_chapter": p.start_chapter,
            "start_verse": p.start_verse,
            "end_book_id": p.end_book_id,
            "end_chapter": p.end_chapter,
            "end_verse": p.end_verse,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in passagens
    ]


@app.get("/api/v1/search", tags=["biblia"])
def buscar(
    q: str,
    translation_id: int = 3,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """
    Busca texto na Bíblia (case-insensitive).

    Parâmetros:
      q              — termo de busca (obrigatório)
      translation_id — tradução (padrão: 3 = Bíblia Livre)
      limit          — máximo de resultados (padrão: 20, máx: 100)

    Retorna até `limit` versículos cujo texto contenha o termo.
    """
    if not q or len(q.strip()) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Termo de busca precisa ter pelo menos 2 caracteres.",
        )

    # Limita o limit
    limit = max(1, min(limit, 100))

    # Busca case-insensitive
    termo = f"%{q.strip()}%"
    versiculos = db.query(Verse).filter(
        Verse.translation_id == translation_id,
        Verse.text.ilike(termo),
    ).order_by(Verse.book_id, Verse.chapter, Verse.verse).limit(limit).all()

    if not versiculos:
        return {
            "query": q,
            "translation_id": translation_id,
            "total": 0,
            "resultados": [],
        }

    # Enriquece com nome do livro
    livros_cache = {b.id: b for b in db.query(Book).all()}
    resultados = []
    for v in versiculos:
        livro = livros_cache.get(v.book_id)
        resultados.append({
            "book_id": v.book_id,
            "book_name": livro.name if livro else "?",
            "book_abbrev": livro.abbrev if livro else "?",
            "chapter": v.chapter,
            "verse": v.verse,
            "text": v.text,
        })

    return {
        "query": q,
        "translation_id": translation_id,
        "total": len(resultados),
        "resultados": resultados,
    }


@app.get("/api/v1/passages/{passage_id}/verses", tags=["passages"])
def listar_versiculos_da_passagem(passage_id: str, db: Session = Depends(get_db)):
    p = db.query(Passage).filter(Passage.passage_id == passage_id).first()
    if not p:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Passagem {passage_id} não encontrada.",
        )

    todos = db.query(Verse).filter(
        Verse.translation_id == p.translation_id,
    ).order_by(Verse.book_id, Verse.chapter, Verse.verse).all()

    inicio = (p.start_book_id, p.start_chapter, p.start_verse)
    fim = (p.end_book_id, p.end_chapter, p.end_verse)

    selecionados = [
        v for v in todos
        if inicio <= (v.book_id, v.chapter, v.verse) <= fim
    ]

    return {
        "passage_id": p.passage_id,
        "total": len(selecionados),
        "versiculos": [
            {"book_id": v.book_id, "chapter": v.chapter, "verse": v.verse, "text": v.text}
            for v in selecionados
        ],
    }



# ---------------------------------------------------------------------------
# Rotas — Favoritos
# ---------------------------------------------------------------------------

@app.post("/api/v1/favorites", status_code=status.HTTP_201_CREATED, tags=["favorites"])
def adicionar_favorito(dados: dict, db: Session = Depends(get_db)):
    """
    Marca uma passagem como favorita.

    Corpo esperado:
    {
      "passage_id": "PASSAGE-XXXXXXXX",
      "user_id": "default",   (opcional, padrão "default")
      "note": "..."           (opcional)
    }
    """
    passage_id = dados.get("passage_id")
    if not passage_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Campo 'passage_id' é obrigatório.",
        )

    # Verifica se a passagem existe
    passagem = db.query(Passage).filter(Passage.passage_id == passage_id).first()
    if not passagem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Passagem {passage_id} não encontrada.",
        )

    user_id = dados.get("user_id") or "default"

    # Verifica se já existe
    existente = db.query(Favorite).filter(
        Favorite.passage_id == passage_id,
        Favorite.user_id == user_id,
    ).first()
    if existente:
        return {
            "id": existente.id,
            "passage_id": existente.passage_id,
            "user_id": existente.user_id,
            "note": existente.note,
            "created_at": existente.created_at.isoformat() if existente.created_at else None,
            "mensagem": "Favorito já existia.",
        }

    favorito = Favorite(
        passage_id=passage_id,
        user_id=user_id,
        note=dados.get("note"),
    )
    db.add(favorito)
    db.commit()
    db.refresh(favorito)

    return {
        "id": favorito.id,
        "passage_id": favorito.passage_id,
        "user_id": favorito.user_id,
        "note": favorito.note,
        "created_at": favorito.created_at.isoformat() if favorito.created_at else None,
    }


@app.get("/api/v1/favorites", tags=["favorites"])
def listar_favoritos(user_id: str = "default", db: Session = Depends(get_db)):
    """Lista os favoritos de um usuário (padrão: 'default')."""
    favoritos = db.query(Favorite).filter(
        Favorite.user_id == user_id
    ).order_by(Favorite.id.desc()).all()

    resultado = []
    for f in favoritos:
        # Enriquece com dados da passagem
        p = db.query(Passage).filter(Passage.passage_id == f.passage_id).first()
        item = {
            "id": f.id,
            "passage_id": f.passage_id,
            "user_id": f.user_id,
            "note": f.note,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        if p:
            item["passage"] = {
                "translation_id": p.translation_id,
                "start_book_id": p.start_book_id,
                "start_chapter": p.start_chapter,
                "start_verse": p.start_verse,
                "end_book_id": p.end_book_id,
                "end_chapter": p.end_chapter,
                "end_verse": p.end_verse,
            }
        resultado.append(item)

    return resultado


@app.get("/api/v1/favorites/check/{passage_id}", tags=["favorites"])
def verificar_favorito(passage_id: str, user_id: str = "default", db: Session = Depends(get_db)):
    """Verifica se uma passagem está favoritada."""
    f = db.query(Favorite).filter(
        Favorite.passage_id == passage_id,
        Favorite.user_id == user_id,
    ).first()
    return {
        "passage_id": passage_id,
        "user_id": user_id,
        "favorito": f is not None,
    }


@app.delete("/api/v1/favorites/{passage_id}", tags=["favorites"])
def remover_favorito(passage_id: str, user_id: str = "default", db: Session = Depends(get_db)):
    """Remove um favorito."""
    f = db.query(Favorite).filter(
        Favorite.passage_id == passage_id,
        Favorite.user_id == user_id,
    ).first()
    if not f:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Favorito {passage_id} não encontrado para o usuário {user_id}.",
        )
    db.delete(f)
    db.commit()
    return {"mensagem": f"Favorito {passage_id} removido.", "passage_id": passage_id}



# ---------------------------------------------------------------------------
# Rotas — Anotações pessoais
# ---------------------------------------------------------------------------

@app.post("/api/v1/notes", status_code=status.HTTP_201_CREATED, tags=["notes"])
def criar_anotacao(dados: dict, db: Session = Depends(get_db)):
    """
    Cria uma anotação sobre uma passagem.

    Corpo esperado:
    {
      "passage_id": "PASSAGE-XXXXXXXX",
      "content": "texto da anotação",
      "user_id": "default"   (opcional)
    }
    """
    passage_id = dados.get("passage_id")
    content = dados.get("content")

    if not passage_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Campo 'passage_id' é obrigatório.",
        )
    if not content or not content.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Campo 'content' é obrigatório e não pode ser vazio.",
        )

    # Verifica se a passagem existe
    passagem = db.query(Passage).filter(Passage.passage_id == passage_id).first()
    if not passagem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Passagem {passage_id} não encontrada.",
        )

    anotacao = Note(
        passage_id=passage_id,
        user_id=dados.get("user_id") or "default",
        content=content.strip(),
    )
    db.add(anotacao)
    db.commit()
    db.refresh(anotacao)

    return {
        "id": anotacao.id,
        "passage_id": anotacao.passage_id,
        "user_id": anotacao.user_id,
        "content": anotacao.content,
        "created_at": anotacao.created_at.isoformat() if anotacao.created_at else None,
        "updated_at": anotacao.updated_at.isoformat() if anotacao.updated_at else None,
    }


@app.get("/api/v1/notes/{passage_id}", tags=["notes"])
def listar_anotacoes(passage_id: str, user_id: str = "default", db: Session = Depends(get_db)):
    """Lista todas as anotações de uma passagem."""
    anotacoes = db.query(Note).filter(
        Note.passage_id == passage_id,
        Note.user_id == user_id,
    ).order_by(Note.id.desc()).all()

    return [
        {
            "id": a.id,
            "passage_id": a.passage_id,
            "user_id": a.user_id,
            "content": a.content,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "updated_at": a.updated_at.isoformat() if a.updated_at else None,
        }
        for a in anotacoes
    ]


@app.put("/api/v1/notes/{note_id}", tags=["notes"])
def editar_anotacao(note_id: int, dados: dict, db: Session = Depends(get_db)):
    """Edita o conteúdo de uma anotação."""
    a = db.query(Note).filter(Note.id == note_id).first()
    if not a:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Anotação {note_id} não encontrada.",
        )

    novo = dados.get("content")
    if not novo or not novo.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Campo 'content' é obrigatório e não pode ser vazio.",
        )

    a.content = novo.strip()
    db.commit()
    db.refresh(a)

    return {
        "id": a.id,
        "passage_id": a.passage_id,
        "user_id": a.user_id,
        "content": a.content,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
    }


@app.delete("/api/v1/notes/{note_id}", tags=["notes"])
def remover_anotacao(note_id: int, db: Session = Depends(get_db)):
    """Remove uma anotação."""
    a = db.query(Note).filter(Note.id == note_id).first()
    if not a:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Anotação {note_id} não encontrada.",
        )
    db.delete(a)
    db.commit()
    return {"mensagem": f"Anotação {note_id} removida.", "id": note_id}
