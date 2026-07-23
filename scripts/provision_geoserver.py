# =============================================================
# PNIG — scripts/provision_geoserver.py
# Provisiona o GeoServer via API REST
# Cria workspace, store e publica as SQL Views
#
# Uso:
#   docker compose run --rm etl python scripts/provision_geoserver.py
#   docker compose run --rm etl python scripts/provision_geoserver.py --reset
# =============================================================

import argparse
import os
import sys
import time
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

# =============================================================
# CONFIGURAÇÃO
# =============================================================

GEOSERVER_URL  = os.getenv("GEOSERVER_URL", "http://ecoview_geoserver:8080/geoserver")
GEOSERVER_USER = os.getenv("GEOSERVER_USER", "admin")
GEOSERVER_PASS = os.getenv("GEOSERVER_PASSWORD", "geoserver")
DATABASE_URL   = os.getenv("DATABASE_URL", "")

# Extrai parâmetros do DATABASE_URL
# postgresql://user:pass@host:port/dbname
def parse_db_url(url: str) -> dict:
    url = url.replace("postgresql://", "")
    user_pass, rest = url.split("@")
    user, password   = user_pass.split(":")
    host_port, dbname = rest.split("/")
    host, port = host_port.split(":") if ":" in host_port else (host_port, "5432")
    return { "host": host, "port": port, "user": user, "password": password, "dbname": dbname }

WORKSPACE = "ecoview"
STORE     = "ecoview_postgis"
AUTH      = HTTPBasicAuth(GEOSERVER_USER, GEOSERVER_PASS)
HEADERS   = { "Content-Type": "application/json" }
REST      = f"{GEOSERVER_URL}/rest"

# =============================================================
# HELPERS
# =============================================================

def log(msg: str, level: str = "INFO"):
    icons = { "INFO": "  →", "OK": "  ✅", "WARN": "  ⚠️ ", "ERR": "  ❌", "STEP": "\n  ◆" }
    print(f"{icons.get(level, '·')} {msg}", flush=True)


def req(method: str, path: str, json=None, expected=(200, 201)) -> requests.Response:
    url = f"{REST}/{path}"
    r = getattr(requests, method)(url, auth=AUTH, headers=HEADERS, json=json, timeout=30)
    if r.status_code not in expected:
        log(f"{method.upper()} {path} → {r.status_code}: {r.text[:200]}", "ERR")
    return r


def wait_geoserver(retries: int = 20, delay: int = 5):
    log("Aguardando GeoServer ficar disponível...", "STEP")
    for i in range(retries):
        try:
            r = requests.get(f"{GEOSERVER_URL}/web/", timeout=5)
            if r.status_code == 200:
                log("GeoServer disponível!", "OK")
                return
        except requests.RequestException:
            pass
        print(f"\r    tentativa {i+1}/{retries}...", end="", flush=True)
        time.sleep(delay)
    log("GeoServer não respondeu após várias tentativas.", "ERR")
    sys.exit(1)

# =============================================================
# PROVISIONAMENTO
# =============================================================

def create_workspace():
    log("Criando workspace ecoview...", "STEP")
    r = req("get", f"workspaces/{WORKSPACE}.json", expected=(200, 404))
    if r.status_code == 200:
        log(f"Workspace '{WORKSPACE}' já existe", "OK")
        return

    req("post", "workspaces.json", json={
        "workspace": {
            "name": WORKSPACE,
            "uri":  "http://ecoview.gov.br"
        }
    })
    log(f"Workspace '{WORKSPACE}' criado", "OK")


def create_store():
    log("Criando store PostGIS...", "STEP")
    r = req("get", f"workspaces/{WORKSPACE}/datastores/{STORE}.json", expected=(200, 404))
    if r.status_code == 200:
        log(f"Store '{STORE}' já existe", "OK")
        return

    db = parse_db_url(DATABASE_URL)

    req("post", f"workspaces/{WORKSPACE}/datastores.json", json={
        "dataStore": {
            "name":        STORE,
            "type":        "PostGIS",
            "enabled":     True,
            "workspace":   { "name": WORKSPACE },
            "connectionParameters": {
                "entry": [
                    { "@key": "host",                 "$": db["host"] },
                    { "@key": "port",                 "$": db["port"] },
                    { "@key": "database",             "$": db["dbname"] },
                    { "@key": "user",                 "$": db["user"] },
                    { "@key": "passwd",               "$": db["password"] },
                    { "@key": "dbtype",               "$": "postgis" },
                    { "@key": "schema",               "$": "public" },
                    { "@key": "Expose primary keys",  "$": "true" },
                    { "@key": "Estimated extends",    "$": "false" },
                    { "@key": "encode functions",     "$": "true" },
                    { "@key": "Support on the fly geometry simplification", "$": "true" },
                ]
            }
        }
    })
    log(f"Store '{STORE}' criado", "OK")


