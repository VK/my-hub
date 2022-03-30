kubectl create -f pgdata-persistentvolumeclaim.yaml
kubectl create -f postgres-deployment.yaml
kubectl create -f postgres-service.yaml


kubectl create -f mongodb-persistentvolumeclaim.yaml
kubectl create -f mongodb-config-persistentvolumeclaim.yaml
kubectl create -f mongo-deployment.yaml
kubectl create -f mongo-service.yaml

kubectl create -f mongo-express-deployment.yaml
kubectl create -f mongo-express-service.yaml


kubectl create -f hub-cfg-secret.yaml
kubectl create -f hub-deployment.yaml
kubectl create -f hub-service.yaml


kubectl -n kube-system rollout restart deployment coredns

