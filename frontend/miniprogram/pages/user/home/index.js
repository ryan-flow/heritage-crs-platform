const { request } = require("../../../utils/request");
const { toAbsoluteMediaUrl } = require("../../../utils/media");
const { HERO_DIGITAL_HUMAN_LINE } = require("../../../utils/digital-human-local");

function buildHost() {
  const app = getApp();
  return (app.globalData.apiBaseUrl || "").replace(/\/api\/v1$/, "");
}

function shortenReason(text, fallback) {
  const raw = String(text || "").trim();
  if (!raw) return fallback;
  const normalized = raw.replace(/推荐理由[:：]?/g, "").trim();
  const firstSentence = normalized.split(/[。！？!?,，；;]/)[0].trim();
  const brief = firstSentence || normalized;
  return brief.length > 16 ? `${brief.slice(0, 16)}…` : brief;
}

function buildRecommendSnippet(item, type) {
  if (!item) return "";
  if (type === "content") {
    return String(item.summary || "").trim();
  }
  if (type === "event") {
    const description = String(item.description || "").trim();
    if (description) return description;
    const location = String(item.location || "").trim();
    const startTime = String(item.start_time || item.startTime || "").trim();
    const dateText = startTime ? startTime.slice(0, 10) : "";
    return [location, dateText].filter(Boolean).join(" · ");
  }
  const content = String(item.content || "").replace(/\s+/g, " ").trim();
  if (!content) return "";
  const sentences = content
    .split(/(?<=[。！？!?])/)
    .map((part) => part.trim())
    .filter(Boolean)
    .slice(0, 2);
  return sentences.join("");
}

function shortenSnippet(text, fallback) {
  const raw = String(text || "").replace(/\s+/g, " ").trim();
  if (!raw) return fallback;
  return raw.length > 30 ? `${raw.slice(0, 30)}…` : raw;
}

function buildPrimaryRecommend(recommend) {
  const firstContent = (recommend.contents || [])[0] || null;
  if (firstContent) {
    return {
      type: "content",
      id: firstContent.id,
      title: firstContent.title,
      cover_url: toAbsoluteMediaUrl(firstContent.cover_url),
      summary: firstContent.summary || "推荐阅读",
      note: shortenReason(firstContent.reason, "适合入门阅读"),
      actionText: "先看这篇"
    };
  }
  const firstEvent = (recommend.events || [])[0] || null;
  if (firstEvent) {
    return {
      type: "event",
      id: firstEvent.id,
      title: firstEvent.title,
      cover_url: toAbsoluteMediaUrl(firstEvent.cover_url),
      summary: shortenReason(firstEvent.reason, "热门活动推荐"),
      note: `${firstEvent.location || "地点待定"} · ${firstEvent.status === "open" ? "开放报名" : "已关闭"}`,
      actionText: "去看活动"
    };
  }
  const firstTopic = (recommend.topics || [])[0] || null;
  if (firstTopic) {
    return {
      type: "topic",
      id: firstTopic.id,
      title: firstTopic.title,
      cover_url: toAbsoluteMediaUrl(firstTopic.cover_url),
      summary: shortenReason(firstTopic.reason, "热门讨论"),
      note: "点击查看社区讨论",
      actionText: "去看讨论"
    };
  }
  return null;
}

