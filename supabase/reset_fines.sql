-- Remise à zéro de la saison. Les paiements sont supprimés avant les amendes.
-- À exécuter manuellement dans le SQL Editor Supabase uniquement si nécessaire.
begin;
delete from payments;
delete from fines;
commit;
