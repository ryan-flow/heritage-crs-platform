const DEFAULT_API_BASE = "http://192.168.1.111:8000/api/v1";
const STATIC_API_CANDIDATES = [
  "http://192.168.1.111:8000/api/v1"
];

function uniqueList(list) {
  return list.filter(Boolean).filter((item, index, arr) => arr.indexOf(item) === index);
}

function privateIPv4FromText(text) {
  const raw = String(text || "").trim();
  if (!raw) return "";
  if (/^192\.168\.\d{1,3}\.\d{1,3}$/.test(raw)) return raw;
  if (/^10\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(raw)) return raw;
  if (/^172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}$/.test(raw)) return raw;
  return "";
}

function splitIps(value) {
  if (!value) return [];
  if (Array.isArray(value)) return value;
  if (typeof value === "string") {
    return value
      .split(/[\s,;|/]+/)
      .map((item) => item.trim())
      .filter(Boolean);
  }
  if (typeof value === "object") {
    return Object.values(value)
      .flatMap((item) => splitIps(item))
      .filter(Boolean);
  }
  return [];
}

function isAllowedApiBase(url) {
  const value = String(url || "").trim();
  if (!value) return false;
  return /:8000\/api\/v1$/.test(value);
}

function buildApiByIp(ip) {
  const pure = privateIPv4FromText(ip);
  return pure ? `http://${pure}:8000/api/v1` : "";
}

function getLocalIPs() {
  return new Promise((resolve) => {
    if (typeof wx.getLocalIPAddress !== "function") {
      resolve([]);
      return;
    }

    wx.getLocalIPAddress({
      success: (res) => {
        const candidates = splitIps(res).map(privateIPv4FromText).filter(Boolean);
        resolve(uniqueList(candidates));
      },
      fail: () => resolve([])
    });
  });
}

App({
  globalData: {
    apiBaseUrl: DEFAULT_API_BASE,
    apiCandidates: STATIC_API_CANDIDATES,
    userInfo: null,
    crsMode: ""   /* CRS模式：cold_start/mixed/precision，全局共享给FAB黑塔 */
  },

  async initApiCandidates() {
    const savedApiBaseUrl = wx.getStorageSync("apiBaseUrl");
    const customApiBaseUrl = wx.getStorageSync("customApiBaseUrl");
    const localIps = await getLocalIPs();
    const autoCandidates = uniqueList(localIps.map((ip) => buildApiByIp(ip)).filter(Boolean));

    const merged = uniqueList([
      ...STATIC_API_CANDIDATES,
      DEFAULT_API_BASE,
      customApiBaseUrl,
      savedApiBaseUrl,
      ...autoCandidates
    ]).filter(isAllowedApiBase);

    this.globalData.apiCandidates = merged.length ? merged : [DEFAULT_API_BASE];
    this.globalData.apiBaseUrl = this.globalData.apiCandidates[0] || DEFAULT_API_BASE;
  },

  onLaunch() {
    wx.removeStorageSync("apiBaseUrl");
    wx.removeStorageSync("customApiBaseUrl");

    const session = wx.getStorageSync("session");
    if (session && session.userId) {
      this.globalData.userInfo = session;
    }

    this.initApiCandidates();

    if (typeof wx.onNetworkStatusChange === "function") {
      wx.onNetworkStatusChange(() => {
        this.initApiCandidates();
      });
    }
  }
});







