-- =============================================================
-- PNIG/EcoView — seed_themes.sql
-- Popular temas com hierarquia, color e icon
-- Rodar APÓS a migration add_theme_color_icon
-- =============================================================

-- -------------------------------------------------------------
-- 1. Atualizar temas existentes (id 1 e 2)
-- -------------------------------------------------------------
UPDATE themes SET
  icon      = 'trees',
  color     = '#006633',
  sort_order = 10
WHERE code = 'meio_ambiente';

UPDATE themes SET
  icon      = 'map',
  color     = '#339966',
  sort_order = 20
WHERE code = 'limites';

-- -------------------------------------------------------------
-- 2. Inserir temas raiz
-- -------------------------------------------------------------
INSERT INTO themes (code, name, icon, color, sort_order, parent_id)
VALUES
  ('territorio',     'Território',              'map',            '#339966', 10, NULL),
  ('populacao',      'População e Sociedade',   'users',          '#4f46e5', 30, NULL),
  ('infraestrutura', 'Infraestrutura',          'building',       '#CCCC33', 40, NULL),
  ('economia',       'Economia e Produção',     'bar-chart',      '#669933', 50, NULL),
  ('riscos',         'Riscos e Desastres',      'alert-triangle', '#c2410c', 60, NULL)
ON CONFLICT (code) DO UPDATE SET
  icon      = EXCLUDED.icon,
  color     = EXCLUDED.color,
  sort_order = EXCLUDED.sort_order;

-- -------------------------------------------------------------
-- 3. Atualizar parent_id do tema limites → territorio
-- -------------------------------------------------------------
UPDATE themes
SET parent_id = (SELECT id FROM themes WHERE code = 'territorio')
WHERE code = 'limites';

-- -------------------------------------------------------------
-- 4. Inserir subtemas de territorio
-- -------------------------------------------------------------
INSERT INTO themes (code, name, icon, color, sort_order, parent_id)
VALUES
  ('terras_indigenas', 'Terras Indígenas',         'shield', '#a86b2a', 21, (SELECT id FROM themes WHERE code = 'territorio')),
  ('quilombos',        'Territórios Quilombolas',  'shield', '#8b5e3c', 22, (SELECT id FROM themes WHERE code = 'territorio')),
  ('uc',               'Unidades de Conservação',  'shield', '#008a4b', 23, (SELECT id FROM themes WHERE code = 'territorio'))
ON CONFLICT (code) DO UPDATE SET
  icon      = EXCLUDED.icon,
  color     = EXCLUDED.color,
  sort_order = EXCLUDED.sort_order,
  parent_id  = EXCLUDED.parent_id;

-- -------------------------------------------------------------
-- 5. Inserir subtemas de meio_ambiente
-- -------------------------------------------------------------
INSERT INTO themes (code, name, icon, color, sort_order, parent_id)
VALUES
  ('biomas',        'Biomas e Vegetação',      'trees',          '#006633', 11, (SELECT id FROM themes WHERE code = 'meio_ambiente')),
  ('hidrografia',   'Recursos Hídricos',       'droplet',        '#0369a1', 12, (SELECT id FROM themes WHERE code = 'meio_ambiente')),
  ('queimadas',     'Queimadas e Fogo',        'flame',          '#c2410c', 13, (SELECT id FROM themes WHERE code = 'meio_ambiente')),
  ('desmatamento',  'Desmatamento',            'alert-triangle', '#7f1d1d', 14, (SELECT id FROM themes WHERE code = 'meio_ambiente')),
  ('clima',         'Clima e Meteorologia',    'cloud',          '#0284c7', 15, (SELECT id FROM themes WHERE code = 'meio_ambiente')),
  ('biodiversidade','Biodiversidade',          'leaf',           '#15803d', 16, (SELECT id FROM themes WHERE code = 'meio_ambiente'))
ON CONFLICT (code) DO UPDATE SET
  icon      = EXCLUDED.icon,
  color     = EXCLUDED.color,
  sort_order = EXCLUDED.sort_order,
  parent_id  = EXCLUDED.parent_id;

