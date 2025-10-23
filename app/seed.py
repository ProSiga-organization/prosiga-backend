from sqlalchemy.orm import sessionmaker
from app.database import engine, Base
from app.model import (
    Curso, Disciplina, Aluno, Professor, Coordenador, StatusContaEnum
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_data():
    # Cria todas as tabelas (se ainda não existirem)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # --- 1. Popular Cursos ---
        if db.query(Curso).count() == 0:
            print("Populando a tabela de Cursos...")
            cursos_para_adicionar = [
                Curso(codigo="CC", nome="Ciência da Computação"),
                Curso(codigo="ES", nome="Engenharia de Software"),
                Curso(codigo="EC", nome="Engenharia da Computação"),
                Curso(codigo="SI", nome="Sistemas de Informação"),
                Curso(codigo="DD", nome="Design Digital"),
            ]
            db.add_all(cursos_para_adicionar)
            db.commit()
            print("Cursos populados com sucesso!")
        else:
            print("Tabela de Cursos já populada.")

        # --- 2. Popular Disciplinas ---
        if db.query(Disciplina).count() == 0:
            print("Populando a tabela de Disciplinas...")
            disciplinas_para_adicionar = [
                Disciplina(codigo="COMP101", nome="Introdução à Programação", eh_obrigatoria=True, semestre_ideal=1, descricao="Conceitos básicos de programação..."),
                Disciplina(codigo="COMP102", nome="Estrutura de Dados I", eh_obrigatoria=True, semestre_ideal=2, descricao="Pilhas, filas, listas..."),
                Disciplina(codigo="COMP201", nome="Algoritmos Avançados", eh_obrigatoria=True, semestre_ideal=3, descricao="Grafos, algoritmos gulosos..."),
                Disciplina(codigo="COMP202", nome="Teoria da Computação", eh_obrigatoria=True, semestre_ideal=4, descricao="Autômatos finitos..."),
                Disciplina(codigo="SOFT101", nome="Engenharia de Requisitos", eh_obrigatoria=True, semestre_ideal=2, descricao="Técnicas de elicitação..."),
                Disciplina(codigo="SOFT201", nome="Qualidade de Software", eh_obrigatoria=True, semestre_ideal=3, descricao="Testes de software..."),
                Disciplina(codigo="SOFT301", nome="Arquitetura de Software", eh_obrigatoria=True, semestre_ideal=4, descricao="Padrões de arquitetura..."),
                Disciplina(codigo="MAT101", nome="Cálculo I", eh_obrigatoria=True, semestre_ideal=1, descricao="Limites, derivadas, integrais..."),
                Disciplina(codigo="MAT102", nome="Álgebra Linear", eh_obrigatoria=True, semestre_ideal=2, descricao="Vetores, matrizes..."),
                Disciplina(codigo="FIS101", nome="Física I", eh_obrigatoria=True, semestre_ideal=1, descricao="Mecânica clássica..."),
            ]
            db.add_all(disciplinas_para_adicionar)
            db.commit()
            print("Disciplinas populadas com sucesso!")
        else:
            print("Tabela de Disciplinas já populada.")

        # --- 3. Pré-cadastrar Usuários ---
        if db.query(Aluno).count() == 0:
            print("Pré-cadastrando usuários...")
            usuarios_para_adicionar = [
                # 3 Alunos
                Aluno(cpf="11122233301", nome="Bruno Alves", matricula="20250001", senha_hash="", status=StatusContaEnum.NOVO),
                Aluno(cpf="22233344402", nome="Carla Dias", matricula="20250002", senha_hash="", status=StatusContaEnum.NOVO),
                Aluno(cpf="33344455503", nome="Mariana Costa", matricula="20250003", senha_hash="", status=StatusContaEnum.NOVO),
                # 1 Professor
                Professor(cpf="44455566604", nome="Prof. Ricardo Borges", senha_hash="", status=StatusContaEnum.NOVO),
                # 1 Coordenador
                Coordenador(cpf="55566677705", nome="Coordenadora Helena", senha_hash="", status=StatusContaEnum.NOVO),
            ]
            db.add_all(usuarios_para_adicionar)
            db.commit()
            print("Usuários pré-cadastrados com sucesso!")
        else:
            print("Tabela de Usuários já populada.")

        print("\nProcesso de seeding concluído!")

    except Exception as e:
        print(f"Ocorreu um erro ao popular o banco: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()