# Batch 1 — architecture, permissions, data model

Copy the contents of this zip over the repo root (same folder structure).
It only ADDS files; nothing is overwritten and nothing needs deleting.

New files
  .gitattributes
  docs/02_architecture.md
  docs/04_permissions.md
  docs/06_data_model.md
  backend/scripts/route_access.py
  backend/scripts/schema_doc.py
  backend/tests/test_docs_match_code.py

No backend rebuild is needed (no application code changed). To run the new tests:
  cd backend ; pytest tests/test_docs_match_code.py

Do this FIRST, before `git add`:
  git restore .github        # your working tree lost .github/workflows/ci.yml
Then, once, after copying .gitattributes:
  git add --renormalize .    # removes the phantom CRLF "modified" files
