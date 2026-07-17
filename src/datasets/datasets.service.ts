import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { DatasetQueryDto } from './dto/dataset-query.dto';

@Injectable()
export class DatasetsService {
  constructor(private readonly prisma: PrismaService) {}

  //  Lista todos os datasets publicados
  async findAll(query: DatasetQueryDto) {
    const { theme, search, uf, limit = 20, offset = 0 } = query;

    const where = {
      status: 'published' as const,
      ...(theme && {
        datasetThemes: { some: { theme: { code: theme } } },
      }),
      ...(uf && {
        ufScope: { has: uf.toUpperCase() },
      }),
      ...(search && {
        OR: [
          { title: { contains: search, mode: 'insensitive' as const } },
          { description: { contains: search, mode: 'insensitive' as const } },
        ],
      }),
    };

    const [datasets, total] = await Promise.all([
      this.prisma.dataset.findMany({
        where,
        select: {
          id: true,
          title: true,
          slug: true,
          description: true,
          geometryType: true,
          srid: true,
          ufScope: true,
          tags: true,
          featured: true,
          thumbnailUrl: true,
          dataStartYear: true,
          dataEndYear: true,
          wmsEnabled: true,
          wfsEnabled: true,
          mapserverLayer: true,
          createdAt: true,
          updatedAt: true,
          source: {
            select: { id: true, name: true, acronym: true, website: true },
          },
          datasetThemes: {
            select: {
              isPrimary: true,
              theme: {
                select: { id: true, code: true, name: true, icon: true },
              },
            },
            orderBy: { isPrimary: 'desc' },
          },
          versions: {
            where: { isCurrent: true },
            select: {
              id: true,
              versionTag: true,
              versionNum: true,
              featureCount: true,
              periodStart: true,
              periodEnd: true,
              sourceUrl: true,
              sourceFormat: true,
              publishedAt: true,
            },
            take: 1,
          },
          metadata: {
            select: {
              license: true,
              updateFrequency: true,
              spatialResolution: true,
              referenceDate: true,
              indeCompliant: true,
              keywords: true,
              contactName: true,
              contactEmail: true,
            },
          },
        },
        orderBy: [{ featured: 'desc' }, { title: 'asc' }],
        take: limit,
        skip: offset,
      }),
      this.prisma.dataset.count({ where }),
    ]);

    return {
      data: datasets.map(this.formatDataset.bind(this)),
      meta: { total, limit, offset, hasMore: offset + limit < total },
    };
  }

  //  Busca um dataset pelo slug
  async findBySlug(slug: string) {
    const dataset = await this.prisma.dataset.findUnique({
      where: { slug },
      include: {
        source: true,
        datasetThemes: {
          include: { theme: true },
          orderBy: { isPrimary: 'desc' },
        },
        versions: {
          orderBy: { versionNum: 'desc' },
          select: {
            id: true,
            versionTag: true,
            versionNum: true,
            isCurrent: true,
            featureCount: true,
            periodStart: true,
            periodEnd: true,
            sourceUrl: true,
            sourceFormat: true,
            changelog: true,
            publishedAt: true,
            createdAt: true,
          },
        },
        metadata: true,
      },
    });

    if (!dataset) {
      throw new NotFoundException(`Dataset '${slug}' não encontrado`);
    }

    if (dataset.status !== 'published') {
      throw new NotFoundException(`Dataset '${slug}' não está publicado`);
    }

    return this.formatDataset(dataset);
  }

