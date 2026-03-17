from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
import os

import secrets

from dotenv import load_dotenv
load_dotenv()




DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()

@app.get("/")
def root():
    return {"mensagem": "Bem-vindo à sua API FastAPI dentro do Podman!"}

MEU_USUARIO = os.getenv("MEU_USUARIO")
MINHA_SENHA = os.getenv("MINHA_SENHA")

security = HTTPBasic()



class TarefaDB(Base):
    __tablename__ = "tarefas"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, unique=True, index=True, nullable=False)
    descricao = Column(String, index=True)
    concluida = Column(Boolean, default=False)

class Tarefa(BaseModel):
    nome: str
    descricao: str
    concluida: bool = False

Base.metadata.create_all(bind=engine)



def sessao_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def encontrar_tarefa(nome: str, db: Session):
    return db.query(TarefaDB).filter(TarefaDB.nome == nome).first()

def autenticar_meu_usuario(credentials: HTTPBasicCredentials = Depends(security)):
    is_username_correct = secrets.compare_digest(credentials.username, MEU_USUARIO)
    is_password_correct = secrets.compare_digest(credentials.password, MINHA_SENHA)

    if not (is_username_correct and is_password_correct):
        raise HTTPException(
            status_code=401,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Basic"}
        )

@app.get("/tarefas")
def listar_tarefas(
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(sessao_db),
    credentials: HTTPBasicCredentials = Depends(autenticar_meu_usuario)
):
    if page < 1 or limit < 1:
        raise HTTPException(status_code=400, detail="Valores de página ou limite inválidos!")

    tarefas = db.query(TarefaDB).offset((page - 1) * limit).limit(limit).all()
    
    total_tarefas = db.query(TarefaDB).count()

    return {
        "page": page,
        "limit": limit,
        "total": total_tarefas,
        "tarefas": [
            {
                "nome": tarefa.nome,
                "descricao": tarefa.descricao,
                "concluida": tarefa.concluida
            }
            for tarefa in tarefas
        ]
    }


@app.post("/tarefas")
def post_tarefa(
    tarefa: Tarefa,
    db: Session = Depends(sessao_db),
    credentials: HTTPBasicCredentials = Depends(autenticar_meu_usuario)
):
    db_tarefa = db.query(TarefaDB).filter(TarefaDB.nome == tarefa.nome).first()
    if db_tarefa:
        raise HTTPException(status_code=400, detail="Essa tarefa já existe no banco de dados!")

    nova_tarefa = TarefaDB(
        nome=tarefa.nome,
        descricao=tarefa.descricao,
        concluida=tarefa.concluida
    )
    db.add(nova_tarefa)
    db.commit()
    db.refresh(nova_tarefa)
    return {"message": "A tarefa foi criada com sucesso!"}
    
@app.put("/tarefas/{nome_tarefa}/concluir")
def concluir_tarefa(
    nome_tarefa: str,
    tarefa: Tarefa,
    db: Session = Depends(sessao_db),
    credentials: HTTPBasicCredentials = Depends(autenticar_meu_usuario)
):
    db_tarefa = db.query(TarefaDB).filter(TarefaDB.nome == nome_tarefa).first()
    if not db_tarefa:
        raise HTTPException(status_code=404, detail="Esta tarefa não foi encontrada no seu banco de dados!")

    db_tarefa.nome = tarefa.nome
    db_tarefa.descricao = tarefa.descricao
    db_tarefa.concluida = tarefa.concluida

    db.commit()
    db.refresh(db_tarefa)

    return {"message": "A tarefa foi atualizada com sucesso!"}

@app.delete("/tarefas/{nome_tarefa}")
def delete_tarefa(
    nome_tarefa: str,
    db: Session = Depends(sessao_db),
    credentials: HTTPBasicCredentials = Depends(autenticar_meu_usuario)
):
    db_tarefa = db.query(TarefaDB).filter(TarefaDB.nome == nome_tarefa).first()
    if not db_tarefa:
        raise HTTPException(status_code=404, detail="Esta tarefa não foi encontrada no seu banco de dados!")
    db.delete(db_tarefa)
    db.commit()
    return {"message": "Sua tarefa foi deletada com sucesso!"}