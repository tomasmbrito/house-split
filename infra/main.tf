terraform {
  required_version = ">= 1.6"

  required_providers {
    kind = {
      source  = "tehcyx/kind"
      version = "~> 0.11"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 3.0"
    }
  }
}

# local Kubernetes cluster (one node, runs inside Docker)
resource "kind_cluster" "this" {
  name           = "house-split"
  wait_for_ready = true

  kind_config {
    kind        = "Cluster"
    api_version = "kind.x-k8s.io/v1alpha4"

    node {
      role = "control-plane"

      # nodePort 30080 from k8s/service.yaml -> localhost:8080
      extra_port_mappings {
        container_port = 30080
        host_port      = 8080
      }
    }
  }
}

# helm connects to the kind cluster above
provider "helm" {
  kubernetes = {
    host                   = kind_cluster.this.endpoint
    client_certificate     = kind_cluster.this.client_certificate
    client_key             = kind_cluster.this.client_key
    cluster_ca_certificate = kind_cluster.this.cluster_ca_certificate
  }
}

# Argo CD from the official chart
resource "helm_release" "argocd" {
  name             = "argocd"
  repository       = "https://argoproj.github.io/argo-helm"
  chart            = "argo-cd"
  version          = "10.9.6"
  namespace        = "argocd"
  create_namespace = true
  # first install has to pull all the images
  timeout = 600

  values = [file("${path.module}/argocd-values.yaml")]
}

# our app, registered in Argo CD (see application.yaml)
resource "helm_release" "house_split_app" {
  name       = "house-split-app"
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argocd-apps"
  version    = "2.0.6"
  namespace  = "argocd"

  values = [file("${path.module}/application.yaml")]

  # needs the Application CRD that comes with Argo CD
  depends_on = [helm_release.argocd]
}
