const { request } = require("../../../utils/request");

function buildPreferenceSummary(user) {
  if (!user) return "你还没有设置偏好，推荐会先按精选内容展示。";
  const parts = [];
  const heritage = (user.preferred_heritage_types || []).slice(0, 2).join(" / ");
  const scenes = (user.preferred_scene_types || []).slice(0, 1).join(" / ");
  const regions = (user.preferred_regions || []).slice(0, 1).join(" / ");
  if (heritage) parts.push(`偏好 ${heritage}`);
  if (scenes) parts.push(`常看 ${scenes}`);
  if (regions) parts.push(`关注 ${regions}`);
  return parts.length ? parts.join(" · ") : "你还没有设置偏好，推荐会先按精选内容展示。";
}

Page({
  data: {
    user: null,
    registrations: [],
    myTopics: [],
    portrait: null,
    portraitCards: [],
    feedbackCards: [],
    strategySummary: "",
    loading: false,
    preferenceSummary: "",
    prefChips: [],
    statCards: [],
    // CRS v2.0.6：CRS画像摘要
    crsSummary: {
      mode: "",
      modeDisplay: "",
      confidence: 0,
      dimensions: {}
    },
    // P0-4：6维信号摘要
    browseSummary: "",
    qaSummary: "",
    eventSummary: "",
    socialSummary: ""
  },

  noop() {},

  syncTabBar(selected) {
    const tabBar = typeof this.getTabBar === "function" && this.getTabBar();
    if (tabBar && typeof tabBar.setData === "function") {
      tabBar.setData({ selected });
    }
  },

  onShow() {
    this.syncTabBar(4);
    this.fetchProfile();
  },

  onPullDownRefresh() {
    this.fetchProfile(true);
  },

  async fetchProfile(byRefresh = false) {
    const session = wx.getStorageSync("session");
    if (!session || !session.userId) {
      wx.navigateTo({ url: "/pages/auth/login/index" });
      return;
    }
    this.setData({ loading: true });
    try {
      const userRes = await request({ url: `/users/me/${session.userId}` });
      const regRes = await request({ url: `/users/${session.userId}/registrations` });
      const portraitRes = await request({ url: `/users/${session.userId}/recommend-profile` });
      const topicRes = await request({ url: `/discussion/topics?user_id=${session.userId}&sort=new` });
      const user = userRes.data || null;
      const portraitData = (portraitRes && portraitRes.data) || {};
      const portrait = portraitData.portrait || null;
      const myTopics = ((topicRes && topicRes.data && topicRes.data.items) || [])
        .filter((it) => String(it.user_id) === String(session.userId))
        .slice(0, 20)
        .map((it) => ({
          ...it,
          created_date: String(it.created_at || "").slice(0, 10),
          heat_level_text: Number(it.heat_score || 0) >= 80 ? "当前最火" : Number(it.heat_score || 0) >= 45 ? "非常火" : "有点火"
        }));
      const registrations = (regRes.data && regRes.data.items) || [];
      const activity = portraitData.activity || {};
      const actionBreakdown = portraitData.action_breakdown || {};
      // 信号摘要构建
      const prefChips = []
        .concat((user?.preferred_heritage_types || []).slice(0, 3))
        .concat((user?.preferred_scene_types || []).slice(0, 2))
        .concat((user?.preferred_regions || []).slice(0, 2));
      const browseClicks = (actionBreakdown.content_click || 0) + (actionBreakdown.content_view || 0);
      const browseSummary = browseClicks > 0
        ? `浏览了 ${browseClicks} 次内容` + (browseClicks > 5 ? "，高频用户" : "")
        : "";
      const qaSummary = (activity.qa_count || 0) > 0
        ? `向黑塔提了 ${activity.qa_count} 个问题`
        : "";
      const eventSummary = (activity.registration_count || 0) > 0
        ? `报名了 ${activity.registration_count} 个活动`
        : "";
      const socialTotal = (activity.like_count || 0) + (activity.favorite_count || 0) + (activity.comment_count || 0);
      const socialSummary = socialTotal > 0
        ? `点赞${activity.like_count || 0} / 收藏${activity.favorite_count || 0} / 评论${activity.comment_count || 0}`
        : "";
      this.setData({
        user,
        registrations,
        myTopics,
        portrait,
        portraitCards: [
          { label: "偏好关键词", value: ((portrait && portrait.heritage_terms) || []).slice(0, 3).join(" / ") || "未形成" },
          { label: "活跃场景", value: ((portrait && portrait.scene_terms) || []).slice(0, 2).join(" / ") || "未形成" },
          { label: "关注地区", value: ((portrait && portrait.region_terms) || []).slice(0, 2).join(" / ") || "未形成" }
        ],
        feedbackCards: [
          { label: "内容反馈", value: (portraitRes.data && portraitRes.data.feedback && portraitRes.data.feedback.content) || 0 },
          { label: "活动反馈", value: (portraitRes.data && portraitRes.data.feedback && portraitRes.data.feedback.event) || 0 },
          { label: "讨论反馈", value: (portraitRes.data && portraitRes.data.feedback && portraitRes.data.feedback.topic) || 0 }
        ],
        strategySummary: (portrait && portrait.summary_text) || "",
        preferenceSummary: buildPreferenceSummary(user),
        prefChips,
        browseSummary,
        qaSummary,
        eventSummary,
        socialSummary,
        statCards: [
          { label: "我的发帖", value: myTopics.length },
          { label: "活动记录", value: registrations.length },
          { label: "已选偏好", value: (user?.preferred_heritage_types || []).length + (user?.preferred_scene_types || []).length + (user?.preferred_regions || []).length }
        ]
      });
    } catch (e) {
      wx.showToast({ title: "加载失败", icon: "none" });
    } finally {
      this.setData({ loading: false });
      if (byRefresh) wx.stopPullDownRefresh();
    }
    // CRS v2.0.6：异步加载CRS画像摘要
    this._loadCrsSummary(session.userId);
  },

  async _loadCrsSummary(userId) {
    try {
      const res = await request({
        url: "/ai/crs/state",
        method: "GET",
        data: { user_id: userId }
      });
      const data = (res && res.data) || {};
      const modeMap = {
        cold_start: "刚开始了解",
        mixed: "了解中",
        precision: "精准推荐"
      };
      const rawDims = data.dimensions || {};
      // 将原始权重转换为百分比显示
      const totalDim = (rawDims.explicit || 0) + (rawDims.implicit || 0) + (rawDims.dialogue || 0);
      const explicitPct = totalDim > 0 ? Math.round((rawDims.explicit || 0) / totalDim * 100) : 0;
      const implicitPct = totalDim > 0 ? Math.round((rawDims.implicit || 0) / totalDim * 100) : 0;
      const dialoguePct = totalDim > 0 ? Math.round((rawDims.dialogue || 0) / totalDim * 100) : 0;
      this.setData({
        crsSummary: {
          mode: data.mode || "cold_start",
          modeDisplay: modeMap[data.mode] || "刚开始了解",
          confidence: Math.round(data.confidence_score || 0),
          dimensions: {
            explicit: rawDims.explicit || 0,
            implicit: rawDims.implicit || 0,
            dialogue: rawDims.dialogue || 0,
            explicitPct,
            implicitPct,
            dialoguePct
          }
        }
      });
    } catch (e) {
      // 静默
    }
  },

  toPreferences() {
    wx.navigateTo({ url: "/pages/user/preferences/index" });
  },

  toTopicDetail(e) {
    const id = e.currentTarget.dataset.id;
    if (!id) return;
    wx.navigateTo({ url: `/pages/user/discussion/detail/index?id=${id}` });
  },

  changeNickname() {
    const currentName = this.data.user && this.data.user.nickname || "";
    wx.showModal({
      title: "修改昵称",
      editable: true,
      placeholderText: "输入新昵称",
      content: currentName,
      confirmText: "保存",
      confirmColor: "#9f2d22",
      success: (res) => {
        if (res.confirm && res.content && res.content.trim()) {
          const newName = res.content.trim().slice(0, 20);
          if (newName === currentName) return;
          this.updateNickname(newName);
        }
      }
    });
  },

  async updateNickname(name) {
    const session = wx.getStorageSync("session");
    if (!session || !session.userId) return;
    try {
      await request({
        url: `/users/me/${session.userId}`,
        method: "PUT",
        data: { nickname: name }
      });
      const user = this.data.user || {};
      user.nickname = name;
      this.setData({ user });
      wx.showToast({ title: "昵称已更新", icon: "success" });
    } catch (e) {
      wx.showToast({ title: "修改失败", icon: "none" });
    }
  },

  logout() {
    wx.removeStorageSync("session");
    wx.reLaunch({ url: "/pages/auth/login/index" });
  }
});
