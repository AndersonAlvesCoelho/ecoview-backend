# PNIG — Guia de Operação: ETL e GeoServer

Este guia explica como configurar o GeoServer, importar camadas e adicionar novos datasets à plataforma.

---

## Camadas já importadas

| Camada | Slug | Fonte | Versão | Features | Formato |
|---|---|---|---|---|---|
| Biomas e Sistema Costeiro-Marinho | `biomas-sistema-costeiro-marinho-ibge-2025` | IBGE | 2025 | 6 | SHP |
| Unidades da Federação | `estados-ibge-2025` | IBGE | 2025 | 27 | SHP |
| Municípios do Brasil | `municipios-ibge-2025` | IBGE | 2025 | 5.573 | SHP |

---

## Layers publicados no GeoServer

| Layer | Workspace | Tipo | Descrição |
|---|---|---|---|
| `pnig:features` | pnig | SQL View genérica | Todas as features — filtrar por `dataset_slug` |
| `pnig:biomas` | pnig | SQL View | Biomas e Sistema Costeiro-Marinho IBGE 2025 |
| `pnig:estados` | pnig | SQL View | Unidades da Federação IBGE 2025 |
| `pnig:municipios` | pnig | SQL View | Municípios do Brasil IBGE 2025 |

---

## Configuração do GeoServer

### Provisionamento automático (recomendado)

Cria workspace, store e publica todos os layers automaticamente:

```bash
docker compose run --rm etl python scripts/provision_geoserver.py
```

Para recriar tudo do zero (apaga e recria):

```bash
docker compose run --rm etl python scripts/provision_geoserver.py --reset
```

---

### Configuração manual (passo a passo)

Acesse `http://localhost:8080/geoserver` com as credenciais do `.env`.

#### 1. Criar Workspace

- Menu lateral → **Workspaces** → **Add new workspace**
- Name: `pnig`
- Namespace URI: `http://pnig.gov.br`
- Marcar **Default Workspace**
- Clique **Submit**

#### 2. Criar Store (conexão PostGIS)

- Menu lateral → **Stores** → **Add new store** → **PostGIS**

| Campo | Valor |
|---|---|
| Workspace | pnig |
| Data Source Name | ecoview_postgis |
| Host | ecoview_postgres |
| Port | 5432 |
| Database | ecoview_db |
| User | postgres |
| Password | (senha do .env) |
| Expose primary keys | ✅ marcado |

- Clique **Save**

#### 3. Publicar SQL Views

Para cada layer abaixo:
- Menu lateral → **Layers** → **Add new layer**
- Selecione `pnig:ecoview_postgis`
- Clique **Configure new SQL view...**

##### View: `features` (genérica)

```sql
SELECT
    gf.id,
    gf.nome,
    gf.codigo,
    gf.area_ha,
    gf.properties,
    gf.geom,
    gf.geom_simplified,
    d.slug          AS dataset_slug,
    d.title         AS dataset_title,
    d.geometry_type AS dataset_geometry_type
FROM geo_features gf
JOIN datasets d ON d.id = gf.dataset_id
```

##### View: `biomas`

```sql
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
```

##### View: `estados`

```sql
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
```

##### View: `municipios`

```sql
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
```

#### Configuração de cada View

Após colar o SQL, na seção **Attributes**:

1. Clique **Refresh**
2. Coluna `id` → marque **Identifier** ✅
3. Coluna `geom` → Type: `MultiPolygon` → SRID: `4674`
4. Clique **Save**

Na tela seguinte (Edit Layer):

1. Seção **Bounding Boxes** → clique **Compute from data**
2. Em **Lat/Lon Bounding Box** → clique **Compute from native bounds**
3. Clique **Save**

---

## Importar camadas

### Comandos disponíveis

```bash
# Ver camadas disponíveis e status do cache local
docker compose run --rm etl python scripts/import_layer.py --list

# Inspecionar estrutura do SHP antes de importar
docker compose run --rm etl python scripts/import_layer.py --inspect biomas

# Importar uma camada (baixa automaticamente se não tiver cache)
docker compose run --rm etl python scripts/import_layer.py --layer biomas
docker compose run --rm etl python scripts/import_layer.py --layer estados
docker compose run --rm etl python scripts/import_layer.py --layer municipios

# Importar todas as camadas de uma vez
docker compose run --rm etl python scripts/import_layer.py --all

# Usar arquivo local em vez de baixar
docker compose run --rm etl python scripts/import_layer.py --layer biomas --file data/raw/Biomas_250mil.zip

# Forçar novo download mesmo com cache
docker compose run --rm etl python scripts/import_layer.py --layer biomas --force-download
```

---

## Adicionar uma nova camada

### Passo 1 — Inspecionar o SHP

Antes de qualquer configuração, descubra a estrutura real do arquivo:

```bash
docker compose run --rm etl python scripts/import_layer.py --inspect nome_da_camada
```

O output mostra todas as colunas com tipos e exemplos de valores.

### Passo 2 — Cadastrar no script

