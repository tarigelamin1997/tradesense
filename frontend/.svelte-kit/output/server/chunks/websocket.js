import { d as derived, w as writable } from "./index.js";
function createWebSocketStore() {
  const { subscribe, set, update } = writable({
    status: "disconnected",
    lastMessage: null,
    error: null
  });
  let ws = null;
  function connect() {
    return;
  }
  function disconnect() {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.close();
    }
    ws = null;
  }
  function send(message) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message));
    } else {
      console.error("WebSocket is not connected");
    }
  }
  return {
    subscribe,
    connect,
    disconnect,
    send
  };
}
const websocket = createWebSocketStore();
const wsConnected = derived(
  websocket,
  ($ws) => $ws.status === "connected"
);
derived(
  websocket,
  ($ws) => $ws.lastMessage?.type === "trade_update" ? $ws.lastMessage.data : null
);
derived(
  websocket,
  ($ws) => $ws.lastMessage?.type === "price_update" ? $ws.lastMessage.data : null
);
export {
  wsConnected as a,
  websocket as w
};
