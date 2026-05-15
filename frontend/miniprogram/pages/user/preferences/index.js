const { request } = require("../../../utils/request");

Page({
  data: {
    user: null,
    savingPrefs: false,
    tapTarget: "",
    heritageOptions: ["工艺", "戏曲", "民俗", "医药"],
    sceneOptions: ["知识阅读", "活动体验", "论坛交流"],
    regionOptions: ["华东", "华南", "西南", "华北", "西北", "东北"],
    selectedHeritage: [],
    selectedScene: [],
    selectedRegion: [],
    totalSelected: 0
  },

  onShow() {
    this.fetchPreferences()
  },

  async fetchPreferences() {
    const session = wx.getStorageSync("session") || {}
    if (!session.userId) {
      wx.navigateTo({ url: "/pages/auth/login/index" })
      return
    }
    try {
      const userRes = await request({ url: `/users/me/${session.userId}` })
      const user = userRes.data || null
      const selectedHeritage = user ? (user.preferred_heritage_types || []) : []
      const selectedScene = user ? (user.preferred_scene_types || []) : []
      const selectedRegion = user ? (user.preferred_regions || []) : []
      this.setData({
        user,
        selectedHeritage,
        selectedScene,
        selectedRegion,
        totalSelected: selectedHeritage.length + selectedScene.length + selectedRegion.length
      })
    } catch (e) {
      wx.showToast({ title: "加载失败", icon: "none" })
    }
  },

  togglePref(e) {
    const { type, value, index } = e.currentTarget.dataset
    let key = ""
    if (type === "heritage") key = "selectedHeritage"
    if (type === "scene") key = "selectedScene"
    if (type === "region") key = "selectedRegion"
    if (!key) return

    this.setData({ tapTarget: type + "-" + index })
    setTimeout(() => {
      if (this.data.tapTarget === type + "-" + index) {
        this.setData({ tapTarget: "" })
      }
    }, 350)

    const list = (this.data[key] || []).slice()
    const idx = list.indexOf(value)
    if (idx >= 0) list.splice(idx, 1)
    else list.push(value)

    const updates = { [key]: list }
    updates.totalSelected = this.data.selectedHeritage.length +
      this.data.selectedScene.length +
      this.data.selectedRegion.length +
      (idx >= 0 ? -1 : 1)
    this.setData(updates)
  },

  async savePreferences() {
    const session = wx.getStorageSync("session") || {}
    if (!session.userId) return
    this.setData({ savingPrefs: true })
    try {
      await request({
        url: `/users/me/${session.userId}/preferences`,
        method: "PUT",
        data: {
          heritage_types: this.data.selectedHeritage,
          scene_types: this.data.selectedScene,
          regions: this.data.selectedRegion
        }
      })
      wx.showToast({ title: "偏好已保存", icon: "success" })
      setTimeout(() => wx.navigateBack(), 500)
    } catch (e) {
      wx.showToast({ title: "保存失败", icon: "none" })
    } finally {
      this.setData({ savingPrefs: false })
    }
  }
})
