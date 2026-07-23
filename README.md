# PNIG — Plataforma Nacional de Inteligência Geoespacial

Hub nacional de dados geoespaciais públicos do Brasil. Plataforma Open Source para centralizar, integrar, disponibilizar e analisar dados geoespaciais de diversas fontes públicas.

---

## Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| Backend | Node.js + NestJS |
| Banco de dados | PostgreSQL 16 + PostGIS 3.4 |
| Servidor de mapas | GeoServer 2.25 |
| ETL | Python 3.12 |
| Infraestrutura | Docker + Docker Compose |
| ORM | Prisma 7 |
| Documentação API | Swagger / OpenAPI |

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (futuro)                                      │
│  Mapa interativo · Catálogo · Dashboards BI             │
└────────────────┬──────────────────────┬─────────────────┘
                 │ REST JSON            │ WMS/WFS
┌────────────────▼──────┐   ┌───────────▼─────────────────┐
│  NestJS API           │   │  GeoServer 2.25             │
│  :3000/api            │   │  :8080/geoserver            │
│  Catálogo · BI        │   │  Tiles WMS · Download WFS   │
└────────────────┬──────┘   └───────────┬─────────────────┘
                 │                       │
┌────────────────▼───────────────────────▼─────────────────┐
│  PostgreSQL 16 + PostGIS 3.4                             │
│  geo_features · datasets · dataset_versions · metadata   │
└──────────────────────────────────────────────────────────┘
                 ▲
┌────────────────┴─────────────────────────────────────────┐
│  Python ETL                                              │
│  Importação de SHP, GeoJSON, Excel do IBGE/INPE/ICMBio  │
└──────────────────────────────────────────────────────────┘
```

---

## Estrutura do Projeto

```
ecoview-backend/
├── prisma/
│   ├── schema.prisma                    # Modelos Prisma
│   └── migrations/
│       └── XXXXXXXXXXXXXX_init/
│           └── migration.sql            # Migration com PostGIS
├── scripts/
│   ├── Dockerfile.etl                   # Container Python ETL
│   ├── requirements.etl.txt             # Dependências Python
│   ├── import_layer.py                  # Importador de camadas
│   ├── provision_geoserver.py           # Provisionamento GeoServer
│   └── README.md                        # Guia de operação ETL/GeoServer
├── src/
│   ├── prisma/
│   │   ├── prisma.module.ts
│   │   └── prisma.service.ts
│   ├── datasets/
│   │   ├── datasets.module.ts
│   │   ├── datasets.controller.ts
│   │   ├── datasets.service.ts
│   │   ├── datasets.service.spec.ts
│   │   └── dto/
│   │       └── dataset-query.dto.ts
│   ├── themes/
│   │   ├── themes.module.ts
│   │   ├── themes.controller.ts
│   │   ├── themes.service.ts
│   │   └── themes.service.spec.ts
│   ├── common/
│   │   └── filters/
│   │       └── http-exception.filter.ts
│   ├── app.module.ts
│   └── main.ts
├── data/
│   └── raw/                             # Cache local dos SHPs baixados
├── .env                                 # Variáveis de ambiente (não commitar)
├── .env.example                         # Template de variáveis
├── docker-compose.yml
├── Dockerfile
└── prisma.config.ts
```

---

## Pré-requisitos

- Docker Desktop
- Node.js 20+
- npm 10+

---

## Instalação e Configuração

### 1. Clonar o repositório

```bash
git clone <url-do-repositorio>
cd ecoview-backend
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
```

Edite o `.env` com suas configurações:

```env
APP_PORT=3000
NODE_ENV=development

DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=sua_senha
DB_NAME=ecoview_db

# URL para o Prisma CLI (roda no host)
DATABASE_URL=postgresql://postgres:sua_senha@localhost:5432/ecoview_db

