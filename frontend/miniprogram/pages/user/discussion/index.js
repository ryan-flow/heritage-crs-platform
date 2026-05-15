const { request } = require("../../../utils/request");
const { toAbsoluteMediaUrl } = require("../../../utils/media");

const TAG_OPTIONS = ["戏曲", "工艺", "节俗", "求科普", "活动反馈", "传统音乐", "传统舞蹈", "传统美术", "传统技艺", "民俗"];
const POST_TEMPLATES = [
  {
    id: "tpl-question",
    name: "提问型",
    title: "想请教大家一个非遗问题",
    content: "我最近在了解【项目名】，目前最困惑的是【问题点】。有了解的朋友可以分享下入门路径吗？"
  },
  {
    id: "tpl-experience",
    name: "体验分享型",
    title: "我的一次非遗体验记录",
    content: "今天我参加了【活动/展演】。最打动我的细节是【细节】。如果你也准备去，建议重点关注【建议】。"
  },
  {
    id: "tpl-feedback",
    name: "活动反馈型",
    title: "活动复盘：这场非遗体验值不值？",
    content: "活动名称：【名称】\n地点时间：【地点/时间】\n亮点：【亮点】\n不足：【不足】\n推荐指数：【1-5星】"
  }
];

function buildRecommendMeta(item) {
  const timeLabel = item.publishTime || item.createTime || item.freshness_label || "近期";
  const tagText = item.tags && item.tags.length ? ` · ${item.tags.join(" / ")}` : "";
  return `${timeLabel}${tagText}`;
}

function trimTitle(title, limit = 18) {
  const s = String(title || "").trim();
  return s.length > limit ? `${s.slice(0, limit)}…` : s;
}

function heatLevelText(score) {
  const v = Number(score || 0);
  if (v >= 80) return "当前最火";
  if (v >= 45) return "非常火";
  return "有点火";
}

function dateOnly(v) {
  const s = String(v || "");
  return s.slice(0, 10);
}

function getHost() {
  const app = getApp();
  return (app.globalData.apiBaseUrl || "").replace(/\/api\/v1$/, "");
}

