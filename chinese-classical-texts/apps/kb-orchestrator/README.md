# kb-orchestrator

维护台 API（Studio）— 为 `classical-novels` 站点提供上下文组装、聊天 SSE、变更 proposal。

## 启动

```bash
cd chinese-classical-texts/apps/kb-orchestrator
pip install -r requirements.txt
cp .env.example .env   # 填入 STUDIO_LLM_API_KEY
# NOVELS_ROOT 默认指向 ../classical-novels
python -m uvicorn kb_orchestrator.main:app --reload --port 8787
```

或在 `classical-novels` 目录：

```bash
npm run studio:api
npm run dev   # Astro 代理 /api/studio → :8787
```

## 健康检查

```bash
curl http://127.0.0.1:8787/api/studio/health
```

## 写盘（Phase 1）

- `PATCH apply` 解析 unified diff 写入 `src/content/`、`src/data/`
- 自动追加 `<书>.log.md`（`postApply.logEntry`）
- 顺序执行 `postApply.scripts`（cwd = classical-novels）
- 环境变量 `STUDIO_DRY_RUN=1` 可预览不写盘

## 批处理

```bash
# /lint 体检（只读）
curl http://127.0.0.1:8787/api/studio/lint/honglou

# /graph 预览（不写盘）
curl http://127.0.0.1:8787/api/studio/graph/honglou

# /graph 重建 relations.json
curl -X POST http://127.0.0.1:8787/api/studio/graph/honglou \
  -H "Content-Type: application/json" \
  -d "{\"confirm\":true}"

# /dream tier 目录
curl http://127.0.0.1:8787/api/studio/dream/honglou

# /dream tier14 dry-run 预览
curl http://127.0.0.1:8787/api/studio/dream/honglou/tier14

# /dream tier14 应用（写盘 + postApply）
curl -X POST http://127.0.0.1:8787/api/studio/dream/honglou/tier14 \
  -H "Content-Type: application/json" \
  -d "{\"confirm\":true}"

# /guard Trust Guard
curl http://127.0.0.1:8787/api/studio/guard/honglou

# /ingest 第73回摄取清单（只读）
curl "http://127.0.0.1:8787/api/studio/ingest/honglou/73?edition=chenggao"

# 待办聚合（crosslinks + ingest + 低密度）
curl http://127.0.0.1:8787/api/studio/todos/honglou
```

## 创建会话（贾迎春）

```bash
curl -X POST http://127.0.0.1:8787/api/studio/sessions \
  -H "Content-Type: application/json" \
  -d "{\"book\":\"红楼梦\",\"bookSlug\":\"honglou\",\"page\":{\"kind\":\"character\",\"route\":\"/honglou/c/贾迎春\",\"entityId\":\"贾迎春\"}}"
```

## 创建会话（第73回摄取）

```bash
curl -X POST http://127.0.0.1:8787/api/studio/sessions \
  -H "Content-Type: application/json" \
  -d "{\"book\":\"红楼梦\",\"bookSlug\":\"honglou\",\"page\":{\"kind\":\"chapter\",\"route\":\"/honglou/studio?chapter=73\",\"entityId\":\"73\",\"editionSlug\":\"chenggao\"}}"
```

协议：`../classical-novels/docs/维护台-聊天协议.md`  
操作：`../classical-novels/docs/维护台-使用说明.md`
