import io
from .. import model
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch, cm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from sqlalchemy.orm import Session
from ..matricula.repository import MatriculaRepository

MARGEM_ESQUERDA = 1.5 * cm
MARGEM_SUPERIOR = 2 * cm
LARGURA, ALTURA = A4


def gerar_historico_pdf(
    aluno: model.Aluno,
    matriculas: list[model.Matricula],
    semestre_atual: int,
    ira: float | None,
) -> io.BytesIO:
    """
    Gera o histórico acadêmico de um aluno em PDF.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setTitle(f"Histórico - {aluno.nome}")

    y_atual = ALTURA - MARGEM_SUPERIOR
    c.setFont("Helvetica-Bold", 16)
    c.drawString(MARGEM_ESQUERDA, y_atual, "Histórico Acadêmico")
    y_atual -= 0.5 * cm
    c.setStrokeColorRGB(0, 0, 0)
    c.line(MARGEM_ESQUERDA, y_atual, LARGURA - MARGEM_ESQUERDA, y_atual)

    y_atual -= 1 * cm
    c.setFont("Helvetica", 12)
    c.drawString(MARGEM_ESQUERDA, y_atual, f"Nome: {aluno.nome}")
    c.drawRightString(
        LARGURA - MARGEM_ESQUERDA,
        y_atual,
        f"Semestre Atual (Estimado): {semestre_atual}",
    )
    y_atual -= 0.5 * cm
    c.drawString(MARGEM_ESQUERDA, y_atual, f"Matrícula: {aluno.matricula}")
    ira_str = f"{ira:.2f}" if ira is not None else "N/A"
    c.drawRightString(LARGURA - MARGEM_ESQUERDA, y_atual, f"IRA (0-5): {ira_str}")
    y_atual -= 0.5 * cm
    c.drawString(
        MARGEM_ESQUERDA, y_atual, f"CPF: {aluno.cpf[:3]}.***.{aluno.cpf[6:9]}-**"
    )
    y_atual -= 1 * cm

    dados_tabela = []
    dados_tabela.append(
        ["Cód. Disciplina", "Disciplina", "Cód. Turma", "Status", "Nota Final"]
    )
    total_aprovado = 0
    matriculas_ordenadas = sorted(
        [m for m in matriculas if m.turma and m.turma.disciplina],
        key=lambda m: m.turma.disciplina.semestre_ideal or 99,
    )
    for m in matriculas_ordenadas:
        disciplina = m.turma.disciplina
        status = m.status.value if m.status else "N/A"
        nota = str(m.nota_final) if m.nota_final is not None else "--"
        if m.status == model.StatusAprovacaoEnum.APROVADO:
            total_aprovado += 1
        dados_tabela.append(
            [disciplina.codigo, disciplina.nome, m.turma.codigo, status, nota]
        )
    if len(dados_tabela) <= 1:
        c.drawString(MARGEM_ESQUERDA, y_atual, "Nenhuma disciplina cursada.")
    else:
        tabela = Table(
            dados_tabela, colWidths=[3 * cm, 7 * cm, 3 * cm, 3 * cm, 2.5 * cm]
        )
        estilo = TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
            ]
        )
        tabela.setStyle(estilo)
        tabela.wrapOn(c, LARGURA - (2 * MARGEM_ESQUERDA), y_atual)
        tabela.drawOn(c, MARGEM_ESQUERDA, y_atual - tabela._height)
        y_atual -= tabela._height + 1 * cm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(
        MARGEM_ESQUERDA, y_atual, f"Total de Disciplinas Aprovadas: {total_aprovado}"
    )
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


def gerar_diario_classe_pdf(
    turma: model.Turma, matriculas: list[model.Matricula]
) -> io.BytesIO:
    """
    Gera o Diário de Classe (lista de alunos e notas) em PDF.
    """
    buffer = io.BytesIO()
    avaliacoes_colunas = sorted(turma.avaliacoes_definidas, key=lambda x: x.id)
    header = ["Matricula", "Aluno", "Status", "Nota Final"]
    header.extend(
        [
            Paragraph(av.nome, getSampleStyleSheet()["BodyText"])
            for av in avaliacoes_colunas
        ]
    )

    col_widths = [2.5 * cm, 6 * cm, 2.5 * cm, 2 * cm]
    if avaliacoes_colunas:
        largura_avaliacao = max(2 * cm, (13.5 * cm) / len(avaliacoes_colunas))
        col_widths.extend([largura_avaliacao] * len(avaliacoes_colunas))
    largura_tabela = sum(col_widths)
    if largura_tabela > 18 * cm:
        page_size = landscape(A4)
        page_width, page_height = page_size
    else:
        page_size = A4
        page_width, page_height = page_size

    c = canvas.Canvas(buffer, pagesize=page_size)

    y_atual = page_height - MARGEM_SUPERIOR
    c.setFont("Helvetica-Bold", 16)
    c.drawString(MARGEM_ESQUERDA, y_atual, "Diário de Classe")

    y_atual -= 0.7 * cm
    c.setFont("Helvetica", 12)
    c.drawString(
        MARGEM_ESQUERDA, y_atual, f"Turma: {turma.codigo} - {turma.disciplina.nome}"
    )
    y_atual -= 0.5 * cm
    c.drawString(MARGEM_ESQUERDA, y_atual, f"Professor(a): {turma.professor.nome}")

    y_atual -= 1 * cm  #
    dados_tabela = [header]
    for matricula in matriculas:
        if not matricula.aluno:
            continue

        notas_map = {
            nota.id_avaliacao_turma: nota.nota for nota in matricula.notas_avaliacoes
        }

        row = [
            matricula.aluno.matricula,
            Paragraph(matricula.aluno.nome, getSampleStyleSheet()["BodyText"]),
            matricula.status.value if matricula.status else "EM_CURSO",
            str(matricula.nota_final) if matricula.nota_final is not None else "--",
        ]

        for av in avaliacoes_colunas:
            nota = notas_map.get(av.id)
            row.append(str(nota) if nota is not None else "--")

        dados_tabela.append(row)

    tabela = Table(dados_tabela, colWidths=col_widths)
    estilo = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
        ]
    )
    tabela.setStyle(estilo)

    tabela.wrapOn(c, page_width - (2 * MARGEM_ESQUERDA), y_atual)
    tabela.drawOn(c, MARGEM_ESQUERDA, y_atual - tabela._height)
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


def gerar_relatorio_ocupacao_pdf(
    periodo: model.PeriodoLetivo, turmas: list[model.Turma]
) -> io.BytesIO:
    """
    Gera o Relatório de Ocupação de Vagas em PDF para um período letivo.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setTitle(f"Relatório de Ocupação - {periodo.ano}.{periodo.semestre}")
    y_atual = ALTURA - MARGEM_SUPERIOR
    c.setFont("Helvetica-Bold", 16)
    c.drawString(MARGEM_ESQUERDA, y_atual, "Relatório de Ocupação de Vagas")

    y_atual -= 0.7 * cm
    c.setFont("Helvetica", 12)
    c.drawString(
        MARGEM_ESQUERDA, y_atual, f"Período Letivo: {periodo.ano}.{periodo.semestre}"
    )

    y_atual -= 1 * cm

    dados_tabela = []

    dados_tabela.append(
        [
            "Cód. Turma",
            "Disciplina",
            "Professor(a)",
            "Vagas Ofertadas",
            "Vagas Ocupadas",
            "% Ocupação",
        ]
    )

    total_vagas = 0
    total_ocupadas = 0

    turmas_ordenadas = sorted(
        [t for t in turmas if t.disciplina and t.professor],
        key=lambda t: t.disciplina.nome,
    )

    for turma in turmas_ordenadas:
        vagas_ofertadas = turma.vagas
        vagas_ocupadas = len(turma.matriculas)

        if vagas_ofertadas > 0:
            ocupacao = (vagas_ocupadas / vagas_ofertadas) * 100
            ocupacao_str = f"{ocupacao:.1f}%"
        else:
            ocupacao_str = "N/A"

        total_vagas += vagas_ofertadas
        total_ocupadas += vagas_ocupadas

        dados_tabela.append(
            [
                turma.codigo,
                Paragraph(turma.disciplina.nome, getSampleStyleSheet()["BodyText"]),
                Paragraph(turma.professor.nome, getSampleStyleSheet()["BodyText"]),
                str(vagas_ofertadas),
                str(vagas_ocupadas),
                ocupacao_str,
            ]
        )

    if total_vagas > 0:
        ocupacao_total = (total_ocupadas / total_vagas) * 100
        ocupacao_total_str = f"{ocupacao_total:.1f}%"
    else:
        ocupacao_total_str = "N/A"

    dados_tabela.append(
        ["TOTAL", "", "", str(total_vagas), str(total_ocupadas), ocupacao_total_str]
    )

    tabela = Table(
        dados_tabela,
        colWidths=[2.5 * cm, 6 * cm, 4.5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm],
    )

    estilo = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.darkgreen),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("GRID", (0, -1), (-1, -1), 1, colors.black),
        ]
    )
    tabela.setStyle(estilo)

    tabela.wrapOn(c, LARGURA - (2 * MARGEM_ESQUERDA), y_atual)
    tabela.drawOn(c, MARGEM_ESQUERDA, y_atual - tabela._height)

    y_atual -= tabela._height + 1 * cm

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


