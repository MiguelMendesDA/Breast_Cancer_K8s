#!/bin/bash

# ----------------------------
# 1️⃣ Define tag
# ----------------------------
if [ -z "$1" ]; then
  TAG=$(git rev-parse --short=7 HEAD)
  echo "No tag provided. Using current git commit SHA: $TAG"
else
  TAG=$1
fi

echo "🚀 Deploying version: $TAG"

# ----------------------------
# 2️⃣ Update serving Deployment
# ----------------------------
echo "🔹 Updating serving deployment..."
sed "s|IMAGE_TAG|$TAG|g" k8s/serving/deployment.yaml | kubectl apply -f -
kubectl rollout status deployment/breast-cancer-serving -n breast-cancer || exit 1

# ----------------------------
# 3️⃣ Re-run populate DB job
# ----------------------------
echo "🔹 Re-running populate DB job..."
kubectl delete job populate-training-db -n breast-cancer --ignore-not-found
sed "s|IMAGE_TAG|$TAG|g" k8s/training/populate-db-job.yaml | kubectl apply -f -

# ----------------------------
# 4️⃣ Re-run training job
# ----------------------------
echo "🔹 Re-running training job..."
kubectl delete job breast-cancer-training -n breast-cancer --ignore-not-found
sed "s|IMAGE_TAG|$TAG|g" k8s/training/job.yaml | kubectl apply -f -

echo "✅ Deployment complete!"