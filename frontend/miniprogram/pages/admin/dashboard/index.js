const { request } = require("../../../utils/request");

Page({
  data: {
    loading: false,
    dashboard: null,
    actionLoading: false
  },

  onShow() {
    this.fetchData();
  },

  onPullDownRefresh() {
    this.fetchData(true);
  },

  async fetchData(byRefresh = false) {
    this.setData({ loading: true });
    try {
      const dashboardRes = await request({ url: "/stats/dashboard-public" });
      this.setData({ dashboard: (dashboardRes && dashboardRes.data) || null });
    } catch (e) {
      wx.showToast({ title: "看板加载失败", icon: "none" });
    } finally {
      this.setData({ loading: false });
      if (byRefresh) wx.stopPullDownRefresh();
    }
  },

  goContentManage() {
    wx.navigateTo({ url: "/pages/admin/content-manage/index" });
  },

  goActivityManage() {
    wx.navigateTo({ url: "/pages/admin/activity-manage/index" });
  },

  goTopicManage() {
    wx.navigateTo({ url: "/pages/admin/topic-manage/index" });
  },

  goUserManage() {
    wx.navigateTo({ url: "/pages/admin/user-manage/index" });
  },

  async quickRefresh() {
    if (this.data.actionLoading) return;
    this.setData({ actionLoading: true });
    await this.fetchData();
    this.setData({ actionLoading: false });
  }
});
