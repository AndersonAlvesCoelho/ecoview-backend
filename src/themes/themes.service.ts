import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class ThemesService {
  constructor(private readonly prisma: PrismaService) { }

  // Lista todos os temas com contagem de datasets
  async findAll() {
    const themes = await this.prisma.theme.findMany({
      where: { parentId: null }, // só temas raiz
      include: {
        children: {
          include: {
            datasetThemes: {
              where: {
                dataset: { status: 'published' },
              },
            },
          },
        },
        datasetThemes: {
          where: {
            dataset: { status: 'published' },
          },
        },
      },
      orderBy: { sortOrder: 'asc' },
    });

    return themes.map((theme) => ({
      id: theme.id,
      code: theme.code,
      name: theme.name,
      icon: theme.icon,
      color: theme.color,
      datasetCount: theme.datasetThemes.length,
      children: theme.children.map((child) => ({
        id: child.id,
        code: child.code,
        name: child.name,
        icon: child.icon,
        color: child.color,
        datasetCount: child.datasetThemes.length,
      })),
    }));
  }
}