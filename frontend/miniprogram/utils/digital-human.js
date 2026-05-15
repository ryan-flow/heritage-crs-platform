/* global wx, getApp, Behavior, clearInterval, clearTimeout, setInterval, setTimeout, module */

const { request } = require("./request");

const GUIDE_TEXT = {
  content: "有什么想了解的，直接问。",
  activity: "想了解哪场活动，直接问。",
  ai: "有什么想了解的，直接问。"
};

const PERSONA = {
  name: "黑塔",
  title: "非遗数字策展员"
};

function buildHost() {
  const app = getApp();
  return (app.globalData.apiBaseUrl || "").replace(/\/api\/v1$/, "");
}

function stateMeta(scene, speaking, expanded) {
  if (speaking) {
    return {
      mood: "讲解中",
      bubble: scene === "activity" ? "正在帮你梳理活动。" : scene === "ai" ? "正在讲解。" : "正在梳理重点。"
    };
  }
  if (expanded) {
    return {
      mood: "待回应",
      bubble: scene === "activity" ? "想了解哪场活动？" : scene === "ai" ? "有问题随时问。" : "有什么想了解的？"
    };
  }
  return {
    mood: scene === "activity" ? "活动筛选" : scene === "ai" ? "问答助手" : "内容导览",
    bubble: scene === "activity" ? "点击提问关于活动。" : scene === "ai" ? "不懂就问。" : "有问题可以问我。"
  };
}

