set -euo pipefail

REGION="us-east-1"
LAMBDA_NAME=""
OPENSEARCH_DOMAIN=""
EXECUTE=false

usage() {
  echo "Usage: ./teardown.sh [--lambda NAME] [--opensearch DOMAIN] [--execute]"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --lambda)
      [[ $# -ge 2 ]] || { usage; exit 1; }
      LAMBDA_NAME="$2"; shift 2 ;;
    --opensearch)
      [[ $# -ge 2 ]] || { usage; exit 1; }
      OPENSEARCH_DOMAIN="$2"; shift 2 ;;
    --execute)
      EXECUTE=true; shift ;;
    *)
      usage; echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$LAMBDA_NAME" && -z "$OPENSEARCH_DOMAIN" ]]; then
  usage
  echo "Provide at least one exact resource name. No account-wide scan is performed."
  exit 1
fi

if [[ -n "$LAMBDA_NAME" && ! "$LAMBDA_NAME" =~ ^[A-Za-z0-9_-]+$ ]]; then
  echo "Invalid Lambda name."; exit 1
fi

if [[ -n "$OPENSEARCH_DOMAIN" && ! "$OPENSEARCH_DOMAIN" =~ ^[a-z0-9-]+$ ]]; then
  echo "Invalid OpenSearch domain name."; exit 1
fi

echo "Region: $REGION"
echo "Planned targets:"
[[ -n "$LAMBDA_NAME" ]] && echo "  Lambda function: $LAMBDA_NAME"
[[ -n "$OPENSEARCH_DOMAIN" ]] && echo "  OpenSearch domain: $OPENSEARCH_DOMAIN"
echo "RDS, S3, Bedrock, and all other resources are not touched."

if [[ "$EXECUTE" != true ]]; then
  echo "Preview only. Nothing was deleted."
  echo "Review the names, then add --execute only when you're certain."
  exit 0
fi

command -v aws >/dev/null || { echo "AWS CLI not found."; exit 1; }
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "AWS account: $ACCOUNT_ID"
read -r -p 'Type DELETE to proceed: ' CONFIRM
[[ "$CONFIRM" == "DELETE" ]] || { echo "Cancelled."; exit 0; }

if [[ -n "$LAMBDA_NAME" ]]; then
  aws lambda delete-function \
    --function-name "$LAMBDA_NAME" \
    --region "$REGION"
fi

if [[ -n "$OPENSEARCH_DOMAIN" ]]; then
  aws opensearch delete-domain \
    --domain-name "$OPENSEARCH_DOMAIN" \
    --region "$REGION"
fi

echo "Delete requests submitted. AWS may take time to finish."