# =============================================================
# SQL VIEWS
# =============================================================

VIEWS = {

    "features": {
        "title":       "PNIG — Todas as Features",
        "abstract":    "View genérica com todas as features geoespaciais. Use CQL_FILTER=dataset_slug='slug' para filtrar por dataset.",
        "geom_field":  "geom",
        "geom_type":   "MultiPolygon",
        "srid":        4674,
        "identifier":  "id",
        "sql": """
SELECT
    gf.id,
    gf.nome,
    gf.codigo,
    gf.area_ha,
    gf.properties,
    gf.geom,
    gf.geom_simplified,
    d.slug         AS dataset_slug,
    d.title        AS dataset_title,
    d.geometry_type AS dataset_geometry_type
FROM geo_features gf
JOIN datasets d ON d.id = gf.dataset_id
        """.strip(),
        "bbox": { "minx": -73.99, "miny": -33.75, "maxx": -28.84, "maxy": 5.27 }
    },

    "biomas": {
        "title":    "Biomas e Sistema Costeiro-Marinho — IBGE 2025",
        "abstract": "Biomas terrestres e Sistema Costeiro-Marinho do Brasil, escala 1:250.000.",
        "geom_field": "geom",
        "geom_type":  "MultiPolygon",
        "srid":       4674,
        "identifier": "id",
        "sql": """
SELECT
    gf.id,
    gf.nome,
    gf.codigo,
    gf.area_ha,
    gf.properties,
    gf.properties->>'CD_BIOMA' AS cd_bioma,
    gf.properties->>'NM_BIOMA' AS nm_bioma,
    gf.geom
FROM geo_features gf
JOIN datasets d ON d.id = gf.dataset_id
WHERE d.slug = 'biomas-sistema-costeiro-marinho-ibge-2025'
        """.strip(),
        "bbox": { "minx": -73.99, "miny": -33.75, "maxx": -28.84, "maxy": 5.27 }
    },

    "estados": {
        "title":    "Unidades da Federação — IBGE 2025",
        "abstract": "Limites estaduais do Brasil, IBGE 2025. 27 unidades da federação.",
        "geom_field": "geom",
        "geom_type":  "MultiPolygon",
        "srid":       4674,
        "identifier": "id",
        "sql": """
SELECT
    gf.id,
    gf.nome,
    gf.codigo,
    gf.area_ha,
    gf.properties,
    gf.properties->>'CD_UF'     AS cd_uf,
    gf.properties->>'SIGLA_UF'  AS sigla_uf,
    gf.properties->>'NM_REGIAO' AS nm_regiao,
    gf.properties->>'AREA_KM2'  AS area_km2,
    gf.geom
FROM geo_features gf
JOIN datasets d ON d.id = gf.dataset_id
WHERE d.slug = 'estados-ibge-2025'
        """.strip(),
        "bbox": { "minx": -73.99, "miny": -33.75, "maxx": -28.84, "maxy": 5.27 }
    },

    "municipios": {
        "title":    "Municípios do Brasil — IBGE 2025",
        "abstract": "Limites municipais do Brasil, IBGE 2025. 5.573 municípios.",
        "geom_field": "geom",
        "geom_type":  "MultiPolygon",
        "srid":       4674,
        "identifier": "id",
        "sql": """
SELECT
    gf.id,
    gf.nome,
    gf.codigo,
    gf.area_ha,
    gf.properties,
    gf.properties->>'CD_MUN'    AS cd_mun,
    gf.properties->>'SIGLA_UF'  AS sigla_uf,
    gf.properties->>'CD_UF'     AS cd_uf,
    gf.properties->>'NM_UF'     AS nm_uf,
    gf.properties->>'NM_REGIAO' AS nm_regiao,
    gf.properties->>'AREA_KM2'  AS area_km2,
    gf.geom
FROM geo_features gf
JOIN datasets d ON d.id = gf.dataset_id
WHERE d.slug = 'municipios-ibge-2025'
        """.strip(),
        "bbox": { "minx": -73.99, "miny": -33.75, "maxx": -28.84, "maxy": 5.27 }
    },
}


