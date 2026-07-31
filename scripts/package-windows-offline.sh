#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="$(awk -F'"' '/^VERSION = / {print $2; exit}' "${ROOT}/docker/taklite/taklite_service.py" | sed 's/^TAKlite //')"
IMAGE_NAME="${TAKLITE_WINDOWS_IMAGE:-taklite-taklite:offline}"
PLATFORM="${TAKLITE_WINDOWS_PLATFORM:-linux/amd64}"
OUT_DIR="${1:-${ROOT}/dist}"
mkdir -p "${OUT_DIR}"
OUT_DIR="$(cd "${OUT_DIR}" && pwd)"
PACKAGE_NAME="TAKlite-windows-docker-offline-v${VERSION}.zip"
STAGE="$(mktemp -d "${TMPDIR:-/tmp}/taklite-windows-offline.XXXXXX")"

cleanup() {
  rm -rf "${STAGE}"
}
trap cleanup EXIT

echo "[taklite-windows-package] Building frontend assets"
(cd "${ROOT}/frontend" && npm run build)

echo "[taklite-windows-package] Building ${IMAGE_NAME} for ${PLATFORM}"
docker build \
  --platform "${PLATFORM}" \
  --file "${ROOT}/docker/taklite/Dockerfile.runtime" \
  --tag "${IMAGE_NAME}" \
  "${ROOT}"

echo "[taklite-windows-package] Staging bundle"
mkdir -p "${STAGE}/TAKlite-windows-docker-offline/images"

rsync -a \
  --exclude '.git' \
  --exclude '.github' \
  --exclude '.DS_Store' \
  --exclude '.env' \
  --exclude '.gradle' \
  --exclude '__pycache__' \
  --exclude 'build' \
  --exclude 'frontend/node_modules' \
  --exclude 'plugins' \
  --exclude 'docs/plugin-controlled-delivery.md' \
  --exclude 'docs/wintak-plugin-api.md' \
  --exclude 'tests' \
  --exclude 'taklite/data' \
  --exclude 'taklite/packages' \
  --exclude 'taklite/certs' \
  --exclude 'taklite-admin' \
  --exclude 'dist' \
  --exclude '*.zip' \
  --exclude '*.tar' \
  --exclude '*.tar.gz' \
  "${ROOT}/" "${STAGE}/TAKlite-windows-docker-offline/"

echo "[taklite-windows-package] Saving Docker image"
docker save "${IMAGE_NAME}" --output "${STAGE}/TAKlite-windows-docker-offline/images/taklite-offline.tar"

echo "[taklite-windows-package] Creating ${OUT_DIR}/${PACKAGE_NAME}"
rm -f "${OUT_DIR}/${PACKAGE_NAME}"
(cd "${STAGE}" && zip -qr "${OUT_DIR}/${PACKAGE_NAME}" "TAKlite-windows-docker-offline")

echo "${OUT_DIR}/${PACKAGE_NAME}"
