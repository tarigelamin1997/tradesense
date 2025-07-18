# TradeSense Real-Time Collaboration Guide

Comprehensive guide for using TradeSense's collaborative trading features.

## Overview

TradeSense's collaboration features enable teams to work together on trading strategies, share portfolios, and analyze markets in real-time. Key features include:

- **Team Workspaces**: Organized spaces for collaboration
- **Resource Sharing**: Share portfolios, strategies, watchlists
- **Real-time Sync**: See changes as they happen
- **Screen Sharing**: Share your screen for presentations
- **Voice/Video Calls**: Built-in communication tools
- **Comments & Annotations**: Discuss and mark up shared resources

## Getting Started

### Creating a Team

```http
POST /api/v1/collaboration/teams
{
  "name": "Alpha Traders",
  "description": "Professional day trading team"
}
```

### Inviting Members

```http
POST /api/v1/collaboration/teams/{team_id}/invite
{
  "email": "trader@example.com",
  "role": "member"  // owner, admin, member, viewer
}
```

### Creating Workspaces

```http
POST /api/v1/collaboration/teams/{team_id}/workspaces
{
  "name": "Options Trading",
  "description": "Workspace for options strategies"
}
```

## Sharing Resources

### Share a Portfolio

```http
POST /api/v1/collaboration/share
{
  "resource_type": "portfolio",
  "resource_id": "portfolio_123",
  "workspace_id": "workspace_456",
  "permissions": ["view", "comment"]
}
```

### Share a Strategy

```http
POST /api/v1/collaboration/share
{
  "resource_type": "strategy",
  "resource_id": "strategy_789",
  "workspace_id": "workspace_456",
  "permissions": ["view", "comment", "edit"]
}
```

## Real-Time Collaboration

### Connecting to Workspace

```javascript
// Connect to collaboration WebSocket
const ws = new WebSocket('wss://api.tradesense.app/api/v1/collaboration/ws/{workspace_id}');

ws.onopen = () => {
  console.log('Connected to workspace');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch (message.type) {
    case 'collaboration.user_joined':
      console.log(`${message.data.username} joined the workspace`);
      break;
      
    case 'collaboration.resource_changed':
      handleResourceUpdate(message.data);
      break;
      
    case 'collaboration.cursor_update':
      updateUserCursor(message.data);
      break;
      
    case 'collaboration.comment_added':
      displayNewComment(message.data);
      break;
  }
};

// Send cursor position
ws.send(JSON.stringify({
  type: 'cursor_move',
  resource_id: 'portfolio_123',
  position: { x: 100, y: 200 }
}));

// Send selection
ws.send(JSON.stringify({
  type: 'selection_change',
  resource_id: 'strategy_789',
  selection: {
    start: { line: 10, column: 5 },
    end: { line: 15, column: 20 }
  }
}));
```

### Screen Sharing

```javascript
// Start screen sharing
ws.send(JSON.stringify({
  type: 'start_screen_share',
  stream_id: 'stream_123'
}));

// Stop screen sharing
ws.send(JSON.stringify({
  type: 'stop_screen_share'
}));
```

## WebRTC Communication

### Voice/Video Calls

