#!/bin/bash
# ===============================================
# deploy.sh – Helm Chart Deployment for Breast Cancer App
# ===============================================

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
# 3️⃣ Validate required env vars
# ----------------------------
if [[ -z "$MYSQL_USER" || -z "$MYSQL_PASSWORD" ]]; then
  echo "❌ ERROR: MYSQL_USER and MYSQL_PASSWORD must be set"
  exit 1
fi

# ----------------------------
# 4️⃣ Deploy / Upgrade with Helm
# ----------------------------
helm upgrade --install "$HELM_RELEASE" "$HELM_CHART" \
  --namespace "$HELM_NAMESPACE" \
  --create-namespace \
  --set secrets.mysqlUser="$MYSQL_USER" \
  --set secrets.mysqlPassword="$MYSQL_PASSWORD" \
  --set image.populateDB="miguelmendesds/breast-cancer-populate-db:$TAG" \
  --set image.training="miguelmendesds/breast-cancer-train:$TAG" \
  --set image.serving="miguelmendesds/breast-cancer-serving:$TAG"

# ----------------------------
# 5️⃣ Check deployment status
# ----------------------------
kubectl rollout status deployment/breast-cancer-serving -n "$HELM_NAMESPACE"

echo "✅ Deployment complete!"