def gerar_relatorio_turmas_professor_pdf(
    periodo: model.PeriodoLetivo, professores: list[model.Professor]
) -> io.BytesIO:
    """
    Gera o Relatório de Distribuição de Turmas por Professor em PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGEM_ESQUERDA,
        rightMargin=MARGEM_ESQUERDA,
        topMargin=MARGEM_SUPERIOR,
        bottomMargin=MARGEM_SUPERIOR,
    )

    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Relatório de Turmas por Professor", styles["h1"]))
    story.append(
        Paragraph(f"Período Letivo: {periodo.ano}.{periodo.semestre}", styles["h2"])
    )
    story.append(Spacer(1, 0.5 * cm))

    dados_tabela = []
    dados_tabela.append(["Professor(a)", "Cód. Turma", "Disciplina", "Alunos Mat."])

    total_turmas = 0

    for prof in sorted(professores, key=lambda p: p.nome):
        turmas_do_periodo = [
            t for t in prof.turmas if t.id_periodo_letivo == periodo.id and t.disciplina
        ]

        if not turmas_do_periodo:
            continue
        turmas_do_periodo.sort(key=lambda t: t.codigo)

        primeira_linha = [
            Paragraph(prof.nome, styles["BodyText"]),
            turmas_do_periodo[0].codigo,
            Paragraph(turmas_do_periodo[0].disciplina.nome, styles["BodyText"]),
            len(turmas_do_periodo[0].matriculas),
        ]
        dados_tabela.append(primeira_linha)
        total_turmas += 1
        for turma in turmas_do_periodo[1:]:
            dados_tabela.append(
                [
                    "",  # Célula vazia (será mesclada)
                    turma.codigo,
                    Paragraph(turma.disciplina.nome, styles["BodyText"]),
                    len(turma.matriculas),
                ]
            )
            total_turmas += 1

    if len(dados_tabela) <= 1:
        story.append(
            Paragraph(
                "Nenhuma turma alocada para professores neste período.",
                styles["BodyText"],
            )
        )
    else:

        tabela = Table(dados_tabela, colWidths=[5 * cm, 3 * cm, 7 * cm, 2.5 * cm])

        estilo = TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkred),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
            ]
        )

        linha_inicio = 1
        for prof in sorted(professores, key=lambda p: p.nome):
            turmas_do_periodo = [
                t for t in prof.turmas if t.id_periodo_letivo == periodo.id
            ]
            if turmas_do_periodo:
                num_turmas = len(turmas_do_periodo)
                if num_turmas > 1:
                    estilo.add(
                        "SPAN", (0, linha_inicio), (0, linha_inicio + num_turmas - 1)
                    )
                linha_inicio += num_turmas

        tabela.setStyle(estilo)
        story.append(tabela)

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(f"Total de Turmas Alocadas: {total_turmas}", styles["h3"]))
    doc.build(story)

    buffer.seek(0)
    return buffer


def gerar_relatorio_alunos_curso_pdf(
    db: Session, cursos: list[model.Curso]
) -> io.BytesIO:
    """
    Gera o Relatório de Lista de Alunos por Curso em PDF.
    Espera que a lista de cursos já venha com os alunos pré-carregados.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=MARGEM_ESQUERDA,
        rightMargin=MARGEM_ESQUERDA,
        topMargin=MARGEM_SUPERIOR,
        bottomMargin=MARGEM_SUPERIOR,
    )

    styles = getSampleStyleSheet()
    story = []
    repo_matricula = MatriculaRepository()

    story.append(Paragraph("Relatório de Alunos por Curso", styles["h1"]))
    story.append(Spacer(1, 0.5 * cm))

    total_geral_alunos = 0

    for curso in sorted(cursos, key=lambda c: c.nome):
        story.append(Paragraph(f"Curso: {curso.nome} ({curso.codigo})", styles["h2"]))
        story.append(Spacer(1, 0.2 * cm))

        dados_tabela = []
        dados_tabela.append(
            ["Matrícula", "Nome do Aluno", "CPF", "Status da Conta", "Semestre Atual"]
        )

        alunos_do_curso = sorted(curso.alunos, key=lambda a: a.nome)

        if not alunos_do_curso:
            story.append(
                Paragraph("Nenhum aluno matriculado neste curso.", styles["BodyText"])
            )
            story.append(Spacer(1, 0.5 * cm))
            continue

        total_geral_alunos += len(alunos_do_curso)

        for aluno in alunos_do_curso:
            semestre_atual = repo_matricula.get_periodos_cursados_por_aluno(
                db, id_aluno=aluno.id
            )
            dados_tabela.append(
                [
                    aluno.matricula,
                    Paragraph(aluno.nome, styles["BodyText"]),
                    f"{aluno.cpf[:3]}.***.{aluno.cpf[6:9]}-**",
                    aluno.status.value,
                    str(semestre_atual),
                ]
            )

        tabela = Table(
            dados_tabela, colWidths=[3 * cm, 7 * cm, 3.5 * cm, 2.5 * cm, 2.5 * cm]
        )

        estilo = TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.cadetblue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
            ]
        )
        tabela.setStyle(estilo)
        story.append(tabela)
        story.append(Spacer(1, 0.5 * cm))

    story.append(Spacer(1, 1 * cm))
    story.append(
        Paragraph(f"Total Geral de Alunos Listados: {total_geral_alunos}", styles["h3"])
    )

    doc.build(story)

    buffer.seek(0)
    return buffer
