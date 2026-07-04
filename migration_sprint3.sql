-- =====================================================
-- UNITY — Sprint 3 Migration
-- Adds: cuadrillas, turnos, mensajes_chat tables
-- Modifies: perfiles (cuadrilla_id), alertas_sos (tipo_emergencia)
-- Run this in the Supabase SQL Editor.
-- =====================================================

-- 1. Cuadrillas (referenced by perfiles, turnos, mensajes_chat)
CREATE TABLE IF NOT EXISTS cuadrillas (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre_cuadrilla  TEXT NOT NULL
);

-- 2. Add cuadrilla_id to perfiles (nullable for MVP2→MVP3 migration)
ALTER TABLE perfiles
    ADD COLUMN IF NOT EXISTS cuadrilla_id UUID NULL REFERENCES cuadrillas(id);

-- 3. Turnos (schedule blocks linked to user + cuadrilla)
CREATE TABLE IF NOT EXISTS turnos (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id    UUID NOT NULL REFERENCES perfiles(id) ON DELETE CASCADE,
    cuadrilla_id  UUID NOT NULL REFERENCES cuadrillas(id) ON DELETE CASCADE,
    inicio_hora   TIMESTAMPTZ NOT NULL,
    fin_hora      TIMESTAMPTZ NOT NULL,
    dia_semana    INTEGER NOT NULL CHECK (dia_semana BETWEEN 0 AND 6)
);

-- 4. Mensajes de chat (linked to cuadrilla + sender)
CREATE TABLE IF NOT EXISTS mensajes_chat (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cuadrilla_id    UUID NOT NULL REFERENCES cuadrillas(id) ON DELETE CASCADE,
    usuario_id      UUID NOT NULL REFERENCES perfiles(id) ON DELETE CASCADE,
    texto_mensaje   TEXT NOT NULL,
    es_alerta       BOOLEAN NOT NULL DEFAULT FALSE,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 5. Add tipo_emergencia to alertas_sos
ALTER TABLE alertas_sos
    ADD COLUMN IF NOT EXISTS tipo_emergencia TEXT;

-- =====================================================
-- Row Level Security — same permissive policy as existing tables
-- =====================================================

ALTER TABLE cuadrillas ENABLE ROW LEVEL SECURITY;
CREATE POLICY "cuadrillas_auth" ON cuadrillas
    FOR ALL USING (auth.role() = 'authenticated')
    WITH CHECK (auth.role() = 'authenticated');

ALTER TABLE turnos ENABLE ROW LEVEL SECURITY;
CREATE POLICY "turnos_auth" ON turnos
    FOR ALL USING (auth.role() = 'authenticated')
    WITH CHECK (auth.role() = 'authenticated');

ALTER TABLE mensajes_chat ENABLE ROW LEVEL SECURITY;
CREATE POLICY "mensajes_chat_auth" ON mensajes_chat
    FOR ALL USING (auth.role() = 'authenticated')
    WITH CHECK (auth.role() = 'authenticated');

-- =====================================================
-- Seed — Two example cuadrillas
-- =====================================================

INSERT INTO cuadrillas (id, nombre_cuadrilla) VALUES
    ('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Cuadrilla Alpha'),
    ('b2c3d4e5-f6a7-8901-bcde-f12345678901', 'Cuadrilla Bravo')
ON CONFLICT (id) DO NOTHING;
