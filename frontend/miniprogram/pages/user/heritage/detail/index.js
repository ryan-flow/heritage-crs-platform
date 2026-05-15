const { request } = require("../../../../utils/request");
const { toAbsoluteMediaUrl } = require("../../../../utils/media");

// 遗产类别中文映射
const CATEGORY_MAP = {
  "traditional-opera": "传统戏剧",
  "traditional-music": "传统音乐",
  "traditional-dance": "传统舞蹈",
  "folk-art": "民间美术",
  "traditional-skill": "传统技艺",
  "folk-custom": "民俗",
  "traditional-medicine": "传统医药",
  "quyi": "曲艺",
  "sports": "传统体育游艺",
};

// 封面渐变色映射（不同类别对应不同配色）
const COVER_GRADIENTS = [
  "linear-gradient(135deg, #8c3a2b, #d79c53)",
  "linear-gradient(135deg, #5a3e6e, #9b7ec8)",
  "linear-gradient(135deg, #2d5f4a, #7db89a)",
  "linear-gradient(135deg, #4a5a8c, #8ca5c8)",
  "linear-gradient(135deg, #8c6a42, #c9a96e)",
];

Page({
  data: {
    id: null,
    detail: null,
    relatedList: [],
    loading: true,
    coverGradient: "",
    categoryLabel: "",
    isFavorited: false,
    favoriteLoading: false,
    bodyParagraphs: [],
    bodyExpanded: false,
    imageList: [],       // 正文中的图片列表
    qualityScoreText: "",
    displayBlocks: { intro: "", highlights: [], reading_tips: [] },
  },

  onLoad(options) {
    const id = options.id;
    if (!id) {
      this.setData({ loading: false });
      return;
    }
    this.setData({ id });
    this.fetchDetail();
    this.fetchRelated();
  },

  /** 从后端API获取内容详情 */
  async fetchDetail() {
    this.setData({ loading: true });
    try {
      const res = await request({ url: `/contents/${this.data.id}` });
      const detail = res.data || null;
      if (detail) {
        detail.cover_url = toAbsoluteMediaUrl(detail.cover_url || "");

        // 封面渐变色（无封面图时使用）
        const gradientIndex = (detail.id || 0) % COVER_GRADIENTS.length;
        const coverGradient = COVER_GRADIENTS[gradientIndex];

        // 类别标签
        const categoryLabel =
          CATEGORY_MAP[detail.content_type] ||
          detail.content_type ||
          detail.chapter ||
          "非遗文化";

        // 正文分段
        const bodyParagraphs = this._splitBody(detail.body || detail.summary || "");

        // 提取正文中的图片URL（如果有 image_urls 字段）
        const imageList = this._extractImages(detail);

        // 展示块
        const displayBlocks = detail.display_blocks || {
          intro: "",
          highlights: [],
          reading_tips: [],
        };

        // 格式化发布时间
        if (detail.published_at) {
          detail.published_at = this._formatDate(detail.published_at);
        }

        // 质量评分文字（WXML不支持 .toFixed()）
        const qualityScoreText = detail.quality_score
          ? `${Math.round(detail.quality_score * 100)}分`
          : "";

        this.setData({
          detail,
          coverGradient,
          categoryLabel,
          bodyParagraphs,
          imageList,
          displayBlocks,
          qualityScoreText,
        });

        // 检查收藏状态
        this._checkFavorite();

        // 记录浏览行为
        this._trackView(detail);
      }
    } catch (e) {
      wx.showToast({ title: "加载失败", icon: "none" });
    } finally {
      this.setData({ loading: false });
    }
  },

  /** 获取相关推荐内容 */
  async fetchRelated() {
    if (!this.data.id) return;
    try {
      const res = await request({ url: `/contents/${this.data.id}/related`, data: { limit: 4 } });
      const list = res.data || [];
      list.forEach((item) => {
        item.cover_url = toAbsoluteMediaUrl(item.cover_url || "");
      });
      this.setData({ relatedList: list });
    } catch (_e) {
      // 相关推荐加载失败不影响主流程
    }
  },

  /** 检查当前用户是否已收藏 */
  async _checkFavorite() {
    const session = wx.getStorageSync("session") || {};
    if (!session.userId) return;
    try {
      const res = await request({
        url: "/contents/favorites/check",
        data: { content_id: this.data.id, user_id: session.userId },
      });
      if (res.data) {
        this.setData({ isFavorited: !!res.data.is_favorited });
      }
    } catch (_e) {
      // 收藏状态检查失败不影响主流程
    }
  },

  /** 收藏/取消收藏 */
  async onFavoriteTap() {
    if (this.data.favoriteLoading) return;
    const session = wx.getStorageSync("session") || {};
    if (!session.userId) {
      wx.showToast({ title: "请先登录", icon: "none" });
      return;
    }

    this.setData({ favoriteLoading: true });
    const { isFavorited, id } = this.data;

    try {
      if (isFavorited) {
        // 取消收藏
        await request({
          url: "/contents/favorites",
          method: "DELETE",
          data: { content_id: id, user_id: session.userId },
        });
        this.setData({ isFavorited: false });
        wx.showToast({ title: "已取消收藏", icon: "none" });
      } else {
        // 添加收藏
        await request({
          url: "/contents/favorites",
          method: "POST",
          data: { content_id: id, user_id: session.userId },
        });
        this.setData({ isFavorited: true });
        wx.showToast({ title: "收藏成功", icon: "none" });
      }
    } catch (e) {
      wx.showToast({ title: "操作失败，请重试", icon: "none" });
    } finally {
      this.setData({ favoriteLoading: false });
    }
  },

  /** 预览图片 */
  onImagePreview(e) {
    const { src } = e.currentTarget.dataset;
    const urls = this.data.imageList.map((img) => img.url);
    wx.previewImage({
      current: src,
      urls: urls,
    });
  },

  /** 展开/收起正文 */
  toggleBody() {
    this.setData({ bodyExpanded: !this.data.bodyExpanded });
  },

  /** 返回上一页 */
  goBack() {
    const pages = getCurrentPages();
    if (pages.length > 1) {
      wx.navigateBack();
    } else {
      wx.switchTab({ url: "/pages/user/heritage/list/index" });
    }
  },

  /** 将body文本按段落拆分 */
  _splitBody(text) {
    if (!text) return [];
    return text
      .split(/\n+/)
      .map((p) => p.trim())
      .filter(Boolean);
  },

  /** 从详情中提取图片列表 */
  _extractImages(detail) {
    const images = [];
    // 如果后端有 image_urls 字段
    if (detail.image_urls) {
      try {
        const urls = typeof detail.image_urls === "string"
          ? JSON.parse(detail.image_urls)
          : detail.image_urls;
        if (Array.isArray(urls)) {
          urls.forEach((url) => {
            const absUrl = toAbsoluteMediaUrl(url);
            if (absUrl) images.push({ url: absUrl });
          });
        }
      } catch (_e) {
        // 解析失败忽略
      }
    }
    // 如果有 cover_url 也加入
    if (detail.cover_url) {
      images.unshift({ url: detail.cover_url });
    }
    return images;
  },

  /** 格式化日期 */
  _formatDate(dateStr) {
    if (!dateStr) return "";
    try {
      const d = new Date(dateStr);
      if (isNaN(d.getTime())) return dateStr;
      return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
    } catch (_e) {
      return dateStr;
    }
  },

  /** 上报浏览行为 */
  _trackView(detail) {
    const session = wx.getStorageSync("session") || {};
    request({
      url: "/recommend/track",
      method: "POST",
      data: {
        user_id: session.userId || null,
        action: "view",
        target_type: "content",
        target_id: detail.id,
        source_scene: "heritage_detail",
      },
    }).catch(() => {});
  },

  /** 跳转到相关内容详情 */
  onRelatedTap(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/user/heritage/detail/index?id=${id}`,
    });
  },

  /** 复制来源链接 */
  onCopySource() {
    const url = this.data.detail.source_url;
    if (!url) return;
    wx.setClipboardData({
      data: url,
      success: () => {
        wx.showToast({ title: "链接已复制", icon: "none" });
      },
    });
  },

  /** 跳转讨论区 */
  goDiscuss() {
    wx.switchTab({
      url: "/pages/user/discussion/index",
    });
  },

  /** 分享 */
  onShareAppMessage() {
    const detail = this.data.detail;
    return {
      title: detail ? detail.title : "非遗文化",
      path: `/pages/user/heritage/detail/index?id=${this.data.id}`,
    };
  },
});
