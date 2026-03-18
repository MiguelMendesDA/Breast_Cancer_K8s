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
# 2️⃣ Create namespace
# ----------------------------
echo "📦 Applying namespace..."
kubectl apply -f k8s/config/namespace.yaml

# ----------------------------
# 3️⃣ Apply Secrets and ConfigMaps
# ----------------------------
echo "🔐 Applying Secrets..."
kubectl apply -f k8s/secrets/
echo "⚙️ Applying ConfigMaps..."
kubectl apply -f k8s/config/

# ----------------------------
# 4️⃣ Create Persistent Volumes
# ----------------------------
echo "💾 Applying Persistent Volumes..."
kubectl apply -f k8s/storage/

# ----------------------------
# 5️⃣ Deploy Database
# ----------------------------
echo "🛢 Deploying Database..."
kubectl apply -f k8s/db/

# ----------------------------
# 6️⃣ Apply Serving resources (Deployment, Service, Ingress)
# ----------------------------
echo "🔹 Updating serving resources..."
sed "s|IMAGE_TAG|$TAG|g" k8s/serving/deployment.yaml | kubectl apply -f -
kubectl apply -f k8s/serving/service.yaml
kubectl apply -f k8s/serving/ingress.yaml

kubectl rollout status deployment/breast-cancer-serving -n breast-cancer || exit 1

# ----------------------------
# 7️⃣ Re-run populate DB job
# ----------------------------
echo "🔹 Re-running populate DB job..."
kubectl delete job populate-training-db -n breast-cancer --ignore-not-found
sed "s|IMAGE_TAG|$TAG|g" k8s/training/populate-db-job.yaml | kubectl apply -f -

# ----------------------------
# 8️⃣ Re-run manual training job
# ----------------------------
echo "🔹 Re-running manual training job..."
kubectl delete job breast-cancer-training -n breast-cancer --ignore-not-found
sed "s|IMAGE_TAG|$TAG|g" k8s/training/job.yaml | kubectl apply -f -

# ----------------------------
# 9️⃣ Apply CronJob for automatic retraining
# ----------------------------
echo "🔄 Applying CronJob for scheduled retraining..."
kubectl delete cronjob breast-cancer-retrain -n breast-cancer --ignore-not-found
sed "s|IMAGE_TAG|$TAG|g" k8s/training/cronjob.yaml | kubectl apply -f -

echo "✅ Deployment complete!"