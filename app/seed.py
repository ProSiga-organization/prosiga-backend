# app/seed.py

import csv
from sqlalchemy.orm import sessionmaker
from app.database import engine, Base
from app.model import Aluno, Professor, Coordenador, StatusContaEnum

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Abre o ficheiro CSV que está na pasta /app dentro do contentor
        with open('/app/usuarios.csv', mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            print("Lendo ficheiro CSV e pré-cadastrando novos usuários...")

            for row in reader:
                cpf = row['cpf']
                
                usuario_existente = db.query(Aluno).filter(Aluno.cpf == cpf).first()
                if usuario_existente:
                    print(f"Usuário com CPF {cpf} já existe. A ignorar.")
                    continue
                
                tipo_usuario = row['tipo_usuario']
                if tipo_usuario == 'aluno':
                    novo_usuario = Aluno(
                        cpf=cpf,
                        nome=row['nome'],
                        matricula=row['matricula'],
                        senha_hash="", # A senha continua vazia
                        status=StatusContaEnum.NOVO
                    )
                elif tipo_usuario == 'professor':
                    novo_usuario = Professor(
                        cpf=cpf,
                        nome=row['nome'],
                        senha_hash="",
                        status=StatusContaEnum.NOVO
                    )
                elif tipo_usuario == 'coordenador':
                    novo_usuario = Coordenador(
                        cpf=cpf,
                        nome=row['nome'],
                        senha_hash="",
                        status=StatusContaEnum.NOVO
                    )
                else:
                    continue
                
                db.add(novo_usuario)
                print(f"Usuário pré-cadastrado: {row['nome']} ({tipo_usuario})")

            db.commit()
            print("\nProcesso de seeding a partir do CSV concluído!")

    except FileNotFoundError:
        print("\nAVISO: Ficheiro 'novos_usuarios.csv' não encontrado.")
    except Exception as e:
        print(f"Ocorreu um erro ao popular o banco: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()