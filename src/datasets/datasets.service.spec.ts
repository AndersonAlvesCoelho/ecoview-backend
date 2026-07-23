import { NotFoundException } from '@nestjs/common';
import { Test, TestingModule } from '@nestjs/testing';
import { PrismaService } from '../prisma/prisma.service';
import { DatasetsService } from './datasets.service';

// Mock do PrismaService
const mockDataset = {
  id: 'uuid-biomas',
  title: 'Biomas e Sistema Costeiro-Marinho do Brasil',
  slug: 'biomas-sistema-costeiro-marinho-ibge-2025',
  description: 'Biomas terrestres do Brasil.',
  geometryType: 'MULTIPOLYGON',
  srid: 4674,
  ufScope: [],
  tags: ['bioma', 'ibge'],
  featured: false,
  thumbnailUrl: null,
  dataStartYear: null,
  dataEndYear: null,
  wmsEnabled: true,
  wfsEnabled: true,
  mapserverLayer: 'biomas_ibge_2025',
  status: 'published',
  createdAt: new Date('2026-01-01'),
  updatedAt: new Date('2026-01-01'),
  source: {
    id: 'uuid-ibge',
    name: 'Instituto Brasileiro de Geografia e Estatística',
    acronym: 'IBGE',
    website: 'https://www.ibge.gov.br',
  },
  datasetThemes: [
    {
      isPrimary: true,
      theme: {
        id: 1,
        code: 'meio_ambiente',
        name: 'Meio Ambiente',
        icon: null,
        theme: null,
      },
    },
  ],
  versions: [
    {
      id: 'uuid-version-2025',
      versionTag: '2025',
      versionNum: 1,
      isCurrent: true,
      featureCount: BigInt(6),
      periodStart: null,
      periodEnd: null,
      sourceUrl: 'https://geoftp.ibge.gov.br/...',
      sourceFormat: 'shapefile',
      changelog: null,
      publishedAt: new Date('2026-01-01'),
      createdAt: new Date('2026-01-01'),
    },
  ],
  metadata: {
    license: 'CC BY 4.0',
    updateFrequency: 'irregular',
    spatialResolution: '1:250.000',
    referenceDate: new Date('2025-01-01'),
    indeCompliant: true,
    keywords: ['bioma', 'ibge'],
    contactName: null,
    contactEmail: null,
  },
};

const mockPrismaService = {
  dataset: {
    findMany: jest.fn(),
    findUnique: jest.fn(),
    count: jest.fn(),
  },
  datasetVersion: {
    findMany: jest.fn(),
  },
};