```javascript
// Connect to WebRTC signaling
const rtcWs = new WebSocket('wss://api.tradesense.app/api/v1/collaboration/webrtc/{workspace_id}');

// Initialize peer connection
const pc = new RTCPeerConnection({
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'turn:turn.tradesense.app:3478', username: 'user', credential: 'pass' }
  ]
});

// Start voice call
async function startVoiceCall(participantIds) {
  // Get user media
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  stream.getTracks().forEach(track => pc.addTrack(track, stream));
  
  // Create offer
  const offer = await pc.createOffer();
  await pc.setLocalDescription(offer);
  
  // Send to participants
  rtcWs.send(JSON.stringify({
    type: 'start_voice_call',
    participants: participantIds
  }));
  
  // Send offer to each participant
  participantIds.forEach(id => {
    rtcWs.send(JSON.stringify({
      type: 'offer',
      target_id: id,
      offer: offer
    }));
  });
}

// Handle incoming call
rtcWs.onmessage = async (event) => {
  const message = JSON.parse(event.data);
  
  switch (message.type) {
    case 'incoming_call':
      // Show call UI
      if (confirm(`Incoming ${message.call_type} call from ${message.caller_id}`)) {
        acceptCall(message.session_id);
      } else {
        rejectCall(message.session_id);
      }
      break;
      
    case 'offer':
      // Handle WebRTC offer
      await pc.setRemoteDescription(message.offer);
      const answer = await pc.createAnswer();
      await pc.setLocalDescription(answer);
      
      rtcWs.send(JSON.stringify({
        type: 'answer',
        target_id: message.sender_id,
        answer: answer
      }));
      break;
      
    case 'answer':
      // Handle WebRTC answer
      await pc.setRemoteDescription(message.answer);
      break;
      
    case 'ice_candidate':
      // Handle ICE candidate
      await pc.addIceCandidate(message.candidate);
      break;
  }
};

// Handle ICE candidates
pc.onicecandidate = (event) => {
  if (event.candidate) {
    rtcWs.send(JSON.stringify({
      type: 'ice_candidate',
      target_id: peerId,
      candidate: event.candidate
    }));
  }
};
```

## Comments and Annotations

### Adding Comments

```http
POST /api/v1/collaboration/resources/portfolio/portfolio_123/comments
{
  "comment_text": "Great risk management on this position!",
  "parent_id": null  // For replies, include parent comment ID
}
```

### Getting Comments

```http
GET /api/v1/collaboration/resources/portfolio/portfolio_123/comments

Response:
[
  {
    "id": "comment_1",
    "comment_text": "Great risk management on this position!",
    "user": {
      "id": "user_123",
      "username": "john_trader",
      "avatar_url": "https://..."
    },
    "created_at": "2024-01-15T10:30:00Z",
    "replies": [
      {
        "id": "comment_2",
        "comment_text": "Thanks! I learned from our last session.",
        "user": {...},
        "created_at": "2024-01-15T10:35:00Z"
      }
    ]
  }
]
```

## Best Practices

### 1. Resource Permissions

- **View**: Can see the resource
- **Comment**: Can add comments and annotations
- **Edit**: Can modify the resource
- **Delete**: Can remove the resource

Always use the minimum required permissions.

### 2. Real-time Updates

```javascript
// Batch updates for performance
const updateQueue = [];
let updateTimer = null;

function queueUpdate(update) {
  updateQueue.push(update);
  
  if (!updateTimer) {
    updateTimer = setTimeout(() => {
      ws.send(JSON.stringify({
        type: 'batch_update',
        updates: updateQueue
      }));
      
      updateQueue.length = 0;
      updateTimer = null;
    }, 100); // 100ms debounce
  }
}
```

### 3. Conflict Resolution

```javascript
// Handle concurrent edits
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.type === 'collaboration.resource_changed') {
    if (message.data.change_id !== lastChangeId) {
      // Conflict detected
      resolveConflict(message.data);
    }
  }
};

function resolveConflict(remoteChange) {
  // Option 1: Last write wins
  applyRemoteChange(remoteChange);
  
  // Option 2: Merge changes
  const merged = mergeChanges(localChanges, remoteChange);
  applyMergedChanges(merged);
  
  // Option 3: Ask user
  showConflictDialog(localChanges, remoteChange);
}
```

### 4. Security Considerations

- Always validate permissions before sharing
- Use secure WebRTC connections (DTLS/SRTP)
- Implement end-to-end encryption for sensitive data
- Regular permission audits

## UI/UX Implementation

### Cursor Tracking

```css
.user-cursor {
  position: absolute;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid var(--user-color);
  transition: all 0.1s ease-out;
  pointer-events: none;
  z-index: 1000;
}

.user-cursor::after {
  content: attr(data-username);
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: var(--user-color);
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
}
```

