# make up      create the cluster, install Argo CD and register the app
# make status  show what is running
# make argocd  open the Argo CD UI at https://localhost:8081
# make down    delete everything

KUBECTL = kubectl --context kind-house-split

.PHONY: up down status argocd

up:
	terraform -chdir=infra init
	terraform -chdir=infra apply -auto-approve
	@echo "App will be at http://localhost:8080 once Argo CD syncs (~1 min)"

down:
	terraform -chdir=infra destroy -auto-approve

status:
	$(KUBECTL) -n argocd get applications
	$(KUBECTL) -n house-split get pods,svc,pvc

argocd:
	@echo "user: admin"
	@echo "password: $$($(KUBECTL) -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d)"
	$(KUBECTL) -n argocd port-forward svc/argocd-server 8081:443
