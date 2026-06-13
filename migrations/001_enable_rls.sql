-- Enable Row Level Security on all public tables
-- Run this in the Supabase SQL Editor (under Database > SQL Editor)
--
-- This backend uses Firebase auth + a service-role Postgres connection.
-- The service role automatically bypasses RLS, so the API continues to work.
-- RLS policies below only govern direct PostgREST/Supabase-client access.

-- ── 1. Enable RLS ─────────────────────────────────────────────────────────────

ALTER TABLE public.users              ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.foods              ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nutrition_logs     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.exercises          ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workout_plans      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workout_logs       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.diet_plans         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.body_measurements  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_articles ENABLE ROW LEVEL SECURITY;

-- ── 2. Public read-only reference tables ─────────────────────────────────────
-- exercises, workout_plans, knowledge_articles, foods are shared data.
-- Anyone (including anonymous) may SELECT; writes go through the API only.

DROP POLICY IF EXISTS "allow_public_read" ON public.exercises;
CREATE POLICY "allow_public_read" ON public.exercises
    FOR SELECT TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "allow_public_read" ON public.workout_plans;
CREATE POLICY "allow_public_read" ON public.workout_plans
    FOR SELECT TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "allow_public_read" ON public.knowledge_articles;
CREATE POLICY "allow_public_read" ON public.knowledge_articles
    FOR SELECT TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "allow_public_read" ON public.foods;
CREATE POLICY "allow_public_read" ON public.foods
    FOR SELECT TO anon, authenticated USING (true);

-- ── 3. User-specific tables — blocked for direct client access ────────────────
-- No policies are created for users, nutrition_logs, workout_logs,
-- body_measurements, or diet_plans.
-- With RLS enabled and no matching policy, all direct PostgREST/client
-- requests are denied. The backend service role bypasses this automatically.

-- ── 4. (Optional) Grant service_role explicit bypass ─────────────────────────
-- Supabase service_role already bypasses RLS by default, but this makes it
-- explicit and future-proof if the role grants change.

ALTER TABLE public.users              FORCE ROW LEVEL SECURITY;
ALTER TABLE public.nutrition_logs     FORCE ROW LEVEL SECURITY;
ALTER TABLE public.workout_logs       FORCE ROW LEVEL SECURITY;
ALTER TABLE public.body_measurements  FORCE ROW LEVEL SECURITY;
ALTER TABLE public.diet_plans         FORCE ROW LEVEL SECURITY;
