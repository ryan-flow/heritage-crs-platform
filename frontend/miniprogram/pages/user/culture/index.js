const { request } = require("../../../utils/request");

Page({
  data: {
    list: [],
    loading: false
  },

  onShow() {
    this.fetchCulture();
  },

  async fetchCulture() {
    this.setData({ loading: true });
    try {
      const res = await request({ url: "/contents?status=published" });
      const items = ((res && res.data && res.data.items) || []).slice(0, 120);
      const grouped = {};
      items.forEach((it) => {
        const chapter = it.chapter || "非遗综合";
        const sub = it.sub_chapter || it.content_type || "专题";
        if (!grouped[chapter]) grouped[chapter] = [];
        grouped[chapter].push({
          id: it.id,
          name: it.title,
          note: `${sub} · ${it.summary || "点击进入详情"}`
        });
      });

      const list = Object.keys(grouped).map((chapter, idx) => ({
        id: `g${idx + 1}`,
        title: chapter,
        items: grouped[chapter]
      }));

      this.setData({ list });
    } catch (e) {
      wx.showToast({ title: "加载失败", icon: "none" });
    } finally {
      this.setData({ loading: false });
    }
  },

  toDetail(e) {
    const id = e.currentTarget.dataset.id;
    if (!id) return;
    wx.navigateTo({ url: `/pages/user/content/detail/index?id=${id}` });
  }
});
