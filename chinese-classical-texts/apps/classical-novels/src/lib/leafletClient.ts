/** 客户端 Leaflet 单例入口：静态 import，避免 dynamic import + 严格 CSP / 504 dep 缓存问题 */
import L from 'leaflet';

export default L;
