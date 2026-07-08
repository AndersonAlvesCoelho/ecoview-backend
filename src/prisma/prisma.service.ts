import { Injectable, OnModuleInit, OnModuleDestroy, Logger } from '@nestjs/common';
// eslint-disable-next-line @typescript-eslint/no-require-imports
const { PrismaClient } = require('@prisma/client') as typeof import('@prisma/client');
 
type PrismaClientType = InstanceType<typeof PrismaClient>;
 
@Injectable()
export class PrismaService implements OnModuleInit, OnModuleDestroy {
  private readonly logger = new Logger(PrismaService.name);
  private readonly prisma: PrismaClientType;
 
  constructor() {
    this.prisma = new PrismaClient({
      log: process.env.NODE_ENV === 'development' ? ['warn', 'error'] : ['error'],
    });
  }
 
  async onModuleInit(): Promise<void> {
    await this.prisma.$connect();
    this.logger.log('✅ Prisma conectado ao PostgreSQL + PostGIS');
  }
 
  async onModuleDestroy(): Promise<void> {
    await this.prisma.$disconnect();
  }
 
  // ── Acesso aos models ──────────────────────────────────────
  get source()            { return this.prisma.source; }
  get theme()             { return this.prisma.theme; }
  get dataset()           { return this.prisma.dataset; }
  get datasetTheme()      { return this.prisma.datasetTheme; }
  get datasetVersion()    { return this.prisma.datasetVersion; }
  get geoFeature()        { return this.prisma.geoFeature; }
  get timeSeriesFeature() { return this.prisma.timeSeriesFeature; }
  get metadata()          { return this.prisma.metadata; }
  get rasterLayer()       { return this.prisma.rasterLayer; }
  get analysisJob()       { return this.prisma.analysisJob; }
  get accessLog()         { return this.prisma.accessLog; }
  get schemaMigration()   { return this.prisma.schemaMigration; }
 
  // ── Raw queries PostGIS ────────────────────────────────────
  get $queryRaw()   { return this.prisma.$queryRaw.bind(this.prisma); }
  get $executeRaw() { return this.prisma.$executeRaw.bind(this.prisma); }
  get $transaction(){ return this.prisma.$transaction.bind(this.prisma); }
}
 




