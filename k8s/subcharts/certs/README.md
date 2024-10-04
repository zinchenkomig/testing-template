Checkout the tutorial for any questions:
https://cert-manager.io/docs/tutorials/acme/nginx-ingress/#step-5---deploy-cert-manager

Briefly:
Issuers are structures that issue new certificates. They look at the ingress annotations and try to make an ingress instance that confirms the domain ownership. After that the certificate is generated.
In annotations of main app in values.yaml we specified the issuer name - that is how issuer knows whom he controls.
Inside kubernetes cert-manager generation pipeline looks like this CertificateRequest -> Order -> Challenge -> Certificate -> secret

To recreate certificate we can delete zinchenkomig-back-tls, zinchenkomig-tls