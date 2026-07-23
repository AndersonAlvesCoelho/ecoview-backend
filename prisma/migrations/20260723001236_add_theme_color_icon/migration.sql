-- DropIndex
DROP INDEX "access_log_created_brin_idx";

-- DropIndex
DROP INDEX "datasets_bbox_idx";

-- DropIndex
DROP INDEX "geo_features_centroid_idx";

-- DropIndex
DROP INDEX "geo_features_geom_idx";

-- DropIndex
DROP INDEX "geo_features_geom_simplified_idx";

-- DropIndex
DROP INDEX "geo_features_properties_idx";

-- DropIndex
DROP INDEX "ts_features_geom_idx";

-- DropIndex
DROP INDEX "ts_features_properties_idx";

-- AlterTable
ALTER TABLE "datasets" ADD COLUMN     "color" VARCHAR(7);

-- AlterTable
ALTER TABLE "themes" ADD COLUMN     "color" VARCHAR(7);
