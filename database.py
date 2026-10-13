"""
Bíblia Viva — Conexão com o banco de dados SQLite

Este arquivo cria a conexão com o banco de dados SQLite, que é
um banco em arquivo único. Perfeito para rodar no Termux (Android),
sem precisar de servidor de banco de dados.

O arquivo do banco fica em: biblia_viva.db (na mesma pasta deste arquivo)
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path

# Caminho do arquivo do banco (na mesma pasta deste arquivo)
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "biblia_viva.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Engine: conexão com SQLite
# check_same_thread=False é necessário porque o FastAPI pode
# usar threads diferentes para atender requisições.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,  # mude para True se quiser ver o SQL executado
)

# SessionLocal: fábrica de sessões do banco
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base: classe mãe de todos os modelos (tabelas)
Base = declarative_base()


def get_db():
    """
    Dependência do FastAPI: fornece uma sessão do banco para cada requisição,
    e garante que ela seja fechada ao final.

    Uso nas rotas:
        def minha_rota(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def criar_tabelas():
    """
    Cria todas as tabelas no banco, com base nos modelos registrados.
    Deve ser chamada uma vez, na inicialização do app.
    """
    Base.metadata.create_all(bind=engine)
