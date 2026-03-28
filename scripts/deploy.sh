#!/bin/bash
# ===============================================
# deploy.sh – Helm Chart Deployment for Breast Cancer App (using Kubernetes Secrets)
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
# 5️⃣ Deploy DB + Training (Helm handles PVCs)
# ----------------------------
echo "🛢 Cleaning old jobs..."
kubectl delete job populate-training-db -n "$HELM_NAMESPACE" --ignore-not-found
kubectl delete job breast-cancer-training -n "$HELM_NAMESPACE" --ignore-not-found

echo "🛢 Deploying database and training jobs..."
helm upgrade --install "$HELM_RELEASE" "$HELM_CHART" \
  --namespace "$HELM_NAMESPACE" \
  --set image.populateDB="miguelmendesds/breast-cancer-populate-db:$TAG" \
  --set image.training="miguelmendesds/breast-cancer-train:$TAG" \
  --set deployServing=false \
  --wait

# ----------------------------
# 6️⃣ Wait for DB population job
# ----------------------------
echo "⏳ Waiting for populate-training-db job to complete..."
kubectl wait --for=condition=complete job/populate-training-db -n "$HELM_NAMESPACE" --timeout=300s

# ----------------------------
# 7️⃣ Wait for training job
# ----------------------------
echo "⏳ Waiting for breast-cancer-training job to complete..."
kubectl wait --for=condition=complete job/breast-cancer-training -n "$HELM_NAMESPACE" --timeout=600s || true

# ----------------------------
# 8️⃣ Deploy Serving API
# ----------------------------
echo "🔹 Deploying serving API..."
helm upgrade --install "$HELM_RELEASE" "$HELM_CHART" \
  --namespace "$HELM_NAMESPACE" \
  --set deployServing=true \
  --set image.serving="miguelmendesds/breast-cancer-serving:$TAG" \
  --wait

# ----------------------------
# 9️⃣ Check rollout
# ----------------------------
kubectl rollout status deployment/breast-cancer-serving -n "$HELM_NAMESPACE"

echo "✅ Deployment complete!"