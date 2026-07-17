import { Type } from 'class-transformer';
import { IsInt, IsOptional, IsString, Max, Min } from 'class-validator';

export class DatasetQueryDto {
  @IsOptional()
  @IsString()
  theme?: string; // filtrar por tema: ex: meio_ambiente

  @IsOptional()
  @IsString()
  search?: string; // busca por título ou descrição

  @IsOptional()
  @IsString()
  uf?: string; // filtrar por UF: ex: SP

  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  @Max(100)
  limit?: number = 20;

  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(0)
  offset?: number = 0;
}
