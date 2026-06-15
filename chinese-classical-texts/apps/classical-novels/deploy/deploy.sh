#!/usr/bin/env bash
# 在 apps/classical-novels 目录执行：构建并部署到 /opt/chinese-classical-texts/dist
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
DEPLOY_DIST="${DEPLOY_DIST:-/opt/chinese-classical-texts/dist}"

cd "${APP_DIR}"

echo "==> npm run build"
npm run build

if [[ ! -f dist/index.html ]]; then
  echo "ERROR: 构建失败，dist/index.html 不存在"
  exit 1
fi

echo "==> 同步到 ${DEPLOY_DIST}"
mkdir -p "${DEPLOY_DIST}"
rsync -av --delete dist/ "${DEPLOY_DIST}/"

echo "==> 校验"
test -f "${DEPLOY_DIST}/index.html"
test -d "${DEPLOY_DIST}/honglou"
echo "OK: index.html + honglou/ 已就位"
ls -la "${DEPLOY_DIST}/" | head -10
