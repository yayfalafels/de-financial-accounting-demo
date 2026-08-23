#!/usr/bin/env bash
# entrypoint.sh
# Role selector for docker/Dockerfile.spark: the same image is reused for
# spark-master, each spark-worker-*, and jupyter (see
# docs/features/03-dev-env-setup-spark-container.md -> Design -> docker image).
# SPARK_MODE picks the standalone-cluster process to launch in the
# foreground; anything else (e.g. the jupyter service's `command:`) is
# exec'd as-is.

set -euo pipefail

case "${SPARK_MODE:-}" in
  master)
    exec "${SPARK_HOME}/bin/spark-class" org.apache.spark.deploy.master.Master \
      --host 0.0.0.0 --port 7077 --webui-port 8080
    ;;
  worker)
    : "${SPARK_MASTER_URL:?SPARK_MASTER_URL must be set for SPARK_MODE=worker}"
    exec "${SPARK_HOME}/bin/spark-class" org.apache.spark.deploy.worker.Worker \
      --cores "${SPARK_WORKER_CORES:-2}" --memory "${SPARK_WORKER_MEMORY:-2G}" \
      "${SPARK_MASTER_URL}"
    ;;
  *)
    exec "$@"
    ;;
esac