Page({
  data: {
    list: [],
    hotList: [],
    recommendTopics: [],
    loading: false,
    showComposer: false,
    title: "",
    content: "",
    coverUrl: "",
    coverUploading: false,
    selectedTags: [],
    keyword: "",
    activeTag: "",
    sort: "hot",
    favoriteOnly: false,
    tagOptions: TAG_OPTIONS,
    templates: POST_TEMPLATES,
    activeTemplateId: ""
  },

  syncTabBar(selected) {
    const tabBar = typeof this.getTabBar === "function" && this.getTabBar();
    if (tabBar && typeof tabBar.setData === "function") {
      tabBar.setData({ selected });
    }
  },

  onShow() {
    this.syncTabBar(3);
    const session = wx.getStorageSync("session") || {};
    this.fetchList();
    this.fetchRecommend(session.userId || "");
  },

  onPullDownRefresh() {
    this.fetchList(true);
  },

  buildListUrl() {
    const session = wx.getStorageSync("session") || {};
    const params = [
      `user_id=${session.userId || ""}`,
      `sort=${this.data.sort || "hot"}`,
      `favorite_only=${this.data.favoriteOnly ? "true" : "false"}`
    ];
    if (this.data.keyword) params.push(`keyword=${encodeURIComponent(this.data.keyword)}`);
    if (this.data.activeTag) params.push(`tag=${encodeURIComponent(this.data.activeTag)}`);
    return `/discussion/topics?${params.join("&")}`;
  },

  async fetchList(byRefresh = false) {
    this.setData({ loading: true });
    try {
      const res = await request({ url: this.buildListUrl() });
      const data = (res && res.data) || {};
      const list = (data.items || []).map((item) => ({
        ...item,
        cover_full_url: toAbsoluteMediaUrl(item.cover_url),
        title_short: trimTitle(item.title),
        heat_level_text: heatLevelText(item.heat_score),
        created_date: dateOnly(item.created_at)
      }));
      const featuredItems = (data.featured_items || []).map((item) => ({
        ...item,
        cover_full_url: toAbsoluteMediaUrl(item.cover_url),
        title_short: trimTitle(item.title),
        heat_level_text: heatLevelText(item.heat_score),
        created_date: dateOnly(item.created_at)
      }));
      const hotList = (featuredItems.length ? featuredItems : list)
        .slice()
        .sort((a, b) => (b.heat_score || 0) - (a.heat_score || 0))
        .slice(0, 3);
      this.setData({ list, hotList });
    } catch (e) {
      wx.showToast({ title: "讨论加载失败", icon: "none" });
    } finally {
      this.setData({ loading: false });
      if (byRefresh) wx.stopPullDownRefresh();
    }
  },

  async fetchRecommend(userId) {
    try {
      const res = await request({ url: `/recommend?user_id=${userId}&scene=discussion` });
      const data = (res && res.data) || {};
      const recommendTopics = (data.topics || []).slice(0, 3).map((item) => ({
        ...item,
        recommendMeta: buildRecommendMeta(item) // UI优化：推荐时间兜底
      }));
      this.setData({ recommendTopics });
      recommendTopics.forEach((it) => {
        request({
          url: "/recommend/track",
          method: "POST",
          data: { user_id: userId || null, action: "expose", target_type: "topic", target_id: it.id, source_scene: "discussion_page" }
        }).catch(() => {});
      });
    } catch (e) {}
  },

  onKeywordInput(e) {
    this.setData({ keyword: e.detail.value || "" });
  },

  onSearch() {
    this.fetchList();
  },

  clearSearch() {
    this.setData({ keyword: "", activeTag: "" });
    this.fetchList();
  },

  toggleFavoriteOnly() {
    this.setData({ favoriteOnly: !this.data.favoriteOnly }, () => this.fetchList());
  },

  switchSort(e) {
    const sort = e.currentTarget.dataset.sort;
    this.setData({ sort }, () => this.fetchList());
  },

  toggleFilterTag(e) {
    const tag = e.currentTarget.dataset.tag || "";
    this.setData({ activeTag: this.data.activeTag === tag ? "" : tag }, () => this.fetchList());
  },

  toggleComposer() {
    this.setData({ showComposer: !this.data.showComposer });
  },

  applyTemplate(e) {
    const tplId = e.currentTarget.dataset.id;
    const tpl = (this.data.templates || []).find((x) => x.id === tplId);
    if (!tpl) return;
    this.setData({
      activeTemplateId: tplId,
      title: tpl.title,
      content: tpl.content,
      showComposer: true
    });
  },

  onTitleInput(e) {
    this.setData({ title: e.detail.value || "" });
  },

  onContentInput(e) {
    this.setData({ content: e.detail.value || "" });
  },

  toggleTagSelect(e) {
    const tag = e.currentTarget.dataset.tag;
    const next = (this.data.selectedTags || []).slice();
    const idx = next.indexOf(tag);
    if (idx >= 0) next.splice(idx, 1);
    else if (next.length < 3) next.push(tag);
    this.setData({ selectedTags: next });
  },

  chooseCover() {
    wx.chooseMedia({
      count: 1,
      mediaType: ["image"],
      sourceType: ["album"],
      success: async (res) => {
        const file = (res.tempFiles || [])[0];
        if (!file || !file.tempFilePath) return;
        const path = file.tempFilePath;
        if (!/\.(jpg|jpeg|png|webp)$/i.test(path)) {
          wx.showToast({ title: "仅支持jpg/png/webp", icon: "none" });
          return;
        }
        await this.uploadCover(path);
      }
    });
  },

  async uploadCover(filePath) {
    const session = wx.getStorageSync("session") || {};
    const host = getHost();
    this.setData({ coverUploading: true });
    try {
      const resp = await new Promise((resolve, reject) => {
        wx.uploadFile({
          url: `${host}/api/v1/discussion/upload-cover`,
          filePath,
          name: "file",
          header: { "X-User-Id": session.userId || "" },
          success: (r) => {
            try {
              resolve(JSON.parse(r.data || "{}"));
            } catch (e) {
              reject(e);
            }
          },
          fail: reject
        });
      });
      const url = resp && resp.data && resp.data.url;
      if (!url) throw new Error("上传失败");
      this.setData({ coverUrl: toAbsoluteMediaUrl(url) });
      wx.showToast({ title: "封面已上传", icon: "success" });
    } catch (e) {
      wx.showToast({ title: "封面上传失败", icon: "none" });
    } finally {
      this.setData({ coverUploading: false });
    }
  },

  clearCover() {
    this.setData({ coverUrl: "" });
  },

  async submitTopic() {
    const session = wx.getStorageSync("session") || {};
    const title = (this.data.title || "").trim();
    const content = (this.data.content || "").trim();
    if (!session.userId) {
      wx.showToast({ title: "请先登录", icon: "none" });
      return;
    }
    if (!title || !content) {
      wx.showToast({ title: "请填写标题和内容", icon: "none" });
      return;
    }
    try {
      await request({
        url: "/discussion/topics",
        method: "POST",
        data: {
          user_id: session.userId,
          title,
          content,
          cover_url: (this.data.coverUrl || "").replace(/^https?:\/\/[^/]+/i, "") || null,
          tags: this.data.selectedTags,
          image_urls: []
        }
      });
      wx.showToast({ title: "发布成功", icon: "success" });
      this.setData({ showComposer: false, title: "", content: "", coverUrl: "", selectedTags: [], activeTemplateId: "" });
      this.fetchList();
    } catch (e) {
      wx.showToast({ title: (e && e.message) || "发布失败", icon: "none" });
    }
  },

  async toggleLike(e) {
    const session = wx.getStorageSync("session") || {};
    const { id, liked } = e.currentTarget.dataset;
    if (!session.userId) {
      wx.showToast({ title: "请先登录", icon: "none" });
      return;
    }
    try {
      if (liked) await request({ url: `/discussion/topics/${id}/like?user_id=${session.userId}`, method: "DELETE" });
      else await request({ url: `/discussion/topics/${id}/like?user_id=${session.userId}`, method: "POST" });
      this.fetchList();
    } catch (e) {
      wx.showToast({ title: (e && e.message) || "操作失败", icon: "none" });
    }
  },

  async toggleFavorite(e) {
    const session = wx.getStorageSync("session") || {};
    const { id, favorited } = e.currentTarget.dataset;
    if (!session.userId) {
      wx.showToast({ title: "请先登录", icon: "none" });
      return;
    }
    try {
      if (favorited) await request({ url: `/discussion/topics/${id}/favorite?user_id=${session.userId}`, method: "DELETE" });
      else await request({ url: `/discussion/topics/${id}/favorite?user_id=${session.userId}`, method: "POST" });
      this.fetchList();
    } catch (e) {
      wx.showToast({ title: (e && e.message) || "操作失败", icon: "none" });
    }
  },

  toDetail(e) {
    const id = e.currentTarget.dataset.id;
    const session = wx.getStorageSync("session") || {};
    request({
      url: "/recommend/track",
      method: "POST",
      data: { user_id: session.userId || null, action: "click", target_type: "topic", target_id: id, source_scene: "discussion_page" }
    }).catch(() => {});
    wx.navigateTo({ url: `/pages/user/discussion/detail/index?id=${id}` });
  }
});
