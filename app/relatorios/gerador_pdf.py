import io
from .. import model
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch, cm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph

MARGEM_ESQUERDA = 1.5 * cm
MARGEM_SUPERIOR = 2 * cm
LARGURA, ALTURA = A4 

def gerar_historico_pdf(aluno: model.Aluno, matriculas: list[model.Matricula]) -> io.BytesIO:
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
    y_atual -= 0.5 * cm
    c.drawString(MARGEM_ESQUERDA, y_atual, f"Matrícula: {aluno.matricula}")
    y_atual -= 0.5 * cm
    c.drawString(MARGEM_ESQUERDA, y_atual, f"CPF: {aluno.cpf[:3]}.***.{aluno.cpf[6:9]}-**")
    
    y_atual -= 1 * cm

    dados_tabela = []
    dados_tabela.append([
        "Cód. Disciplina", 
        "Disciplina", 
        "Cód. Turma", 
        "Status", 
        "Nota Final"
    ])
    
    total_aprovado = 0
    matriculas_ordenadas = sorted(
        [m for m in matriculas if m.turma and m.turma.disciplina],
        key=lambda m: m.turma.disciplina.semestre_ideal or 99
    )

    for m in matriculas_ordenadas:
        disciplina = m.turma.disciplina
        status = m.status.value if m.status else "N/A"
        nota = str(m.nota_final) if m.nota_final is not None else "--"
        
        if m.status == model.StatusAprovacaoEnum.APROVADO:
            total_aprovado += 1

        dados_tabela.append([
            disciplina.codigo,
            disciplina.nome,
            m.turma.codigo,
            status,
            nota
        ])

    if not dados_tabela:
        c.drawString(MARGEM_ESQUERDA, y_atual, "Nenhuma disciplina cursada.")
    else:
        tabela = Table(dados_tabela, colWidths=[
            3 * cm, 7 * cm, 3 * cm, 3 * cm, 2.5 * cm
        ])
        
        estilo = TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('FONTSIZE', (0,1), (-1,-1), 9),
        ])
        tabela.setStyle(estilo)
        tabela.wrapOn(c, LARGURA - (2 * MARGEM_ESQUERDA), y_atual)
        tabela.drawOn(c, MARGEM_ESQUERDA, y_atual - tabela._height)
        
        y_atual -= (tabela._height + 1 * cm)

    c.setFont("Helvetica-Bold", 10)
    c.drawString(MARGEM_ESQUERDA, y_atual, f"Total de Disciplinas Aprovadas: {total_aprovado}")
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


def gerar_diario_classe_pdf(turma: model.Turma, matriculas: list[model.Matricula]) -> io.BytesIO:
    """
    Gera o Diário de Classe (lista de alunos e notas) em PDF.
    """
    buffer = io.BytesIO()
    avaliacoes_colunas = sorted(turma.avaliacoes_definidas, key=lambda x: x.id)
    header = ["Matricula", "Aluno", "Status", "Nota Final"]
    header.extend([Paragraph(av.nome, getSampleStyleSheet()['BodyText']) for av in avaliacoes_colunas]) # Permite quebra de linha


    col_widths = [2.5 * cm, 6 * cm, 2.5 * cm, 2 * cm]
    if avaliacoes_colunas:
        largura_avaliacao = max(2*cm, (13.5 * cm) / len(avaliacoes_colunas))
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
    c.drawString(MARGEM_ESQUERDA, y_atual, f"Turma: {turma.codigo} - {turma.disciplina.nome}")
    y_atual -= 0.5 * cm
    c.drawString(MARGEM_ESQUERDA, y_atual, f"Professor(a): {turma.professor.nome}")

    y_atual -= 1 * cm # 
    dados_tabela = [header]
    for matricula in matriculas:
        if not matricula.aluno:
            continue
            
        notas_map = {
            nota.id_avaliacao_turma: nota.nota 
            for nota in matricula.notas_avaliacoes
        }
        
        row = [
            matricula.aluno.matricula,
            Paragraph(matricula.aluno.nome, getSampleStyleSheet()['BodyText']), # Permite quebra de linha
            matricula.status.value if matricula.status else "EM_CURSO",
            str(matricula.nota_final) if matricula.nota_final is not None else "--"
        ]
        
        for av in avaliacoes_colunas:
            nota = notas_map.get(av.id)
            row.append(str(nota) if nota is not None else "--")
            
        dados_tabela.append(row)

    tabela = Table(dados_tabela, colWidths=col_widths)
    estilo = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTSIZE', (0,1), (-1,-1), 8),
    ])
    tabela.setStyle(estilo)

    tabela.wrapOn(c, page_width - (2 * MARGEM_ESQUERDA), y_atual)
    tabela.drawOn(c, MARGEM_ESQUERDA, y_atual - tabela._height)
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer