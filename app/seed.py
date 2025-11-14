from sqlalchemy.orm import sessionmaker

from app.database import Base, engine
from app.model import Aluno, Coordenador, Curso, Disciplina, Professor, StatusContaEnum

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def seed_data():
    # Cria todas as tabelas (se ainda não existirem)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        if db.query(Curso).count() == 0:
            print("Populando a tabela de Cursos...")
            cursos_para_adicionar = [
                Curso(codigo="CC", nome="Ciência da Computação"),  # ID 1
                Curso(codigo="ES", nome="Engenharia de Software"),  # ID 2
                Curso(codigo="EC", nome="Engenharia da Computação"),  # ID 3
                Curso(codigo="SI", nome="Sistemas de Informação"),  # ID 4
                Curso(codigo="DD", nome="Design Digital"),  # ID 5
            ]
            db.add_all(cursos_para_adicionar)
            db.commit()
            print("Cursos populados com sucesso!")
        else:
            print("Tabela de Cursos já populada.")

        if db.query(Disciplina).count() == 0:
            print("Populando a tabela de Disciplinas...")
            disciplinas_para_adicionar = [
                Disciplina(
                    codigo="COMP101",
                    nome="Introdução à Programação",
                    semestre_ideal=1,
                    descricao="Conceitos básicos de programação...",
                ),
                Disciplina(
                    codigo="COMP102",
                    nome="Estrutura de Dados I",
                    semestre_ideal=2,
                    descricao="Pilhas, filas, listas...",
                ),
                Disciplina(
                    codigo="SOFT101",
                    nome="Engenharia de Requisitos",
                    semestre_ideal=2,
                    descricao="Técnicas de elicitação...",
                ),
                Disciplina(
                    codigo="MAT101",
                    nome="Cálculo I",
                    semestre_ideal=1,
                    descricao="Limites, derivadas, integrais...",
                ),
                Disciplina(
                    codigo="COMP201",
                    nome="Algoritmos Avançados",
                    semestre_ideal=3,
                    descricao="Grafos, algoritmos gulosos...",
                ),
                Disciplina(
                    codigo="COMP202",
                    nome="Teoria da Computação",
                    semestre_ideal=4,
                    descricao="Autômatos finitos...",
                ),
                Disciplina(
                    codigo="SOFT201",
                    nome="Qualidade de Software",
                    semestre_ideal=3,
                    descricao="Testes de software...",
                ),
                Disciplina(
                    codigo="SOFT301",
                    nome="Arquitetura de Software",
                    semestre_ideal=4,
                    descricao="Padrões de arquitetura...",
                ),
                Disciplina(
                    codigo="MAT102",
                    nome="Álgebra Linear",
                    semestre_ideal=2,
                    descricao="Vetores, matrizes...",
                ),
                Disciplina(
                    codigo="FIS101",
                    nome="Física I",
                    semestre_ideal=1,
                    descricao="Mecânica clássica...",
                ),
                Disciplina(
                    codigo="HUM101",
                    nome="Comunicação e Expressão",
                    semestre_ideal=1,
                    descricao="...",
                ),
                Disciplina(
                    codigo="ADM101",
                    nome="Gestão de Projetos",
                    semestre_ideal=5,
                    descricao="...",
                ),
                Disciplina(
                    codigo="REDES101",
                    nome="Redes de Computadores",
                    semestre_ideal=3,
                    descricao="...",
                ),
                Disciplina(
                    codigo="SO101",
                    nome="Sistemas Operacionais",
                    semestre_ideal=3,
                    descricao="...",
                ),
                Disciplina(
                    codigo="BD101",
                    nome="Banco de Dados I",
                    semestre_ideal=4,
                    descricao="...",
                ),
                Disciplina(
                    codigo="IA101",
                    nome="Inteligência Artificial",
                    semestre_ideal=5,
                    descricao="...",
                ),
                Disciplina(
                    codigo="SEG101",
                    nome="Segurança da Informação",
                    semestre_ideal=6,
                    descricao="...",
                ),
                Disciplina(
                    codigo="WEB101",
                    nome="Desenvolvimento Web",
                    semestre_ideal=4,
                    descricao="...",
                ),
                Disciplina(
                    codigo="MOB101",
                    nome="Desenvolvimento Mobile",
                    semestre_ideal=6,
                    descricao="...",
                ),
                Disciplina(
                    codigo="UX101",
                    nome="Design de Experiência do Usuário",
                    semestre_ideal=5,
                    descricao="...",
                ),
            ]
            db.add_all(disciplinas_para_adicionar)
            db.commit()
            print("Disciplinas populadas com sucesso!")
        else:
            print("Tabela de Disciplinas já populada.")

        if db.query(Aluno).count() == 0:
            print("Pré-cadastrando usuários...")
            curso_cc = db.query(Curso).filter(Curso.codigo == "CC").first()
            curso_es = db.query(Curso).filter(Curso.codigo == "ES").first()
            id_curso_cc = curso_cc.id if curso_cc else None
            id_curso_es = curso_es.id if curso_es else None

            if not id_curso_cc or not id_curso_es:
                print(
                    "AVISO: Cursos CC ou ES não encontrados no seed. id_curso será None para alunos."
                )

            usuarios_para_adicionar = [
                Aluno(
                    cpf="11122233301",
                    nome="Bruno Alves",
                    matricula="20250001",
                    senha_hash="",
                    status=StatusContaEnum.NOVO,
                    id_curso=id_curso_cc,
                ),
                Aluno(
                    cpf="22233344402",
                    nome="Carla Dias",
                    matricula="20250002",
                    senha_hash="",
                    status=StatusContaEnum.NOVO,
                    id_curso=id_curso_es,
                ),
                Aluno(
                    cpf="33344455503",
                    nome="Mariana Costa",
                    matricula="20250003",
                    senha_hash="",
                    status=StatusContaEnum.NOVO,
                    id_curso=id_curso_cc,
                ),
                Professor(
                    cpf="44455566604",
                    nome="Prof. Ricardo Borges",
                    senha_hash="",
                    status=StatusContaEnum.NOVO,
                ),
                Coordenador(
                    cpf="55566677705",
                    nome="Coordenadora Helena",
                    senha_hash="",
                    status=StatusContaEnum.NOVO,
                ),
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
