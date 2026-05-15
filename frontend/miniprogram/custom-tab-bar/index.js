Component({
  data: {
    selected: 0,
    color: "#8c6a42",
    selectedColor: "#9f2d22",
    list: [
      { key: "ai", pagePath: "/pages/user/home/index", text: "主页" },
      { key: "content", pagePath: "/pages/user/content/index", text: "文化" },
      { key: "activity", pagePath: "/pages/user/activity/index", text: "活动" },
      { key: "discussion", pagePath: "/pages/user/discussion/index", text: "讨论" },
      { key: "profile", pagePath: "/pages/user/profile/index", text: "我的" }
    ]
  },

  lifetimes: {
    attached() {
      const pages = getCurrentPages();
      const current = pages.length ? `/${pages[pages.length - 1].route}` : "";
      const selected = this.data.list.findIndex((it) => it.pagePath === current);
      if (selected >= 0) this.setData({ selected });
    }
  },

  methods: {
    switchTab(e) {
      const data = e.currentTarget.dataset || {};
      const url = data.path;
      const index = Number(data.index || 0);
      if (!url) return;
      this.setData({ selected: index });
      wx.switchTab({ url });
    }
  }
});
