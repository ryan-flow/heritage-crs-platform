const { request } = require("../../../utils/request");
const { LOGIN_DIGITAL_HUMAN_LINE } = require("../../../utils/digital-human-local");

function buildHost() {
  const app = getApp();
  return (app.globalData.apiBaseUrl || "").replace(/\/api\/v1$/, "");
}

Page({
  data: {
    nickname: "",
    loading: false,
    loginHeroMood: "curious",
    loginHeroState: "open"
  },

  onShow() {
    const session = wx.getStorageSync("session");
    if (session && session.userId) {
      wx.reLaunch({ url: "/pages/user/home/index" });
    }
  },

  onHide() {
    this.stopLoginHeroInteraction();
  },

  onUnload() {
    this.stopLoginHeroInteraction(true);
  },

  ensureLoginHeroAudio() {
    if (this.loginHeroAudio) return;
    this.loginHeroAudio = wx.createInnerAudioContext();
    this.loginHeroAudio.obeyMuteSwitch = false;
    this.loginHeroAudio.onEnded(() => {
      this.restoreLoginHeroState();
    });
    this.loginHeroAudio.onError(() => {
      this.restoreLoginHeroState();
      wx.showToast({ title: "语音播报失败", icon: "none" });
    });
  },

  restoreLoginHeroState() {
    if (this.loginHeroTimer) {
      clearTimeout(this.loginHeroTimer);
      this.loginHeroTimer = null;
    }
    this.setData({
      loginHeroMood: "curious",
      loginHeroState: "open"
    });
  },

  stopLoginHeroInteraction(forceStop = false) {
    if (this.loginHeroTimer) {
      clearTimeout(this.loginHeroTimer);
      this.loginHeroTimer = null;
    }
    if (this.loginHeroAudio) {
      try {
        this.loginHeroAudio.stop();
      } catch (e) {}
    }
    if (forceStop) {
      this.setData({
        loginHeroMood: "curious",
        loginHeroState: "open"
      });
      return;
    }
    this.restoreLoginHeroState();
  },

  async playLoginHeroAudio(text, localAudioPath) {
    const content = String(text || "").trim();
    if (!content) return;

    this.ensureLoginHeroAudio();
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
      this.loginHeroAudio.stop();
    } catch (e) {}
    this.loginHeroAudio.src = finalAudioSrc;
    this.loginHeroAudio.play();
  },

  async triggerLoginHeroInteraction() {
    const line = LOGIN_DIGITAL_HUMAN_LINE || {};
    const text = String(line.text || "").trim();
    const mood = line.mood || "confident";
    const state = line.state || "speaking";

    if (this.loginHeroTimer) {
      clearTimeout(this.loginHeroTimer);
      this.loginHeroTimer = null;
    }

    this.setData({
      loginHeroMood: mood,
      loginHeroState: state
    });

    const audioPath = String(line.audioPath || "").trim();
    try {
      await this.playLoginHeroAudio(text, audioPath);
    } catch (e) {
      this.loginHeroTimer = setTimeout(() => {
        this.restoreLoginHeroState();
      }, 2600);
      wx.showToast({ title: "语音服务暂不可用", icon: "none" });
    }
  },

  onNicknameInput(e) {
    this.setData({ nickname: e.detail.value || "" });
  },

  doWxLogin() {
    if (this.data.loading) return;
    this.setData({ loading: true });

    wx.login({
      success: async (res) => {
        if (!res.code) {
          this.setData({ loading: false });
          wx.showToast({ title: "获取登录凭证失败", icon: "none" });
          return;
        }
        try {
          const apiRes = await request({
            url: "/auth/wx-login",
            method: "POST",
            data: {
              code: res.code,
              nickname: this.data.nickname || "微信用户"
            }
          });
          const data = apiRes.data || {};
          const session = {
            userId: data.user_id,
            openid: data.openid,
            role: data.role,
            token: data.openid
          };
          wx.setStorageSync("session", session);
          wx.showToast({ title: "登录成功", icon: "success" });
          setTimeout(() => {
            wx.reLaunch({ url: "/pages/user/home/index" });
          }, 300);
        } catch (err) {
          wx.showToast({ title: (err && err.message) || "登录失败", icon: "none" });
        } finally {
          this.setData({ loading: false });
        }
      },
      fail: () => {
        this.setData({ loading: false });
        wx.showToast({ title: "微信登录失败", icon: "none" });
      }
    });
  }
});
