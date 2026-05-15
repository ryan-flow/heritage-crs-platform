const digitalHuman = require("../../utils/digital-human");

/** CRS模式 → 黑塔表情映射 */
function crsModeToMood(mode) {
  if (mode === "precision") return "confident";
  if (mode === "mixed") return "thinking";
  return "curious";
}

Component({
  behaviors: [digitalHuman],

  properties: {
    scene: {
      type: String,
      value: "content"
    },
    /** 心情：curious(好奇) / thinking(思考) / confident(自信) */
    digitalHumanMood: {
      type: String,
      value: "curious"
    }
  },

  lifetimes: {
    attached() {
      this.initDigitalHuman(this.properties.scene || "content");
      this._syncCrsMood();
    },
    detached() {
      this.destroyDigitalHuman();
    }
  },

  methods: {
    /* 阻止触摸移动事件冒泡，避免FAB拖动页面 */
    preventMove() { return; },

    /** 从globalData读取CRS模式并同步mood */
    _syncCrsMood() {
      const app = getApp();
      if (app && app.globalData && app.globalData.crsMode) {
        const mood = crsModeToMood(app.globalData.crsMode);
        if (mood !== this.data.digitalHumanMood) {
          this.setData({ digitalHumanMood: mood });
        }
      }
    }
  },

  pageLifetimes: {
    show() {
      this.initDigitalHuman(this.properties.scene || "content");
      this._syncCrsMood();
    },
    hide() {
      if (this.digitalHumanAudio) {
        try {
          this.digitalHumanAudio.stop();
        } catch (e) {}
      }
      this.setData({ digitalHumanSpeaking: false });
      if (typeof this.syncDigitalHumanStage === "function") {
        this.syncDigitalHumanStage();
      }
    }
  }
});