describe('DatasetsService', () => {
  let service: DatasetsService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        DatasetsService,
        { provide: PrismaService, useValue: mockPrismaService },
      ],
    }).compile();

    service = module.get<DatasetsService>(DatasetsService);
    jest.clearAllMocks();
  });

  // findAll
  describe('findAll', () => {
    it('deve retornar lista paginada de datasets', async () => {
      mockPrismaService.dataset.findMany.mockResolvedValue([mockDataset]);
      mockPrismaService.dataset.count.mockResolvedValue(1);

      const result = await service.findAll({ limit: 20, offset: 0 });

      expect(result.data).toHaveLength(1);
      expect(result.meta.total).toBe(1);
      expect(result.meta.hasMore).toBe(false);
      expect(result.data[0].slug).toBe(
        'biomas-sistema-costeiro-marinho-ibge-2025',
      );
    });

    it('deve filtrar por tema', async () => {
      mockPrismaService.dataset.findMany.mockResolvedValue([mockDataset]);
      mockPrismaService.dataset.count.mockResolvedValue(1);

      await service.findAll({ theme: 'meio_ambiente', limit: 20, offset: 0 });

      expect(mockPrismaService.dataset.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: expect.objectContaining({
            datasetThemes: { some: { theme: { code: 'meio_ambiente' } } },
          }),
        }),
      );
    });

    it('deve filtrar por UF em maiusculo', async () => {
      mockPrismaService.dataset.findMany.mockResolvedValue([]);
      mockPrismaService.dataset.count.mockResolvedValue(0);

      await service.findAll({ uf: 'sp', limit: 20, offset: 0 });

      expect(mockPrismaService.dataset.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: expect.objectContaining({
            ufScope: { has: 'SP' },
          }),
        }),
      );
    });

    it('deve respeitar paginacao', async () => {
      mockPrismaService.dataset.findMany.mockResolvedValue([]);
      mockPrismaService.dataset.count.mockResolvedValue(50);

      const result = await service.findAll({ limit: 10, offset: 20 });

      expect(result.meta.hasMore).toBe(true);
      expect(mockPrismaService.dataset.findMany).toHaveBeenCalledWith(
        expect.objectContaining({ take: 10, skip: 20 }),
      );
    });

    it('deve incluir wms e wfs no retorno', async () => {
      mockPrismaService.dataset.findMany.mockResolvedValue([mockDataset]);
      mockPrismaService.dataset.count.mockResolvedValue(1);

      const result = await service.findAll({ limit: 20, offset: 0 });
      const dataset = result.data[0];

      expect(dataset.wms).not.toBeNull();
      expect(dataset.wms?.layer).toBe('ecoview:biomas_ibge_2025');
      expect(dataset.wfs).not.toBeNull();
    });
  });

  // findBySlug
  describe('findBySlug', () => {
    it('deve retornar dataset pelo slug', async () => {
      mockPrismaService.dataset.findUnique.mockResolvedValue(mockDataset);

      const result = await service.findBySlug(
        'biomas-sistema-costeiro-marinho-ibge-2025',
      );

      expect(result.slug).toBe('biomas-sistema-costeiro-marinho-ibge-2025');
      expect(result.source?.acronym).toBe('IBGE');
      expect(result.themes).toHaveLength(1);
      expect(result.themes[0].isPrimary).toBe(true);
    });

    it('deve lancar NotFoundException para slug inexistente', async () => {
      mockPrismaService.dataset.findUnique.mockResolvedValue(null);

      await expect(service.findBySlug('nao-existe')).rejects.toThrow(
        NotFoundException,
      );
    });

    it('deve lancar NotFoundException para dataset nao publicado', async () => {
      mockPrismaService.dataset.findUnique.mockResolvedValue({
        ...mockDataset,
        status: 'draft',
      });

      await expect(
        service.findBySlug('biomas-sistema-costeiro-marinho-ibge-2025'),
      ).rejects.toThrow(NotFoundException);
    });

    it('deve retornar versao atual corretamente', async () => {
      mockPrismaService.dataset.findUnique.mockResolvedValue(mockDataset);

      const result = await service.findBySlug(
        'biomas-sistema-costeiro-marinho-ibge-2025',
      );

      expect(result.currentVersion).not.toBeNull();
      expect(result.currentVersion?.tag).toBe('2025');
      expect(result.currentVersion?.featureCount).toBe(6);
    });

    it('deve converter featureCount de BigInt para number', async () => {
      mockPrismaService.dataset.findUnique.mockResolvedValue(mockDataset);

      const result = await service.findBySlug(
        'biomas-sistema-costeiro-marinho-ibge-2025',
      );

      expect(typeof result.currentVersion?.featureCount).toBe('number');
    });
  });

  // findVersions
  describe('findVersions', () => {
    it('deve retornar versoes de um dataset', async () => {
      mockPrismaService.dataset.findUnique.mockResolvedValue({
        id: 'uuid-biomas',
        title: 'Biomas',
        slug: 'biomas-sistema-costeiro-marinho-ibge-2025',
        status: 'published',
      });
      mockPrismaService.datasetVersion.findMany.mockResolvedValue([
        {
          id: 'uuid-v1',
          versionTag: '2025',
          versionNum: 1,
          isCurrent: true,
          featureCount: BigInt(6),
          periodStart: null,
          periodEnd: null,
          sourceUrl: 'https://geoftp.ibge.gov.br/...',
          sourceFormat: 'shapefile',
          changelog: null,
          publishedAt: new Date('2026-01-01'),
          createdAt: new Date('2026-01-01'),
        },
      ]);

      const result = await service.findVersions(
        'biomas-sistema-costeiro-marinho-ibge-2025',
      );

      expect(result.total).toBe(1);
      expect(result.versions[0].tag).toBe('2025');
      expect(result.versions[0].isCurrent).toBe(true);
    });

    it('deve lancar NotFoundException para dataset inexistente', async () => {
      mockPrismaService.dataset.findUnique.mockResolvedValue(null);

      await expect(service.findVersions('nao-existe')).rejects.toThrow(
        NotFoundException,
      );
    });
  });

  // formatDataset
  describe('formatDataset', () => {
    it('deve retornar null para wms quando wmsEnabled = false', () => {
      const result = service.formatDataset({
        ...mockDataset,
        wmsEnabled: false,
      });
      expect(result.wms).toBeNull();
    });

    it('deve retornar null para wfs quando wfsEnabled = false', () => {
      const result = service.formatDataset({
        ...mockDataset,
        wfsEnabled: false,
      });
      expect(result.wfs).toBeNull();
    });

    it('deve retornar metadata formatado corretamente', () => {
      const result = service.formatDataset(mockDataset);
      expect(result.metadata?.license).toBe('CC BY 4.0');
      expect(result.metadata?.indeCompliant).toBe(true);
      expect(result.metadata?.contact).toEqual({ name: null, email: null });
    });
  });
});
