-- =============================================================================
-- Grants for the Databricks App's service principal.
--
-- Replace <app-service-principal-id> with the application ID shown on the app's
-- page in the workspace (Apps > your app > Authorization / Overview).
-- Run this from a notebook or the SQL editor as a user who owns the catalog.
--
-- The SQL warehouse itself is granted separately: attach it as a resource on the
-- app's Edit page with permission "Can use". That grant is not expressible here.
-- =============================================================================

GRANT USE CATALOG ON CATALOG pvdaq_catalog TO `1b4cc676-eff2-4007-ae3d-5591bf180b61`;
GRANT USE SCHEMA  ON SCHEMA  pvdaq_catalog.gold TO `1b4cc676-eff2-4007-ae3d-5591bf180b61`;

GRANT SELECT ON TABLE pvdaq_catalog.gold.system_daily_performance
  TO `1b4cc676-eff2-4007-ae3d-5591bf180b61`;
GRANT SELECT ON TABLE pvdaq_catalog.gold.system_annual_performance
  TO `1b4cc676-eff2-4007-ae3d-5591bf180b61`;

-- Verify
SHOW GRANTS `1b4cc676-eff2-4007-ae3d-5591bf180b61` ON TABLE pvdaq_catalog.gold.system_daily_performance;