module.exports = Behavior({
  data: {
    digitalHumanVisible: true,
    digitalHumanExpanded: false,
    digitalHumanInput: "",
    digitalHumanMessages: [],
    digitalHumanSending: false,
    digitalHumanSpeaking: false,
    digitalHumanScene: "content",
    digitalHumanLiveCaption: "",
    digitalHumanCaptionVisible: false,
    digitalHumanCaptionProgress: 0,
    digitalHumanPersonaName: PERSONA.name,
    digitalHumanPersonaTitle: PERSONA.title,
    digitalHumanMood: "内容导览",
    digitalHumanBubble: "这页我已经替你看过一遍了。",
    digitalHumanVisualState: "idle",
    scrollToMsg: ""
  },

  methods: {
    syncDigitalHumanStage() {
      const meta = stateMeta(this.data.digitalHumanScene, this.data.digitalHumanSpeaking, this.data.digitalHumanExpanded);
      const visualState = this.data.digitalHumanSpeaking
        ? "speaking"
        : this.data.digitalHumanExpanded
          ? "open"
          : "idle";
      this.setData({
        digitalHumanMood: meta.mood,
        digitalHumanBubble: meta.bubble,
        digitalHumanVisualState: visualState
      });
    },

    async initDigitalHuman(scene) {
      const currentScene = scene || "content";
      const greeting = GUIDE_TEXT[currentScene] || GUIDE_TEXT.content;
      const messages = [{ role: "guide", text: greeting }];
      // 预处理长文本：按换行符拆分为多行，避免单段溢出
      messages.forEach((m) => {
        m.textLines = String(m.text || "").split(/\n/).filter((l) => l.trim());
      });
      this.setData({
        digitalHumanScene: currentScene,
        digitalHumanVisible: true,
        digitalHumanExpanded: false,
        digitalHumanInput: "",
        digitalHumanMessages: messages,
        digitalHumanLiveCaption: greeting,
        digitalHumanCaptionVisible: false,
        digitalHumanCaptionProgress: 0,
        digitalHumanSpeaking: false
      });
      this.syncDigitalHumanStage();
      const session = wx.getStorageSync("session") || {};
      if (session.userId) {
        try {
          const res = await request({ url: `/recommend?user_id=${session.userId}` });
          const data = (res && res.data) || {};
          const recommendText = data.guide_text;
          if (recommendText) {
            this.setData({
              digitalHumanMessages: messages.concat([{ role: "guide", text: recommendText }]),
              digitalHumanLiveCaption: recommendText,
              digitalHumanBubble: currentScene === "activity" ? "我替你把推荐活动先挑出来了。" : "我已经先帮你整理好推荐路径了。"
            });
          }
        } catch (e) {}
      }
    },

    ensureDigitalHumanAudio() {
      if (this.digitalHumanAudio) return;
      this.digitalHumanAudio = wx.createInnerAudioContext();
      this.digitalHumanAudio.obeyMuteSwitch = false;
      this.digitalHumanAudio.onEnded(() => {
        this.stopDigitalHumanCaptionTimer();
        this.setData({
          digitalHumanSpeaking: false,
          digitalHumanCaptionProgress: 100,
          digitalHumanCaptionVisible: false
        });
        this.syncDigitalHumanStage();
      });
      this.digitalHumanAudio.onError(() => {
        this.stopDigitalHumanCaptionTimer();
        this.setData({
          digitalHumanSpeaking: false,
          digitalHumanCaptionVisible: false
        });
        this.syncDigitalHumanStage();
        wx.showToast({ title: "讲解播报失败", icon: "none" });
      });
    },

    stopDigitalHumanCaptionTimer() {
      if (this.digitalHumanCaptionTimer) {
        clearInterval(this.digitalHumanCaptionTimer);
        this.digitalHumanCaptionTimer = null;
      }
    },

    runDigitalHumanCaption(text) {
      const content = String(text || "").trim();
      this.stopDigitalHumanCaptionTimer();
      if (!content) {
        this.setData({
          digitalHumanLiveCaption: "",
          digitalHumanCaptionVisible: false,
          digitalHumanCaptionProgress: 0
        });
        return;
      }
      this.setData({
        digitalHumanLiveCaption: "",
        digitalHumanCaptionVisible: true,
        digitalHumanCaptionProgress: 0
      });
      let cursor = 0;
      const step = content.length > 120 ? 3 : 2;
      this.digitalHumanCaptionTimer = setInterval(() => {
        cursor = Math.min(content.length, cursor + step);
        const progress = Math.round((cursor / content.length) * 100);
        this.setData({
          digitalHumanLiveCaption: content.slice(0, cursor),
          digitalHumanCaptionProgress: progress
        });
        if (cursor >= content.length) {
          this.stopDigitalHumanCaptionTimer();
        }
      }, 90);
    },

    async narrateDigitalHumanText(text) {
      const content = String(text || "").trim();
      if (!content) {
        wx.showToast({ title: "暂无可播报内容", icon: "none" });
        return;
      }
      this.ensureDigitalHumanAudio();
      try {
        if (this.data.digitalHumanSpeaking) {
          this.digitalHumanAudio.stop();
          this.stopDigitalHumanCaptionTimer();
          this.setData({
            digitalHumanSpeaking: false,
            digitalHumanCaptionVisible: false
          });
          this.syncDigitalHumanStage();
          return;
        }
        this.setData({
          digitalHumanSpeaking: true,
          digitalHumanLiveCaption: content,
          digitalHumanBubble: "我在讲，先别急着往下翻。"
        });
        this.syncDigitalHumanStage();
        if (typeof this.clearTypingTimer === "function") {
          this.clearTypingTimer();
        }
        this.setData({ speakingIndex: -1 });
        this.runDigitalHumanCaption(content);
        // 请求 TTS 音频
        let audioUrl = null;
        try {
          const res = await request({
            url: "/ai/tts",
            method: "POST",
            data: { text: content }
          });
          audioUrl = res && res.data && res.data.audio_url;
          // 检查后端是否返回了错误（code !== 0）
          if (res && res.code !== 0) {
            throw new Error(res.message || "TTS 服务返回错误");
          }
        } catch (netErr) {
          console.warn("TTS 请求失败:", netErr);
          throw new Error("语音服务暂时不可用");
        }

        if (!audioUrl || typeof audioUrl !== "string" || !audioUrl.startsWith("/")) {
          throw new Error("音频地址无效");
        }
        // 构建完整 URL：apiBaseUrl 去掉 /api/v1 后缀 + 返回的静态路径
        const host = buildHost();
        const fullUrl = `${host}${audioUrl}`;
        console.log("[digital-human] TTS audio:", fullUrl);
        this.digitalHumanAudio.src = fullUrl;

        // 使用 Promise 包装播放，捕获解码错误
        await new Promise((resolvePlay, rejectPlay) => {
          const onPlayError = (err) => {
            console.error("[digital-human] Audio play failed:", err?.errMsg || err);
            rejectPlay(new Error(err?.errMsg || "音频播放失败"));
          };
          // 先清除旧的错误回调
          this.digitalHumanAudio.offError();
          this.digitalHumanAudio.onError(onPlayError);
          this.digitalHumanAudio.play();
          // 给 500ms 让底层检测解码问题
          setTimeout(() => resolvePlay(), 500);
        });
      } catch (e) {
        console.error("[digital-human] narrate failed:", e);
        this.stopDigitalHumanCaptionTimer();
        // 修复：TTS失败后更新bubble为已就绪状态，避免卡在"待回应"
        this.setData({
          digitalHumanSpeaking: false,
          digitalHumanCaptionVisible: false,
          digitalHumanBubble: "语音播报失败，但文字回复已经准备好了。"
        });
        this.syncDigitalHumanStage();
        // 区分错误类型给出提示
        const msg = (e.message || "");
        if (msg.includes("不可用") || msg.includes("服务")) {
          wx.showToast({ title: "语音服务暂不可用", icon: "none", duration: 2000 });
        } else if (msg.includes("地址") || msg.includes("解码")) {
          wx.showToast({ title: "音频文件异常", icon: "none", duration: 2000 });
        } else {
          wx.showToast({ title: "播报失败", icon: "none", duration: 1500 });
        }
      }
    },

    toggleDigitalHuman() {
      this.setData({ digitalHumanExpanded: !this.data.digitalHumanExpanded });
      this.syncDigitalHumanStage();
    },

    closeDigitalHumanPanel() {
      this.setData({ digitalHumanExpanded: false });
      this.syncDigitalHumanStage();
    },

    onDigitalHumanInput(e) {
      this.setData({ digitalHumanInput: e.detail.value || "" });
    },

    async sendDigitalHumanQuestion() {
      const question = String(this.data.digitalHumanInput || "").trim();
      if (!question || this.data.digitalHumanSending) return;
      const session = wx.getStorageSync("session") || {};
      const nextMessages = (this.data.digitalHumanMessages || []).concat([{ role: "user", text: question }]);
      this.setData({
        digitalHumanSending: true,
        digitalHumanInput: "",
        digitalHumanExpanded: true,
        digitalHumanMessages: nextMessages,
        digitalHumanBubble: "正在思考...",
        scrollToMsg: "dhMsgBottom"
      });
      this.syncDigitalHumanStage();
      try {
        const res = await request({
          url: "/ai/chat",
          method: "POST",
          data: {
            question,
            user_id: session.userId || null
          }
        });
        const answer = (res.data && res.data.answer) || "暂时没有答案，换个问题试试。";
        const answerLines = String(answer).split(/\n/).filter((l) => l.trim());
        this.setData({
          digitalHumanMessages: nextMessages.concat([{ role: "guide", text: answer, textLines: answerLines }]),
          digitalHumanLiveCaption: answer,
          digitalHumanBubble: "整理好了，可以语音播报。",
          scrollToMsg: "dhMsgBottom"
        });
        // TTS 播报失败不影响对话展示
        this.narrateDigitalHumanText(answer).catch((e) => {
          console.warn("[digital-human] auto-tts failed:", e.message);
        });
      } catch (e) {
        wx.showToast({ title: "数字人回复失败", icon: "none" });
      } finally {
        this.setData({ digitalHumanSending: false });
        this.syncDigitalHumanStage();
      }
    },

    async speakDigitalHumanLatest() {
      const messages = this.data.digitalHumanMessages || [];
      const latestGuideMessage = [...messages].reverse().find((item) => item.role === "guide" && item.text);
      await this.narrateDigitalHumanText(latestGuideMessage && latestGuideMessage.text);
    },

    destroyDigitalHuman() {
      this.stopDigitalHumanCaptionTimer();
      if (this.digitalHumanAudio) {
        try {
          this.digitalHumanAudio.destroy();
        } catch (e) {}
        this.digitalHumanAudio = null;
      }
    }
  }
});
