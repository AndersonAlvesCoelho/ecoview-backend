# =============================================================
# PNIG — scripts/import_layer.py
# Importador híbrido de camadas geoespaciais
#
# Uso dentro do Docker:
#   docker compose run --rm etl python scripts/import_layer.py --list
#   docker compose run --rm etl python scripts/import_layer.py --inspect biomas
#   docker compose run --rm etl python scripts/import_layer.py --layer biomas
#   docker compose run --rm etl python scripts/import_layer.py --all
#   docker compose run --rm etl python scripts/import_layer.py --layer biomas --force-download
#   docker compose run --rm etl python scripts/import_layer.py --layer biomas --file data/raw/arquivo.zip
# =============================================================

import argparse
import json
import os
import sys
import zipfile
from pathlib import Path

import geopandas as gpd
import psycopg2
import requests
from dotenv import load_dotenv
from psycopg2.extras import execute_values

load_dotenv()

# =============================================================
# CONFIGURAÇÃO
# =============================================================

DATABASE_URL = os.getenv("DATABASE_URL", "")
DATA_DIR     = Path("data/raw")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================
# CATÁLOGO DE CAMADAS
# field_nome / field_codigo / properties_fields serão confirmados
# após rodar --inspect e ver as colunas reais do SHP
# =============================================================

LAYERS = {

    "biomas": {
        "title":           "Biomas e Sistema Costeiro-Marinho do Brasil",
        "slug":            "biomas-sistema-costeiro-marinho-ibge-2025",
        "description":     (
            "Biomas terrestres e Sistema Costeiro-Marinho do Brasil, "
            "escala 1:250.000, edição 2025. Produzido pelo IBGE."
        ),
        "geometry_type":   "MULTIPOLYGON",
        "version_tag":     "2025",
        "tags":            ["bioma", "sistema costeiro", "marinho", "vegetação", "ibge", "brasil"],
        "mapserver_layer": "biomas_ibge_2025",
        "wms_enabled":     True,
        "wfs_enabled":     True,
        "source_name":     "Instituto Brasileiro de Geografia e Estatística",
        "source_acronym":  "IBGE",
        "source_website":  "https://www.ibge.gov.br",
        "source_page_url": "https://www.ibge.gov.br/geociencias/informacoes-ambientais/estudos-ambientais/15842-biomas.html",
        "download_url": (
            "https://geoftp.ibge.gov.br/informacoes_ambientais/"
            "estudos_ambientais/biomas/vetores/"
            "2025_Biomas-e-Sistema-Costeiro-Marinho-do-Brasil-1-250000_shp.zip"
        ),
        "local_file":    DATA_DIR / "2025_Biomas-e-Sistema-Costeiro-Marinho_shp.zip",
        "source_format": "shapefile",
        "license":             "CC BY 4.0",
        "spatial_resolution":  "1:250.000",
        "update_frequency":    "irregular",
        "inde_compliant":      True,
        "lineage": (
            "Elaborado pelo IBGE com base em imagens de satélite e levantamentos "
            "de campo. Atualização 2025 inclui revisão dos limites dos Biomas e "
            "adequação do Sistema Costeiro-Marinho à Amazônia Azul."
        ),
        "reference_date":  "2025-01-01",
        "theme_codes":     ["meio_ambiente"],
        "theme_primary":   "meio_ambiente",
        "field_nome":        ["NM_BIOMA"],
        "field_codigo":      ["CD_BIOMA"],
        "properties_fields": ["CD_BIOMA", "NM_BIOMA"],
    },

    "estados": {
        "title":           "Unidades da Federação do Brasil",
        "slug":            "estados-ibge-2025",
        "description":     "Limites estaduais do Brasil (UFs), IBGE 2025. 27 unidades.",
        "geometry_type":   "MULTIPOLYGON",
        "version_tag":     "2025",
        "tags":            ["estado", "uf", "limite", "ibge", "brasil"],
        "mapserver_layer": "estados_ibge_2025",
        "wms_enabled":     True,
        "wfs_enabled":     True,
        "source_name":     "Instituto Brasileiro de Geografia e Estatística",
        "source_acronym":  "IBGE",
        "source_website":  "https://www.ibge.gov.br",
        "source_page_url": "https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/15774-malhas.html",
        "download_url": "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2025/Brasil/BR_UF_2025.zip",
        "local_file":    DATA_DIR / "BR_UF_2025.zip",
        "source_format": "shapefile",
        "license":            "CC BY 4.0",
        "spatial_resolution": "1:250.000",
        "update_frequency":   "yearly",
        "inde_compliant":     True,
        "lineage":            "Malha estadual produzida pelo IBGE, edição 2025.",
        "reference_date":     "2025-01-01",
        "theme_codes":        ["limites"],
        "theme_primary":      "limites",
        "field_nome":        ["NM_UF"],
        "field_codigo":      ["CD_UF"],
        "properties_fields": ["CD_UF", "NM_UF", "SIGLA_UF", "CD_REGIAO", "NM_REGIAO", "SIGLA_RG", "AREA_KM2"],
    },

    "municipios": {
        "title":           "Municípios do Brasil",
        "slug":            "municipios-ibge-2025",
        "description":     "Limites municipais do Brasil, IBGE 2025. 5.570 municípios.",
        "geometry_type":   "MULTIPOLYGON",
        "version_tag":     "2025",
        "tags":            ["município", "limite", "ibge", "brasil"],
        "mapserver_layer": "municipios_ibge_2025",
        "wms_enabled":     True,
        "wfs_enabled":     True,
        "source_name":     "Instituto Brasileiro de Geografia e Estatística",
        "source_acronym":  "IBGE",
        "source_website":  "https://www.ibge.gov.br",
        "source_page_url": "https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/15774-malhas.html",
        "download_url": "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2025/Brasil/BR_Municipios_2025.zip",
        "local_file":    DATA_DIR / "BR_Municipios_2025.zip",
        "source_format": "shapefile",
        "license":            "CC BY 4.0",
        "spatial_resolution": "1:250.000",
        "update_frequency":   "yearly",
        "inde_compliant":     True,
        "lineage":            "Malha municipal produzida pelo IBGE, edição 2025.",
        "reference_date":     "2025-01-01",
        "theme_codes":        ["limites"],
        "theme_primary":      "limites",
        "field_nome":        ["NM_MUN"],
        "field_codigo":      ["CD_MUN"],
        "properties_fields": [
            "CD_MUN", "NM_MUN", "SIGLA_UF", "CD_UF", "NM_UF",
            "CD_REGIAO", "NM_REGIAO", "SIGLA_RG",
            "CD_RGI", "NM_RGI", "CD_RGINT", "NM_RGINT",
            "CD_CONCURB", "NM_CONCURB", "AREA_KM2",
        ],
    },
}

