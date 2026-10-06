output "app_url" {
  value = "http://localhost:8080"
}

output "kube_context" {
  value = "kind-${kind_cluster.this.name}"
}
