# 实时语音对讲模块 API 文档

## 1. 概述

本文档描述了实时语音对讲模块的API接口，包括后端Socket.IO信令接口和前端JavaScript API。

## 2. 后端 Socket.IO 信令 API

### 2.1 事件列表

| 事件名称 | 方向 | 描述 |
|---------|------|------|
| `voice:join` | 客户端→服务端 | 加入语音会话 |
| `voice:leave` | 客户端→服务端 | 离开语音会话 |
| `voice:mute` | 客户端→服务端 | 静音/取消静音 |
| `voice:mute-all` | 客户端→服务端 | 全体静音/取消全体静音（仅管理员） |
| `voice:speaking` | 客户端→服务端 | 报告讲话状态变化 |
| `voice:signal` | 客户端→服务端 | WebRTC信令转发 |
| `voice:network-stats` | 客户端→服务端 | 上报网络状态统计 |
| `voice:user-joined` | 服务端→客户端 | 有用户加入语音 |
| `voice:user-left` | 服务端→客户端 | 有用户离开语音 |
| `voice:state` | 服务端→客户端 | 语音会话状态广播 |
| `voice:signal` | 服务端→客户端 | WebRTC信令转发 |
| `voice:mute-forced` | 服务端→客户端 | 被管理员强制静音 |
| `voice:speaking-change` | 服务端→客户端 | 某用户讲话状态变化 |
| `voice:network-update` | 服务端→客户端 | 某用户网络状态更新 |

---

### 2.2 voice:join

**描述**：客户端请求加入语音会话

**请求参数**：
```json
{
  "roomCode": "ABC123"
}
```

**响应参数**：
```json
{
  "success": true,
  "isAdmin": true,
  "participants": [
    {
      "userId": "user_xxx",
      "userName": "张三",
      "userColor": "#ef4444",
      "isMuted": false,
      "isSpeaking": false,
      "isAdmin": true
    }
  ]
}
```

**错误响应**：
```json
{
  "success": false,
  "error": "语音会话最多支持10人"
}
```

---

### 2.3 voice:leave

**描述**：客户端请求离开语音会话

**请求参数**：
```json
{
  "roomCode": "ABC123"
}
```

**响应参数**：
```json
{
  "success": true
}
```

---

### 2.4 voice:mute

**描述**：静音/取消静音自己或他人（仅管理员可静音他人）

**请求参数**：
```json
{
  "roomCode": "ABC123",
  "isMuted": true,
  "targetUserId": "user_xxx"  // 可选，不填则操作自己
}
```

**响应参数**：
```json
{
  "success": true
}
```

---

### 2.5 voice:mute-all

**描述**：全体静音/取消全体静音（仅管理员）

**请求参数**：
```json
{
  "roomCode": "ABC123",
  "isMuted": true
}
```

**响应参数**：
```json
{
  "success": true
}
```

---

### 2.6 voice:speaking

**描述**：客户端报告自己的讲话状态变化

**请求参数**：
```json
{
  "roomCode": "ABC123",
  "isSpeaking": true
}
```

---

### 2.7 voice:signal

**描述**：WebRTC信令转发（Offer/Answer/ICE Candidate）

**请求参数**：
```json
{
  "targetUserId": "user_xxx",
  "data": {
    "type": "offer",
    "sdp": "v=0\r\no=- 1234567890..."
  }
}
```

**服务端转发参数**：
```json
{
  "senderUserId": "user_yyy",
  "senderUserName": "李四",
  "senderUserColor": "#3b82f6",
  "data": {
    "type": "offer",
    "sdp": "v=0\r\no=- 1234567890..."
  }
}
```

---

### 2.8 voice:network-stats

**描述**：客户端上报网络状态统计

**请求参数**：
```json
{
  "roomCode": "ABC123",
  "stats": {
    "avgRtt": 85,
    "avgJitter": 15,
    "totalPacketsLost": 2,
    "peerCount": 3,
    "timestamp": 1718888888888
  }
}
```

---

## 3. 前端 JavaScript API

### 3.1 VoiceChatManager 类

#### 构造函数
```javascript
new VoiceChatManager(socketClient, userInfo)
```

**参数**：
- `socketClient` - SocketClient 实例
- `userInfo` - 用户信息对象
  - `userId` - 用户ID
  - `userName` - 用户名
  - `userColor` - 用户颜色
  - `roomCode` - 房间码

---

#### 3.1.1 join()

**描述**：加入语音会话

**返回**：`Promise<{ success: boolean, error?: string }>`

**示例**：
```javascript
const result = await voiceChatManager.join();
if (result.success) {
  console.log('加入语音成功');
} else {
  console.error('加入失败:', result.error);
}
```

---

#### 3.1.2 leave()

**描述**：离开语音会话

**返回**：`Promise<{ success: boolean, error?: string }>`

---

#### 3.1.3 setMuted(isMuted)

**描述**：设置自己的静音状态

