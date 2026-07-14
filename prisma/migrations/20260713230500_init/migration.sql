-- Extensões PostGIS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- CreateEnum
CREATE TYPE "dataset_status" AS ENUM ('draft', 'published', 'deprecated', 'archived');

-- CreateEnum
CREATE TYPE "geometry_type" AS ENUM ('POINT', 'MULTIPOINT', 'LINESTRING', 'MULTILINESTRING', 'POLYGON', 'MULTIPOLYGON', 'GEOMETRYCOLLECTION', 'RASTER');

-- CreateEnum
CREATE TYPE "update_frequency" AS ENUM ('realtime', 'daily', 'weekly', 'monthly', 'quarterly', 'yearly', 'irregular', 'static');

-- CreateEnum
CREATE TYPE "source_type" AS ENUM ('organization', 'portal', 'api', 'research_institution');

-- CreateEnum
CREATE TYPE "job_status" AS ENUM ('queued', 'processing', 'completed', 'failed', 'expired');

-- CreateTable
CREATE TABLE "sources" (
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "name" VARCHAR(255) NOT NULL,
    "acronym" VARCHAR(20),
    "source_type" "source_type" NOT NULL,
    "website" VARCHAR(500),
    "source_url" TEXT,
    "cnpj" VARCHAR(18),
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL,

    CONSTRAINT "sources_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "themes" (
    "id" SERIAL NOT NULL,
    "code" VARCHAR(30) NOT NULL,
    "name" VARCHAR(150) NOT NULL,
    "description" TEXT,
    "icon" VARCHAR(100),
    "sort_order" SMALLINT NOT NULL DEFAULT 0,
    "parent_id" INTEGER,

    CONSTRAINT "themes_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "datasets" (
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "source_id" UUID NOT NULL,
    "title" VARCHAR(500) NOT NULL,
    "slug" VARCHAR(255) NOT NULL,
    "description" TEXT,
    "status" "dataset_status" NOT NULL DEFAULT 'draft',
    "geometry_type" "geometry_type",
    "srid" INTEGER NOT NULL DEFAULT 4674,
    "uf_scope" CHAR(2)[],
    "tags" TEXT[] DEFAULT ARRAY[]::TEXT[],
    "featured" BOOLEAN NOT NULL DEFAULT false,
    "thumbnail_url" TEXT,
    "data_start_year" INTEGER,
    "data_end_year" INTEGER,
    "wms_enabled" BOOLEAN NOT NULL DEFAULT true,
    "wfs_enabled" BOOLEAN NOT NULL DEFAULT true,
    "mapserver_layer" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL,

    CONSTRAINT "datasets_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "dataset_themes" (
    "dataset_id" UUID NOT NULL,
    "theme_id" INTEGER NOT NULL,
    "is_primary" BOOLEAN NOT NULL DEFAULT false,

    CONSTRAINT "dataset_themes_pkey" PRIMARY KEY ("dataset_id","theme_id")
);