# =============================================================
# HELPERS — LOG
# =============================================================

def log(msg: str, level: str = "INFO"):
    icons = {
        "INFO":  "  →",
        "OK":    "  ✅",
        "WARN":  "  ⚠️ ",
        "ERR":   "  ❌",
        "STEP":  "\n  ◆",
    }
    print(f"{icons.get(level, '  ·')} {msg}", flush=True)

# =============================================================
# HELPERS — ARQUIVO
# =============================================================

def download_file(url: str, dest: Path) -> Path:
    log(f"Baixando:\n     {url}", "STEP")
    try:
        r = requests.get(url, stream=True, timeout=300)
        r.raise_for_status()
    except requests.RequestException as e:
        log(f"Falha no download: {e}", "ERR")
        sys.exit(1)

    total      = int(r.headers.get("content-length", 0))
    downloaded = 0
    with open(dest, "wb") as f:
        for chunk in r.iter_content(chunk_size=65536):
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = downloaded / total * 100
                mb  = downloaded / 1024 / 1024
                print(f"\r     {pct:5.1f}%  ({mb:.1f} MB)", end="", flush=True)
    print()
    log(f"Salvo em: {dest}", "OK")
    return dest


def get_zip(cfg: dict, local_file: str = None, force: bool = False) -> Path:
    """Retorna o caminho do ZIP — baixa se necessário."""
    zip_path = Path(local_file) if local_file else cfg["local_file"]

    if force and zip_path.exists():
        log("--force-download: removendo cache local...", "WARN")
        zip_path.unlink()

    if not zip_path.exists():
        download_file(cfg["download_url"], zip_path)
    else:
        mb = zip_path.stat().st_size / 1024 / 1024
        log(f"Cache local encontrado: {zip_path} ({mb:.1f} MB)", "OK")

    return zip_path


