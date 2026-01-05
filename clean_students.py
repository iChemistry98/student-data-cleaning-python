import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

RAW_FILE = os.path.join(DATA_DIR, "students_raw.csv")  # si no renombras, cambia aquí
CLEAN_FILE = os.path.join(DATA_DIR, "students_clean.csv")
SUMMARY_FILE = os.path.join(BASE_DIR, "summary.txt")


def normalize_colname(col: str) -> str:
    """
    Normaliza nombres de columnas:
    - minúsculas
    - espacios -> _
    - elimina saltos y dobles espacios
    """
    col = col.strip().lower().replace("\n", " ")
    col = "_".join(col.split())  # colapsa espacios
    return col


def main():
    if not os.path.exists(RAW_FILE):
        raise FileNotFoundError(f"No se encontró el archivo: {RAW_FILE}")

    # Intenta leer con utf-8; si falla, prueba latin-1 (común en CSV de Windows/Excel)
    try:
        df = pd.read_csv(RAW_FILE, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(RAW_FILE, encoding="latin-1")

    original_rows, original_cols = df.shape

    # 1) Normalizar columnas
    df.columns = [normalize_colname(c) for c in df.columns]

    # 2) Quitar filas completamente vacías
    df = df.dropna(how="all")

    # 3) Quitar duplicados
    df = df.drop_duplicates()

    # 4) Limpieza ligera de strings: recorta espacios
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()

    # 5) Convertir a numérico lo que parezca numérico (sin romper texto)
    #    Esto intenta convertir columnas tipo "18", "78.5", etc.
    for col in df.columns:
        if df[col].dtype == "object":
            converted = pd.to_numeric(df[col], errors="ignore")
            df[col] = converted

    # Guardar CSV limpio
    df.to_csv(CLEAN_FILE, index=False, encoding="utf-8")

    # 6) Resumen básico
    cleaned_rows, cleaned_cols = df.shape
    nulls_total = int(df.isna().sum().sum())
    duplicates_removed = original_rows - cleaned_rows

    # Top 10 columnas con más nulos
    nulls_by_col = df.isna().sum().sort_values(ascending=False).head(10)

    # Estadísticas de columnas numéricas (si existen)
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    stats_text = ""
    if numeric_cols:
        desc = df[numeric_cols].describe().round(2)
        stats_text = desc.to_string()

    summary_lines = []
    summary_lines.append("RESUMEN DE LIMPIEZA DE DATOS (dataset educativo)\n")
    summary_lines.append(f"Archivo de entrada: {os.path.basename(RAW_FILE)}")
    summary_lines.append(f"Filas/Columnas originales: {original_rows} / {original_cols}")
    summary_lines.append(f"Filas/Columnas después de limpieza: {cleaned_rows} / {cleaned_cols}")
    summary_lines.append(f"Duplicados eliminados (estimado): {duplicates_removed}")
    summary_lines.append(f"Valores nulos totales: {nulls_total}\n")

    summary_lines.append("Top columnas con más valores nulos:")
    summary_lines.append(nulls_by_col.to_string())
    summary_lines.append("")

    if stats_text:
        summary_lines.append("Estadísticas básicas (numéricas):")
        summary_lines.append(stats_text)
        summary_lines.append("")
    else:
        summary_lines.append("No se detectaron columnas numéricas para estadísticas.\n")

    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines))

    print("Limpieza completada.")
    print(f"CSV limpio: {CLEAN_FILE}")
    print(f"Resumen: {SUMMARY_FILE}")


if __name__ == "__main__":
    main()
