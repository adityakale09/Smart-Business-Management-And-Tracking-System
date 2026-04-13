# Keep/Archive Cleanup Report

Date: 2026-04-13
Scope: low-risk cleanup only

## Keep (Core)

- `backend/app/**` core backend application code
- `frontend/src/**` core frontend application code
- `database/**` schema/init scripts
- `docs/API.md` API reference
- `backend/main.py` backend entrypoint
- `docker-compose.yml` container orchestration
- `README.md` project overview (updated to point to authoritative guide)
- `DEVELOPER_GUIDE.md` single authoritative setup/run guide
- `SETUP.md` retained as compatibility pointer doc (updated)
- Backend test scripts: `backend/test_new_endpoints.py`, `backend/test_validation.py`

## Archive (Low-Risk)

### Docs moved to `archive/docs/`

- `API_ENHANCEMENTS.md`
- `APPLICATION_RUNNING.md`
- `ENHANCEMENTS.md`
- `IMPLEMENTATION_CHECKLIST.md`
- `IMPROVEMENTS_COMPLETED.md`
- `INVENTORY_MODULE_IMPROVEMENTS.md`
- `INVENTORY_QUICK_REFERENCE.md`
- `PROJECT_UNDERSTANDING.md`
- `DOCKER.md`

### Scripts moved to `archive/scripts/`

- `docker-logs.ps1`
- `docker-start.ps1`
- `docker-stop.ps1`
- `reset_local_admin.py`
- `backend/analyze_table_usage.py`
- `backend/check_admin_state.py`
- `backend/check_status.py`
- `backend/check_users.py`
- `backend/debug_login.py`
- `backend/fix_admin.py`
- `backend/show_database_structure.py`
- `backend/verify_db_connection.py`
- `backend/verify_indexes.py`

## Notes

- No core app modules were removed.
- Existing uncommitted functional changes were not modified.
- Archive move is reversible via `git mv` history.