-- -------------------------------------------------------------
-- 6. Inserir subtemas de populacao
-- -------------------------------------------------------------
INSERT INTO themes (code, name, icon, color, sort_order, parent_id)
VALUES
  ('demografia', 'Demografia', 'users', '#4f46e5', 31, (SELECT id FROM themes WHERE code = 'populacao')),
  ('saude',      'Saúde',      'heart', '#dc2626', 32, (SELECT id FROM themes WHERE code = 'populacao')),
  ('educacao',   'Educação',   'book',  '#7c3aed', 33, (SELECT id FROM themes WHERE code = 'populacao'))
ON CONFLICT (code) DO UPDATE SET
  icon      = EXCLUDED.icon,
  color     = EXCLUDED.color,
  sort_order = EXCLUDED.sort_order,
  parent_id  = EXCLUDED.parent_id;

-- -------------------------------------------------------------
-- 7. Inserir subtemas de infraestrutura
-- -------------------------------------------------------------
INSERT INTO themes (code, name, icon, color, sort_order, parent_id)
VALUES
  ('transportes',  'Transportes', 'truck',    '#b45309', 41, (SELECT id FROM themes WHERE code = 'infraestrutura')),
  ('energia',      'Energia',     'zap',      '#ca8a04', 42, (SELECT id FROM themes WHERE code = 'infraestrutura')),
  ('saneamento',   'Saneamento',  'droplet',  '#0891b2', 43, (SELECT id FROM themes WHERE code = 'infraestrutura')),
  ('urbanizacao',  'Urbanização', 'building', '#6b7280', 44, (SELECT id FROM themes WHERE code = 'infraestrutura'))
ON CONFLICT (code) DO UPDATE SET
  icon      = EXCLUDED.icon,
  color     = EXCLUDED.color,
  sort_order = EXCLUDED.sort_order,
  parent_id  = EXCLUDED.parent_id;

-- -------------------------------------------------------------
-- 8. Inserir subtemas de economia
-- -------------------------------------------------------------
INSERT INTO themes (code, name, icon, color, sort_order, parent_id)
VALUES
  ('agricultura', 'Agricultura', 'wheat',  '#65a30d', 51, (SELECT id FROM themes WHERE code = 'economia')),
  ('uso_solo',    'Uso do Solo', 'layers', '#84cc16', 52, (SELECT id FROM themes WHERE code = 'economia')),
  ('mineracao',   'Mineração',   'hammer', '#78716c', 53, (SELECT id FROM themes WHERE code = 'economia'))
ON CONFLICT (code) DO UPDATE SET
  icon      = EXCLUDED.icon,
  color     = EXCLUDED.color,
  sort_order = EXCLUDED.sort_order,
  parent_id  = EXCLUDED.parent_id;

-- -------------------------------------------------------------
-- 9. Inserir subtemas de riscos
-- -------------------------------------------------------------
INSERT INTO themes (code, name, icon, color, sort_order, parent_id)
VALUES
  ('gestao_riscos',  'Gestão de Riscos',         'alert-triangle', '#dc2626', 61, (SELECT id FROM themes WHERE code = 'riscos')),
  ('enchentes',      'Enchentes e Alagamentos',  'droplet',        '#1d4ed8', 62, (SELECT id FROM themes WHERE code = 'riscos')),
  ('deslizamentos',  'Deslizamentos',             'mountain',       '#92400e', 63, (SELECT id FROM themes WHERE code = 'riscos'))
ON CONFLICT (code) DO UPDATE SET
  icon      = EXCLUDED.icon,
  color     = EXCLUDED.color,
  sort_order = EXCLUDED.sort_order,
  parent_id  = EXCLUDED.parent_id;

-- -------------------------------------------------------------
-- Verificar resultado
-- -------------------------------------------------------------
SELECT
  t.code,
  t.name,
  t.icon,
  t.color,
  t.sort_order,
  p.code AS parent_code
FROM themes t
LEFT JOIN themes p ON p.id = t.parent_id
ORDER BY t.sort_order, t.id;