-- CreateTable
CREATE TABLE "dataset_versions" (
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "dataset_id" UUID NOT NULL,
    "version_tag" VARCHAR(50) NOT NULL,
    "version_num" INTEGER NOT NULL DEFAULT 1,
    "is_current" BOOLEAN NOT NULL DEFAULT true,
    "feature_count" BIGINT NOT NULL DEFAULT 0,
    "period_start" DATE,
    "period_end" DATE,
    "source_url" TEXT,
    "source_format" VARCHAR(30),
    "changelog" TEXT,
    "published_at" TIMESTAMPTZ,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "dataset_versions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "geo_features" (
    "id" BIGSERIAL NOT NULL,
    "version_id" UUID NOT NULL,
    "dataset_id" UUID NOT NULL,
    "nome" VARCHAR(500),
    "codigo" VARCHAR(100),
    "data_ref" DATE,
    "area_ha" DECIMAL(14,4),
    "properties" JSONB NOT NULL DEFAULT '{}',
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "geo_features_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "time_series_features" (
    "id" BIGSERIAL NOT NULL,
    "dataset_id" UUID NOT NULL,
    "captured_at" TIMESTAMPTZ NOT NULL,
    "properties" JSONB NOT NULL DEFAULT '{}',
    "biome" VARCHAR(50),
    "uf" CHAR(2),
    "municipality_code" VARCHAR(10),
    "uc_id" UUID,
    "ti_id" UUID,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "time_series_features_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "metadata" (
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "dataset_id" UUID NOT NULL,
    "language" VARCHAR(10) NOT NULL DEFAULT 'pt-BR',
    "license" VARCHAR(100) NOT NULL DEFAULT 'CC BY 4.0',
    "source_url" TEXT,
    "lineage" TEXT,
    "positional_accuracy" DECIMAL(10,2),
    "spatial_resolution" VARCHAR(50),
    "update_frequency" "update_frequency" NOT NULL DEFAULT 'irregular',
    "reference_date" DATE,
    "reference_date_end" DATE,
    "inde_compliant" BOOLEAN NOT NULL DEFAULT false,
    "inspire_compliant" BOOLEAN NOT NULL DEFAULT false,
    "keywords" TEXT[] DEFAULT ARRAY[]::TEXT[],
    "contact_name" VARCHAR(255),
    "contact_email" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL,

    CONSTRAINT "metadata_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "raster_layers" (
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "dataset_id" UUID NOT NULL,
    "tile_x" INTEGER NOT NULL,
    "tile_y" INTEGER NOT NULL,
    "overview_level" SMALLINT NOT NULL DEFAULT 0,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "raster_layers_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "analysis_jobs" (
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "status" "job_status" NOT NULL DEFAULT 'queued',
    "query_params" JSONB NOT NULL,
    "result" JSONB,
    "error_message" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "started_at" TIMESTAMPTZ,
    "finished_at" TIMESTAMPTZ,
    "expires_at" TIMESTAMPTZ NOT NULL,

    CONSTRAINT "analysis_jobs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "access_log" (
    "id" BIGSERIAL NOT NULL,
    "dataset_id" UUID,
    "version_id" UUID,
    "action" VARCHAR(50) NOT NULL,
    "format" VARCHAR(30),
    "row_count" INTEGER,
    "duration_ms" INTEGER,
    "ip_address" VARCHAR(45),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "access_log_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "schema_migrations" (
    "version" BIGINT NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    "applied_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "checksum" VARCHAR(64),

    CONSTRAINT "schema_migrations_pkey" PRIMARY KEY ("version")
);

-- CreateIndex
CREATE INDEX "sources_acronym_idx" ON "sources"("acronym");

-- CreateIndex
CREATE INDEX "sources_is_active_idx" ON "sources"("is_active");

-- CreateIndex
CREATE UNIQUE INDEX "themes_code_key" ON "themes"("code");

-- CreateIndex
CREATE INDEX "themes_parent_id_idx" ON "themes"("parent_id");

-- CreateIndex
CREATE UNIQUE INDEX "datasets_slug_key" ON "datasets"("slug");

-- CreateIndex
CREATE INDEX "datasets_status_idx" ON "datasets"("status");

-- CreateIndex
CREATE INDEX "datasets_source_id_idx" ON "datasets"("source_id");

-- CreateIndex
CREATE INDEX "datasets_featured_idx" ON "datasets"("featured");

-- CreateIndex
CREATE INDEX "dataset_themes_theme_id_idx" ON "dataset_themes"("theme_id");

-- CreateIndex
CREATE INDEX "dataset_versions_dataset_id_idx" ON "dataset_versions"("dataset_id");

-- CreateIndex
CREATE INDEX "dataset_versions_is_current_idx" ON "dataset_versions"("is_current");

-- CreateIndex
CREATE UNIQUE INDEX "dataset_versions_dataset_id_version_num_key" ON "dataset_versions"("dataset_id", "version_num");

-- CreateIndex
CREATE INDEX "geo_features_version_id_idx" ON "geo_features"("version_id");

-- CreateIndex
CREATE INDEX "geo_features_dataset_id_idx" ON "geo_features"("dataset_id");

-- CreateIndex
CREATE INDEX "geo_features_nome_idx" ON "geo_features"("nome");

-- CreateIndex
CREATE INDEX "geo_features_codigo_idx" ON "geo_features"("codigo");

-- CreateIndex
CREATE INDEX "time_series_features_dataset_id_idx" ON "time_series_features"("dataset_id");

-- CreateIndex
CREATE INDEX "time_series_features_captured_at_idx" ON "time_series_features"("captured_at");

-- CreateIndex
CREATE INDEX "time_series_features_biome_idx" ON "time_series_features"("biome");

-- CreateIndex
CREATE INDEX "time_series_features_uf_idx" ON "time_series_features"("uf");

-- CreateIndex
CREATE INDEX "time_series_features_uc_id_idx" ON "time_series_features"("uc_id");

-- CreateIndex
CREATE INDEX "time_series_features_ti_id_idx" ON "time_series_features"("ti_id");

-- CreateIndex
CREATE UNIQUE INDEX "metadata_dataset_id_key" ON "metadata"("dataset_id");

-- CreateIndex
CREATE INDEX "raster_layers_dataset_id_idx" ON "raster_layers"("dataset_id");