def extract_shp(zip_path: Path) -> tuple[gpd.GeoDataFrame, Path]:
    """Extrai ZIP e retorna (GeoDataFrame, caminho do SHP)."""
    extract_dir = zip_path.parent / zip_path.stem
    extract_dir.mkdir(exist_ok=True)

    log(f"Extraindo {zip_path.name}...", "STEP")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(extract_dir)

    shp_files = list(extract_dir.rglob("*.shp"))
    if not shp_files:
        log("Nenhum .shp encontrado no ZIP!", "ERR")
        sys.exit(1)

    if len(shp_files) > 1:
        log(f"{len(shp_files)} SHPs encontrados — usando o primeiro:", "WARN")
        for f in shp_files:
            log(f"  {f.name}", "INFO")

    shp_path = shp_files[0]
    log(f"Lendo {shp_path.name}...", "STEP")
    gdf = gpd.read_file(shp_path)
    log(f"{len(gdf)} features | CRS: {gdf.crs}", "OK")
    return gdf, shp_path

# =============================================================
# COMANDO: --inspect
# Mostra as colunas reais do SHP com tipos e exemplos de valores
# =============================================================

def inspect_layer(layer_name: str, local_file: str = None, force: bool = False):
    if layer_name not in LAYERS:
        log(f"Camada '{layer_name}' não reconhecida.", "ERR")
        sys.exit(1)

    cfg      = LAYERS[layer_name]
    zip_path = get_zip(cfg, local_file, force)
    gdf, shp_path = extract_shp(zip_path)

    # Reprojetar para verificar CRS
    if gdf.crs and gdf.crs.to_epsg() != 4674:
        log(f"CRS original: EPSG:{gdf.crs.to_epsg()} → será reprojetado para EPSG:4674 na importação", "WARN")
    else:
        log("CRS: EPSG:4674 (SIRGAS 2000) ✅ — nenhuma reprojeção necessária", "OK")

    print(f"\n{'═'*65}")
    print(f"  INSPEÇÃO: {cfg['title']}")
    print(f"  Arquivo : {shp_path.name}")
    print(f"  Features: {len(gdf)}")
    print(f"  CRS     : {gdf.crs}")
    print(f"{'═'*65}")
    print(f"\n  {'COLUNA':<25} {'TIPO':<12} EXEMPLOS DE VALORES")
    print(f"  {'-'*62}")

    for col in gdf.columns:
        if col == "geometry":
            geom_types = gdf.geometry.geom_type.unique().tolist()
            print(f"  {'geometry':<25} {'geometry':<12} {geom_types}")
            continue

        dtype    = str(gdf[col].dtype)
        # Pega até 3 valores únicos não nulos como exemplo
        examples = gdf[col].dropna().unique()
        samples  = [str(v) for v in examples[:3] if str(v) not in ("nan", "None", "")]
        sample_str = " | ".join(samples) if samples else "(vazio)"

        print(f"  {col:<25} {dtype:<12} {sample_str}")

    print(f"\n{'═'*65}")
    print(f"\n  ⚠️  Preencha no script as configurações abaixo com base nas colunas acima:")
    print(f"\n  LAYERS[\"{layer_name}\"][\"field_nome\"]        = [\"COLUNA_QUE_TEM_O_NOME\"]")
    print(f"  LAYERS[\"{layer_name}\"][\"field_codigo\"]      = [\"COLUNA_QUE_TEM_O_CODIGO\"]")
    print(f"  LAYERS[\"{layer_name}\"][\"properties_fields\"] = [\"COL1\", \"COL2\", ...]  # todas que quer guardar")
    print(f"\n  Depois rode:")
    print(f"  docker compose run --rm etl python scripts/import_layer.py --layer {layer_name}")
    print()

# =============================================================
# HELPERS — IMPORTAÇÃO
# =============================================================

def safe_value(val):
    if val is None:
        return None
    if hasattr(val, "item"):
        val = val.item()
    s = str(val).strip()
    return None if s in ("nan", "None", "NaN", "") else s


def find_column(gdf: gpd.GeoDataFrame, candidates: list) -> str | None:
    upper_map = {c.upper(): c for c in gdf.columns}
    for c in candidates:
        real = upper_map.get(c.upper())
        if real:
            return real
    return None


def build_properties(row, fields: list, all_cols: list) -> dict:
    upper_map = {c.upper(): c for c in all_cols}
    props = {}
    for f in fields:
        real = upper_map.get(f.upper())
        if real and real in row.index:
            v = safe_value(row[real])
            if v is not None:
                props[real] = v
    return props

# =============================================================
# BANCO — CONEXÃO E UPSERTS
# =============================================================