def publish_view(name: str, cfg: dict):
    log(f"Publicando layer '{name}'...", "STEP")

    # Verificar se já existe
    r = req("get",
            f"workspaces/{WORKSPACE}/datastores/{STORE}/featuretypes/{name}.json",
            expected=(200, 404))
    if r.status_code == 200:
        log(f"Layer '{name}' já existe — atualizando...", "WARN")
        req("put",
            f"workspaces/{WORKSPACE}/datastores/{STORE}/featuretypes/{name}.json",
            json=build_featuretype(name, cfg),
            expected=(200, 201))
        log(f"Layer '{name}' atualizado", "OK")
        return

    req("post",
        f"workspaces/{WORKSPACE}/datastores/{STORE}/featuretypes.json",
        json=build_featuretype(name, cfg))
    log(f"Layer '{name}' publicado", "OK")


def build_featuretype(name: str, cfg: dict) -> dict:
    bbox = cfg["bbox"]
    return {
        "featureType": {
            "name":      name,
            "nativeName": name,
            "title":     cfg["title"],
            "abstract":  cfg["abstract"],
            "enabled":   True,
            "srs":       f"EPSG:{cfg['srid']}",
            "nativeSRS": f"EPSG:{cfg['srid']}",
            "projectionPolicy": "FORCE_DECLARED",
            "nativeBoundingBox": {
                "minx": bbox["minx"], "miny": bbox["miny"],
                "maxx": bbox["maxx"], "maxy": bbox["maxy"],
                "crs":  f"EPSG:{cfg['srid']}"
            },
            "latLonBoundingBox": {
                "minx": bbox["minx"], "miny": bbox["miny"],
                "maxx": bbox["maxx"], "maxy": bbox["maxy"],
                "crs":  "EPSG:4326"
            },
            "metadata": {
                "entry": [
                    {
                        "@key": "JDBC_VIRTUAL_TABLE",
                        "virtualTable": {
                            "name":     name,
                            "sql":      cfg["sql"],
                            "escapeSql": False,
                            "geometry": {
                                "name": cfg["geom_field"],
                                "type": cfg["geom_type"],
                                "srid": cfg["srid"]
                            }
                        }
                    }
                ]
            }
        }
    }


def delete_workspace():
    log(f"Removendo workspace '{WORKSPACE}'...", "STEP")
    r = req("delete",
            f"workspaces/{WORKSPACE}?recurse=true",
            expected=(200, 404))
    if r.status_code in (200, 404):
        log(f"Workspace '{WORKSPACE}' removido", "OK")


# =============================================================
# MAIN
# =============================================================

def provision():
    print(f"\n{'═'*55}")
    print(f"  PNIG — Provisionamento do GeoServer")
    print(f"  URL: {GEOSERVER_URL}")
    print(f"{'═'*55}")

    wait_geoserver()
    create_workspace()
    create_store()

    for name, cfg in VIEWS.items():
        publish_view(name, cfg)

    print(f"\n{'═'*55}")
    print(f"  ✅ Provisionamento concluído!")
    print(f"\n  Layers publicados:")
    for name in VIEWS:
        print(f"    {WORKSPACE}:{name}")
    print(f"\n  WMS: {GEOSERVER_URL}/{WORKSPACE}/wms")
    print(f"  WFS: {GEOSERVER_URL}/{WORKSPACE}/wfs")
    print(f"{'═'*55}\n")


def main():
    parser = argparse.ArgumentParser(
        description="PNIG — Provisionamento do GeoServer"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Remove e recria todo o workspace (cuidado!)"
    )
    args = parser.parse_args()

    if args.reset:
        print("\n  ⚠️  RESET: removendo workspace e recriando tudo...")
        delete_workspace()
        time.sleep(2)

    provision()


if __name__ == "__main__":
    main()