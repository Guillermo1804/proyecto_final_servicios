import pdfplumber


def parsear_pdf_materias(archivo_pdf):
    """
    Parsea un PDF de programación académica de la BUAP.
    Retorna una tupla (lista_materias, contador_errores).
    """
    materias_parseadas = []
    errores_count = 0

    try:
        with pdfplumber.open(archivo_pdf) as pdf:
            for page in pdf.pages:
                tabla = page.extract_table()
                if not tabla:
                    continue
                
                for fila in tabla:
                    try:
                        # Asegurar tener suficientes columnas (necesitamos hasta la 6 para Profesor)
                        if len(fila) >= 7:
                            nrc = str(fila[0] or "").strip()
                            # Ignorar filas de encabezado o vacías
                            if not nrc or nrc.upper() == "NRC":
                                continue
                            
                            # Validar que NRC sea numérico o alfanumérico básico
                            if not nrc.isalnum():
                                errores_count += 1
                                continue
                            
                            clave = str(fila[1] or "").replace("\n", " ").strip()
                            nombre = str(fila[2] or "").replace("\n", " ").strip()
                            seccion = str(fila[3] or "").replace("\n", " ").strip()
                            dias = str(fila[4] or "").replace("\n", " ").strip()
                            hora = str(fila[5] or "").replace("\n", " ").strip()
                            docente = str(fila[6] or "").replace("\n", " ").strip()
                            
                            horario = f"{dias} {hora}".strip()
                            
                            materias_parseadas.append({
                                "nrc": nrc,
                                "clave": clave,
                                "nombre": nombre,
                                "seccion": seccion,
                                "docente_nombre": docente,
                                "horario": horario,
                            })
                        else:
                            # Fila muy corta, podría ser malformada si tiene datos
                            if any(fila):
                                errores_count += 1
                    except Exception:
                        errores_count += 1
    except Exception as e:
        raise ValueError(f"Error procesando PDF: {str(e)}")

    # Consolidar horarios para NRCs repetidos en diferentes filas (diferentes días)
    materias_combinadas = {}
    for mat in materias_parseadas:
        nrc = mat["nrc"]
        if nrc in materias_combinadas:
            horario_existente = materias_combinadas[nrc]["horario"]
            nuevo_horario = mat["horario"]
            if nuevo_horario and nuevo_horario not in horario_existente:
                materias_combinadas[nrc]["horario"] = f"{horario_existente} / {nuevo_horario}"
        else:
            materias_combinadas[nrc] = mat

    return list(materias_combinadas.values()), errores_count
