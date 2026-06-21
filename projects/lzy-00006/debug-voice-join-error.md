# 调试会话：语音加入错误（voice-join-error）

**状态**：[OPEN]
**创建时间**：2026-06-21
**问题描述**：用户已成功加入协作房间，但点击"加入语音"按钮时，系统错误地提示"未加入房间"，导致语音对讲功能无法正常启动。

---

## 🔬 可证伪假设（Falsifiable Hypotheses）

### H1：页面跳转后WebSocket连接未重新加入房间
- **机制**：用户在首页(index.html)加入房间后跳转到board.html，创建了新的WebSocket连接（新socket.id），但新连接未在后端roomState中注册。
- **验证点**：检查app.js初始化时是否调用了joinRoom重新加入房间。
- **预测**：app.js中只有socketClient.connect()，没有调用joinRoom()。

### H2：roomState中使用了错误的键存储用户状态
- **机制**：后端voice.js使用`socket.id`作为键查询roomState，但roomState可能使用了其他键（如userId）存储。
- **验证点**：检查room.js中roomState.set()使用的键。
- **预测**：roomState使用socket.id作为键，但页面跳转后socket.id改变了。

### H3：前端传递的roomCode与后端存储的不匹配
- **机制**：前端voice-manager.js发送的roomCode与后端roomState中存储的roomCode不一致。
- **验证点**：检查sessionStorage中存储的roomCode和后端验证逻辑。
- **预测**：roomCode是正确的，但socket.id不匹配导致验证失败。

### H4：Socket.IO连接建立后roomState设置存在时序问题
- **机制**：initSocket()调用socketClient.connect()是异步的，initVoiceManagerSocket()可能在socket连接建立前就执行了。
- **验证点**：检查socket连接建立的时序和roomState设置时机。
- **预测**：连接建立是异步的，但主要问题是缺少重新加入房间的调用。

---

## 📊 证据收集计划

1. **前端插桩**：在app.js的initSocket和initVoiceManagerSocket中添加日志，确认socket连接状态和初始化时序。
2. **后端插桩**：在voice.js的voice:join处理中添加日志，输出socket.id、roomState查询结果。
3. **复现步骤**：
   - 打开首页创建/加入房间
   - 跳转到画板页面
   - 点击"加入语音"按钮
   - 收集日志分析

---

## 📝 日志记录

### 修复前日志（Pre-fix）

**后端日志：**
```
[DEBUG voice-join] socket.id: Zfex4YQCt0JMFqrjAAAH
[DEBUG voice-join] roomCode from client: 5UZ7XP
[DEBUG voice-join] roomState.get(socket.id): undefined
[DEBUG voice-join] roomState keys: []
[DEBUG voice-join] roomState entries: []
[DEBUG voice-join] FAILED: state not found or roomCode mismatch
```

**前端日志：**
```
[DEBUG app] initSocket called
[DEBUG app] currentRoomCode: 5UZ7XP
[DEBUG app] currentUserId: user_1782044719984_203icfrej
[DEBUG app] currentUserName: 调试用户
[DEBUG app] Socket connected, socket.id: Zfex4YQCt0JMFqrjAAAH
[DEBUG app] Will rejoin room with: {roomCode: 5UZ7XP, userName: 调试用户}
[DEBUG app] toggleVoiceChat called
[DEBUG app] voiceEnabled: false
[DEBUG app] voiceChatManager exists: true
[DEBUG app] voiceChatManager.roomCode: 5UZ7XP
[DEBUG app] voiceChatManager.socket exists: true
[DEBUG app] voiceChatManager.join() result: {success: false, error: 未加入房间}
```

**证据分析结论：**
- ✅ H1确认：页面跳转后新的WebSocket连接未重新加入房间
- ✅ H2确认：roomState使用socket.id作为键，但页面跳转后socket.id改变
- ❌ H3排除：roomCode正确
- ❌ H4排除：连接时序正常

**根本原因：**
用户在首页创建/加入房间时使用socket.id-A在roomState中注册。页面跳转到board.html后，创建了新的WebSocket连接（新socket.id），但新连接没有重新加入房间，导致roomState中没有对应的记录。

### 修复后日志（Post-fix）

**后端日志：**
```
[DEBUG voice-join] socket.id: ghHo9tz8FItwraaLAAAJ
[DEBUG voice-join] roomCode from client: 5AXD7S
[DEBUG voice-join] roomState.get(socket.id): {
  roomCode: '5AXD7S',
  userId: 'user_1782045080601_xvuiotl58',
  userName: '修复验证用户',
  color: '#8b5cf6'
}
[DEBUG voice-join] roomState keys: [ 'ghHo9tz8FItwraaLAAAJ' ]
[DEBUG voice-join] roomState entries: [
  {
    socketId: 'ghHo9tz8FItwraaLAAAJ',
    roomCode: '5AXD7S',
    userId: 'user_1782045080601_xvuiotl58'
  }
]
[DEBUG voice-join] SUCCESS: state found, roomCode matches
```

**前端日志：**
```
[DEBUG app] Rejoining room...
[DEBUG app] Rejoin room success: {success: true, roomCode: 5AXD7S, userId: user_1782045080601_xvuiotl58, userName: 修复验证用户, color: #8b5cf6}
[DEBUG app] voiceChatManager.join() result: {success: true}
```

---

## ✅ 修复验证检查清单

- [x] 用户加入房间后跳转到画板页面
- [x] 新的WebSocket连接成功建立
- [x] 前端自动重新加入房间（调用joinRoom）
- [x] 后端roomState中正确注册新的socket.id
- [x] 点击"加入语音"按钮成功加入语音会话
- [x] 不再提示"未加入房间"错误
- [x] 调试插桩已成功移除
- [ ] 语音面板UI正确更新状态
- [ ] 不影响现有绘图等核心功能

## 🎯 修复总结

### 问题根因
用户在首页创建/加入房间时使用 `socket.id-A` 在 `roomState` 中注册。页面跳转到 `board.html` 后，创建了新的WebSocket连接（新的 `socket.id`），但新连接没有重新加入房间，导致 `roomState` 中没有对应的记录。

### 修复方案
在 `app.js` 的 `initSocket()` 函数中，当 socket 连接建立后，自动调用 `socketClient.joinRoom()` 重新加入房间，确保新的 `socket.id` 在后端 `roomState` 中正确注册。

### 修改的文件
- `public/js/app.js` - 在 `socket.on('connect')` 回调中添加重新加入房间的逻辑
