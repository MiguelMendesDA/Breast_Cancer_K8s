# ----------------------------
# deploy.sh
# Automatic deployment of 3 images on Minikube/Kubernetes
# ----------------------------

# Use the short git SHA as the tag if none is provided
if [ -z "$1" ]; then
  TAG=$(git rev-parse --short HEAD)
  echo "No tag provided. Using current git commit SHA: $TAG"
else
  TAG=$1
fi

echo "🚀 Deploying version: $TAG"

# ----------------------------
# 1️⃣ Update the Deployment (serving)
# ----------------------------
echo "🔹 Updating serving deployment..."
kubectl set image deployment/breast-cancer-serving \
  serving=miguelmendesds/breast-cancer-serving:$TAG \
  -n breast-cancer

kubectl rollout status deployment/breast-cancer-serving -n breast-cancer

# ----------------------------
# 2️⃣ Re-run the populate-db Job
# ----------------------------
echo "🔹 Re-running populate DB job..."
kubectl delete job populate-training-db -n breast-cancer --ignore-not-found

kubectl create job populate-training-db \
  --image=miguelmendesds/breast-cancer-populate-db:$TAG \
  -n breast-cancer

# ----------------------------
# 3️⃣ Re-run the training Job
# ----------------------------
echo "🔹 Re-running training job..."
kubectl delete job training-job -n breast-cancer --ignore-not-found

kubectl create job training-job \
  --image=miguelmendesds/breast-cancer-training:$TAG \
  -n breast-cancer

echo "✅ Deployment complete!"