# 在 API 文档中测试受保护的接口

FastAPI 的自动交互式 API 文档（Swagger UI）对 OAuth2 提供了出色的支持。你可以直接在文档界面中完成身份验证，并测试需要认证的接口。

## 准备工作

1. **重启 Uvicorn 服务器**（确保你的最新代码已生效）。
2. 打开 FastAPI 自动生成的文档页面：  
   [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

你会注意到页面右上角多了一个绿色的 **“Authorize”** 按钮！

---

## 测试流程

### 第一步：获取访问令牌（Access Token）

1. 在文档中找到 `/auth/login` 接口（通常为 `POST /auth/login`）。
2. 点击 **“Try it out”**，输入你的用户名和密码。
3. 点击 **“Execute”** 发起登录请求。
4. 成功后，响应体中会包含一个 `access_token` 字段。  
   ✅ **完整复制这个 token 字符串**（它通常很长，以 `eyJ...` 开头）。

---

### 第二步：在文档中授权

1. 点击页面右上角的 **“Authorize”** 按钮。
2. 在弹出的窗口中，找到 **“value”** 输入框。
3. 将刚才复制的 `access_token` 粘贴进去（**不需要加 `Bearer ` 前缀**，FastAPI 会自动处理）。
4. 点击 **“Authorize”**，然后关闭弹窗。

> ✅ 此时，API 文档已处于“已认证”状态。后续所有请求都会自动携带：  
> `Authorization: Bearer <your-access-token>`

---

### 第三步：调用受保护的接口

1. 找到并展开 `GET /users/me` 接口。
2. 点击 **“Try it out”** → **“Execute”**。

#### 预期结果：

- **✅ 已正确授权**：  
  返回 `200 OK`，响应体中包含当前用户信息（如 ID、用户名、邮箱等）。  
  这说明 `get_current_user` 依赖成功解析了 token 并返回了用户数据。

- **❌ 未授权 / Token 错误或过期**：  
  返回 `401 Unauthorized`，响应体提示类似：
  ```json
  { "detail": "Not authenticated" }