-- CreateIndex
CREATE UNIQUE INDEX "raster_layers_dataset_id_tile_x_tile_y_overview_level_key" ON "raster_layers"("dataset_id", "tile_x", "tile_y", "overview_level");

-- CreateIndex
CREATE INDEX "analysis_jobs_status_idx" ON "analysis_jobs"("status");

-- CreateIndex
CREATE INDEX "analysis_jobs_created_at_idx" ON "analysis_jobs"("created_at");

-- CreateIndex
CREATE INDEX "access_log_dataset_id_idx" ON "access_log"("dataset_id");

-- CreateIndex
CREATE INDEX "access_log_created_at_idx" ON "access_log"("created_at");

-- AddForeignKey
ALTER TABLE "themes" ADD CONSTRAINT "themes_parent_id_fkey" FOREIGN KEY ("parent_id") REFERENCES "themes"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "datasets" ADD CONSTRAINT "datasets_source_id_fkey" FOREIGN KEY ("source_id") REFERENCES "sources"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "dataset_themes" ADD CONSTRAINT "dataset_themes_dataset_id_fkey" FOREIGN KEY ("dataset_id") REFERENCES "datasets"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "dataset_themes" ADD CONSTRAINT "dataset_themes_theme_id_fkey" FOREIGN KEY ("theme_id") REFERENCES "themes"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "dataset_versions" ADD CONSTRAINT "dataset_versions_dataset_id_fkey" FOREIGN KEY ("dataset_id") REFERENCES "datasets"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "geo_features" ADD CONSTRAINT "geo_features_version_id_fkey" FOREIGN KEY ("version_id") REFERENCES "dataset_versions"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "time_series_features" ADD CONSTRAINT "time_series_features_dataset_id_fkey" FOREIGN KEY ("dataset_id") REFERENCES "datasets"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "metadata" ADD CONSTRAINT "metadata_dataset_id_fkey" FOREIGN KEY ("dataset_id") REFERENCES "datasets"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "raster_layers" ADD CONSTRAINT "raster_layers_dataset_id_fkey" FOREIGN KEY ("dataset_id") REFERENCES "datasets"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "access_log" ADD CONSTRAINT "access_log_dataset_id_fkey" FOREIGN KEY ("dataset_id") REFERENCES "datasets"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "access_log" ADD CONSTRAINT "access_log_version_id_fkey" FOREIGN KEY ("version_id") REFERENCES "dataset_versions"("id") ON DELETE SET NULL ON UPDATE CASCADE;


-- Colunas geometry em geo_features
ALTER TABLE "geo_features"
  ADD COLUMN "geom"            geometry,
  ADD COLUMN "geom_simplified" geometry,
  ADD COLUMN "centroid"        geometry(Point, 4674);

-- Coluna geometry em time_series_features
ALTER TABLE "time_series_features"
  ADD COLUMN "geom" geometry(Point, 4674);

-- Coluna bbox em datasets
ALTER TABLE "datasets"
  ADD COLUMN "bbox" geometry(Polygon, 4674);

-- Índices GIST/GIN/BRIN
CREATE INDEX "geo_features_geom_idx"            ON "geo_features" USING GIST ("geom");
CREATE INDEX "geo_features_geom_simplified_idx" ON "geo_features" USING GIST ("geom_simplified");
CREATE INDEX "geo_features_centroid_idx"         ON "geo_features" USING GIST ("centroid");
CREATE INDEX "geo_features_properties_idx"       ON "geo_features" USING GIN  ("properties");
CREATE INDEX "ts_features_geom_idx"              ON "time_series_features" USING GIST ("geom");
CREATE INDEX "ts_features_properties_idx"        ON "time_series_features" USING GIN  ("properties");
CREATE INDEX "datasets_bbox_idx"                 ON "datasets" USING GIST ("bbox");
CREATE INDEX "access_log_created_brin_idx"       ON "access_log" USING BRIN ("created_at");

-- Trigger: calcular area_ha, centroid e geom_simplified na inserção
CREATE OR REPLACE FUNCTION fn_geo_features_computed()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.geom IS NOT NULL THEN
    NEW.area_ha = ROUND((ST_Area(NEW.geom::geography) / 10000.0)::numeric, 4);
    NEW.centroid = ST_Centroid(NEW.geom);
    IF NEW.geom_simplified IS NULL THEN
      NEW.geom_simplified = ST_SimplifyPreserveTopology(NEW.geom, 0.0001);
    END IF;
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER "trg_geo_features_computed"
  BEFORE INSERT ON "geo_features"
  FOR EACH ROW EXECUTE FUNCTION fn_geo_features_computed();