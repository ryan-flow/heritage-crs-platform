Component({
  properties: {
    /** 变体：hero(首页Banner) / ai(对话页) / fab(悬浮按钮) */
    variant: {
      type: String,
      value: 'fab'
    },
    /** 状态：idle / open / speaking / wink */
    state: {
      type: String,
      value: 'idle'
    },
    /** 心情：curious(好奇/冷启动) / thinking(思考/混合) / confident(自信/精准) */
    mood: {
      type: String,
      value: 'curious'
    }
  }
});
