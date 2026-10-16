# Unit 3 Capstone: Multi-Agent System

This project uses an orchestrator to route questions to a SQL agent, a document-retrieval agent, or both. The agents use Amazon Bedrock to generate responses, which the orchestrator combines into a final answer.

 Project structure

- `Source/orchestrator.py`: routes questions and combines agent responses
- `Source/agents/`: SQL and document-retrieval agents
- `Source/bedrock_client.py`: Bedrock model calls
- `Source/onnx_embed.py`: document embedding support
- `Source/tokenomics_logger.py`: token and cost logging
- `Source/lambda_handler.py`: Lambda handler code
- `Source/test_sql_validator.py`: SQL validator tests
- `evidence/`: test results and progress notes
- `reflection/`: project reflection
 Verified

- All five SQL validator tests passed.
- Three route-only checks selected the expected SQL, retrieval, and combined routes.
- The Bedrock connectivity test passed.
- `orchestrator.py` passed a Python syntax check.


Running the SQL validator tests

From the `Source` directory, run `python test_sql_validator.py`. The recorded result was five tests passed.