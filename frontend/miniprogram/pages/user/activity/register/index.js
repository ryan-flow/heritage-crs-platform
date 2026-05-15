const { request } = require("../../../../utils/request");

Page({
  data: {
    eventId: null,
    remark: "",
    submitting: false,
    agreeNotice: false,
    submitFx: false
  },

  onLoad(options) {
    this.setData({ eventId: options.eventId || null });
  },

  onRemarkInput(e) {
    this.setData({ remark: e.detail.value || "" });
  },

  onAgreeChange(e) {
    this.setData({ agreeNotice: !!e.detail.value.length });
  },

  async submitRegister() {
    const session = wx.getStorageSync("session");
    if (!session || !session.userId) {
      wx.showToast({ title: "请先登录", icon: "none" });
      wx.navigateTo({ url: "/pages/auth/login/index" });
      return;
    }
    if (!this.data.agreeNotice) {
      wx.showToast({ title: "请先阅读并勾选报名须知", icon: "none" });
      return;
    }
    if (this.data.submitting) return;
    this.setData({ submitting: true });
    try {
      await request({
        url: `/events/${this.data.eventId}/register`,
        method: "POST",
        data: {
          user_id: session.userId,
          remark: this.data.remark
        }
      });
      request({
        url: "/recommend/track",
        method: "POST",
        data: { user_id: session.userId, action: "click", target_type: "event", target_id: Number(this.data.eventId), source_scene: "register_success" }
      }).catch(() => {});
      this.setData({ submitFx: true });
      wx.showToast({ title: "报名成功", icon: "success" });
      setTimeout(() => {
        this.setData({ submitFx: false });
        wx.navigateBack();
      }, 700);
    } catch (e) {
      const errMsg = (e && e.message) || "报名失败";
      wx.showToast({ title: errMsg, icon: "none" });
    } finally {
      this.setData({ submitting: false });
    }
  }
});