def get_conn():
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        log(f"Erro de conexão: {e}", "ERR")
        log(f"DATABASE_URL: {DATABASE_URL}", "ERR")
        sys.exit(1)


def upsert_source(conn, cfg: dict) -> str:
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM sources WHERE acronym = %s", (cfg["source_acronym"],))
        row = cur.fetchone()
        if row:
            log(f"Fonte existente: {cfg['source_acronym']}", "OK")
            return str(row[0])
        cur.execute("""
            INSERT INTO sources (name, acronym, source_type, website, source_url, updated_at)
            VALUES (%s, %s, 'organization', %s, %s, NOW()) RETURNING id
        """, (cfg["source_name"], cfg["source_acronym"],
              cfg["source_website"], cfg["source_page_url"]))
        sid = str(cur.fetchone()[0])
        conn.commit()
        log(f"Fonte criada: {cfg['source_acronym']} → {sid}", "OK")
        return sid


def upsert_theme(conn, code: str) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM themes WHERE code = %s", (code,))
        row = cur.fetchone()
        if row:
            return row[0]
        names = {
            "meio_ambiente":    "Meio Ambiente",
            "limites":          "Limites Territoriais",
            "queimadas":        "Queimadas",
            "desmatamento":     "Desmatamento",
            "terras_indigenas": "Terras Indígenas",
            "uc":               "Unidades de Conservação",
            "hidrografia":      "Hidrografia",
            "clima":            "Clima",
        }
        cur.execute("""
            INSERT INTO themes (code, name, sort_order)
            VALUES (%s, %s, 0) RETURNING id
        """, (code, names.get(code, code.replace("_", " ").title())))
        tid = cur.fetchone()[0]
        conn.commit()
        log(f"Tema criado: {code} → {tid}", "OK")
        return tid


def upsert_dataset(conn, cfg: dict, source_id: str) -> str:
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM datasets WHERE slug = %s", (cfg["slug"],))
        row = cur.fetchone()
        if row:
            log(f"Dataset existente: {cfg['slug']}", "OK")
            return str(row[0])
        cur.execute("""
            INSERT INTO datasets (
                source_id, title, slug, description, status,
                geometry_type, srid, tags,
                wms_enabled, wfs_enabled, mapserver_layer, updated_at
            ) VALUES (
                %s, %s, %s, %s, 'published',
                %s::\"geometry_type\", 4674, %s,
                %s, %s, %s, NOW()
            ) RETURNING id
        """, (
            source_id, cfg["title"], cfg["slug"], cfg["description"],
            cfg["geometry_type"], cfg["tags"],
            cfg["wms_enabled"], cfg["wfs_enabled"], cfg["mapserver_layer"],
        ))
        did = str(cur.fetchone()[0])
        for code in cfg["theme_codes"]:
            tid = upsert_theme(conn, code)
            cur.execute("""
                INSERT INTO dataset_themes (dataset_id, theme_id, is_primary)
                VALUES (%s, %s, %s) ON CONFLICT DO NOTHING
            """, (did, tid, code == cfg["theme_primary"]))
        conn.commit()
        log(f"Dataset criado: {cfg['slug']} → {did}", "OK")
        return did


def create_version(conn, dataset_id: str, cfg: dict, feature_count: int) -> str:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id FROM dataset_versions
            WHERE dataset_id = %s AND version_tag = %s
        """, (dataset_id, cfg["version_tag"]))
        if cur.fetchone():
            log(f"Versão '{cfg['version_tag']}' já existe. Use --force-download para reimportar.", "WARN")
            sys.exit(0)

        cur.execute("""
            UPDATE dataset_versions SET is_current = false
            WHERE dataset_id = %s AND is_current = true
        """, (dataset_id,))

        cur.execute("""
            SELECT COALESCE(MAX(version_num), 0) + 1
            FROM dataset_versions WHERE dataset_id = %s
        """, (dataset_id,))
        vnum = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO dataset_versions (
                dataset_id, version_tag, version_num, is_current,
                feature_count, source_url, source_format, published_at
            ) VALUES (%s, %s, %s, true, %s, %s, %s, NOW()) RETURNING id
        """, (dataset_id, cfg["version_tag"], vnum,
              feature_count, cfg["download_url"], cfg["source_format"]))
        vid = str(cur.fetchone()[0])
        conn.commit()
        log(f"Versão criada: {cfg['version_tag']} (num {vnum}) → {vid}", "OK")
        return vid


