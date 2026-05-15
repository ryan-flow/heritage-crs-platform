const { request } = require("../../../utils/request");
const digitalHuman = require("../../../utils/digital-human");
const { toAbsoluteMediaUrl } = require("../../../utils/media");

function monthOf(v) {
  if (!v) return "";
  const s = String(v);
  const m = s.match(/-(\d{2})-/);
  return m ? m[1] : "";
}

function formatMonthText(monthKey) {
  if (!monthKey) return "时间待定";
  return `${monthKey} 月活动`;
}

function shortenReason(text, fallback) {
  const raw = String(text || "").trim();
  if (!raw) return fallback;
  const normalized = raw.replace(/推荐理由[:：]?/g, "").trim();
  const firstSentence = normalized.split(/[。！？!?,，；;]/)[0].trim();
  const brief = firstSentence || normalized;
  return brief.length > 16 ? `${brief.slice(0, 16)}…` : brief;
}

Page({
  behaviors: [digitalHuman],

  data: {
    list: [],
    loading: false,
    recommend: {
      guide_text: "",
      contents: [],
      events: [],
      topics: []
    },
    monthFilter: "all",
    months: ["all", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"],
    successFxId: null,
  },

  syncTabBar(selected) {
    const tabBar = typeof this.getTabBar === "function" && this.getTabBar();
    if (tabBar && typeof tabBar.setData === "function") {
      tabBar.setData({ selected });
    }
  },

  onShow() {
    this.syncTabBar(2);
    const session = wx.getStorageSync("session") || {};
    this.fetchList();
    this.fetchRecommend(session.userId || "");
    this.initDigitalHuman("activity");
  },

  onUnload() {
    this.destroyDigitalHuman();
  },

  onHide() {
    if (this.digitalHumanAudio) {
      try {
        this.digitalHumanAudio.stop();
      } catch (e) {}
    }
    this.setData({ digitalHumanSpeaking: false });
  },

  onPullDownRefresh() {
    this.fetchList(true);
  },

  switchMonth(e) {
    const monthFilter = e.currentTarget.dataset.month || "all";
    this.setData({ monthFilter }, () => this.fetchList());
  },

  async fetchList(byRefresh = false) {
    this.setData({ loading: true });
    try {
      const res = await request({ url: "/events" });
      const data = (res && res.data) || {};
      let list = (data.items || []).map((it, idx) => {
        const month_key = monthOf(it.start_time);
        const max = Number(it.max_participants || 0);
        const heatText = idx < 2 ? "本月主推" : idx < 6 ? "参与度较高" : formatMonthText(month_key);
        return {
          ...it,
          cover_full_url: toAbsoluteMediaUrl(it.cover_url),
          month_key,
          heat_text: heatText,
          quota_text: max ? `${max} 人以内` : "人数待定"
        };
      });
      if (this.data.monthFilter !== "all") {
        list = list.filter((it) => it.month_key === this.data.monthFilter);
      }
      this.setData({ list });
    } catch (e) {
      wx.showToast({ title: "活动加载失败", icon: "none" });
    } finally {
      this.setData({ loading: false });
      if (byRefresh) wx.stopPullDownRefresh();
    }
  },

  async fetchRecommend(userId) {
    try {
      const res = await request({ url: `/recommend?user_id=${userId}&scene=activity` });
      const recommend = (res && res.data) || { guide_text: "", contents: [], events: [], topics: [], profile_summary: null, scene: "activity" };
      recommend.events = (recommend.events || []).map((item) => ({
        ...item,
        cover_url: toAbsoluteMediaUrl(item.cover_url),
        reason: shortenReason(item.reason, "适合优先报名")
      }));
      this.setData({ recommend });

      const exposes = recommend.events || [];
      exposes.forEach((it) => {
        request({
          url: "/recommend/track",
          method: "POST",
          data: {
            user_id: userId || null,
            action: "expose",
            target_type: "event",
            target_id: it.id,
            source_scene: "activity_page"
          }
        }).catch(() => {});
      });
    } catch (e) {}
  },

  toDetail(e) {
    const id = e.currentTarget.dataset.id;
    const session = wx.getStorageSync("session") || {};
    request({
      url: "/recommend/track",
      method: "POST",
      data: {
        user_id: session.userId || null,
        action: "click",
        target_type: "event",
        target_id: id,
        source_scene: "activity_page"
      }
    }).catch(() => {});
    wx.navigateTo({ url: `/pages/user/activity/detail/index?id=${id}` });
  },

  toRegisterFx(e) {
    const id = Number(e.currentTarget.dataset.id);
    this.setData({ successFxId: id });
    setTimeout(() => this.setData({ successFxId: null }), 900);
    wx.navigateTo({ url: `/pages/user/activity/register/index?eventId=${id}` });
  },

  toContentDetail(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/user/content/detail/index?id=${id}` });
  }
});
