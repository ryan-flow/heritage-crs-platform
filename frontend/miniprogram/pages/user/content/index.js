const { request } = require("../../../utils/request");
const digitalHuman = require("../../../utils/digital-human");
const { toAbsoluteMediaUrl } = require("../../../utils/media");

function buildColumns(items) {
  const left = [];
  const right = [];
  items.forEach((it, idx) => {
    (idx % 2 === 0 ? left : right).push(it);
  });
  return { left, right };
}

function shortenReason(text, fallback) {
  const raw = String(text || "").trim();
  if (!raw) return fallback;
  const normalized = raw.replace(/推荐理由[:：]?/g, "").trim();
  const firstSentence = normalized.split(/[。！？!?,，；;]/)[0].trim();
  const brief = firstSentence || normalized;
  return brief.length > 16 ? `${brief.slice(0, 16)}…` : brief;
}

Page({
  behaviors: [digitalHuman],

  data: {
    list: [],
    loading: false,
    featured: null,
    spotlight: [],
    columns: { left: [], right: [] },
    recommend: {
      guide_text: "",
      contents: [],
      events: [],
      topics: []
    }
  },

  syncTabBar(selected) {
    const tabBar = typeof this.getTabBar === "function" && this.getTabBar();
    if (tabBar && typeof tabBar.setData === "function") {
      tabBar.setData({ selected });
    }
  },

  onShow() {
    this.syncTabBar(1);
    const session = wx.getStorageSync("session") || {};
    this.fetchList();
    this.fetchRecommend(session.userId || "");
    this.initDigitalHuman("content");
  },

  onUnload() {
    this.destroyDigitalHuman();
  },

  onHide() {
    if (this.digitalHumanAudio) {
      try {
        this.digitalHumanAudio.stop();
      } catch (e) {}
    }
    this.setData({ digitalHumanSpeaking: false });
  },

  onPullDownRefresh() {
    this.fetchList(true);
  },

  async fetchList(byRefresh = false) {
    this.setData({ loading: true });
    try {
      const res = await request({ url: "/contents?status=published" });
      const data = (res && res.data) || {};
      const list = (data.items || []).map((it, idx) => ({
        ...it,
        cover_full_url: toAbsoluteMediaUrl(it.cover_url),
        display_tag: idx < 3 ? "策展精选" : (it.sub_chapter || it.content_type || "专题阅读")
      }));
      const featured = list[0] || null;
      const spotlight = list.slice(1, 3);
      const columns = buildColumns(list.slice(3));
      this.setData({ list, featured, spotlight, columns });
    } catch (e) {
      wx.showToast({ title: "内容加载失败", icon: "none" });
    } finally {
      this.setData({ loading: false });
      if (byRefresh) wx.stopPullDownRefresh();
    }
  },

  async fetchRecommend(userId) {
    try {
      const res = await request({ url: `/recommend?user_id=${userId}&scene=content` });
      const recommend = (res && res.data) || { guide_text: "", contents: [], events: [], topics: [], profile_summary: null, scene: "content" };
      recommend.contents = (recommend.contents || []).map((item) => ({
        ...item,
        cover_url: toAbsoluteMediaUrl(item.cover_url),
        reason: shortenReason(item.reason, "适合继续阅读")
      }));
      this.setData({ recommend });

      const exposes = recommend.contents || [];
      exposes.forEach((it) => {
        request({
          url: "/recommend/track",
          method: "POST",
          data: {
            user_id: userId || null,
            action: "expose",
            target_type: "content",
            target_id: it.id,
            source_scene: "content_page"
          }
        }).catch(() => {});
      });
    } catch (e) {}
  },

  toDetail(e) {
    const id = e.currentTarget.dataset.id;
    const session = wx.getStorageSync("session") || {};
    request({
      url: "/recommend/track",
      method: "POST",
      data: {
        user_id: session.userId || null,
        action: "click",
        target_type: "content",
        target_id: id,
        source_scene: "content_page"
      }
    }).catch(() => {});
    wx.navigateTo({ url: `/pages/user/content/detail/index?id=${id}` });
  },

  toEventDetail(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/user/activity/detail/index?id=${id}` });
  }
});