Page({
  data: {
    recommend: {
      guide_text: "",
      contents: [],
      events: [],
      topics: [],
      profile_summary: null
    },
    strategySummary: "",
    primaryRecommend: null,
    // CRS v2.0.8：首页CRS主线文案
    crsState: {
      mode: "",
      confidence_score: 0,
      confidence_score_raw: 0,
      stage_progress_percent: 0,
      need_cold_start: false
    },
    crsModeDisplay: "",
    crsConfidencePercent: 0,
    heroMood: "curious",
    heroState: "open",
    heroTitle: "用AI发现你喜欢的非遗",
    heroDesc: "聊天、获取推荐、参与活动",
    heroCtaText: "立即开始",
    heroBubbleText: ""
  },

  syncTabBar(selected) {
    const tabBar = typeof this.getTabBar === "function" && this.getTabBar();
    if (tabBar && typeof tabBar.setData === "function") {
      tabBar.setData({ selected });
    }
  },

  onShow() {
    this.syncTabBar(0);
    const session = wx.getStorageSync("session");
    if (!session || !session.userId) {
      wx.reLaunch({ url: "/pages/auth/login/index" });
      return;
    }
    this.fetchRecommend(session.userId);
  },

  fetchRecommend(userId) {
    request({ url: `/recommend/?user_id=${userId}&scene=home` })
      .then((res) => {
        // 后端返回 {code, message, data} 格式，真正的推荐数据在 data 字段里
        const recommend = (res && res.data) || res || { guide_text: "", contents: [], events: [], topics: [], profile_summary: null, scene: "home" };
        // CRS v2.0.8：CRS模式驱动首页文案
        const crsState = recommend.crs_state || recommend.crsState || { mode: "", confidence_score: 0, need_cold_start: false };
        const modeMap = {
          cold_start: "想认识你",
          mixed: "正在了解你",
          precision: "已懂你"
        };
        const crsMode = crsState.mode || "";
        const heroText = {
          title: "和黑塔聊聊",
          desc: "已经准备好你感兴趣的推荐了",
          cta: "开始聊天",
          bubble: ""
        };
        const heroMood = crsMode === "precision" ? "confident" : crsMode === "mixed" ? "thinking" : "curious";
        // cover_url 转绝对路径
        (recommend.contents || []).forEach((c) => {
          c.cover_url = toAbsoluteMediaUrl(c.cover_url);
          c.reason = shortenReason(c.reason, "适合继续阅读");
          c.snippet = shortenSnippet(buildRecommendSnippet(c, "content"), "查看内容详情");
        });
        (recommend.events || []).forEach((e) => {
          e.cover_url = toAbsoluteMediaUrl(e.cover_url);
          e.reason = shortenReason(e.reason, "适合优先报名");
          e.snippet = shortenSnippet(buildRecommendSnippet(e, "event"), "查看活动信息");
        });
        (recommend.topics || []).forEach((t) => {
          t.cover_url = toAbsoluteMediaUrl(t.cover_url);
          t.reason = shortenReason(t.reason, "适合继续讨论");
          t.snippet = shortenSnippet(buildRecommendSnippet(t, "topic"), "查看讨论详情");
        });
        const primaryRecommend = buildPrimaryRecommend(recommend);
        const dedupedRecommend = {
          ...recommend,
          contents: primaryRecommend && primaryRecommend.type === "content"
            ? (recommend.contents || []).filter((item) => item.id !== primaryRecommend.id)
            : (recommend.contents || []),
          events: primaryRecommend && primaryRecommend.type === "event"
            ? (recommend.events || []).filter((item) => item.id !== primaryRecommend.id)
            : (recommend.events || []),
          topics: primaryRecommend && primaryRecommend.type === "topic"
            ? (recommend.topics || []).filter((item) => item.id !== primaryRecommend.id)
            : (recommend.topics || [])
        };
        this.setData({
          recommend: dedupedRecommend,
          strategySummary: (recommend.profile_summary && recommend.profile_summary.summary_text) || "",
          primaryRecommend,
          crsState,
          crsModeDisplay: modeMap[crsMode] || "",
          crsConfidencePercent: Number(crsState.stage_progress_percent || 0),
          heroMood,
          heroState: "open",
          heroTitle: heroText.title,
          heroDesc: heroText.desc,
          heroCtaText: heroText.cta,
          heroBubbleText: heroText.bubble
        });
        // 同步CRS模式到全局，FAB黑塔可读取
        const app = getApp();
        if (app && app.globalData) {
          app.globalData.crsMode = crsState.mode || "";
        }

        [
          ...(recommend.contents || []).slice(0, 2).map((item) => ({ ...item, target_type: "content" })),
          ...(recommend.events || []).slice(0, 2).map((item) => ({ ...item, target_type: "event" })),
          ...(recommend.topics || []).slice(0, 2).map((item) => ({ ...item, target_type: "topic" }))
        ].forEach((item) => {
          request({
            url: "/recommend/track",
            method: "POST",
            data: {
              user_id: userId || null,
              action: "expose",
              target_type: item.target_type,
              target_id: item.id,
              source_scene: "home_page"
            }
          }).catch(() => {});
        });
      })
      .catch(() => {});
  },

  onHide() {
    this.stopHeroInteraction();
  },

  onUnload() {
    this.stopHeroInteraction(true);
  },

  ensureHeroAudio() {
    if (this.heroAudio) return;
    this.heroAudio = wx.createInnerAudioContext();
    this.heroAudio.obeyMuteSwitch = false;
    this.heroAudio.onEnded(() => {
      this.restoreHeroInteractionState();
    });
    this.heroAudio.onError(() => {
      this.restoreHeroInteractionState();
      wx.showToast({ title: "语音播报失败", icon: "none" });
    });
  },

  restoreHeroInteractionState() {
    if (this.heroInteractionTimer) {
      clearTimeout(this.heroInteractionTimer);
      this.heroInteractionTimer = null;
    }
    this.setData({
      heroState: "open",
      heroMood: this.data.crsState.mode === "precision" ? "confident" : this.data.crsState.mode === "mixed" ? "thinking" : "curious"
    });
  },

  stopHeroInteraction() {
    if (this.heroInteractionTimer) {
      clearTimeout(this.heroInteractionTimer);
      this.heroInteractionTimer = null;
    }
    if (this.heroAudio) {
      try {
        this.heroAudio.stop();
      } catch (e) {}
    }
    this.restoreHeroInteractionState();
  },

  async playHeroInteractionAudio(text, localAudioPath) {
    const content = String(text || "").trim();
    if (!content) return;

    this.ensureHeroAudio();
    let finalAudioSrc = String(localAudioPath || "").trim();

    if (!finalAudioSrc) {
      const res = await request({
        url: "/ai/tts",
        method: "POST",
        data: { text: content }
      });
      const audioUrl = res && res.data && res.data.audio_url;
      if (res && res.code !== 0) {
        throw new Error(res.message || "TTS 服务返回错误");
      }
      if (!audioUrl || typeof audioUrl !== "string" || !audioUrl.startsWith("/")) {
        throw new Error("音频地址无效");
      }
      finalAudioSrc = `${buildHost()}${audioUrl}`;
    }

    try {
      this.heroAudio.stop();
    } catch (e) {}
    this.heroAudio.src = finalAudioSrc;
    this.heroAudio.play();
  },

  async triggerHeroDigitalHumanInteraction() {
    const line = HERO_DIGITAL_HUMAN_LINE || {};
    const text = String(line.text || "").trim();
    const mood = line.mood || "confident";
    const state = line.state || "speaking";

    if (this.heroInteractionTimer) {
      clearTimeout(this.heroInteractionTimer);
      this.heroInteractionTimer = null;
    }

    this.setData({
      heroMood: mood,
      heroState: state
    });

    const audioPath = String(line.audioPath || "").trim();
    try {
      await this.playHeroInteractionAudio(text, audioPath);
    } catch (e) {
      this.heroInteractionTimer = setTimeout(() => {
        this.restoreHeroInteractionState();
      }, 2600);
      wx.showToast({ title: "语音服务暂不可用", icon: "none" });
    }
  },

  toAi() {
    wx.navigateTo({ url: "/pages/user/ai/index" });
  },

  toHistory() {
    wx.navigateTo({ url: "/pages/user/history/index" });
  },

  toPlaces() {
    wx.navigateTo({ url: "/pages/user/places/index" });
  },

  toCulture() {
    wx.navigateTo({ url: "/pages/user/culture/index" });
  },

  toDiscussion() {
    wx.switchTab({ url: "/pages/user/discussion/index" });
  },

  toContent() {
    wx.switchTab({ url: "/pages/user/content/index" });
  },

  toActivity() {
    wx.switchTab({ url: "/pages/user/activity/index" });
  },

  toContentDetail(e) {
    const id = e.currentTarget.dataset.id;
    const session = wx.getStorageSync("session") || {};
    request({
      url: "/recommend/track",
      method: "POST",
      data: { user_id: session.userId || null, action: "click", target_type: "content", target_id: id, source_scene: "home_page" }
    }).catch(() => {});
    wx.navigateTo({ url: `/pages/user/content/detail/index?id=${id}` });
  },

  toEventDetail(e) {
    const id = e.currentTarget.dataset.id;
    const session = wx.getStorageSync("session") || {};
    request({
      url: "/recommend/track",
      method: "POST",
      data: { user_id: session.userId || null, action: "click", target_type: "event", target_id: id, source_scene: "home_page" }
    }).catch(() => {});
    wx.navigateTo({ url: `/pages/user/activity/detail/index?id=${id}` });
  },

  toTopicDetail(e) {
    const id = e.currentTarget.dataset.id;
    const session = wx.getStorageSync("session") || {};
    request({
      url: "/recommend/track",
      method: "POST",
      data: { user_id: session.userId || null, action: "click", target_type: "topic", target_id: id, source_scene: "home_page" }
    }).catch(() => {});
    wx.navigateTo({ url: `/pages/user/discussion/detail/index?id=${id}` });
  },

  openPrimaryRecommend(e) {
    const { id, type } = e.currentTarget.dataset;
    if (!id) return;
    const session = wx.getStorageSync("session") || {};
    request({
      url: "/recommend/track",
      method: "POST",
      data: { user_id: session.userId || null, action: "click", target_type: type === "event" ? "event" : type === "topic" ? "topic" : "content", target_id: id, source_scene: "home_page" }
    }).catch(() => {});
    if (type === "event") {
      wx.navigateTo({ url: `/pages/user/activity/detail/index?id=${id}` });
      return;
    }
    if (type === "topic") {
      wx.navigateTo({ url: `/pages/user/discussion/detail/index?id=${id}` });
      return;
    }
    wx.navigateTo({ url: `/pages/user/content/detail/index?id=${id}` });
  }
});
