import pdfplumber
import re

def parse_pdf_docentes(file_path):
    """
    Parses a PDF containing institutional directory of docentes.
    Returns (rows, errors) where rows is a list of dicts with keys:
    nombre, apellido, email, departamento.
    """
    rows = []
    errors = []
    email_regex = re.compile(r"[^@]+@[^@]+\.[^@]+")
    
    try:
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                tables = page.extract_tables()
                if not tables:
                    continue
                
                for table in tables:
                    for r_idx, r in enumerate(table):
                        # Clean cells
                        clean_row = [str(cell or "").strip() for cell in r]
                        if not any(clean_row):
                            continue
                            
                        if len(clean_row) < 4:
                            errors.append(f"Pág {page_num}, Fila {r_idx}: Menos de 4 columnas: {clean_row}")
                            continue
                            
                        # Detect headers
                        if "nombre" in clean_row[0].lower() or "email" in clean_row[2].lower():
                            continue
                            
                        nombre = clean_row[0]
                        apellido = clean_row[1]
                        email = clean_row[2]
                        departamento = clean_row[3]
                        
                        if not nombre or not email:
                            errors.append(f"Pág {page_num}, Fila {r_idx}: Nombre o email vacíos en: {clean_row}")
                            continue
                            
                        if not email_regex.match(email):
                            errors.append(f"Pág {page_num}, Fila {r_idx}: Email inválido '{email}' en: {clean_row}")
                            continue
                            
                        rows.append({
                            "nombre": nombre,
                            "apellido": apellido,
                            "email": email,
                            "departamento": departamento
                        })
    except Exception as e:
        errors.append(f"Error crítico al leer PDF: {str(e)}")
        
    return rows, errors
