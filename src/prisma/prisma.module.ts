// =============================================================
// src/prisma/prisma.module.ts
// Módulo global — disponível em todo o projeto sem re-importar
// =============================================================
import { Global, Module } from '@nestjs/common';
import { PrismaService } from './prisma.service';

@Global()
@Module({
  providers: [PrismaService],
  exports: [PrismaService],
})
export class PrismaModule {}