def upsert_metadata(conn, dataset_id: str, cfg: dict):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO metadata (
                dataset_id, license, source_url, lineage,
                spatial_resolution, update_frequency,
                inde_compliant, reference_date, keywords, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s::\"update_frequency\", %s, %s, %s, NOW())
            ON CONFLICT (dataset_id) DO UPDATE SET
                license            = EXCLUDED.license,
                lineage            = EXCLUDED.lineage,
                spatial_resolution = EXCLUDED.spatial_resolution,
                update_frequency   = EXCLUDED.update_frequency,
                inde_compliant     = EXCLUDED.inde_compliant,
                reference_date     = EXCLUDED.reference_date,
                keywords           = EXCLUDED.keywords,
                updated_at         = NOW()
        """, (
            dataset_id, cfg["license"], cfg["source_page_url"], cfg["lineage"],
            cfg["spatial_resolution"], cfg["update_frequency"], cfg["inde_compliant"],
            cfg["reference_date"], cfg["tags"],
        ))
        conn.commit()
        log("Metadados salvos", "OK")


def import_features(conn, gdf: gpd.GeoDataFrame,
                    version_id: str, dataset_id: str, cfg: dict) -> int:
    nome_col   = find_column(gdf, cfg["field_nome"])
    codigo_col = find_column(gdf, cfg["field_codigo"])
    all_cols   = list(gdf.columns)

    log(f"Campo nome   → {nome_col   or '⚠️  não encontrado'}", "INFO")
    log(f"Campo código → {codigo_col or '⚠️  não encontrado'}", "INFO")

    total    = len(gdf)
    inserted = 0
    errors   = 0
    batch    = []
    BATCH_SZ = 200

    log(f"Inserindo {total} features em lotes de {BATCH_SZ}...", "STEP")

    with conn.cursor() as cur:
        for _, row in gdf.iterrows():
            try:
                geom_wkt = None
                if row.geometry and not row.geometry.is_empty:
                    from shapely.geometry import MultiPolygon, Polygon
                    geom = row.geometry
                    # Normaliza Polygon → MultiPolygon para consistência
                    if isinstance(geom, Polygon):
                        geom = MultiPolygon([geom])
                    geom_wkt = geom.wkt
                nome     = safe_value(row[nome_col])   if nome_col   else None
                codigo   = safe_value(row[codigo_col]) if codigo_col else None
                props    = build_properties(row, cfg["properties_fields"], all_cols)
                batch.append((version_id, dataset_id, nome, codigo,
                               json.dumps(props, ensure_ascii=False), geom_wkt))
            except Exception as e:
                errors += 1
                log(f"Erro na feature {_}: {e}", "WARN")
                continue

            if len(batch) >= BATCH_SZ:
                execute_values(cur, """
                    INSERT INTO geo_features
                        (version_id, dataset_id, nome, codigo, properties, geom)
                    VALUES %s
                """, batch, template="""(
                    %s::uuid, %s::uuid, %s, %s, %s::jsonb,
                    ST_GeomFromText(%s, 4674)
                )""")
                conn.commit()
                inserted += len(batch)
                batch = []
                print(f"\r     {inserted}/{total} features inseridas...", end="", flush=True)

        if batch:
            execute_values(cur, """
                INSERT INTO geo_features
                    (version_id, dataset_id, nome, codigo, properties, geom)
                VALUES %s
            """, batch, template="""(
                %s::uuid, %s::uuid, %s, %s, %s::jsonb,
                ST_GeomFromText(%s, 4674)
            )""")
            conn.commit()
            inserted += len(batch)

    print()
    if errors:
        log(f"{errors} features ignoradas por erro", "WARN")
    log(f"{inserted} features inseridas com sucesso", "OK")
    return inserted


def update_bbox(conn, dataset_id: str):
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE datasets
            SET bbox = (
                SELECT ST_Envelope(ST_Union(geom))
                FROM geo_features
                WHERE dataset_id = %s::uuid AND geom IS NOT NULL
            )
            WHERE id = %s::uuid
        """, (dataset_id, dataset_id))
        conn.commit()
    log("Bounding box do dataset atualizado", "OK")

# =============================================================
# VALIDAÇÃO: garante que os campos foram configurados
# =============================================================