  //  Lista versões de um dataset
  async findVersions(slug: string) {
    const dataset = await this.prisma.dataset.findUnique({
      where: { slug },
      select: { id: true, title: true, slug: true, status: true },
    });

    if (!dataset || dataset.status !== 'published') {
      throw new NotFoundException(`Dataset '${slug}' não encontrado`);
    }

    const versions = await this.prisma.datasetVersion.findMany({
      where: { datasetId: dataset.id },
      orderBy: { versionNum: 'desc' },
      select: {
        id: true,
        versionTag: true,
        versionNum: true,
        isCurrent: true,
        featureCount: true,
        periodStart: true,
        periodEnd: true,
        sourceUrl: true,
        sourceFormat: true,
        changelog: true,
        publishedAt: true,
        createdAt: true,
      },
    });

    return {
      dataset: { id: dataset.id, title: dataset.title, slug: dataset.slug },
      total: versions.length,
      versions: versions.map((v) => ({
        id: v.id,
        tag: v.versionTag,
        num: v.versionNum,
        isCurrent: v.isCurrent,
        featureCount: Number(v.featureCount),
        periodStart: v.periodStart,
        periodEnd: v.periodEnd,
        sourceUrl: v.sourceUrl,
        sourceFormat: v.sourceFormat,
        changelog: v.changelog,
        publishedAt: v.publishedAt,
        createdAt: v.createdAt,
      })),
    };
  }

  //  Formata o dataset para resposta
  formatDataset(dataset: any) {
    const geoserverUrl =
      process.env.GEOSERVER_URL ?? 'http://localhost:8080/geoserver';
    const layerName = dataset.mapserverLayer ?? dataset.slug;
    const currentVersion =
      dataset.versions?.find((v: any) => v.isCurrent) ?? dataset.versions?.[0];

    return {
      id: dataset.id,
      title: dataset.title,
      slug: dataset.slug,
      description: dataset.description,
      geometryType: dataset.geometryType,
      srid: dataset.srid,
      ufScope: dataset.ufScope,
      tags: dataset.tags,
      featured: dataset.featured,
      thumbnailUrl: dataset.thumbnailUrl,
      dataStartYear: dataset.dataStartYear,
      dataEndYear: dataset.dataEndYear,
      wms: dataset.wmsEnabled
        ? {
            enabled: true,
            url: `${geoserverUrl}/pnig/wms`,
            layer: `pnig:${layerName}`,
          }
        : null,
      wfs: dataset.wfsEnabled
        ? {
            enabled: true,
            url: `${geoserverUrl}/pnig/wfs`,
            layer: `pnig:${layerName}`,
          }
        : null,
      source: dataset.source
        ? {
            id: dataset.source.id,
            name: dataset.source.name,
            acronym: dataset.source.acronym,
            website: dataset.source.website,
          }
        : null,
      themes:
        dataset.datasetThemes?.map((dt: any) => ({
          id: dt.theme.id,
          code: dt.theme.code,
          name: dt.theme.name,
          icon: dt.theme.icon,
          isPrimary: dt.isPrimary,
        })) ?? [],
      currentVersion: currentVersion
        ? {
            id: currentVersion.id,
            tag: currentVersion.versionTag,
            num: currentVersion.versionNum,
            featureCount: Number(currentVersion.featureCount),
            periodStart: currentVersion.periodStart,
            periodEnd: currentVersion.periodEnd,
            sourceUrl: currentVersion.sourceUrl,
            sourceFormat: currentVersion.sourceFormat,
            publishedAt: currentVersion.publishedAt,
          }
        : null,
      versions:
        dataset.versions?.map((v: any) => ({
          id: v.id,
          tag: v.versionTag,
          num: v.versionNum,
          isCurrent: v.isCurrent,
          featureCount: Number(v.featureCount),
          periodStart: v.periodStart,
          periodEnd: v.periodEnd,
          changelog: v.changelog,
          publishedAt: v.publishedAt,
        })) ?? [],
      metadata: dataset.metadata
        ? {
            license: dataset.metadata.license,
            updateFrequency: dataset.metadata.updateFrequency,
            spatialResolution: dataset.metadata.spatialResolution,
            referenceDate: dataset.metadata.referenceDate,
            indeCompliant: dataset.metadata.indeCompliant,
            keywords: dataset.metadata.keywords,
            contact: {
              name: dataset.metadata.contactName,
              email: dataset.metadata.contactEmail,
            },
          }
        : null,
      createdAt: dataset.createdAt,
      updatedAt: dataset.updatedAt,
    };
  }
}
