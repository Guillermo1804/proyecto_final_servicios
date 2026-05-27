import pandas as pd
import io

def parse_alumnos_file(file_obj, filename):
    """
    Parsea un archivo CSV o XLSX de alumnos.
    Retorna (validas, errores).
    """
    try:
        # Leer archivo según extensión
        if filename.lower().endswith('.csv'):
            # El CSV de BUAP usa comas. 
            df = pd.read_csv(file_obj)
        elif filename.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_obj)
        else:
            return [], ["Formato de archivo no soportado. Use .csv o .xlsx"]
            
        # Normalización de nombres de columnas (case-insensitive y strip)
        df.columns = [c.lower().strip() for c in df.columns]

        # Mapeo flexible para el CSV de BUAP (paterno/materno -> apellido)
        if "apellido" not in df.columns:
            if "paterno" in df.columns:
                df["apellido"] = df["paterno"]
                if "materno" in df.columns:
                    df["apellido"] = df["apellido"] + " " + df["materno"]
            elif "apellido_paterno" in df.columns:
                df["apellido"] = df["apellido_paterno"]
                if "apellido_materno" in df.columns:
                    df["apellido"] = df["apellido"] + " " + df["apellido_materno"]

        # Columnas mínimas requeridas según MS3 spec
        required = ["matricula", "nombre", "apellido", "email"]
        missing = [col for col in required if col not in df.columns]
        if missing:
            return [], [f"Faltan columnas obligatorias: {', '.join(missing)}"]

        validas = []
        errores = []
        
        # Limitar a los primeros 1000 para el preview por rendimiento si es muy grande,
        # pero para el ejercicio procesaremos todo lo que venga en el objeto.
        for index, row in df.iterrows():
            try:
                # Convertir fila a dict y limpiar valores
                row_dict = {str(k): (str(v).strip() if pd.notnull(v) else "") for k, v in row.to_dict().items()}
                
                matricula = row_dict.get("matricula")
                if not matricula:
                    errores.append(f"Fila {index + 1}: Matrícula vacía")
                    continue
                
                nombre = row_dict.get("nombre")
                if not nombre:
                    errores.append(f"Fila {index + 1}: Nombre vacío")
                    continue

                # Preparar item para el preview JSON
                item = {
                    "matricula": matricula,
                    "nombre": nombre,
                    "apellido": row_dict.get("apellido", ""),
                    "email": row_dict.get("email", ""),
                    "carrera": row_dict.get("carrera", "ICC"),
                    "semestre": 1
                }
                
                # Intentar parsear semestre si existe
                semestre_val = row_dict.get("semestre")
                if semestre_val and semestre_val.isdigit():
                    item["semestre"] = int(semestre_val)
                
                validas.append(item)
            except Exception as e:
                errores.append(f"Fila {index + 1}: Error inesperado - {str(e)}")
                
        return validas, errores
    except Exception as e:
        return [], [f"Error crítico al leer el archivo: {str(e)}"]
