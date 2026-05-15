const historyItems = [
  {
    id: 1,
    year: "1950年代",
    title: "非遗抢救与民间文艺调查启动",
    summary:
      "新中国成立后，各地陆续开展戏曲、曲艺、民间美术与传统工艺的普查整理，为后续系统保护打下基础。",
    heritageId: "kunqu"
  },
  {
    id: 2,
    year: "2001年",
    title: "昆曲入选首批“人类口头和非物质遗产代表作”",
    summary:
      "昆曲成为中国非遗走向世界的重要标志，也推动了社会对传统戏曲保护的持续关注。",
    heritageId: "kunqu"
  },
  {
    id: 3,
    year: "2006年",
    title: "第一批国家级非物质文化遗产名录公布",
    summary:
      "我国开始以国家名录形式系统保护传统戏剧、传统技艺、民俗等非遗项目，非遗保护进入制度化阶段。",
    heritageId: "paper-cut"
  },
  {
    id: 4,
    year: "2011年",
    title: "《中华人民共和国非物质文化遗产法》施行",
    summary:
      "非遗保护有了明确法律依据，传承人认定、项目保护、合理利用与传播工作进一步规范。",
    heritageId: "shadow-play"
  },
  {
    id: 5,
    year: "新时代",
    title: "数字化传播与文旅融合成为新趋势",
    summary:
      "短视频、直播、数字展馆与研学活动不断拓展非遗传播边界，让传统文化走向年轻群体与大众生活。",
    heritageId: "su-embroidery"
  }
];

Page({
  data: {
    list: historyItems
  },

  toDetail(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/user/heritage/detail/index?id=${id}` });
  }
});
