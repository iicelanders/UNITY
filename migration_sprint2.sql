-- =====================================================
-- UNITY — Sprint 2 Migration
-- Adds tour_completado column to perfiles table.
-- Run this in the Supabase SQL Editor.
-- =====================================================

ALTER TABLE perfiles
    ADD COLUMN IF NOT EXISTS tour_completado BOOLEAN NOT NULL DEFAULT FALSE;
