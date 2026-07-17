import { Controller, Get, HttpCode, HttpStatus } from '@nestjs/common';
import { ApiOperation, ApiResponse, ApiTags } from '@nestjs/swagger';
import { ThemesService } from './themes.service';

@ApiTags('Themes')
@Controller('themes')
export class ThemesController {
  constructor(private readonly themesService: ThemesService) {}

  @Get()
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ summary: 'Listar temas temáticos com contagem de datasets' })
  @ApiResponse({ status: 200, description: 'Lista de temas e subtemas' })
  findAll() {
    return this.themesService.findAll();
  }
}