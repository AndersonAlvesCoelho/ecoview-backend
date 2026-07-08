# PNIG — Setup Prisma 6+ + PostGIS

## O que mudou no Prisma 6+

A conexão com o banco saiu do `schema.prisma` e foi para `prisma.config.ts`.
O `schema.prisma` agora só tem models e ENUMs — sem `url` no datasource.

```
Antes (Prisma 5):  datasource db { url = env("DATABASE_URL") }
Depois (Prisma 6): prisma.config.ts com adapter PrismaPg
```

---

## 1. Instalar dependências

```bash
npm install prisma @prisma/client @prisma/adapter-pg pg
npm install -D @types/pg
```

---

## 2. Estrutura de pastas esperada

```
ecoview-backend/
├── prisma/
│   ├── schema.prisma                        ← models e ENUMs
│   └── migrations/
│       ├── manual/
│       │   └── 0001_postgis_spatial.sql     ← geometrias, índices, seed
│       └── (geradas pelo Prisma CLI)
├── src/
│   ├── prisma/
│   │   ├── prisma.module.ts
│   │   └── prisma.service.ts
│   └── app.module.ts
├── prisma.config.ts                         ← conexão Prisma 6+
├── .env
└── docker-compose.yml
```

---

## 3. Rodar a primeira migration

```bash
# 1. Subir o banco
docker compose up ecoview_postgres -d

# 2. Criar e aplicar migration Prisma (tabelas principais)
npx prisma migrate dev --name init

# 3. Aplicar migration manual PostGIS
#    (adiciona colunas geometry, índices GIST/GIN, seed de temas e fontes)
psql postgresql://postgres:16798577@localhost:5432/ecoview_db \
  -f prisma/migrations/manual/0001_postgis_spatial.sql
```

---

## 4. Verificar

```bash
# Abrir Prisma Studio
npx prisma studio

# Verificar extensões PostGIS instaladas
docker compose exec ecoview_postgres psql \
  -U postgres -d ecoview_db \
  -c "SELECT name, installed_version FROM pg_extension WHERE name IN ('postgis','uuid-ossp','pg_trgm');"

# Verificar tabelas criadas
docker compose exec ecoview_postgres psql \
  -U postgres -d ecoview_db \
  -c "\dt"
```

---

## 5. Registrar PrismaModule no AppModule

```typescript
// src/app.module.ts
import { Module } from '@nestjs/common';
import { PrismaModule } from './prisma/prisma.module';

@Module({
  imports: [PrismaModule],
})
export class AppModule {}
```

---

## 6. Usar PrismaService em qualquer módulo

```typescript
// Exemplo: src/datasets/datasets.service.ts
import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class DatasetsService {
  constructor(private readonly prisma: PrismaService) {}

  findAll() {
    return this.prisma.dataset.findMany({
      where: { status: 'published' },
      include: { source: true, datasetThemes: { include: { theme: true } } },
      orderBy: { createdAt: 'desc' },
    });
  }
}
```

---

## 7. Queries espaciais com $queryRaw

Para operações PostGIS, use sempre `$queryRaw`:

```typescript
// Buscar features por bounding box
const features = await this.prisma.$queryRaw`
  SELECT
    id,
    nome,
    codigo,
    area_ha,
    ST_AsGeoJSON(geom)::json AS geometry,
    properties
  FROM geo_features
  WHERE ST_Intersects(
    geom,
    ST_MakeEnvelope(${xmin}, ${ymin}, ${xmax}, ${ymax}, 4674)
  )
  AND dataset_id = ${datasetId}::uuid
  LIMIT 1000
`;
```

---

## 8. Fluxo de migrations futuras

```bash
# Alterar schema.prisma → criar migration Prisma
npx prisma migrate dev --name nome_da_mudanca

# Para mudanças PostGIS (novas colunas geometry, índices GIST):
# criar arquivo em prisma/migrations/manual/000X_descricao.sql
# e executar manualmente via psql
```
