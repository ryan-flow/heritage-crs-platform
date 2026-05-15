const { request } = require("../../../utils/request");

Page({
  data: {
    loading: false,
    keyword: "",
    active: "all",
    list: [],

    behaviorVisibleMap: {},
    behaviorMap: {},

    editingUserId: null,
    editNickname: "",
    editPhone: "",
    editRole: "user",
    saving: false
  },

  onShow() {
    this.fetchList();
  },

  onKeywordInput(e) {
    this.setData({ keyword: e.detail.value || "" });
  },

  onActiveChange(e) {
    this.setData({ active: e.currentTarget.dataset.active || "all" }, () => this.fetchList());
  },

  async fetchList() {
    this.setData({ loading: true });
    try {
      const url = `/admin/users?keyword=${encodeURIComponent(this.data.keyword || "")}&active=${this.data.active}`;
      const res = await request({ url });
      const data = (res && res.data) || {};
      this.setData({ list: data.items || [] });
    } catch (e) {
      wx.showToast({ title: (e && e.message) || "加载失败", icon: "none" });
    } finally {
      this.setData({ loading: false });
    }
  },

  async toggleUserActive(e) {
    const { id, active } = e.currentTarget.dataset;
    const next = !active;
    try {
      await request({ url: `/admin/users/${id}/active?is_active=${next ? "true" : "false"}`, method: "PUT" });
      wx.showToast({ title: next ? "已启用" : "已封禁", icon: "success" });
      this.fetchList();
    } catch (er) {
      wx.showToast({ title: (er && er.message) || "操作失败", icon: "none" });
    }
  },

  openEdit(e) {
    const item = e.currentTarget.dataset.item;
    if (!item) return;
    this.setData({
      editingUserId: item.id,
      editNickname: item.nickname || "",
      editPhone: item.phone || "",
      editRole: item.role || "user"
    });
  },

  cancelEdit() {
    this.setData({ editingUserId: null, editNickname: "", editPhone: "", editRole: "user" });
  },

  onEditInput(e) {
    const key = e.currentTarget.dataset.key;
    const value = e.detail.value || "";
    this.setData({ [key]: value });
  },

  async saveEdit() {
    if (!this.data.editingUserId || this.data.saving) return;
    this.setData({ saving: true });
    try {
      await request({
        url: `/admin/users/${this.data.editingUserId}`,
        method: "PUT",
        data: {
          nickname: this.data.editNickname || null,
          phone: this.data.editPhone || null,
          role: this.data.editRole || "user",
          is_active: true
        }
      });
      wx.showToast({ title: "更新成功", icon: "success" });
      this.cancelEdit();
      this.fetchList();
    } catch (e) {
      wx.showToast({ title: (e && e.message) || "更新失败", icon: "none" });
    } finally {
      this.setData({ saving: false });
    }
  },

  async deleteUser(e) {
    const id = e.currentTarget.dataset.id;
    wx.showModal({
      title: "确认删除用户",
      content: "该操作不可恢复，是否继续？",
      success: async (r) => {
        if (!r.confirm) return;
        try {
          await request({ url: `/admin/users/${id}`, method: "DELETE" });
          wx.showToast({ title: "已删除", icon: "success" });
          this.fetchList();
        } catch (er) {
          wx.showToast({ title: (er && er.message) || "删除失败", icon: "none" });
        }
      }
    });
  },

  async toggleBehavior(e) {
    const id = Number(e.currentTarget.dataset.id);
    const key = `behaviorVisibleMap.${id}`;
    const opened = !!this.data.behaviorVisibleMap[id];
    this.setData({ [key]: !opened });
    if (opened) return;
    try {
      const res = await request({ url: `/admin/users/${id}/behavior` });
      this.setData({ [`behaviorMap.${id}`]: (res && res.data) || null });
    } catch (er) {
      wx.showToast({ title: (er && er.message) || "行为统计加载失败", icon: "none" });
    }
  }
});
