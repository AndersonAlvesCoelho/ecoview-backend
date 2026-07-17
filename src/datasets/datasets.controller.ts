import {
  Controller,
  Get,
  HttpCode,
  HttpStatus,
  Param,
  Query,
} from '@nestjs/common';
import {
  ApiOperation,
  ApiParam,
  ApiQuery,
  ApiResponse,
  ApiTags,
} from '@nestjs/swagger';
import { DatasetsService } from './datasets.service';
import { DatasetQueryDto } from './dto/dataset-query.dto';

@ApiTags('Datasets')
@Controller('datasets')
export class DatasetsController {
  constructor(private readonly datasetsService: DatasetsService) {}

  @Get()
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ summary: 'Listar datasets publicados' })
  @ApiQuery({
    name: 'theme',
    required: false,
    description: 'Filtrar por código de tema. Ex: meio_ambiente',
  })
  @ApiQuery({
    name: 'search',
    required: false,
    description: 'Busca por título ou descrição',
  })
  @ApiQuery({
    name: 'uf',
    required: false,
    description: 'Filtrar por UF. Ex: SP',
  })
  @ApiQuery({
    name: 'limit',
    required: false,
    description: 'Itens por página (padrão: 20)',
  })
  @ApiQuery({
    name: 'offset',
    required: false,
    description: 'Offset para paginação (padrão: 0)',
  })
  @ApiResponse({
    status: 200,
    description: 'Lista de datasets com metadados e versão atual',
  })
  findAll(@Query() query: DatasetQueryDto) {
    return this.datasetsService.findAll(query);
  }

  @Get(':slug')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ summary: 'Detalhes de um dataset pelo slug' })
  @ApiParam({
    name: 'slug',
    description:
      'Slug único do dataset. Ex: biomas-sistema-costeiro-marinho-ibge-2025',
  })
  @ApiResponse({ status: 200, description: 'Detalhes completos do dataset' })
  @ApiResponse({ status: 404, description: 'Dataset não encontrado' })
  findOne(@Param('slug') slug: string) {
    return this.datasetsService.findBySlug(slug);
  }

  @Get(':slug/versions')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ summary: 'Listar versões de um dataset' })
  @ApiParam({ name: 'slug', description: 'Slug do dataset' })
  @ApiResponse({ status: 200, description: 'Lista de versões disponíveis' })
  @ApiResponse({ status: 404, description: 'Dataset não encontrado' })
  findVersions(@Param('slug') slug: string) {
    return this.datasetsService.findVersions(slug);
  }
}
