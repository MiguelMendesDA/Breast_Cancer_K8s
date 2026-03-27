#!/bin/bash
# ===============================================
# deploy.sh – Helm Chart Deployment for Breast Cancer App
# ===============================================

set -e

# ----------------------------
# 1️⃣ Define image tag
# ----------------------------
TAG=${1:-$(git rev-parse --short=7 HEAD)}
echo "🚀 Deploying Helm chart with image tag: $TAG"

# ----------------------------
# 2️⃣ Helm values
# ----------------------------
HELM_NAMESPACE="breast-cancer"
HELM_RELEASE="breast-cancer"
HELM_CHART="./helm-chart"

# ----------------------------
# 3️⃣ Load environment variables from root .env
# ----------------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_PATH="$SCRIPT_DIR/../.env"

if [ -f "$ENV_PATH" ]; then
  echo "📄 Loading environment variables from $ENV_PATH"
  export $(grep -v '^#' "$ENV_PATH" | xargs)
else
  echo "⚠️  .env file not found at $ENV_PATH"
fi

# Check required variables
if [ -z "$MYSQL_USER" ] || [ -z "$MYSQL_PASSWORD" ]; then
  echo "❌ ERROR: MYSQL_USER and MYSQL_PASSWORD must be set (from .env or environment)"
  exit 1
fi

# ----------------------------
# 4️⃣ Ensure namespace exists
# ----------------------------
echo "📦 Creating namespace if not exists..."
kubectl create namespace "$HELM_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# ----------------------------
# 5️⃣ Deploy DB and Training Jobs first
# ----------------------------
echo "🛢 Deploying database and training jobs..."
helm upgrade --install "$HELM_RELEASE" "$HELM_CHART" \
  --namespace "$HELM_NAMESPACE" \
  --set secrets.mysqlUser="$MYSQL_USER" \
  --set secrets.mysqlPassword="$MYSQL_PASSWORD" \
  --set image.populateDB="miguelmendesds/breast-cancer-populate-db:$TAG" \
  --set image.training="miguelmendesds/breast-cancer-train:$TAG" \
  --set deployServing=false

# Wait for populate DB job to complete
echo "⏳ Waiting for populate-training-db job to complete..."
kubectl wait --for=condition=complete job/populate-training-db -n "$HELM_NAMESPACE" --timeout=300s

# Wait for manual training job if it exists
echo "⏳ Waiting for breast-cancer-training job to complete..."
kubectl wait --for=condition=complete job/breast-cancer-training -n "$HELM_NAMESPACE" --timeout=600s || true

# ----------------------------
# 6️⃣ Deploy Serving API
# ----------------------------
echo "🔹 Deploying serving API..."
helm upgrade --install "$HELM_RELEASE" "$HELM_CHART" \
  --namespace "$HELM_NAMESPACE" \
  --set deployServing=true \
  --set image.serving="miguelmendesds/breast-cancer-serving:$TAG"

# ----------------------------
# 7️⃣ Check deployment status
# ----------------------------
kubectl rollout status deployment/breast-cancer-serving -n "$HELM_NAMESPACE"

echo "✅ Deployment complete!"