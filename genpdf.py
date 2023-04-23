import os
from random import shuffle
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

def generate_pdfs(worksheet, title, mcqs, tfs, fibs):
    question_filename = os.path.join('static', worksheet.question_pdf)
    answer_filename = os.path.join('static', worksheet.answer_pdf)

    styles = getSampleStyleSheet()

    question_doc = SimpleDocTemplate(question_filename, pagesize=letter)
    answer_doc = SimpleDocTemplate(answer_filename, pagesize=letter)

    question_elements = []
    answer_elements = []

    # Add centered title to both question and answer PDFs
    question_elements.append(Paragraph(f'<para align=center>{title}</para>', styles["Heading1"]))
    answer_elements.append(Paragraph(f'<para align=center>{title}</para>', styles["Heading1"]))
    question_elements.append(Spacer(1, 12))
    answer_elements.append(Spacer(1, 12))

    # Add Name and Date fields
    name_and_date = '<para>Name: ________________________</para>'
    question_elements.append(Paragraph(name_and_date, styles["Normal"]))
    question_elements.append(Spacer(1, 12))

    if len(mcqs)>0:
        # Add MCQ heading
        mcq_heading = "Choose the correct one out of the following options for the questions given below."
        question_elements.append(Paragraph(mcq_heading, styles["Normal"]))
        question_elements.append(Spacer(1, 12))

        # Add "Answer Key" subheading to the answers PDF
        answer_elements.append(Paragraph("Answer Key", styles["Heading2"]))
        answer_elements.append(Spacer(1, 12))

        for index, mcq in enumerate(mcqs, start=1):
            # Add the question
            question_elements.append(Paragraph(f'{index}. {mcq["question"]}', styles["BodyText"]))

            # Create the answer options
            options = [mcq["correct_answer"]] + mcq["incorrect_answers"]
            shuffle(options)

            # Add the answer options to the question PDF in a vertical layout
            table_data = [[Paragraph(f'{chr(i)}. {opt}', styles["Normal"])] for i, opt in enumerate(options, start=97)]
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black)
            ]))
        
            question_elements.append(table)
            question_elements.append(Spacer(1, 12))

            # Add the answer to the answer PDF
            correct_answer_index = options.index(mcq["correct_answer"])
            answer_elements.append(Paragraph(f'{index}. {chr(97 + correct_answer_index)}', styles["BodyText"]))
            answer_elements.append(Spacer(1, 12))

    if len(tfs)>0:
        # Add True/False heading
        tf_heading = "True or False Questions"
        question_elements.append(Paragraph(tf_heading, styles["Heading2"]))
        question_elements.append(Spacer(1, 12))
        answer_elements.append(Paragraph(tf_heading, styles["Heading2"]))
        answer_elements.append(Spacer(1, 12))
        for index, tf in enumerate(tfs, start=1):
            # Add the question to the question PDF
            question_elements.append(Paragraph(f'{index}. {tf["question"]}', styles["BodyText"]))

            # Add the answer box to the question PDF
            table = Table([["T/F:_____"]])
            table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black)
            ]))
            table.hAlign = "LEFT"  # Add this line to left-align the table

            question_elements.append(table)
            question_elements.append(Spacer(1, 12))

            # Add the answer to the answer PDF
            answer_elements.append(Paragraph(f'{index}. {tf["correct_answer"]}', styles["BodyText"]))
            answer_elements.append(Spacer(1, 12))

    if len(fibs)>0:
        # Add Fill-in-the-blank heading
        fib_heading = "Answer the following in brief"
        question_elements.append(Paragraph(fib_heading, styles["Heading2"]))
        question_elements.append(Spacer(1, 12))
        answer_elements.append(Paragraph(fib_heading, styles["Heading2"]))
        answer_elements.append(Spacer(1, 12))
        for index, fib in enumerate(fibs, start=1):
            # Add the question to the question PDF
            question_elements.append(Paragraph(f'{index}. {fib["question"]}', styles["BodyText"]))

            # Add the answer line to the question PDF
            table = Table([["Answer: ____________________________"]])
            table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black)
            ]))
            table.hAlign = "LEFT"  # Add this line to left-align the table

            question_elements.append(table)
            question_elements.append(Spacer(1, 12))

            # Add the answer to the answer PDF
            answer_elements.append(Paragraph(f'{index}. {fib["correct_answer"]}', styles["BodyText"]))
            answer_elements.append(Spacer(1, 12))

    # Build the PDFs
    question_doc.build(question_elements)
    answer_doc.build(answer_elements)
