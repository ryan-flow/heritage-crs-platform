const { request } = require("../../../../utils/request");
const { toAbsoluteMediaUrl } = require("../../../../utils/media");

Page({
  data: {
    id: null,
    topic: null,
    comments: [],
    commentText: "",
    loading: true
  },

  onLoad(options) {
    this.setData({ id: options.id || null });
    this.fetchDetail();
  },

  async fetchDetail() {
    if (!this.data.id) return;
    const session = wx.getStorageSync("session") || {};
    this.setData({ loading: true });
    try {
      const res = await request({ url: `/discussion/topics/${this.data.id}?user_id=${session.userId || ""}` });
      const data = (res && res.data) || {};
      const topic = data.topic || null;
      if (topic && topic.cover_url) topic.cover_full_url = toAbsoluteMediaUrl(topic.cover_url);
      if (topic) {
        topic.displayBlocks = topic.display_blocks || { highlights: [], guide_questions: [], tone: "经验分享" };
        request({
          url: "/recommend/track",
          method: "POST",
          data: { user_id: session.userId || null, action: "view", target_type: "topic", target_id: topic.id, source_scene: "topic_detail" }
        }).catch(() => {});
      }
      this.setData({ topic, comments: data.comments || [] });
    } catch (e) {
      wx.showToast({ title: "详情加载失败", icon: "none" });
    } finally {
      this.setData({ loading: false });
    }
  },

  onCommentInput(e) {
    this.setData({ commentText: e.detail.value || "" });
  },

  async submitComment() {
    const session = wx.getStorageSync("session") || {};
    const content = (this.data.commentText || "").trim();
    if (!session.userId) {
      wx.showToast({ title: "请先登录", icon: "none" });
      return;
    }
    if (!content) {
      wx.showToast({ title: "请输入评论内容", icon: "none" });
      return;
    }
    try {
      await request({ url: `/discussion/topics/${this.data.id}/comments`, method: "POST", data: { user_id: session.userId, content } });
      wx.showToast({ title: "评论成功", icon: "success" });
      this.setData({ commentText: "" });
      this.fetchDetail();
    } catch (e) {
      wx.showToast({ title: (e && e.message) || "评论失败", icon: "none" });
    }
  },

  async toggleLike() {
    const session = wx.getStorageSync("session") || {};
    if (!session.userId || !this.data.topic) {
      wx.showToast({ title: "请先登录", icon: "none" });
      return;
    }
    try {
      if (this.data.topic.liked) await request({ url: `/discussion/topics/${this.data.id}/like?user_id=${session.userId}`, method: "DELETE" });
      else await request({ url: `/discussion/topics/${this.data.id}/like?user_id=${session.userId}`, method: "POST" });
      this.fetchDetail();
    } catch (e) {
      wx.showToast({ title: (e && e.message) || "操作失败", icon: "none" });
    }
  },

  async toggleFavorite() {
    const session = wx.getStorageSync("session") || {};
    if (!session.userId || !this.data.topic) {
      wx.showToast({ title: "请先登录", icon: "none" });
      return;
    }
    try {
      if (this.data.topic.favorited) await request({ url: `/discussion/topics/${this.data.id}/favorite?user_id=${session.userId}`, method: "DELETE" });
      else await request({ url: `/discussion/topics/${this.data.id}/favorite?user_id=${session.userId}`, method: "POST" });
      this.fetchDetail();
    } catch (e) {
      wx.showToast({ title: (e && e.message) || "操作失败", icon: "none" });
    }
  }
});
