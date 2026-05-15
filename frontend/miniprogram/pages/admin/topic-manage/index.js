const { request } = require("../../../utils/request");

function emptyForm() {
  return {
    title: "",
    nickname: "运营同学",
    content: "",
    cover_url: "",
    like_count: 0,
    favorite_count: 0,
    comment_count: 0,
    is_featured: false
  };
}

Page({
  data: {
    loading: false,
    keyword: "",
    list: [],
    showForm: false,
    editingId: null,
    form: emptyForm(),
    saving: false
  },

  onShow() {
    this.fetchList();
  },

  onKeywordInput(e) {
    this.setData({ keyword: e.detail.value || "" });
  },

  async fetchList() {
    this.setData({ loading: true });
    try {
      const url = `/admin/topics?keyword=${encodeURIComponent(this.data.keyword || "")}`;
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

  openEdit(e) {
    const item = e.currentTarget.dataset.item;
    if (!item) return;
    this.setData({
      showForm: true,
      editingId: item.id,
      form: {
        title: item.title || "",
        nickname: item.nickname || "运营同学",
        content: item.content || "",
        cover_url: item.cover_url || "",
        like_count: item.like_count || 0,
        favorite_count: item.favorite_count || 0,
        comment_count: item.comment_count || 0,
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
    if (!this.data.editingId) return;
    if (this.data.saving) return;
    const form = this.data.form;
    if (!form.title || !form.content) {
      wx.showToast({ title: "标题和内容必填", icon: "none" });
      return;
    }
    this.setData({ saving: true });
    try {
      await request({
        url: `/admin/topics/${this.data.editingId}`,
        method: "PUT",
        data: {
          ...form,
          like_count: Number(form.like_count || 0),
          favorite_count: Number(form.favorite_count || 0),
          comment_count: Number(form.comment_count || 0)
        }
      });
      wx.showToast({ title: "保存成功", icon: "success" });
      this.closeForm();
      this.fetchList();
    } catch (e) {
      wx.showToast({ title: (e && e.message) || "保存失败", icon: "none" });
    } finally {
      this.setData({ saving: false });
    }
  },

  async toggleFeatured(e) {
    const { id, featured } = e.currentTarget.dataset;
    try {
      await request({ url: `/admin/topics/${id}/feature?is_featured=${featured ? 'false' : 'true'}`, method: "PUT" });
      wx.showToast({ title: featured ? "已取消精选" : "已设精选", icon: "success" });
      this.fetchList();
    } catch (er) {
      wx.showToast({ title: (er && er.message) || "操作失败", icon: "none" });
    }
  }
});
