# QuickStart
First things first you need pipx
```bash
sudo apt install pipx
```
Now you can install copier. We use it to make this template work.
```
pipx install copier
```
Now you can initialize your project.
```
mkdir myproject
cd myproject
copier copy https://github.com/zinchenkomig/base-users-template.git .
```
It will ask you to fill data for the project templates.
Now your template is good to go.

You need a k8s cluster. Since it's a small project I prefer using [k3s](https://k3s.io/) - a smaller version of k8s. It is easier to setup than k8s.
Check out documentation for k3s: https://docs.k3s.io/quick-start

To install it you just need to type:
```
curl -sfL https://get.k3s.io | sh -
```
And you also need to install helm.
```
curl https://baltocdn.com/helm/signing.asc | gpg --dearmor | sudo tee /usr/share/keyrings/helm.gpg > /dev/null
sudo apt-get install apt-transport-https --yes
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/helm.gpg] https://baltocdn.com/helm/stable/debian/ all main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list
sudo apt-get update
sudo apt-get install helm
```
When your k3s is ready it's time to set up the infrastructure.
Get all helm repositories required.
```
make repos
```
Deploy all services:
```
make all
```
Check the state using
```
kubectl get pods
```
When everything is running you can initialize grafana dashboards:
```
make grafana-init
```
## Additional Infra Set Up
1. [Vault](k8s/subcharts/vault/README.md)
2. [Cert-Manager](k8s/subcharts/certs/README.md)
3. [Minio](k8s/subcharts/minio-readme.md)

## Secrets Required
- `TESTING_TEMPLATE_S3_ACCESS_KEY` -- create through minio console 
- `TESTING_TEMPLATE_S3_SECRET_KEY` -- create through minio console
- `TESTING_TEMPLATE_TG_TOKEN` -- create with Telegram Botfather
- `TESTING_TEMPLATE_GMAIL_API_TOKEN` -- create with Google console

## Secrets for Github actions
- `KUBECONFIG` - copy it from the machine where your kuber is located and replace the 127.0.0.1 to the static IP of your kuber machine
- `DOCKER_USERNAME`
- `DOCKER_PASSWORD`

You also need to make a kubernetes secret with your docker credentials:
```
kubectl create secret docker-registry image-secrets --docker-server=cr.yandex --docker-username=<username> --docker-password=<password>
```
