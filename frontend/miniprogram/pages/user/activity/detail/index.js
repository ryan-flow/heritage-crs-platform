const { request } = require("../../../../utils/request");
const { toAbsoluteMediaUrl } = require("../../../../utils/media");

function formatDateTime(value) {
  if (!value) return "待定";
  return String(value).replace("T", " ").slice(0, 16);
}

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
      const res = await request({ url: `/events/${this.data.id}?user_id=${session.userId || ""}` });
      const detail = res.data || null;
      if (detail) {
        detail.start_time_text = formatDateTime(detail.start_time);
        detail.end_time_text = formatDateTime(detail.end_time);
        detail.cover_url = toAbsoluteMediaUrl(detail.cover_url || "");
        detail.organizer = detail.organizer || "中国非遗文化推广中心";
        detail.notes = detail.notes || "请提前15分钟签到，遵守现场秩序，文明参与体验活动。";
        detail.displayBlocks = detail.display_blocks || { highlights: [], agenda: [], tips: [] };
        request({
          url: "/recommend/track",
          method: "POST",
          data: { user_id: session.userId || null, action: "view", target_type: "event", target_id: detail.id, source_scene: "event_detail" }
        }).catch(() => {});
      }
      this.setData({ detail });
    } catch (e) {
      wx.showToast({ title: "活动详情加载失败", icon: "none" });
    } finally {
      this.setData({ loading: false });
    }
  },

  toRegister() {
    if (!this.data.id) return;
    wx.navigateTo({ url: `/pages/user/activity/register/index?eventId=${this.data.id}` });
  },

  async cancelRegistration() {
    const session = wx.getStorageSync("session") || {};
    if (!session.userId) {
      wx.showToast({ title: "请先登录", icon: "none" });
      return;
    }
    if (!this.data.id) return;

    try {
      await request({ url: `/events/${this.data.id}/cancel?user_id=${session.userId}`, method: "POST" });
      wx.showToast({ title: "已取消报名", icon: "success" });
      this.fetchDetail();
    } catch (e) {
      wx.showToast({ title: (e && e.message) || "取消失败", icon: "none" });
    }
  }
});