GEOSERVER_PORT=8080
GEOSERVER_USER=admin
GEOSERVER_PASSWORD=sua_senha_geoserver
```

### 3. Instalar dependências Node.js

```bash
npm install
```

### 4. Subir os containers

```bash
docker compose up -d
```

Serviços que sobem:
- `ecoview_db_dev` — PostgreSQL + PostGIS na porta 5432
- `ecoview_api_dev` — NestJS API na porta 3000
- `ecoview_geoserver_dev` — GeoServer na porta 8080

### 5. Aplicar a migration do banco

```bash
npx prisma migrate deploy
```

### 6. Provisionar o GeoServer

```bash
docker compose run --rm etl python scripts/provision_geoserver.py
```

Cria automaticamente o workspace `ecoview`, store `ecoview_postgis` e publica as SQL Views.

### 7. Importar as camadas base

```bash
docker compose run --rm etl python scripts/import_layer.py --layer biomas
docker compose run --rm etl python scripts/import_layer.py --layer estados
docker compose run --rm etl python scripts/import_layer.py --layer municipios
```

---

## Uso

### API REST

```
http://localhost:3000/api
```

| Endpoint | Descrição |
|---|---|
| `GET /api/datasets` | Lista todos os datasets publicados |
| `GET /api/datasets?theme=meio_ambiente` | Filtra por tema |
| `GET /api/datasets?search=bioma` | Busca por texto |
| `GET /api/datasets?uf=SP` | Filtra por estado |
| `GET /api/datasets/:slug` | Detalhes de um dataset |
| `GET /api/datasets/:slug/versions` | Versões disponíveis |
| `GET /api/themes` | Lista temas temáticos |

### Documentação Swagger

```
http://localhost:3000/api/docs
```

### GeoServer

```
http://localhost:8080/geoserver
```

Login: `admin` / senha definida no `.env`

#### WMS — Visualização de mapas

```
http://localhost:8080/geoserver/ecoview/wms?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap
  &LAYERS=ecoview:biomas
  &BBOX=-73.98,-33.75,-28.84,5.27
  &WIDTH=800&HEIGHT=600
  &SRS=EPSG:4674
  &FORMAT=image/png
```

#### WFS — Download de dados

```
http://localhost:8080/geoserver/ecoview/wfs?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature
  &TYPENAMES=ecoview:biomas
  &OUTPUTFORMAT=application/json
```

---

## Modelo de Dados

### Schemas

| Schema | Responsabilidade |
|---|---|
| `public` (catalog) | datasets, versões, features, metadados |
| `audit` | logs de acesso, migrações |
| `staging` | reservado para ETL futuro |

### Tabelas principais

```
sources           → fontes de dados (IBGE, ICMBio, INPE...)
themes            → categorias temáticas (hierárquico)
dataset_themes    → N:N entre datasets e themes
datasets          → catálogo de camadas
dataset_versions  → versões de cada camada
geo_features      → features vetoriais (polígonos, linhas, pontos)
time_series_features → séries temporais densas (focos de calor, alertas)
metadata          → metadados Dublin Core + INDE
raster_layers     → tiles raster GeoTIFF
analysis_jobs     → fila de análises assíncronas
access_log        → log de acessos por dataset
```

---

## SRID Padrão

**EPSG:4674 — SIRGAS 2000** (padrão oficial IBGE/Brasil desde 2005)

Outros SRIDs aceitos: 4326 (WGS84), 31981–31985 (UTM SIRGAS 2000)

---

## Testes

```bash
# Rodar todos os testes
npm test

# Com cobertura
npm run test:cov

# Watch mode
npm run test:watch
```

---

## Comandos Úteis

```bash
# Ver status dos containers
docker compose ps

# Logs da API
docker compose logs -f api

# Logs do GeoServer
docker compose logs -f ecoview_geoserver

# Acessar o banco via psql
docker compose exec ecoview_postgres psql -U postgres -d ecoview_db

# Listar datasets importados
docker compose exec ecoview_postgres psql -U postgres -d ecoview_db \
  -c "SELECT slug, status, geometry_type FROM datasets ORDER BY created_at;"

# Prisma Studio (visualizar banco no browser)
npx prisma studio

# Resetar banco (CUIDADO: apaga todos os dados)
npx prisma migrate reset
```

---

## Recuperação após perda de dados

Se os volumes Docker forem removidos (`docker compose down -v`):

```bash
# 1. Recriar containers
docker compose up -d

# 2. Reaplicar migration
npx prisma migrate deploy

# 3. Provisionar GeoServer
docker compose run --rm etl python scripts/provision_geoserver.py

# 4. Reimportar dados (usa cache local em data/raw/)
docker compose run --rm etl python scripts/import_layer.py --all
```

---

## Licença

Open Source — MIT License