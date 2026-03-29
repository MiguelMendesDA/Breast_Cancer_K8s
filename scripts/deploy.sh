#!/bin/bash
# ===============================================
# deploy.sh – Helm Deployment
# ===============================================

set -e

# ----------------------------
# 1️⃣ Define image tag
# ----------------------------
TAG=${1:-$(git rev-parse --short=7 HEAD)}
echo "🚀 Deploying Helm chart with image tag: $TAG"

# ----------------------------
# 2️⃣ Helm variables
# ----------------------------
HELM_NAMESPACE="breast-cancer"
HELM_RELEASE="breast-cancer"
HELM_CHART="./helm-chart"

# ----------------------------
# 3️⃣ Ensure namespace exists
# ----------------------------
echo "📦 Ensuring namespace exists..."
kubectl create namespace "$HELM_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# ----------------------------
# 4️⃣ Ensure MySQL secret exists
# ----------------------------
echo "🔑 Ensuring MySQL secret exists..."
kubectl apply -f k8s/secrets/secrets.yaml -n "$HELM_NAMESPACE"

# ----------------------------
# 5️⃣ Clean old Jobs
# ----------------------------
echo "🧹 Cleaning old jobs..."
kubectl delete job populate-training-db -n "$HELM_NAMESPACE" --ignore-not-found
kubectl delete job breast-cancer-training -n "$HELM_NAMESPACE" --ignore-not-found

# ----------------------------
# 6️⃣ Deploy everything
# ----------------------------
echo "🛢 Deploying Jobs + API..."
helm upgrade --install "$HELM_RELEASE" "$HELM_CHART" \
  --namespace "$HELM_NAMESPACE" \
  --set image.populateDB="miguelmendesds/breast-cancer-populate-db:$TAG" \
  --set image.training="miguelmendesds/breast-cancer-train:$TAG" \
  --set image.serving="miguelmendesds/breast-cancer-serving:$TAG" \
  --set deployServing=true \
  --set createConfig=true \
  --wait

# ----------------------------
# 7️⃣ Wait for DB population job
# ----------------------------
echo "⏳ Waiting for populate-training-db..."
kubectl wait --for=condition=complete job/populate-training-db \
  -n "$HELM_NAMESPACE" --timeout=300s

# ----------------------------
# 8️⃣ Wait for training job
# ----------------------------
echo "⏳ Waiting for training job..."
kubectl wait --for=condition=complete job/breast-cancer-training \
  -n "$HELM_NAMESPACE" --timeout=600s || true

# ----------------------------
# 9️⃣ Check rollout for API
# ----------------------------
kubectl rollout status deployment/breast-cancer-serving -n "$HELM_NAMESPACE"

echo "✅ Deployment complete!"