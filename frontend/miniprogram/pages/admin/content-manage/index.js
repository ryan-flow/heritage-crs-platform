const { request } = require("../../../utils/request");

function emptyForm() {
  return {
    title: "",
    cover_url: "",
    content_type: "article",
    chapter: "",
    sub_chapter: "",
    summary: "",
    body: "",
    status: "draft",
    review_status: "pending",
    quality_score: 0.9,
    is_featured: false,
    published_at: "",
    created_by: null
  };
}

Page({
  data: {
    adminUsername: "admin",
    adminPassword: "admin123",
    loggingIn: false,
    hasAdminToken: false,

    loading: false,
    keyword: "",
    status: "all",
    list: [],

    showForm: false,
    editingId: null,
    form: emptyForm(),
    saving: false
  },

  onShow() {
    this.setData({ hasAdminToken: !!wx.getStorageSync("adminToken") });
    this.fetchList();
  },

  async adminLogin() {
    if (this.data.loggingIn) return;
    this.setData({ loggingIn: true });
    try {
      const res = await request({
        url: "/auth/admin/login",
        method: "POST",
        data: {
          username: this.data.adminUsername,
          password: this.data.adminPassword
        }
      });
      const token = res && res.data && res.data.token;
      if (!token) throw new Error("登录失败");
      wx.setStorageSync("adminToken", token);
      this.setData({ hasAdminToken: true });
      wx.showToast({ title: "管理员已登录", icon: "success" });
      this.fetchList();
    } catch (e) {
      wx.showToast({ title: (e && e.message) || "登录失败", icon: "none" });
    } finally {
      this.setData({ loggingIn: false });
    }
  },

  adminLogout() {
    wx.removeStorageSync("adminToken");
    this.setData({ hasAdminToken: false });
    wx.showToast({ title: "已退出管理员", icon: "none" });
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
      const url = `/admin/contents?keyword=${encodeURIComponent(this.data.keyword || "")}&status=${this.data.status}`;
      const res = await request({ url });
      const data = (res && res.data) || {};
      this.setData({ list: data.items || [] });
    } catch (e) {
      wx.showToast({ title: (e && e.message) || "加载失败", icon: "none" });
      this.setData({ list: [] });
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
        content_type: item.content_type || "article",
        chapter: item.chapter || "",
        sub_chapter: item.sub_chapter || "",
        summary: item.summary || "",
        body: item.body || "",
        status: item.status || "draft",
        review_status: item.review_status || "pending",
        quality_score: item.quality_score == null ? 0.9 : item.quality_score,
        is_featured: !!item.is_featured,
        published_at: item.published_at ? String(item.published_at).slice(0, 19) : "",
        created_by: item.created_by || null
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
    const form = this.data.form;
    if (!form.title || !form.content_type) {
      wx.showToast({ title: "标题和类型必填", icon: "none" });
      return;
    }
    if (this.data.saving) return;
    this.setData({ saving: true });
    try {
      const editingId = this.data.editingId;
      const payload = {
        ...form,
        quality_score: Number(form.quality_score || 0),
        created_by: form.created_by ? Number(form.created_by) : null
      };
      if (editingId) {
        await request({ url: `/admin/contents/${editingId}`, method: "PUT", data: payload });
      } else {
        await request({ url: "/admin/contents", method: "POST", data: payload });
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

  async toggleStatus(e) {
    const { id, status } = e.currentTarget.dataset;
    const next = status === "published" ? "draft" : "published";
    try {
      await request({ url: `/admin/contents/${id}/status?status=${next}`, method: "PUT" });
      wx.showToast({ title: next === "published" ? "已上架" : "已下架", icon: "success" });
      this.fetchList();
    } catch (er) {
      wx.showToast({ title: (er && er.message) || "操作失败", icon: "none" });
    }
  },

  async toggleFeatured(e) {
    const { id, featured } = e.currentTarget.dataset;
    try {
      await request({ url: `/admin/contents/${id}/feature?is_featured=${featured ? 'false' : 'true'}`, method: "PUT" });
      wx.showToast({ title: featured ? "已取消精选" : "已设精选", icon: "success" });
      this.fetchList();
    } catch (er) {
      wx.showToast({ title: (er && er.message) || "操作失败", icon: "none" });
    }
  },

  async removeItem(e) {
    const id = e.currentTarget.dataset.id;
    wx.showModal({
      title: "确认删除",
      content: "删除后不可恢复，是否继续？",
      success: async (r) => {
        if (!r.confirm) return;
        try {
          await request({ url: `/admin/contents/${id}`, method: "DELETE" });
          wx.showToast({ title: "已删除", icon: "success" });
          this.fetchList();
        } catch (er) {
          wx.showToast({ title: (er && er.message) || "删除失败", icon: "none" });
        }
      }
    });
  }
});
