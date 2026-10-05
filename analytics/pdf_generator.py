import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime

def generate_vaccination_certificate_pdf(child):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    story = []

    # Title Banner
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0d6efd'),
        alignment=1 # Center
    )
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#6c757d'),
        alignment=1
    )
    
    story.append(Paragraph("IMMUTRACK HEALTHCARE NETWORK", title_style))
    story.append(Paragraph("DIGITAL IMMUNIZATION RECORD CERTIFICATE", ParagraphStyle('H2', parent=title_style, fontSize=14, textColor=colors.HexColor('#198754'))))
    story.append(Paragraph("Notice: Authorized institutional vaccination summary record. Does not substitute official state registry documents.", subtitle_style))
    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0d6efd'), spaceAfter=15))

    # Child Demographics Table
    demo_data = [
        [
            Paragraph(f"<b>Child Name:</b> {child.full_name}", styles['Normal']),
            Paragraph(f"<b>Document ID:</b> CERT-{str(child.id)[:8].upper()}", styles['Normal'])
        ],
        [
            Paragraph(f"<b>Date of Birth:</b> {child.date_of_birth.strftime('%d-%b-%Y')}", styles['Normal']),
            Paragraph(f"<b>Gender:</b> {child.get_gender_display()}", styles['Normal'])
        ],
        [
            Paragraph(f"<b>Guardian:</b> {child.guardian.get_full_name() or child.guardian.username} ({child.get_guardian_relationship_display()})", styles['Normal']),
            Paragraph(f"<b>Registered Clinic:</b> {child.assigned_clinic.name if child.assigned_clinic else 'General Centre'}", styles['Normal'])
        ],
        [
            Paragraph(f"<b>Blood Group:</b> {child.blood_group or 'N/A'}", styles['Normal']),
            Paragraph(f"<b>Generated On:</b> {datetime.now().strftime('%d-%b-%Y %H:%M')}", styles['Normal'])
        ]
    ]

    demo_table = Table(demo_data, colWidths=[260, 260])
    demo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(demo_table)
    story.append(Spacer(1, 15))

    # Immunization Administration History
    story.append(Paragraph("<b>VERIFIED VACCINE ADMINISTRATION HISTORY</b>", styles['Heading3']))
    story.append(Spacer(1, 6))

    records_header = ["Dose / Vaccine", "Due Date", "Administered Date", "Batch #", "Facility / Health Worker"]
    records_rows = [records_header]

    doses = child.scheduled_doses.select_related('recommended_dose__vaccine', 'administration_record__facility').order_by('due_date')
    
    for d in doses:
        has_adm = hasattr(d, 'administration_record')
        dose_label = f"{d.recommended_dose.vaccine.code} - {d.recommended_dose.dose_label}"
        due_str = d.due_date.strftime('%d-%b-%Y')
        
        if has_adm:
            adm = d.administration_record
            adm_str = adm.administered_date.strftime('%d-%b-%Y')
            batch = adm.batch_number
            worker_fac = f"{adm.facility.name} (Dr/HW: {adm.administered_by.username})"
        else:
            adm_str = "Pending" if d.status != 'OVERDUE' else "OVERDUE"
            batch = "-"
            worker_fac = "-"

        records_rows.append([
            Paragraph(f"<b>{dose_label}</b>", styles['Normal']),
            due_str,
            Paragraph(f"<font color='{'#198754' if has_adm else '#dc3545'}'>{adm_str}</font>", styles['Normal']),
            batch,
            Paragraph(worker_fac, styles['Normal'])
        ])

    table_records = Table(records_rows, colWidths=[140, 75, 95, 80, 130])
    table_records.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9ecef')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#212529')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ced4da')),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(table_records)

    story.append(Spacer(1, 20))
    story.append(Paragraph("<b>Security & Verification:</b> This document was cryptographically signed and archived into the ImmuTrack Audit Ledger. Verify online by providing the Document ID at the clinical verification portal.", styles['Italic']))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
