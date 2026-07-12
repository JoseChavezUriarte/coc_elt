terraform {
  # PASO 1 (Bootstrap): Comenta el bloque "gcs" durante el despliegue inicial con estado local.
  # PASO 2 (Migración): Descomenta este bloque e inicializa de nuevo (terraform init -migrate-state) para subir el estado al bucket creado.
  # backend "gcs" {
  # }
}