def validate_fields(layer_name: str, cfg: dict):
    missing = []
    for key in ("field_nome", "field_codigo", "properties_fields"):
        if cfg.get(key) is None:
            missing.append(key)
    if missing:
        print(f"\n  ❌ Campos não configurados para '{layer_name}': {missing}")
        print(f"\n  Execute primeiro:")
        print(f"  docker compose run --rm etl python scripts/import_layer.py --inspect {layer_name}")
        print(f"\n  Depois preencha os campos no LAYERS[\"{layer_name}\"] no script e rode novamente.\n")
        sys.exit(1)

# =============================================================
# FUNÇÃO PRINCIPAL DE IMPORTAÇÃO
# =============================================================

def import_layer(layer_name: str, local_file: str = None, force: bool = False):
    if layer_name not in LAYERS:
        log(f"Camada '{layer_name}' não reconhecida.", "ERR")
        sys.exit(1)

    cfg = LAYERS[layer_name]

    # Garante que os campos foram preenchidos após o --inspect
    validate_fields(layer_name, cfg)

    print(f"\n{'═'*60}")
    print(f"  {cfg['title']}")
    print(f"  Versão: {cfg['version_tag']}")
    print(f"{'═'*60}")

    # 1. Arquivo
    zip_path      = get_zip(cfg, local_file, force)

    # 2. Ler SHP
    gdf, _        = extract_shp(zip_path)

    # 3. Reprojetar se necessário
    if gdf.crs and gdf.crs.to_epsg() != 4674:
        log(f"Reprojetando EPSG:{gdf.crs.to_epsg()} → EPSG:4674...", "STEP")
        gdf = gdf.to_crs(epsg=4674)
        log("Reprojeção concluída", "OK")

    # 4. Banco — metadados
    log("Conectando ao banco...", "STEP")
    conn       = get_conn()
    log("Conectado!", "OK")

    log("Salvando metadados...", "STEP")
    source_id  = upsert_source(conn, cfg)
    dataset_id = upsert_dataset(conn, cfg, source_id)
    version_id = create_version(conn, dataset_id, cfg, len(gdf))
    upsert_metadata(conn, dataset_id, cfg)

    # 5. Features
    log("Importando features...", "STEP")
    count = import_features(conn, gdf, version_id, dataset_id, cfg)

    # 6. Bbox
    log("Atualizando bounding box...", "STEP")
    update_bbox(conn, dataset_id)

    conn.close()

    print(f"\n{'═'*60}")
    print(f"  ✅ Importação concluída!")
    print(f"     Camada     : {cfg['title']}")
    print(f"     Versão     : {cfg['version_tag']}")
    print(f"     Features   : {count}")
    print(f"     Dataset ID : {dataset_id}")
    print(f"     Version ID : {version_id}")
    print(f"{'═'*60}\n")

# =============================================================
# CLI
# =============================================================

def main():
    parser = argparse.ArgumentParser(
        description="PNIG — Importador de camadas geoespaciais",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Fluxo recomendado:
  1. Inspecionar o SHP para ver as colunas reais:
     docker compose run --rm etl python scripts/import_layer.py --inspect biomas

  2. Preencher field_nome, field_codigo e properties_fields no script

  3. Importar:
     docker compose run --rm etl python scripts/import_layer.py --layer biomas
        """
    )
    parser.add_argument("--layer",          help="Nome da camada para importar")
    parser.add_argument("--inspect",        help="Inspecionar SHP sem importar")
    parser.add_argument("--all",            action="store_true", help="Importar todas as camadas")
    parser.add_argument("--list",           action="store_true", help="Listar camadas disponíveis")
    parser.add_argument("--file",           help="Caminho local do ZIP (opcional)")
    parser.add_argument("--force-download", action="store_true", help="Forçar novo download")

    args = parser.parse_args()

    if args.list:
        print("\nCamadas disponíveis:\n")
        for name, cfg in LAYERS.items():
            exists    = cfg["local_file"].exists()
            cache     = f"✅ cache ({cfg['local_file'].stat().st_size/1024/1024:.1f} MB)" if exists else "⬇  sem cache"
            fields_ok = "✅ campos configurados" if cfg.get("field_nome") else "⚠️  rode --inspect primeiro"
            print(f"  {name:<15} {cache:<35} {fields_ok}")
            print(f"               {cfg['title']} — v{cfg['version_tag']}")
            print()
        return

    if args.inspect:
        inspect_layer(args.inspect, args.file, args.force_download)
        return

    if args.all:
        for name in LAYERS:
            import_layer(name, force=args.force_download)
        return

    if args.layer:
        import_layer(args.layer, args.file, args.force_download)
        return

    parser.print_help()


if __name__ == "__main__":
    main()