Abra `scripts/import_layer.py` e adicione um novo entry no dicionário `LAYERS`:

```python
"nome_da_camada": {
    # Metadados do dataset
    "title":           "Nome completo da camada",
    "slug":            "slug-unico-da-camada",
    "description":     "Descrição da camada.",
    "geometry_type":   "MULTIPOLYGON",  # ou POINT, LINESTRING
    "version_tag":     "2025",
    "tags":            ["tag1", "tag2"],
    "mapserver_layer": "nome_layer_geoserver",
    "wms_enabled":     True,
    "wfs_enabled":     True,

    # Fonte
    "source_name":     "Nome da organização",
    "source_acronym":  "SIGLA",
    "source_website":  "https://www.site.gov.br",
    "source_page_url": "https://www.site.gov.br/pagina-dos-dados",

    # Download
    "download_url":    "https://url-direta-do-arquivo.zip",
    "local_file":      DATA_DIR / "nome_do_arquivo.zip",
    "source_format":   "shapefile",

    # Metadados técnicos
    "license":             "CC BY 4.0",
    "spatial_resolution":  "1:250.000",
    "update_frequency":    "yearly",  # realtime|daily|weekly|monthly|quarterly|yearly|irregular|static
    "inde_compliant":      True,
    "lineage":             "Como os dados foram produzidos.",
    "reference_date":      "2025-01-01",

    # Temas
    "theme_codes":   ["meio_ambiente"],  # códigos dos temas
    "theme_primary": "meio_ambiente",    # tema principal

    # Campos do SHP — preencher APÓS rodar --inspect
    "field_nome":        None,   # ex: ["NM_NOME", "NOME"]
    "field_codigo":      None,   # ex: ["CD_CODIGO"]
    "properties_fields": None,   # ex: ["CD_CODIGO", "NM_NOME", "AREA_KM2"]
},
```

### Passo 3 — Inspecionar e preencher campos

```bash
docker compose run --rm etl python scripts/import_layer.py --inspect nome_da_camada
```

Com base no output, preencha `field_nome`, `field_codigo` e `properties_fields` no dicionário.

### Passo 4 — Importar

```bash
docker compose run --rm etl python scripts/import_layer.py --layer nome_da_camada
```

### Passo 5 — Publicar no GeoServer

Crie uma SQL View no GeoServer para a nova camada:

```sql
SELECT
    gf.id,
    gf.nome,
    gf.codigo,
    gf.area_ha,
    gf.properties,
    -- extraia os campos relevantes do JSONB:
    gf.properties->>'CAMPO_1' AS campo_1,
    gf.properties->>'CAMPO_2' AS campo_2,
    gf.geom
FROM geo_features gf
JOIN datasets d ON d.id = gf.dataset_id
WHERE d.slug = 'slug-unico-da-camada'
```

Ou adicione ao script `provision_geoserver.py` na variável `VIEWS` e rode:

```bash
docker compose run --rm etl python scripts/provision_geoserver.py
```

---

## Temas disponíveis

| Código | Nome |
|---|---|
| `meio_ambiente` | Meio Ambiente |
| `queimadas` | Queimadas |
| `desmatamento` | Desmatamento |
| `biodiversidade` | Biodiversidade |
| `hidrografia` | Hidrografia |
| `clima` | Clima |
| `agricultura` | Agricultura |
| `demografia` | Demografia |
| `infraestrutura` | Infraestrutura |
| `saude` | Saúde |
| `educacao` | Educação |
| `terras_indigenas` | Terras Indígenas |
| `quilombos` | Quilombos |
| `uc` | Unidades de Conservação |
| `geologia` | Geologia e Solos |
| `energia` | Energia |
| `transportes` | Transportes |
| `urbanizacao` | Urbanização |
| `limites` | Limites Territoriais |
| `gestao_riscos` | Gestão de Riscos |

---

## Verificar dados importados

```bash
# Listar todos os datasets
docker compose exec ecoview_postgres psql -U postgres -d ecoview_db \
  -c "SELECT slug, status, geometry_type FROM datasets ORDER BY created_at;"

# Contar features por dataset
docker compose exec ecoview_postgres psql -U postgres -d ecoview_db \
  -c "SELECT d.slug, dv.version_tag, dv.feature_count FROM datasets d JOIN dataset_versions dv ON dv.dataset_id = d.id AND dv.is_current = true ORDER BY d.title;"

# Verificar geometrias
docker compose exec ecoview_postgres psql -U postgres -d ecoview_db \
  -c "SELECT nome, ST_GeometryType(geom), ST_IsValid(geom) FROM geo_features LIMIT 10;"
```

---

## Recuperação após reset do Docker

Se o GeoServer perder as configurações (`docker compose down -v`):

```bash
# 1. Subir containers
docker compose up -d

# 2. Reaplicar migration do banco
npx prisma migrate deploy

# 3. Reimportar dados (usa cache em data/raw/)
docker compose run --rm etl python scripts/import_layer.py --all

# 4. Reprovisionar GeoServer
docker compose run --rm etl python scripts/provision_geoserver.py
```