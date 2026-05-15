/* global wx, getApp, module */

const FAIL_COOLDOWN_MS = 25000;
const failUntilMap = {};

function getAppInstance() {
  return getApp();
}

function getApiCandidates(app) {
  return (app.globalData.apiCandidates || [app.globalData.apiBaseUrl])
    .filter(Boolean)
    .filter((item, index, arr) => arr.indexOf(item) === index);
}

function getHealthyCandidates(candidates) {
  const now = Date.now();
  const healthy = candidates.filter((baseUrl) => (failUntilMap[baseUrl] || 0) <= now);
  return healthy.length ? healthy : candidates;
}

function markNetworkFail(baseUrl) {
  failUntilMap[baseUrl] = Date.now() + FAIL_COOLDOWN_MS;
}

function clearNetworkFail(baseUrl) {
  delete failUntilMap[baseUrl];
}

function normalizeApiPath(path) {
  // FastAPI 对路由尾斜杠敏感：/recommend → 307 → /recommend/
  // 微信小程序 wx.request 对 307 重定向处理不稳定
  // 解决方案：GET/DELETE 请求的 API 路径统一加尾斜杠
  if (!path) return path;
  if (path.includes("?")) {
    const [base, query] = path.split("?", 2);
    return base.endsWith("/") ? path : `${base}/?${query}`;
  }
  return path.endsWith("/") ? path : `${path}/`;
}

function doRequest(baseUrl, options) {
  return new Promise((resolve, reject) => {
    const session = wx.getStorageSync("session") || {};
    const defaultHeader = {
      "Content-Type": "application/json",
      "X-User-Id": session.userId || "",
      "X-Admin-Token": wx.getStorageSync("adminToken") || ""
    };
    const method = (options.method || "GET").toUpperCase();
    const apiPath = (method === "GET" || method === "DELETE")
      ? normalizeApiPath(options.url)
      : options.url;
    wx.request({
      url: `${baseUrl}${apiPath}`,
      method: options.method || "GET",
      data: options.data || {},
      timeout: options.timeout || 12000,
      header: { ...defaultHeader, ...(options.header || {}) },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else {
          reject({ type: "http", data: res.data || { message: "请求失败" }, statusCode: res.statusCode });
        }
      },
      fail: (err) => reject({ type: "network", error: err })
    });
  });
}

async function request(options) {
  const app = getAppInstance();
  const orderedCandidates = getHealthyCandidates(getApiCandidates(app));

  let lastError = null;
  for (const baseUrl of orderedCandidates) {
    try {
      const data = await doRequest(baseUrl, options);
      clearNetworkFail(baseUrl);
      if (app.globalData.apiBaseUrl !== baseUrl) {
        app.globalData.apiBaseUrl = baseUrl;
        app.globalData.apiCandidates = [baseUrl].concat(
          orderedCandidates.filter((item) => item !== baseUrl)
        );
        wx.setStorageSync("apiBaseUrl", baseUrl);
      }
      return data;
    } catch (err) {
      lastError = err;
      if (err && err.type === "network") {
        markNetworkFail(baseUrl);
      }
      if (err && err.type === "http") {
        break;
      }
    }
  }

  if (lastError && lastError.type === "http") {
    return Promise.reject(lastError.data);
  }
  return Promise.reject((lastError && lastError.error) || { message: "网络连接失败" });
}

module.exports = { request };
