Routing checks
- “How many active projects do we have?” → sql
- “What is our onboarding process?” → retrieval
- “How many active projects do we have, and what is our onboarding policy?” → both

SQL validator checks: all 5 passed
- Valid SELECT allowed
- Destructive statement blocked
- deleted_at column allowed
- Stacked query with a blocked keyword blocked
- Two SELECT statements joined by a semicolon blocked

Bedrock test: passed

SQL validator tests
Command: python test_sql_validator.py (run from FinalCapstone/Source)
Result: Ran 5 tests in 0.000s
Cases: valid SELECT allowed; destructive statement blocked; deleted_at column allowed; stacked query with blocked keyword blocked; stacked SELECT statements blocked.
