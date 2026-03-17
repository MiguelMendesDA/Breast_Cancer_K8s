#!/bin/bash

if [ -z "$1" ]; then
  TAG=$(git rev-parse --short HEAD)
  echo "No tag provided. Using current git commit SHA: $TAG"
else
  TAG=$1
fi

echo "🚀 Deploying version: $TAG"

# ----------------------------
# 1️⃣ Update Deployment
# ----------------------------
echo "🔹 Updating serving deployment..."
kubectl set image deployment/breast-cancer-serving \
  serving=miguelmendesds/breast-cancer-serving:$TAG \
  -n breast-cancer

kubectl rollout status deployment/breast-cancer-serving -n breast-cancer || exit 1

# ----------------------------
# 2️⃣ Re-run populate DB job
# ----------------------------
echo "🔹 Re-running populate DB job..."
kubectl delete job populate-training-db -n breast-cancer --ignore-not-found
kubectl apply -f k8s/training/populate-db-job.yaml

# ----------------------------
# 3️⃣ Re-run training job
# ----------------------------
echo "🔹 Re-running training job..."
kubectl delete job breast-cancer-training -n breast-cancer --ignore-not-found
kubectl apply -f k8s/training/job.yaml

echo "✅ Deployment complete!"