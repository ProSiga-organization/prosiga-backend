import io
from .. import model
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

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
    for m in sorted(matriculas, key=lambda x: x.turma.disciplina.semestre_ideal if (x.turma and x.turma.disciplina) else 99):
        
        if not m.turma or not m.turma.disciplina:
            continue 

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