import { ValidationPipe } from '@nestjs/common';
import { NestFactory } from '@nestjs/core';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';
import { AppModule } from './app.module';
import { GlobalExceptionFilter } from './common/filters/http-exception.filter';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  app.setGlobalPrefix('api');

  // Filtro global de erros
  app.useGlobalFilters(new GlobalExceptionFilter());

  // Validação automática dos DTOs
  app.useGlobalPipes(
    new ValidationPipe({
      transform: true,
      whitelist: true,
      forbidNonWhitelisted: false,
    }),
  );

  // CORS
  app.enableCors({ origin: '*', methods: ['GET'] });

  // Swagger
  const config = new DocumentBuilder()
    .setTitle('PNIG — Plataforma Nacional de Inteligência Geoespacial')
    .setDescription(
      'API REST para acesso ao catálogo de dados geoespaciais públicos do Brasil. ' +
        'Dados servidos via WMS/WFS pelo GeoServer.',
    )
    .setVersion('1.0.0')
    .addTag('Datasets', 'Catálogo de camadas geoespaciais')
    .addTag('Themes', 'Temas temáticos')
    .build();

  const document = SwaggerModule.createDocument(app, config);
  SwaggerModule.setup('api/docs', app, document, {
    customSiteTitle: 'PNIG API Docs',
    swaggerOptions: { persistAuthorization: true },
  });

  const port = process.env.APP_PORT ?? 3000;
  await app.listen(port);
  console.log(`API:     http://localhost:${port}/api`);
  console.log(`Swagger: http://localhost:${port}/api/docs`);
}

bootstrap();
