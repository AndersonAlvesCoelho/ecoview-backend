import { Test, TestingModule } from '@nestjs/testing';
import { PrismaService } from '../prisma/prisma.service';
import { ThemesService } from './themes.service';

const mockThemes = [
  {
    id:       1,
    code:     'meio_ambiente',
    name:     'Meio Ambiente',
    icon:     null,
    sortOrder: 1,
    parentId: null,
    datasetThemes: [
      { dataset: { status: 'published' } },
      { dataset: { status: 'published' } },
    ],
    children: [
      {
        id:       2,
        code:     'queimadas',
        name:     'Queimadas',
        icon:     null,
        datasetThemes: [{ dataset: { status: 'published' } }],
      },
    ],
  },
  {
    id:       3,
    code:     'limites',
    name:     'Limites Territoriais',
    icon:     null,
    sortOrder: 2,
    parentId: null,
    datasetThemes: [
      { dataset: { status: 'published' } },
    ],
    children: [],
  },
];

const mockPrismaService = {
  theme: {
    findMany: jest.fn(),
  },
};

describe('ThemesService', () => {
  let service: ThemesService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        ThemesService,
        { provide: PrismaService, useValue: mockPrismaService },
      ],
    }).compile();

    service = module.get<ThemesService>(ThemesService);
    jest.clearAllMocks();
  });

  describe('findAll', () => {
    it('deve retornar lista de temas raiz com contagem', async () => {
      mockPrismaService.theme.findMany.mockResolvedValue(mockThemes);

      const result = await service.findAll();

      expect(result).toHaveLength(2);
      expect(result[0].code).toBe('meio_ambiente');
      expect(result[0].datasetCount).toBe(2);
    });

    it('deve incluir subtemas', async () => {
      mockPrismaService.theme.findMany.mockResolvedValue(mockThemes);

      const result = await service.findAll();

      expect(result[0].children).toHaveLength(1);
      expect(result[0].children[0].code).toBe('queimadas');
    });

    it('deve contar datasets dos subtemas', async () => {
      mockPrismaService.theme.findMany.mockResolvedValue(mockThemes);

      const result = await service.findAll();

      expect(result[0].children[0].datasetCount).toBe(1);
    });

    it('deve retornar lista vazia quando nao ha temas', async () => {
      mockPrismaService.theme.findMany.mockResolvedValue([]);

      const result = await service.findAll();

      expect(result).toHaveLength(0);
    });

    it('deve buscar somente temas raiz (parentId null)', async () => {
      mockPrismaService.theme.findMany.mockResolvedValue([]);

      await service.findAll();

      expect(mockPrismaService.theme.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: { parentId: null },
        }),
      );
    });
  });
});