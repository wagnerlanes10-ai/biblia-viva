"""
Bíblia Viva — Modelos do banco de dados (SQLAlchemy)

Cada classe aqui representa uma tabela no banco SQLite.
Estas tabelas guardam os dados de forma persistente.

Regra do projeto: a IA não é fonte da Bíblia.
O texto bíblico fica na tabela verses e vem de tradução autorizada.
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from database import Base


def agora_utc():
    """Retorna o momento atual em UTC (timezone-aware)."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Traduções
# ---------------------------------------------------------------------------

class Translation(Base):
    """Uma tradução da Bíblia (ex: Almeida 1911, World English Bible)."""
    __tablename__ = "translations"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    language = Column(String(10), nullable=False)
    created_at = Column(DateTime(timezone=True), default=agora_utc)


# ---------------------------------------------------------------------------
# Livros
# ---------------------------------------------------------------------------

class Book(Base):
    """Um dos 66 livros da Bíblia."""
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    abbrev = Column(String(10), nullable=False)
    testament = Column(String(5), nullable=False)  # "AT" ou "NT"
    order_num = Column(Integer, nullable=False)     # ordem canônica
    chapters = Column(Integer, nullable=False)


# ---------------------------------------------------------------------------
# Versículos
# ---------------------------------------------------------------------------

class Verse(Base):
    """
    Um versículo específico em uma tradução específica.
    Chave única: (translation_id, book_id, chapter, verse).
    """
    __tablename__ = "verses"

    id = Column(Integer, primary_key=True, index=True)
    translation_id = Column(Integer, ForeignKey("translations.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    chapter = Column(Integer, nullable=False)
    verse = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "translation_id", "book_id", "chapter", "verse",
            name="uq_verse_unique"
        ),
    )


# ---------------------------------------------------------------------------
# Passagens (o coração da experiência)
# ---------------------------------------------------------------------------

class Passage(Base):
    """
    Uma passagem bíblica: um versículo único ou um intervalo contínuo.

    A passagem é o núcleo reutilizável do Bíblia Viva.
    Ela alimenta leitura, áudio, estudo, favoritos e vídeo.
    """
    __tablename__ = "passages"

    id = Column(Integer, primary_key=True, index=True)
    passage_id = Column(String(50), unique=True, nullable=False, index=True)

    translation_id = Column(Integer, ForeignKey("translations.id"), nullable=False)

    start_book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    start_chapter = Column(Integer, nullable=False)
    start_verse = Column(Integer, nullable=False)

    end_book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    end_chapter = Column(Integer, nullable=False)
    end_verse = Column(Integer, nullable=False)

    created_at = Column(DateTime(timezone=True), default=agora_utc)


# ---------------------------------------------------------------------------
# Favoritos
# ---------------------------------------------------------------------------

class Favorite(Base):
    """
    Um favorito: uma passagem marcada pelo usuário.

    Por enquanto o user_id é opcional (MVP). Quando houver login,
    ele passa a referenciar a tabela de usuários.
    """
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    passage_id = Column(String(50), ForeignKey("passages.passage_id"), nullable=False, index=True)
    user_id = Column(String(100), nullable=True, index=True)  # futuro
    note = Column(Text, nullable=True)                        # futuro: anotação pessoal
    created_at = Column(DateTime(timezone=True), default=agora_utc)

    __table_args__ = (
        UniqueConstraint("passage_id", "user_id", name="uq_favorite_passage_user"),
    )


# ---------------------------------------------------------------------------
# Anotações pessoais
# ---------------------------------------------------------------------------

class Note(Base):
    """
    Uma anotação pessoal do usuário sobre uma passagem.

    Diferente de Favorite.note, aqui o usuário pode ter VÁRIAS
    anotações por passagem, e pode editá-las.
    """
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    passage_id = Column(String(50), ForeignKey("passages.passage_id"), nullable=False, index=True)
    user_id = Column(String(100), nullable=True, index=True)  # futuro: usuário real
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=agora_utc)
    updated_at = Column(DateTime(timezone=True), default=agora_utc, onupdate=agora_utc)