**参数**：
- `isMuted: boolean` - 是否静音

---

#### 3.1.4 toggleMute()

**描述**：切换静音状态

---

#### 3.1.5 muteUser(targetUserId, isMuted)

**描述**：静音/取消静音指定用户（仅管理员）

**参数**：
- `targetUserId: string` - 目标用户ID
- `isMuted: boolean` - 是否静音

**返回**：`Promise<{ success: boolean, error?: string }>`

---

#### 3.1.6 muteAll(isMuted)

**描述**：全体静音/取消全体静音（仅管理员）

**参数**：
- `isMuted: boolean` - 是否静音

**返回**：`Promise<{ success: boolean, error?: string }>`

---

#### 3.1.7 setPTTActive(active)

**描述**：设置按键说话（PTT）状态

**参数**：
- `active: boolean` - 是否激活PTT

---

#### 3.1.8 setAudioOutputDevice(deviceId)

**描述**：设置音频输出设备

**参数**：
- `deviceId: string` - 音频设备ID

---

#### 3.1.9 setSpeakingThreshold(threshold)

**描述**：设置语音活动检测阈值

**参数**：
- `threshold: number` - 分贝阈值（默认-50）

---

#### 3.1.10 getParticipants()

**描述**：获取当前语音会话参与者列表

**返回**：`Array<Participant>`

---

#### 3.1.11 getConnectionState()

**描述**：获取当前连接状态

**返回**：`'disconnected' | 'connecting' | 'connected' | 'reconnecting'`

---

#### 3.1.12 destroy()

**描述**：销毁实例，清理资源

---

### 3.2 静态方法

#### VoiceChatManager.isSupported()

**描述**：检查浏览器是否支持WebRTC语音功能

**返回**：`boolean`

---

#### VoiceChatManager.checkPermissions()

**描述**：检查麦克风权限状态

**返回**：`Promise<'granted' | 'denied' | 'prompt'>`

---

### 3.3 回调事件设置方法

| 方法 | 回调参数 | 描述 |
|------|---------|------|
| `setOnJoinedCallback(callback)` | `(participants: Participant[]) => void` | 加入语音成功 |
| `setOnLeftCallback(callback)` | `() => void` | 离开语音 |
| `setOnParticipantJoinedCallback(callback)` | `(user: Participant) => void` | 有用户加入 |
| `setOnParticipantLeftCallback(callback)` | `(userId: string, newAdminId?: string) => void` | 有用户离开 |
| `setOnSpeakingChangeCallback(callback)` | `(userId: string, isSpeaking: boolean) => void` | 某用户讲话状态变化 |
| `setOnMuteChangeCallback(callback)` | `(userId: string, isMuted: boolean, isForced: boolean) => void` | 静音状态变化 |
| `setOnStateChangeCallback(callback)` | `() => void` | 语音会话状态变化 |
| `setOnErrorCallback(callback)` | `(errorMessage: string) => void` | 发生错误 |
| `setOnVolumeChangeCallback(callback)` | `(userId: string, volume: number) => void` | 音量变化（0-1） |
| `setOnConnectionStateChangeCallback(callback)` | `(state: string) => void` | 连接状态变化 |

---

### 3.4 Participant 对象

```typescript
interface Participant {
  userId: string;
  userName: string;
  userColor: string;
  isMuted: boolean;
  isSpeaking: boolean;
  isAdmin: boolean;
  networkStats?: NetworkStats;
}

interface NetworkStats {
  avgRtt: number;        // 平均延迟(ms)
  avgJitter: number;     // 平均抖动(ms)
  totalPacketsLost: number;  // 丢包总数
  peerCount: number;     // 已连接对等端数量
  timestamp: number;     // 统计时间戳
}
```

---

## 4. 音频参数配置

### 4.1 音频约束

```javascript
{
  audio: {
    sampleRate: 48000,        // 48kHz 采样率
    channelCount: 1,           // 单声道
    echoCancellation: true,    // 回声消除
    noiseSuppression: true,    // 噪声抑制
    autoGainControl: true,     // 自动增益控制
    latency: 0.02              // 20ms 低延迟
  }
}
```

### 4.2 WebRTC 配置

```javascript
{
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' },
    { urls: 'stun:stun2.l.google.com:19302' }
  ],
  iceCandidatePoolSize: 10,
  rtcpMuxPolicy: 'require',
  bundlePolicy: 'max-bundle'
}
```

### 4.3 码率配置

- 默认码率：64 kbps
- 最低码率：16 kbps
- 最高码率：128 kbps
- 自适应调整间隔：2 秒

---

## 5. 安全说明

1. **DTLS-SRTP 加密**：所有语音数据通过DTLS-SRTP协议加密传输
2. **用户授权**：获取麦克风前必须获得用户明确同意
3. **不存储语音**：系统不存储任何语音通话内容
4. **隐私控制**：用户可随时开启/关闭语音功能
