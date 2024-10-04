# Set Up Vault
You must be at vault directory to run the tutorial.
```
cd k8s/subcharts/vault
```
1. Install vault with helm
```bash
helm install vault hashicorp/vault --values vault-values.yaml
```

2. Initialize vault if needed and unseal it

```bash
kubectl exec --stdin=true --tty=true vault-0 -- vault operator init \
    -key-shares=1 \
    -key-threshold=1 \
    -format=json > cluster-keys.json
# get the root and unseal tokens    

kubectl exec --stdin=true --tty=true vault-0 -- vault operator unseal <unseal-token>
```

3. Initialize role with policy
First run:

```bash
kubectl exec --stdin=true --tty=true vault-0 -- env PASS_ENCODING=$(openssl rand -hex 32) /bin/sh
```

Then inside the vault shell login with root token

```bash
vault login
```

Then run these commands:
```bash
vault auth enable kubernetes
vault write auth/kubernetes/config \
	kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443"
vault secrets enable -path=main kv-v2
vault policy write dev - <<EOF
path "main/*" {
   capabilities = ["read"]
}
EOF
vault write auth/kubernetes/role/k8s_auth_role \
	bound_service_account_names=default \
	bound_service_account_namespaces=default \
	policies=dev \
	audience=vault \
	ttl=24h
vault kv put -mount=main testing_template TESTING_TEMPLATE_PASS_ENCODING_SECRET=$PASS_ENCODING
exit
```


4. Now we need to install the vault-secrets-operator
```bash
helm install vault-secrets-operator hashicorp/vault-secrets-operator --values vault-secrets-operator-values.yaml
```
5. Add service account for vault-secrets-operator to authenticate into vault and read secrets

```bash
kubectl apply -f vault-auth-static.yaml
kubectl apply -f vault-static-secret.yaml
```

6. Now you can login to your vault UI at http://vault.mikhailzinchenko.test using your root token from `cluster_keys.json`.
7. You can now store secrets at main/testing_template and they will be automatically sent to secretkv Kubernetes Secrets.
By default your backend application uses the contents of this Kubernetes Secret and mounts it as env variables.

