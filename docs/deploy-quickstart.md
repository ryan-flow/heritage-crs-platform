# 项目本地一键部署运行手册（极简）

## 1. 环境准备

- Python 3.11+
- 微信开发者工具

## 2. 启动命令

```bash
cd "d:\桌面\毕业设计\backend"
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## 3. 演示步骤

1. 微信开发者工具导入 `frontend/miniprogram`。
2. 登录小程序，进入首页。
3. 演示内容浏览、活动报名、AI问答、个人中心。
4. 浏览器访问 `http://127.0.0.1:8000/docs` 展示接口文档。
