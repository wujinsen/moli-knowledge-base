#!/usr/bin/env bash
# 在服务器上执行（root 或 sudo）
# 解决 chinese-classical-texts 403：目录 traversable + dist 可读
set -euo pipefail

DEPLOY_ROOT=/opt/chinese-classical-texts
DIST="${DEPLOY_ROOT}/dist"
NGINX_USER="${NGINX_USER:-www-data}"

mkdir -p "${DIST}"

# nginx 必须能「进入」/opt 下的每一层目录（至少 others 有 x）
chmod o+x /opt 2>/dev/null || true
chmod o+x "${DEPLOY_ROOT}"
chmod -R o+rX "${DIST}"

# 若仍 403，可改为 nginx 用户拥有 dist（二选一）
# chown -R "${NGINX_USER}:${NGINX_USER}" "${DIST}"

echo "检查部署目录："
ls -la "${DEPLOY_ROOT}" || true
echo "---"
if [[ -f "${DIST}/index.html" ]]; then
  echo "OK: ${DIST}/index.html 存在"
  head -c 80 "${DIST}/index.html"; echo
else
  echo "ERROR: 缺少 ${DIST}/index.html"
  echo "常见原因：rsync 目标写错，文件在 ${DEPLOY_ROOT}/ 而不是 ${DIST}/"
  echo "正确：rsync -av --delete dist/ user@host:${DIST}/"
  exit 1
fi

echo "以 nginx 用户测试读权限（Debian/Ubuntu 为 www-data）："
sudo -u "${NGINX_USER}" test -r "${DIST}/index.html" && echo "OK: www-data 可读" || echo "FAIL: www-data 不可读，执行 chown -R ${NGINX_USER}:${NGINX_USER} ${DIST}"