### Selection Highlighting

```javascript
function highlightSelection(selection, userColor) {
  const elements = getElementsInRange(selection.start, selection.end);
  
  elements.forEach(element => {
    element.style.backgroundColor = `${userColor}20`; // 20% opacity
    element.style.borderLeft = `3px solid ${userColor}`;
  });
}
```

### Activity Indicators

```javascript
// Show active collaborators
function updateActiveUsers(users) {
  const container = document.getElementById('active-users');
  container.innerHTML = '';
  
  users.forEach(user => {
    const avatar = document.createElement('div');
    avatar.className = 'user-avatar';
    avatar.style.borderColor = user.color;
    avatar.title = user.username;
    
    if (user.isActive) {
      avatar.classList.add('active');
    }
    
    container.appendChild(avatar);
  });
}
```

## Troubleshooting

### Connection Issues

1. **WebSocket won't connect**
   - Check authentication token
   - Verify workspace permissions
   - Check firewall/proxy settings

2. **WebRTC connection fails**
   - Verify STUN/TURN server configuration
   - Check browser permissions (camera/microphone)
   - Test with different network configurations

3. **Sync delays**
   - Check network latency
   - Implement optimistic updates
   - Use connection quality indicators

### Performance Optimization

1. **Large teams (50+ members)**
   - Implement virtual scrolling for member lists
   - Paginate activity feeds
   - Use Redis for session management

2. **Heavy resources**
   - Implement lazy loading
   - Use incremental sync
   - Cache frequently accessed data

3. **Mobile optimization**
   - Reduce update frequency on mobile
   - Implement touch-friendly controls
   - Use adaptive quality for calls

## API Reference

### Team Management
- `POST /teams` - Create team
- `GET /teams` - List user's teams
- `GET /teams/{id}/members` - Get team members
- `POST /teams/{id}/invite` - Invite member

### Workspace Management
- `POST /teams/{id}/workspaces` - Create workspace
- `GET /teams/{id}/workspaces` - List workspaces
- `GET /workspaces/{id}/resources` - Get shared resources

### Resource Sharing
- `POST /share` - Share resource
- `PUT /resources/{type}/{id}` - Update resource
- `GET /resources/{type}/{id}/comments` - Get comments
- `POST /resources/{type}/{id}/comments` - Add comment

### WebSocket Endpoints
- `/ws/{workspace_id}` - Collaboration WebSocket
- `/webrtc/{workspace_id}` - WebRTC signaling

## Examples

### React Integration

```jsx
import { useCollaboration } from '@tradesense/collaboration';

function TradingWorkspace({ workspaceId }) {
  const { 
    activeUsers, 
    sharedResources, 
    sendUpdate,
    startScreenShare 
  } = useCollaboration(workspaceId);
  
  return (
    <div className="workspace">
      <ActiveUsersBar users={activeUsers} />
      <ResourceList resources={sharedResources} />
      <CollaborativeEditor onUpdate={sendUpdate} />
      <button onClick={startScreenShare}>
        Share Screen
      </button>
    </div>
  );
}
```

### Mobile Support

```swift
// iOS WebRTC implementation
class CollaborationManager {
    private var webRTCClient: WebRTCClient
    private var signalingChannel: SignalingChannel
    
    func startVoiceCall(with participants: [String]) {
        webRTCClient.startCall(audio: true, video: false)
        signalingChannel.invite(participants)
    }
    
    func shareScreen() {
        let screenRecorder = RPScreenRecorder.shared()
        screenRecorder.startCapture { sampleBuffer, type, error in
            self.webRTCClient.send(sampleBuffer)
        }
    }
}
```

## Support

- **Documentation**: https://docs.tradesense.app/collaboration
- **Support Email**: collaboration@tradesense.app
- **Community Forum**: https://forum.tradesense.app/collaboration
