/* global getApp, module */

function normalizeSlashes(raw) {
  return String(raw || "").trim().replace(/\\/g, "/");
}

function pickStoragePath(raw) {
  const input = normalizeSlashes(raw);
  if (!input) return "";

  const decoded = decodeURIComponent(input);
  const normalized = normalizeSlashes(decoded);

  const storageIdx = normalized.indexOf("/storage/");
  if (storageIdx >= 0) return normalized.slice(storageIdx);

  const staticIdx = normalized.indexOf("/static/");
  if (staticIdx >= 0) {
    return normalized.slice(staticIdx);
  }

  const crawlIdx = normalized.indexOf("/web_crawl/");
  if (crawlIdx >= 0) return `/storage${normalized.slice(crawlIdx)}`;

  const coverIdx = normalized.indexOf("/covers/");
  if (coverIdx >= 0) return `/storage${normalized.slice(coverIdx)}`;

  const discussionIdx = normalized.indexOf("/discussion_covers/");
  if (discussionIdx >= 0) return `/storage${normalized.slice(discussionIdx)}`;

  const ttsIdx = normalized.indexOf("/tts/");
  if (ttsIdx >= 0) return `/storage${normalized.slice(ttsIdx)}`;

  const fileNameMatch = normalized.match(/\/([^/]+\.(png|jpe?g|webp|gif|svg|mp3))$/i);
  if (fileNameMatch && fileNameMatch[1]) {
    const name = fileNameMatch[1];
    if (/\.mp3$/i.test(name)) return `/storage/tts/${name}`;
    if (/^(topic_|discussion_)/i.test(name)) return `/storage/discussion_covers/${name}`;
    if (/^(crawler-|guqin|kunqu|yunjin|dragon|paper|seal|silk|tibetan|woodblock|xuan|cantonese)/i.test(name)) return `/storage/covers/${name}`;
    return `/storage/web_crawl/assets/images/${name}`;
  }

  return "";
}

function isDiskPath(raw) {
  const s = String(raw || "").trim();
  if (!s) return false;
  return /(^[a-zA-Z]:[\\/])|(%3A[\\/])|(\/\w:[\\/])/i.test(s);
}

function buildHost() {
  const app = getApp();
  return String((app && app.globalData && app.globalData.apiBaseUrl) || "").replace(/\/api\/v1$/, "");
}

function toAbsoluteMediaUrl(url) {
  const raw = String(url || "").trim();
  if (!raw) return "";

  const host = buildHost();
  const storagePath = pickStoragePath(raw);

  if (storagePath && host) return `${host}${storagePath}`;
  if (storagePath) return storagePath;

  if (/^https?:\/\//i.test(raw)) {
    if (isDiskPath(raw)) return "";

    // 真机场景下，后端若返回 localhost/127.0.0.1 绝对地址，手机无法访问
    // 统一改写为当前 apiBase 对应主机地址
    if (host && /^(https?:\/\/)(127\.0\.0\.1|localhost)(:\d+)?/i.test(raw)) {
      return raw.replace(/^(https?:\/\/)(127\.0\.0\.1|localhost)(:\d+)?/i, host);
    }

    return raw;
  }

  if (isDiskPath(raw)) return "";

  if (!host) return raw;
  if (raw.startsWith("/")) return `${host}${raw}`;
  return `${host}/${raw}`;
}

module.exports = { toAbsoluteMediaUrl };
