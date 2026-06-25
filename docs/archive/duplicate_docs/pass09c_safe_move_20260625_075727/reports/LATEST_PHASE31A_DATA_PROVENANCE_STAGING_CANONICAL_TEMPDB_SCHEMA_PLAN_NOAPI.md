# PHASE31A_DATA_PROVENANCE_STAGING_CANONICAL_TEMPDB_SCHEMA_PLAN_NOAPI

FINAL_GATE=ERROR_PHASE31A_DATA_PROVENANCE_STAGING_CANONICAL_TEMPDB_SCHEMA_PLAN_NOAPI
RC=1
ERROR=OperationalError('table provenance_validated_events_v1 has 11 columns but 10 values were supplied')

```
Traceback (most recent call last):
  File "/tmp/PHASE31A_DATA_PROVENANCE_STAGING_CANONICAL_TEMPDB_SCHEMA_PLAN_NOAPI.py", line 956, in <module>
    raise SystemExit(main())
                     ~~~~^^
  File "/tmp/PHASE31A_DATA_PROVENANCE_STAGING_CANONICAL_TEMPDB_SCHEMA_PLAN_NOAPI.py", line 599, in main
    create_temp_schema()
    ~~~~~~~~~~~~~~~~~~^^
  File "/tmp/PHASE31A_DATA_PROVENANCE_STAGING_CANONICAL_TEMPDB_SCHEMA_PLAN_NOAPI.py", line 437, in create_temp_schema
    cur.execute(
    ~~~~~~~~~~~^
        "INSERT INTO provenance_validated_events_v1 VALUES (?,?,?,?,?,?,?,?,?,?)",
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<12 lines>...
        )
        ^
    )
    ^
sqlite3.OperationalError: table provenance_validated_events_v1 has 11 columns but 10 values were supplied

```
PROMPT_RETURNED_NO_LOGOUT=1
