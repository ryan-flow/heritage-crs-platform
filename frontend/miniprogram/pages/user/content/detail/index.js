const { request } = require("../../../../utils/request");
const { toAbsoluteMediaUrl } = require("../../../../utils/media");

Page({
  data: {
    id: null,
    detail: null,
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
      const res = await request({ url: `/contents/${this.data.id}` });
      const detail = res.data || null;
      if (detail) {
        detail.cover_url = toAbsoluteMediaUrl(detail.cover_url || "");
        detail.chapter_text = [detail.chapter, detail.sub_chapter].filter(Boolean).join(" · ");
        detail.displayBlocks = detail.display_blocks || { intro: "", highlights: [], reading_tips: [] };
        request({
          url: "/recommend/track",
          method: "POST",
          data: { user_id: session.userId || null, action: "view", target_type: "content", target_id: detail.id, source_scene: "content_detail" }
        }).catch(() => {});
      }
      this.setData({ detail });
    } catch (e) {
      wx.showToast({ title: "详情加载失败", icon: "none" });
    } finally {
      this.setData({ loading: false });
    }
  }
});
