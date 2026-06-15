# 部署说明

## 关键：上传的是 `dist/`，不是源码目录

| 错误做法 | 结果 |
|----------|------|
| 打包整个 `classical-novels/` 上传到 nginx root | 没有 `index.html` → **403** |
| 只上传 `_astro`、`.prerender`（构建中断） | 没有 `index.html` → **403** |
| zip 解压到 `/opt/chinese-classical-texts/` 而非 `.../dist/` | 路径不对 → **403/404** |

**正确**：nginx `root` 目录下**直接**有 `index.html`：

```
/opt/chinese-classical-texts/dist/index.html
/opt/chinese-classical-texts/dist/honglou/
/opt/chinese-classical-texts/dist/_astro/
...
```

---

## Windows 本机构建 + 打包

```powershell
cd D:\work\moli_project\moli-knowledge-base\chinese-classical-texts\apps\classical-novels
npm run pack
```

产物在 `release/classical-novels-dist-YYYY-MM-DD.tar.gz`。

---

## 上传到 EC2

```bash
# 服务器上清空旧的不完整产物
sudo rm -rf /opt/chinese-classical-texts/dist/*
sudo mkdir -p /opt/chinese-classical-texts/dist

# 上传 tar.gz 后解压到 dist（注意 -C 目标）
sudo tar -xzf classical-novels-dist-*.tar.gz -C /opt/chinese-classical-texts/dist/

# 校验
ls -la /opt/chinese-classical-texts/dist/index.html
curl -I -H "Host: chinese-classical-texts.wu-jinsen.com" http://127.0.0.1/
```

---

## 在 EC2 上直接构建（需 Node 18+）

```bash
cd ~/chinese-classical-texts/apps/classical-novels
npm install
npm run build          # 必须跑完，不要 Ctrl+C
ls dist/index.html     # 必须有
bash deploy/deploy.sh  # 同步到 /opt/chinese-classical-texts/dist
```

`dist/` 在 `.gitignore` 里，**git pull 不会带 index.html**，必须在某处执行 `npm run build`。
