# Unit 3 Capstone: Multi-Agent System

T# Unit 3 Capstone: Multi-Agent System

This project uses an orchestrator to route questions to a SQL agent, a document-retrieval agent, or both. The project includes Amazon Bedrock model-call support, and the orchestrator combines agent responses.

## Project structure

- `Source/orchestrator.py`: routes questions and combines agent responses
- `Source/agents/`: SQL and document-retrieval agents
- `Source/bedrock_client.py`: Bedrock model calls
- `Source/onnx_embed.py`: document embedding support
- `Source/tokenomics_logger.py`: token and cost logging
- `Source/lambda_handler.py`: Lambda handler code
- `Source/test_sql_validator.py`: SQL validator tests
- `evidence/`: test results and progress notes
- `reflection/`: project reflection

## Individual resolutions

### Question routing

The orchestrator routes questions to the SQL agent, retrieval agent, or both. Three route-only checks selected the expected route for SQL, document-retrieval, and combined questions. These checks confirmed route selection, not complete end-to-end answers.

### SQL safety validation

The SQL agent validates generated queries before database execution. The five tests cover an allowed `SELECT`, a blocked destructive statement, an allowed `deleted_at` column, a stacked query containing a blocked keyword, and two `SELECT` statements separated by a semicolon. All five tests passed.

## Verified

- Three route-only checks selected the expected routes.
- All five SQL validator tests passed.
- The Bedrock connectivity test passed.
- `orchestrator.py` passed a Python syntax check.



## Running the SQL validator tests

From the `Source` directory, run `python test_sql_validator.py`. The recorded result was five tests passed.