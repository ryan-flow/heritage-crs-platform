const { request } = require("../../../utils/request");

function emptyForm() {
  return {
    title: "",
    cover_url: "",
    location: "",
    organizer: "",
    start_time: "2026-05-01T10:00:00",
    end_time: "2026-05-01T12:00:00",
    max_participants: 50,
    description: "",
    notes: "",
    status: "open",
    is_featured: false
  };
}

Page({
  data: {
    loading: false,
    keyword: "",
    status: "all",
    list: [],

    showForm: false,
    editingId: null,
    form: emptyForm(),
    saving: false,

    regVisibleMap: {},
    registrationMap: {}
  },

  onShow() {
    this.fetchList();
  },

  onKeywordInput(e) {
    this.setData({ keyword: e.detail.value || "" });
  },

  onStatusChange(e) {
    this.setData({ status: e.currentTarget.dataset.status || "all" }, () => this.fetchList());
  },

  async fetchList() {
    this.setData({ loading: true });
    try {
      const url = `/admin/activities?keyword=${encodeURIComponent(this.data.keyword || "")}&status=${this.data.status}`;
      const res = await request({ url });
      const data = (res && res.data) || {};
      this.setData({ list: data.items || [] });
    } catch (e) {
      wx.showToast({ title: (e && e.message) || "加载失败", icon: "none" });
    } finally {
      this.setData({ loading: false });
    }
  },

  openCreate() {
    this.setData({ showForm: true, editingId: null, form: emptyForm() });
  },

  openEdit(e) {
    const item = e.currentTarget.dataset.item;
    if (!item) return;
    this.setData({
      showForm: true,
      editingId: item.id,
      form: {
        title: item.title || "",
        cover_url: item.cover_url || "",
        location: item.location || "",
        organizer: item.organizer || "",
        start_time: item.start_time ? String(item.start_time).slice(0, 19) : "",
        end_time: item.end_time ? String(item.end_time).slice(0, 19) : "",
        max_participants: item.max_participants || 50,
        description: item.description || "",
        notes: item.notes || "",
        status: item.status || "open",
        is_featured: !!item.is_featured
      }
    });
  },

  closeForm() {
    this.setData({ showForm: false, editingId: null, form: emptyForm() });
  },

  onFormInput(e) {
    const key = e.currentTarget.dataset.key;
    const value = e.detail.value || "";
    this.setData({ [`form.${key}`]: value });
  },

  onSwitchChange(e) {
    const key = e.currentTarget.dataset.key;
    this.setData({ [`form.${key}`]: !!e.detail.value });
  },

  async saveForm() {
    if (this.data.saving) return;
    const form = this.data.form;
    if (!form.title || !form.start_time || !form.end_time) {
      wx.showToast({ title: "标题/开始/结束时间必填", icon: "none" });
      return;
    }
    this.setData({ saving: true });
    try {
      const payload = { ...form, max_participants: Number(form.max_participants || 50) };
      if (this.data.editingId) {
        await request({ url: `/admin/activities/${this.data.editingId}`, method: "PUT", data: payload });
      } else {
        await request({ url: "/admin/activities", method: "POST", data: payload });
      }
      wx.showToast({ title: "保存成功", icon: "success" });
      this.closeForm();
      this.fetchList();
    } catch (e) {
      wx.showToast({ title: (e && e.message) || "保存失败", icon: "none" });
    } finally {
      this.setData({ saving: false });
    }
  },

  async toggleActivityStatus(e) {
    const { id, status } = e.currentTarget.dataset;
    const next = status === "open" ? "closed" : "open";
    try {
      await request({ url: `/admin/activities/${id}/status?status=${next}`, method: "PUT" });
      wx.showToast({ title: next === "open" ? "已开放" : "已关闭", icon: "success" });
      this.fetchList();
    } catch (er) {
      wx.showToast({ title: (er && er.message) || "操作失败", icon: "none" });
    }
  },

  async toggleFeatured(e) {
    const { id, featured } = e.currentTarget.dataset;
    try {
      await request({ url: `/admin/activities/${id}/feature?is_featured=${featured ? 'false' : 'true'}`, method: "PUT" });
      wx.showToast({ title: featured ? "已取消精选" : "已设精选", icon: "success" });
      this.fetchList();
    } catch (er) {
      wx.showToast({ title: (er && er.message) || "操作失败", icon: "none" });
    }
  },

  async deleteActivity(e) {
    const id = e.currentTarget.dataset.id;
    wx.showModal({
      title: "确认删除活动",
      content: "删除后不可恢复，继续吗？",
      success: async (r) => {
        if (!r.confirm) return;
        try {
          await request({ url: `/admin/activities/${id}`, method: "DELETE" });
          wx.showToast({ title: "已删除", icon: "success" });
          this.fetchList();
        } catch (er) {
          wx.showToast({ title: (er && er.message) || "删除失败", icon: "none" });
        }
      }
    });
  },

  async toggleRegs(e) {
    const activityId = Number(e.currentTarget.dataset.id);
    const key = `regVisibleMap.${activityId}`;
    const current = !!this.data.regVisibleMap[activityId];
    this.setData({ [key]: !current });
    if (current) return;
    try {
      const res = await request({ url: `/admin/activities/${activityId}/registrations` });
      const list = (res && res.data && res.data.items) || [];
      this.setData({ [`registrationMap.${activityId}`]: list });
    } catch (er) {
      wx.showToast({ title: (er && er.message) || "报名记录加载失败", icon: "none" });
    }
  },

  async setRegistrationStatus(e) {
    const { registrationId, status, activityId } = e.currentTarget.dataset;
    try {
      await request({
        url: `/admin/activities/registrations/${registrationId}/status?status=${status}`,
        method: "PUT"
      });
      wx.showToast({ title: "状态已更新", icon: "success" });
      const res = await request({ url: `/admin/activities/${activityId}/registrations` });
      this.setData({ [`registrationMap.${activityId}`]: (res && res.data && res.data.items) || [] });
      this.fetchList();
    } catch (er) {
      wx.showToast({ title: (er && er.message) || "更新失败", icon: "none" });
    }
  }
});
