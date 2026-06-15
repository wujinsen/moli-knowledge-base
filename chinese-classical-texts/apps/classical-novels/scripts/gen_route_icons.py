#!/usr/bin/env python3
"""生成取经路线节点示意 SVG（可替换为手绘/AI 素材）。"""
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "public" / "xiyouji" / "route" / "icons"
OUT.mkdir(parents=True, exist_ok=True)

ICONS = {
    "chang-an.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect x="4" y="22" width="40" height="18" rx="2" fill="#8b6914" stroke="#f6df9a" stroke-width="1.5"/><path d="M24 6 L34 22 H14 Z" fill="#c9a227" stroke="#fff3c4"/><rect x="20" y="28" width="8" height="12" fill="#5c3d0e"/><rect x="10" y="26" width="6" height="8" fill="#3d2810" opacity=".8"/><rect x="32" y="26" width="6" height="8" fill="#3d2810" opacity=".8"/></svg>',
    "huoyanshan.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path d="M6 40 L24 10 L42 40 Z" fill="#7a3b12"/><path d="M12 40 Q24 24 36 40" fill="#e85d04"/><path d="M16 34 Q24 20 32 34" fill="#ffba08"/><path d="M20 30 Q24 18 28 30" fill="#fff3bf"/></svg>',
    "leiyin.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect x="14" y="28" width="20" height="12" fill="#c9a227"/><path d="M10 28 L24 8 L38 28 Z" fill="#f6df9a" stroke="#fff"/><rect x="20" y="14" width="8" height="6" fill="#e0a93a"/><circle cx="24" cy="6" r="3" fill="#ffd700"/></svg>',
    "liushahe.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect x="0" y="28" width="48" height="14" fill="#3d7a9a"/><path d="M0 32 Q12 26 24 32 T48 32" fill="none" stroke="#7ec8e3" stroke-width="2"/><ellipse cx="24" cy="36" rx="8" ry="3" fill="#c2b280"/></svg>',
    "longgong.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect width="48" height="48" fill="#0d3d56" rx="4"/><path d="M8 30 Q24 14 40 30" fill="none" stroke="#22c1d6" stroke-width="3"/><path d="M12 20 Q18 12 24 20 Q30 12 36 20" fill="#1a8fa8"/><circle cx="24" cy="32" r="6" fill="#f6df9a"/></svg>',
    "lingxiao.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect x="8" y="30" width="32" height="10" fill="#2d6a9a"/><path d="M12 30 L24 6 L36 30 Z" fill="#5eb6e6" stroke="#dff4ff"/><rect x="20" y="18" width="8" height="8" fill="#3d8fbf"/><circle cx="24" cy="8" r="4" fill="#ffd700"/></svg>',
    "diyu.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><ellipse cx="24" cy="38" rx="18" ry="6" fill="#2d1f4e"/><path d="M10 38 C10 20 38 20 38 38" fill="#4a3570" stroke="#9b87f5"/><rect x="18" y="22" width="12" height="16" fill="#1a1030" stroke="#b8a4ff"/></svg>',
    "putuo.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><circle cx="24" cy="30" r="12" fill="#37c98d" opacity=".35"/><path d="M24 8 L28 20 H36 L30 28 L32 40 L24 34 L16 40 L18 28 L12 20 H20 Z" fill="#2ea86f" stroke="#b7f7d8"/></svg>',
    "doushuai.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><circle cx="24" cy="24" r="16" fill="#5eb6e6" opacity=".4"/><rect x="16" y="26" width="16" height="12" fill="#3d8fbf"/><path d="M14 26 L24 10 L34 26 Z" fill="#7ec8f0" stroke="#fff"/></svg>',
    "liangjie.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path d="M4 40 L20 12 L28 12 L44 40 Z" fill="#6b5a3e"/><line x1="24" y1="12" x2="24" y2="40" stroke="#f6df9a" stroke-width="2" stroke-dasharray="4 3"/></svg>',
    "yingchoujian.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path d="M4 40 Q24 8 44 40" fill="#3d5a40"/><path d="M18 20 L24 10 L30 20 L28 16 L32 22 L24 18 L16 22 L20 16 Z" fill="#8ab4f8"/></svg>',
    "gaolaozhuang.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect x="8" y="24" width="14" height="14" fill="#a67c52"/><rect x="26" y="20" width="14" height="18" fill="#8b6914"/><path d="M15 24 L15 16 L19 16 L19 24" fill="#c0392b"/><rect x="30" y="12" width="6" height="8" fill="#7a5230"/></svg>',
    "huangfengling.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path d="M6 40 L24 14 L42 40 Z" fill="#8a7a2e"/><path d="M10 36 Q24 20 38 36" fill="none" stroke="#f1c40f" stroke-width="3" opacity=".8"/></svg>',
    "baihuling.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path d="M6 40 L24 12 L42 40 Z" fill="#9ca3af"/><ellipse cx="24" cy="28" rx="10" ry="6" fill="#f8fafc" opacity=".9"/></svg>',
    "lianhuadong.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><ellipse cx="24" cy="32" rx="16" ry="10" fill="#4a3728"/><circle cx="24" cy="22" r="10" fill="#e85d8a"/><circle cx="24" cy="22" r="5" fill="#ffd6e7"/></svg>',
    "huoyundong.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><ellipse cx="24" cy="30" rx="18" ry="12" fill="#3d2810"/><path d="M14 28 Q24 14 34 28" fill="#e85d04" opacity=".85"/></svg>',
    "wujiguo.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect x="10" y="18" width="28" height="22" fill="#c9a227" stroke="#fff3c4"/><path d="M16 18 V12 H32 V18" fill="none" stroke="#fff3c4"/><circle cx="24" cy="10" r="5" fill="#ffd700"/></svg>',
    "chechiguo.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect x="12" y="16" width="24" height="24" fill="#5c4d7a"/><circle cx="24" cy="24" r="8" fill="none" stroke="#c4b5fd" stroke-width="2"/><path d="M24 16 V32 M16 24 H32" stroke="#c4b5fd"/></svg>',
    "tongtianhe.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect x="0" y="20" width="48" height="22" fill="#1e5f8a"/><path d="M0 28 Q12 22 24 28 T48 28" fill="none" stroke="#7ec8e3" stroke-width="2.5"/><path d="M0 34 Q12 30 24 34 T48 34" fill="none" stroke="#7ec8e3" stroke-width="1.5" opacity=".7"/></svg>',
    "xiliang.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect x="10" y="20" width="28" height="18" fill="#d4a5a5"/><path d="M18 20 Q24 8 30 20" fill="#f8b4c4"/><circle cx="18" cy="30" r="3" fill="#fff"/><circle cx="30" cy="30" r="3" fill="#fff"/></svg>',
    "jisaiguo.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect x="18" y="10" width="12" height="30" fill="#c9a227"/><path d="M12 40 H36" stroke="#8b6914" stroke-width="3"/><rect x="14" y="14" width="20" height="4" fill="#f6df9a"/></svg>',
    "zhuziguo.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect x="8" y="22" width="32" height="16" fill="#9b59b6" opacity=".8"/><path d="M24 8 L32 22 H16 Z" fill="#d4ac0d"/></svg>',
    "shituoling.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path d="M6 40 L24 10 L42 40 Z" fill="#5c4033"/><circle cx="16" cy="28" r="5" fill="#f4d03f"/><circle cx="32" cy="28" r="5" fill="#f4d03f"/></svg>',
    "biqiuguo.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect x="12" y="18" width="24" height="20" fill="#e0a93a"/><circle cx="20" cy="30" r="4" fill="#fff"/><circle cx="28" cy="30" r="4" fill="#fff"/></svg>',
    "mieffaguo.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect x="14" y="16" width="20" height="22" fill="#7f8c8d"/><line x1="10" y1="12" x2="38" y2="38" stroke="#e74c3c" stroke-width="3"/></svg>',
    "wuzhuang.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect x="16" y="26" width="16" height="14" fill="#8b6914"/><circle cx="24" cy="18" r="12" fill="#27ae60"/><circle cx="24" cy="16" r="4" fill="#f39c12"/></svg>',
    "tianzhuguo.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path d="M20 40 V18 L24 8 L28 18 V40" fill="#e67e22"/><circle cx="24" cy="12" r="6" fill="#f6df9a"/></svg>',
    "realm-mortal.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><circle cx="24" cy="24" r="14" fill="#e0a93a" stroke="#f6df9a" stroke-width="2"/></svg>',
    "realm-buddha.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path d="M24 6 L30 20 H42 L32 30 L36 42 L24 34 L12 42 L16 30 L6 20 H18 Z" fill="#f6df9a"/></svg>',
    "realm-heaven.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect x="10" y="10" width="28" height="28" rx="6" fill="#5eb6e6" stroke="#dff4ff" stroke-width="2" transform="rotate(45 24 24)"/></svg>',
    "realm-south.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><circle cx="24" cy="24" r="14" fill="#37c98d" stroke="#b7f7d8" stroke-width="2"/></svg>',
    "realm-east.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><circle cx="24" cy="24" r="14" fill="#22c1d6" stroke="#b8f0f8" stroke-width="2"/></svg>',
    "realm-hell.svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><circle cx="24" cy="24" r="14" fill="#9b87f5" stroke="#d4c4ff" stroke-width="2"/></svg>',
}

for name, svg in ICONS.items():
    (OUT / name).write_text(svg, encoding="utf-8")

print(f"wrote {len(ICONS)} icons -> {OUT}")
