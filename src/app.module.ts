// src/app.module.ts
import { Module } from '@nestjs/common';
import { PrismaModule } from './prisma/prisma.module';
import { DatasetsModule } from './datasets/datasets.module';
import { ThemesModule } from './themes/themes.module';

@Module({
  imports: [
    PrismaModule,
    DatasetsModule,
    ThemesModule,
  ],
})
export class AppModule { }
