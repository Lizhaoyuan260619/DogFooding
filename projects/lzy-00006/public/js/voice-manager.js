class VoiceChatManager {
    constructor(socketClient, userInfo) {
        this.socketClient = socketClient;
        this.socket = null;
        this.userId = userInfo.userId;
        this.userName = userInfo.userName;
        this.userColor = userInfo.userColor;
        this.roomCode = userInfo.roomCode;

        this.localStream = null;
        this.audioContext = null;
        this.analyser = null;
        this.mediaRecorder = null;
        this.vadInterval = null;
        this.statsInterval = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;

        this.isJoined = false;
        this.isAdmin = false;
        this.isMuted = false;
        this.isSpeaking = false;
        this.isPTTActive = false;
        this.connectionState = 'disconnected';

        this.peers = new Map();
        this.participants = [];
        this.pendingSignals = new Map();

        this.audioOutputDevices = [];
        this.currentAudioOutputDevice = 'default';

        this.bitrate = 64000;
        this.minBitrate = 16000;
        this.maxBitrate = 128000;

        this.onJoinedCallback = null;
        this.onLeftCallback = null;
        this.onParticipantJoinedCallback = null;
        this.onParticipantLeftCallback = null;
        this.onSpeakingChangeCallback = null;
        this.onMuteChangeCallback = null;
        this.onStateChangeCallback = null;
        this.onErrorCallback = null;
        this.onVolumeChangeCallback = null;
        this.onConnectionStateChangeCallback = null;

        this.speakingThreshold = -50;
        this.speakingHoldTime = 300;
        this.lastSpeakingTime = 0;
    }

    initSocket(socket) {
        this.socket = socket;
        this._initSocketListeners();
    }

    _initSocketListeners() {
        this.socket.on('voice:user-joined', (data) => {
            this._handleParticipantJoined(data.user);
        });

        this.socket.on('voice:user-left', (data) => {
            this._handleParticipantLeft(data.userId, data.newAdminId);
        });

        this.socket.on('voice:state', (data) => {
            this._handleStateUpdate(data);
        });

        this.socket.on('voice:signal', (data) => {
            this._handleSignal(data);
        });

        this.socket.on('voice:mute-forced', (data) => {
            this.setMuted(data.isMuted);
            if (this.onMuteChangeCallback) {
                this.onMuteChangeCallback(this.userId, data.isMuted, true);
            }
        });

        this.socket.on('voice:speaking-change', (data) => {
            if (this.onSpeakingChangeCallback) {
                this.onSpeakingChangeCallback(data.userId, data.isSpeaking);
            }
        });

        this.socket.on('voice:network-update', (data) => {
            this._handleNetworkUpdate(data);
        });
    }

    async join() {
        if (this.isJoined) return { success: true };

        try {
            this.connectionState = 'connecting';
            this._notifyConnectionStateChange();

            await this._initAudioDevices();

            this.localStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: 48000,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    latency: 0.02
                },
                video: false
            });

            await this._setupAudioProcessing();

            const result = await new Promise((resolve) => {
                this.socket.emit('voice:join', { roomCode: this.roomCode }, (response) => {
                    resolve(response);
                });
            });

            if (!result.success) {
                this._cleanup();
                return { success: false, error: result.error };
            }

            this.isJoined = true;
            this.isAdmin = result.isAdmin;
            this.participants = result.participants;

            await this._connectToExistingParticipants();

            this._startVAD();
            this._startStatsMonitoring();

            this.connectionState = 'connected';
            this._notifyConnectionStateChange();

            if (this.onJoinedCallback) {
                this.onJoinedCallback(this.participants);
            }

            return { success: true };
        } catch (err) {
            console.error('Join voice error:', err);
            this.connectionState = 'disconnected';
            this._notifyConnectionStateChange();
            this._cleanup();

            let errorMessage = '加入语音失败';
            if (err.name === 'NotAllowedError') {
                errorMessage = '麦克风权限被拒绝，请在浏览器设置中允许麦克风访问';
            } else if (err.name === 'NotFoundError') {
                errorMessage = '未检测到麦克风设备';
            } else if (err.name === 'OverconstrainedError') {
                errorMessage = '麦克风不支持要求的参数';
            }

            if (this.onErrorCallback) {
                this.onErrorCallback(errorMessage);
            }

            return { success: false, error: errorMessage };
        }
    }

    async leave() {
        if (!this.isJoined) return { success: true };

        try {
            for (const [peerId, peer] of this.peers.entries()) {
                this._closePeerConnection(peerId, peer);
            }
            this.peers.clear();

            const result = await new Promise((resolve) => {
                this.socket.emit('voice:leave', { roomCode: this.roomCode }, (response) => {
                    resolve(response);
                });
            });

            this._cleanup();

            this.isJoined = false;
            this.isAdmin = false;
            this.isMuted = false;
            this.isSpeaking = false;
            this.connectionState = 'disconnected';
            this.participants = [];
            this.reconnectAttempts = 0;

            this._notifyConnectionStateChange();

            if (this.onLeftCallback) {
                this.onLeftCallback();
            }

            return result;
        } catch (err) {
            console.error('Leave voice error:', err);
            return { success: false, error: '离开语音失败' };
        }
    }

    async _initAudioDevices() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            this.audioOutputDevices = devices.filter(d => d.kind === 'audiooutput');

            navigator.mediaDevices.addEventListener('devicechange', async () => {
                const newDevices = await navigator.mediaDevices.enumerateDevices();
                this.audioOutputDevices = newDevices.filter(d => d.kind === 'audiooutput');
            });
        } catch (err) {
            console.warn('Failed to enumerate audio devices:', err);
        }
    }

    async _setupAudioProcessing() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();

            const source = this.audioContext.createMediaStreamSource(this.localStream);
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 256;
            this.analyser.smoothingTimeConstant = 0.8;

            source.connect(this.analyser);

            const audioTrack = this.localStream.getAudioTracks()[0];
            if (audioTrack) {
                const constraints = audioTrack.getConstraints();
                Object.assign(constraints, {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                });
                await audioTrack.applyConstraints(constraints);
            }
        } catch (err) {
            console.warn('Audio processing setup warning:', err);
        }
    }

    _startVAD() {
        if (this.vadInterval) return;

        const dataArray = new Uint8Array(this.analyser.frequencyBinCount);

        this.vadInterval = setInterval(() => {
            if (!this.analyser || this.isMuted) {
                this._updateSpeaking(false);
                return;
            }

            this.analyser.getByteFrequencyData(dataArray);

            let sum = 0;
            for (let i = 0; i < dataArray.length; i++) {
                sum += dataArray[i];
            }
            const average = sum / dataArray.length;
            const db = average > 0 ? 20 * Math.log10(average / 255) : -100;

            if (this.onVolumeChangeCallback) {
                this.onVolumeChangeCallback(this.userId, Math.max(0, (db + 100) / 100));
            }

            const now = Date.now();
            if (db > this.speakingThreshold) {
                this.lastSpeakingTime = now;
                this._updateSpeaking(true);
            } else if (now - this.lastSpeakingTime > this.speakingHoldTime) {
                this._updateSpeaking(false);
            }
        }, 100);
    }

    _stopVAD() {
        if (this.vadInterval) {
            clearInterval(this.vadInterval);
            this.vadInterval = null;
        }
    }

    _updateSpeaking(isSpeaking) {
        if (this.isSpeaking === isSpeaking) return;

        this.isSpeaking = isSpeaking;

        this.socket.emit('voice:speaking', {
            roomCode: this.roomCode,
            isSpeaking
        });

        if (this.onSpeakingChangeCallback) {
            this.onSpeakingChangeCallback(this.userId, isSpeaking);
        }
    }

    _startStatsMonitoring() {
        if (this.statsInterval) return;

        this.statsInterval = setInterval(async () => {
            if (!this.isJoined) return;

            const stats = await this._getNetworkStats();
            if (stats) {
                this.socket.emit('voice:network-stats', {
                    roomCode: this.roomCode,
                    stats
                });

                this._adjustBitrate(stats);
            }
        }, 2000);
    }

    _stopStatsMonitoring() {
        if (this.statsInterval) {
            clearInterval(this.statsInterval);
            this.statsInterval = null;
        }
    }

    async _getNetworkStats() {
        const peerStats = [];

        for (const [peerId, peer] of this.peers.entries()) {
            try {
                if (peer.connection && peer.connection.iceConnectionState === 'connected') {
                    const stats = await peer.connection.getStats();
                    let rtt = 0;
                    let jitter = 0;
                    let packetsLost = 0;
                    let bitrate = 0;

                    stats.forEach(report => {
                        if (report.type === 'candidate-pair' && report.state === 'succeeded') {
                            rtt = report.currentRoundTripTime * 1000;
                        }
                        if (report.type === 'inbound-rtp' && report.mediaType === 'audio') {
                            jitter = report.jitter * 1000;
                            packetsLost = report.packetsLost;
                            bitrate = report.bytesReceived * 8 / 2;
                        }
                    });

                    peerStats.push({
                        peerId,
                        rtt,
                        jitter,
                        packetsLost,
                        bitrate,
                        state: peer.connection.iceConnectionState
                    });
                }
            } catch (err) {
                console.warn('Get stats error:', err);
            }
        }

        if (peerStats.length === 0) return null;

        const avgRtt = peerStats.reduce((sum, p) => sum + p.rtt, 0) / peerStats.length;
        const avgJitter = peerStats.reduce((sum, p) => sum + p.jitter, 0) / peerStats.length;
        const totalPacketsLost = peerStats.reduce((sum, p) => sum + p.packetsLost, 0);

        return {
            avgRtt,
            avgJitter,
            totalPacketsLost,
            peerCount: peerStats.length,
            timestamp: Date.now()
        };
    }

    _adjustBitrate(stats) {
        const { avgRtt, avgJitter, totalPacketsLost } = stats;

        let targetBitrate = this.bitrate;

        if (avgRtt > 300 || avgJitter > 50 || totalPacketsLost > 10) {
            targetBitrate = Math.max(this.minBitrate, this.bitrate * 0.8);
        } else if (avgRtt < 100 && avgJitter < 20 && totalPacketsLost < 2) {
            targetBitrate = Math.min(this.maxBitrate, this.bitrate * 1.2);
        }

        if (Math.abs(targetBitrate - this.bitrate) > 8000) {
            this.bitrate = Math.round(targetBitrate);
            this._updateSenderBitrate();
        }
    }

    async _updateSenderBitrate() {
        for (const [peerId, peer] of this.peers.entries()) {
            try {
                const senders = peer.connection.getSenders();
                for (const sender of senders) {
                    if (sender.track && sender.track.kind === 'audio') {
                        const params = sender.getParameters();
                        if (!params.encodings) params.encodings = [{}];
                        params.encodings[0].maxBitrate = this.bitrate;
                        params.encodings[0].minBitrate = Math.max(16000, this.bitrate * 0.5);
                        params.encodings[0].networkPriority = 'high';
                        await sender.setParameters(params);
                    }
                }
            } catch (err) {
                console.warn('Update bitrate error:', err);
            }
        }
    }

    _handleNetworkUpdate(data) {
        const participant = this.participants.find(p => p.userId === data.userId);
        if (participant) {
            participant.networkStats = data.stats;
        }
    }

    async _connectToExistingParticipants() {
        for (const participant of this.participants) {
            if (participant.userId === this.userId) continue;

            const pendingSignals = this.pendingSignals.get(participant.userId) || [];
            this.pendingSignals.delete(participant.userId);

            const peer = await this._createPeerConnection(participant.userId, true);

            for (const signal of pendingSignals) {
                await this._handleSignalData(peer, signal);
            }
        }
    }

    async _createPeerConnection(peerUserId, isInitiator) {
        if (this.peers.has(peerUserId)) {
            return this.peers.get(peerUserId);
        }

        const configuration = {
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' },
                { urls: 'stun:stun1.l.google.com:19302' },
                { urls: 'stun:stun2.l.google.com:19302' }
            ],
            iceCandidatePoolSize: 10,
            rtcpMuxPolicy: 'require',
            bundlePolicy: 'max-bundle'
        };

        const peerConnection = new RTCPeerConnection(configuration);

        peerConnection.ontrack = (event) => {
            this._handleTrack(peerUserId, event);
        };

        peerConnection.onicecandidate = (event) => {
            if (event.candidate) {
                this.socket.emit('voice:signal', {
                    targetUserId: peerUserId,
                    data: { type: 'ice-candidate', candidate: event.candidate }
                });
            }
        };

        peerConnection.oniceconnectionstatechange = () => {
            this._handleIceStateChange(peerUserId, peerConnection);
        };

        peerConnection.onsignalingstatechange = () => {
        };

        peerConnection.onconnectionstatechange = () => {
        };

        if (this.localStream) {
            for (const track of this.localStream.getTracks()) {
                peerConnection.addTrack(track, this.localStream);
            }
        }

        const peer = {
            connection: peerConnection,
            userId: peerUserId,
            isInitiator,
            audioElement: null,
            remoteStream: null,
            iceCandidates: []
        };

        this.peers.set(peerUserId, peer);

        if (isInitiator) {
            try {
                const offer = await peerConnection.createOffer({
                    offerToReceiveAudio: true,
                    offerToReceiveVideo: false,
                    voiceActivityDetection: true
                });

                await peerConnection.setLocalDescription(offer);

                this.socket.emit('voice:signal', {
                    targetUserId: peerUserId,
                    data: { type: 'offer', sdp: offer.sdp }
                });
            } catch (err) {
                console.error('Create offer error:', err);
            }
        }

        return peer;
    }

    _handleTrack(peerUserId, event) {
        const peer = this.peers.get(peerUserId);
        if (!peer) return;

        const [stream] = event.streams;
        peer.remoteStream = stream;

        const audioElement = document.createElement('audio');
        audioElement.autoplay = true;
        audioElement.style.display = 'none';

        if (typeof audioElement.sinkId !== 'undefined') {
            audioElement.setSinkId(this.currentAudioOutputDevice).catch(() => {});
        }

        audioElement.srcObject = stream;
        document.body.appendChild(audioElement);

        peer.audioElement = audioElement;

        if (this.onStateChangeCallback) {
            this.onStateChangeCallback();
        }
    }

    async _handleIceStateChange(peerUserId, peerConnection) {
        const state = peerConnection.iceConnectionState;

        if (state === 'failed' || state === 'disconnected') {
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                this.connectionState = 'reconnecting';
                this._notifyConnectionStateChange();

                setTimeout(() => {
                    this._reconnectPeer(peerUserId);
                }, 1000 * this.reconnectAttempts);
            } else {
                this._closePeerConnection(peerUserId, this.peers.get(peerUserId));
            }
        } else if (state === 'connected' || state === 'completed') {
            this.reconnectAttempts = 0;
            this.connectionState = 'connected';
            this._notifyConnectionStateChange();
        }
    }

    async _reconnectPeer(peerUserId) {
        const peer = this.peers.get(peerUserId);
        if (!peer) return;

        this._closePeerConnection(peerUserId, peer);

        const participant = this.participants.find(p => p.userId === peerUserId);
        if (participant) {
            await this._createPeerConnection(peerUserId, true);
        }
    }

    _closePeerConnection(peerUserId, peer) {
        if (peer) {
            try {
                if (peer.audioElement) {
                    peer.audioElement.pause();
                    peer.audioElement.srcObject = null;
                    peer.audioElement.remove();
                }
            } catch (err) {
                console.warn('Close audio element error:', err);
            }

            try {
                if (peer.connection) {
                    peer.connection.close();
                }
            } catch (err) {
                console.warn('Close peer connection error:', err);
            }
        }

        this.peers.delete(peerUserId);

        if (this.onStateChangeCallback) {
            this.onStateChangeCallback();
        }
    }

    async _handleSignal(data) {
        const { senderUserId, data: signalData } = data;

        if (!this.isJoined) {
            const pending = this.pendingSignals.get(senderUserId) || [];
            pending.push(signalData);
            this.pendingSignals.set(senderUserId, pending);
            return;
        }

        let peer = this.peers.get(senderUserId);
        if (!peer) {
            peer = await this._createPeerConnection(senderUserId, false);
        }

        await this._handleSignalData(peer, signalData);
    }

    async _handleSignalData(peer, signalData) {
        try {
            switch (signalData.type) {
                case 'offer':
                    await peer.connection.setRemoteDescription(
                        new RTCSessionDescription({ type: 'offer', sdp: signalData.sdp })
                    );

                    const answer = await peer.connection.createAnswer({
                        offerToReceiveAudio: true,
                        offerToReceiveVideo: false,
                        voiceActivityDetection: true
                    });

                    await peer.connection.setLocalDescription(answer);

                    this.socket.emit('voice:signal', {
                        targetUserId: peer.userId,
                        data: { type: 'answer', sdp: answer.sdp }
                    });
                    break;

                case 'answer':
                    await peer.connection.setRemoteDescription(
                        new RTCSessionDescription({ type: 'answer', sdp: signalData.sdp })
                    );
                    break;

                case 'ice-candidate':
                    if (signalData.candidate) {
                        try {
                            await peer.connection.addIceCandidate(
                                new RTCIceCandidate(signalData.candidate)
                            );
                        } catch (err) {
                            console.warn('Add ICE candidate error:', err);
                        }
                    }
                    break;
            }
        } catch (err) {
            console.error('Handle signal error:', err);
        }
    }

    _handleParticipantJoined(user) {
        const existing = this.participants.find(p => p.userId === user.userId);
        if (!existing) {
            this.participants.push(user);
        }

        if (user.userId !== this.userId && !this.peers.has(user.userId)) {
            this._createPeerConnection(user.userId, true);
        }

        if (this.onParticipantJoinedCallback) {
            this.onParticipantJoinedCallback(user);
        }

        if (this.onStateChangeCallback) {
            this.onStateChangeCallback();
        }
    }

    _handleParticipantLeft(userId, newAdminId) {
        this.participants = this.participants.filter(p => p.userId !== userId);

        const peer = this.peers.get(userId);
        if (peer) {
            this._closePeerConnection(userId, peer);
        }

        if (newAdminId === this.userId) {
            this.isAdmin = true;
        }

        if (this.onParticipantLeftCallback) {
            this.onParticipantLeftCallback(userId, newAdminId);
        }

        if (this.onStateChangeCallback) {
            this.onStateChangeCallback();
        }
    }

    _handleStateUpdate(data) {
        this.participants = data.participants;
        if (data.adminId === this.userId) {
            this.isAdmin = true;
        }

        if (this.onStateChangeCallback) {
            this.onStateChangeCallback();
        }
    }

    setMuted(isMuted) {
        if (!this.isJoined || !this.localStream) return;

        this.isMuted = isMuted;

        for (const track of this.localStream.getAudioTracks()) {
            track.enabled = !isMuted;
        }

        this.socket.emit('voice:mute', {
            roomCode: this.roomCode,
            isMuted
        });

        if (this.onMuteChangeCallback) {
            this.onMuteChangeCallback(this.userId, isMuted, false);
        }

        if (isMuted) {
            this._updateSpeaking(false);
        }
    }

    toggleMute() {
        this.setMuted(!this.isMuted);
    }

    async muteUser(targetUserId, isMuted) {
        if (!this.isAdmin) {
            return { success: false, error: '仅管理员可静音他人' };
        }

        return new Promise((resolve) => {
            this.socket.emit('voice:mute', {
                roomCode: this.roomCode,
                isMuted,
                targetUserId
            }, (response) => {
                resolve(response);
            });
        });
    }

    async muteAll(isMuted) {
        if (!this.isAdmin) {
            return { success: false, error: '仅管理员可全体静音' };
        }

        return new Promise((resolve) => {
            this.socket.emit('voice:mute-all', {
                roomCode: this.roomCode,
                isMuted
            }, (response) => {
                resolve(response);
            });
        });
    }

    setPTTActive(active) {
        if (!this.isJoined) return;

        this.isPTTActive = active;
        this.setMuted(!active);
    }

    setAudioOutputDevice(deviceId) {
        this.currentAudioOutputDevice = deviceId;

        for (const [peerId, peer] of this.peers.entries()) {
            if (peer.audioElement && typeof peer.audioElement.sinkId !== 'undefined') {
                peer.audioElement.setSinkId(deviceId).catch(() => {});
            }
        }
    }

    setSpeakingThreshold(threshold) {
        this.speakingThreshold = threshold;
    }

    getParticipants() {
        return this.participants;
    }

    getConnectionState() {
        return this.connectionState;
    }

    _notifyConnectionStateChange() {
        if (this.onConnectionStateChangeCallback) {
            this.onConnectionStateChangeCallback(this.connectionState);
        }
    }

    _cleanup() {
        this._stopVAD();
        this._stopStatsMonitoring();

        if (this.localStream) {
            for (const track of this.localStream.getTracks()) {
                track.stop();
            }
            this.localStream = null;
        }

        if (this.audioContext) {
            this.audioContext.close().catch(() => {});
            this.audioContext = null;
            this.analyser = null;
        }

        for (const [peerId, peer] of this.peers.entries()) {
            this._closePeerConnection(peerId, peer);
        }
        this.peers.clear();

        this.pendingSignals.clear();
    }

    destroy() {
        this.leave();
    }

    setOnJoinedCallback(callback) {
        this.onJoinedCallback = callback;
    }

    setOnLeftCallback(callback) {
        this.onLeftCallback = callback;
    }

    setOnParticipantJoinedCallback(callback) {
        this.onParticipantJoinedCallback = callback;
    }

    setOnParticipantLeftCallback(callback) {
        this.onParticipantLeftCallback = callback;
    }

    setOnSpeakingChangeCallback(callback) {
        this.onSpeakingChangeCallback = callback;
    }

    setOnMuteChangeCallback(callback) {
        this.onMuteChangeCallback = callback;
    }

    setOnStateChangeCallback(callback) {
        this.onStateChangeCallback = callback;
    }

    setOnErrorCallback(callback) {
        this.onErrorCallback = callback;
    }

    setOnVolumeChangeCallback(callback) {
        this.onVolumeChangeCallback = callback;
    }

    setOnConnectionStateChangeCallback(callback) {
        this.onConnectionStateChangeCallback = callback;
    }

    static isSupported() {
        return !!(navigator.mediaDevices &&
            navigator.mediaDevices.getUserMedia &&
            window.RTCPeerConnection &&
            window.RTCSessionDescription &&
            window.RTCIceCandidate);
    }

    static async checkPermissions() {
        try {
            const result = await navigator.permissions.query({ name: 'microphone' });
            return result.state;
        } catch (err) {
            return 'prompt';
        }
    }
}

window.VoiceChatManager = VoiceChatManager;
