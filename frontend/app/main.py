from flask import Flask, render_template, request, send_file, abort, jsonify
import requests
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from io import BytesIO
import os

app = Flask(__name__)
BACKEND_URL = os.getenv('BACKEND_URL', 'http://backend:8000')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/facturas/<id_factura>', methods=['GET'])
def get_factura(id_factura):
    """Obtiene los datos de una factura desde el backend"""
    try:
        response = requests.get(f'{BACKEND_URL}/facturas/v1/{id_factura}')
        if response.status_code != 200:
            return jsonify({"error": "Factura no encontrada"}), 404
        return jsonify(response.json())
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Error de conexión con el servidor"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generar-pdf', methods=['POST'])
def generar_pdf():
    try:
        id_factura = request.form['id_factura']
        response = requests.get(f'{BACKEND_URL}/facturas/v1/{id_factura}')
        
        if response.status_code != 200:
            abort(404, description="Factura no encontrada")
            
        factura = response.json()
        
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=18*mm)
        elements = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=20, spaceAfter=10, textColor=colors.HexColor("#2c3e50"))
        subtitle_style = ParagraphStyle('SubtitleStyle', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor("#34495e"), spaceAfter=6)
        body_style = styles['Normal']

        # Título e información básica de la factura
        elements.append(Paragraph(f"FACTURA: {factura['numero_factura']}", title_style))
        elements.append(Paragraph(f"Fecha de emisión: {factura['fecha_emision']}", body_style))
        elements.append(Spacer(1, 10*mm))

        # Información de la empresa y el cliente
        info_data = [
            [Paragraph(f"<b>DE:</b><br/>{factura['empresa']['nombre']}<br/>{factura['empresa']['email']}<br/>{factura['empresa']['direccion']}", body_style),
             Paragraph(f"<b>PARA:</b><br/>{factura['cliente']['nombre']}<br/>{factura['cliente']['direccion']}<br/>{factura['cliente']['telefono']}", body_style)]
        ]
        info_table = Table(info_data, colWidths=[85*mm, 85*mm])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 8*mm))

        # Información detallada del cliente
        elements.append(Paragraph("Detalles del cliente", subtitle_style))
        client_info_data = [
            [Paragraph("<b>Nombre:</b>", body_style), Paragraph(factura['cliente']['nombre'], body_style)],
            [Paragraph("<b>Dirección:</b>", body_style), Paragraph(factura['cliente']['direccion'], body_style)],
            [Paragraph("<b>Teléfono:</b>", body_style), Paragraph(factura['cliente']['telefono'], body_style)]
        ]
        client_info_table = Table(client_info_data, colWidths=[35*mm, 135*mm])
        client_info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LINEBELOW', (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
        ]))
        elements.append(client_info_table)
        elements.append(Spacer(1, 15*mm))

        # Detalle de la factura: cantidad, descripción, precio unitario y total
        data = [["Cant.", "Descripción", "P. Unitario", "Subtotal"]] # Encabezado de tabla
        
        for item in factura['detalle']:
            data.append([
                item['cantidad'],
                Paragraph(item['descripcion'], body_style), # Paragraph permite que el texto haga wrap
                f"${item['precio_unitario']}",
                f"${item['total']}"
            ])

        # Estilo de la tabla de productos
        items_table = Table(data, colWidths=[20*mm, 90*mm, 30*mm, 30*mm])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#34495e")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'), # Descripción alineada a la izquierda
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 10*mm))

        totals_data = [
            ["", "Subtotal:", f"${factura['subtotal']}"],
            ["", "Impuestos (IVA):", f"${factura['impuesto']}"],
            ["", "TOTAL:", f"${factura['total']}"]
        ]
        
        totals_table = Table(totals_data, colWidths=[90*mm, 40*mm, 40*mm])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('FONTNAME', (1, 2), (2, 2), 'Helvetica-Bold'),
            ('TEXTCOLOR', (1, 2), (2, 2), colors.HexColor("#e74c3c")),
            ('SIZE', (1, 2), (2, 2), 12),
        ]))
        elements.append(totals_table)

        # Generar el doc y limpiar el buffer
        doc.build(elements)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=False,
            download_name=f"Factura_{id_factura}.pdf"
        )
        
    except requests.exceptions.ConnectionError:
        abort(503, description="Error de conexión con el servidor")
    except Exception as e:
        abort(500, description=str(e))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)

