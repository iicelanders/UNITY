-- =====================================================
-- UNITY — Supabase Schema
-- Execute this in the Supabase SQL Editor once.
-- =====================================================

-- 1. Perfiles (linked to auth.users)
CREATE TABLE IF NOT EXISTS perfiles (
    id            UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    nombre_completo TEXT NOT NULL,
    habilidades   JSONB DEFAULT '[]',
    disponibilidad TEXT,
    rol           TEXT NOT NULL DEFAULT 'voluntario'
                  CHECK (rol IN ('voluntario', 'lider_cuadrilla', 'comando')),
    tour_completado BOOLEAN NOT NULL DEFAULT FALSE,
    creado_en     TIMESTAMPTZ DEFAULT now()
);

-- 2. Alertas SOS
CREATE TABLE IF NOT EXISTS alertas_sos (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id    UUID NOT NULL REFERENCES perfiles(id) ON DELETE CASCADE,
    latitud       NUMERIC(10, 6) NOT NULL,
    longitud      NUMERIC(10, 6) NOT NULL,
    resuelta      BOOLEAN NOT NULL DEFAULT false,
    fecha_alerta  TIMESTAMPTZ DEFAULT now()
);

-- 3. Inventario de herramientas
CREATE TABLE IF NOT EXISTS inventario_herramientas (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre_herramienta  TEXT NOT NULL,
    cantidad_total      INTEGER NOT NULL DEFAULT 0,
    cantidad_disponible INTEGER NOT NULL DEFAULT 0
);

-- 4. Entregas de material
CREATE TABLE IF NOT EXISTS entregas_material (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    herramienta_id    UUID NOT NULL REFERENCES inventario_herramientas(id),
    usuario_asignado  UUID NOT NULL REFERENCES perfiles(id),
    cantidad          INTEGER NOT NULL,
    fecha_entrega     TIMESTAMPTZ DEFAULT now()
);

-- =====================================================
-- Row Level Security (§6.11)
-- Permissive: all operations for authenticated users only.
-- =====================================================

ALTER TABLE perfiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "perfiles_auth" ON perfiles
    FOR ALL USING (auth.role() = 'authenticated')
    WITH CHECK (auth.role() = 'authenticated');

ALTER TABLE alertas_sos ENABLE ROW LEVEL SECURITY;
CREATE POLICY "alertas_auth" ON alertas_sos
    FOR ALL USING (auth.role() = 'authenticated')
    WITH CHECK (auth.role() = 'authenticated');

ALTER TABLE inventario_herramientas ENABLE ROW LEVEL SECURITY;
CREATE POLICY "inventario_auth" ON inventario_herramientas
    FOR ALL USING (auth.role() = 'authenticated')
    WITH CHECK (auth.role() = 'authenticated');

ALTER TABLE entregas_material ENABLE ROW LEVEL SECURITY;
CREATE POLICY "entregas_auth" ON entregas_material
    FOR ALL USING (auth.role() = 'authenticated')
    WITH CHECK (auth.role() = 'authenticated');
