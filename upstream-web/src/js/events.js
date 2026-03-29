import { getApiBaseUrl } from "./api.js";

function toWebSocketUrl(baseUrl) {
  return `${baseUrl.replace(/^http/, "ws")}/ws/events`;
}

export function connectEventStream({ onMessage, onStatusChange }) {
  const socket = new WebSocket(toWebSocketUrl(getApiBaseUrl()));

  socket.addEventListener("open", () => {
    onStatusChange?.("live");
  });

  socket.addEventListener("message", (event) => {
    try {
      const payload = JSON.parse(event.data);
      onMessage?.(payload);
    } catch (error) {
      console.error("Failed to parse event payload", error);
    }
  });

  socket.addEventListener("close", () => {
    onStatusChange?.("disconnected");
  });

  socket.addEventListener("error", () => {
    onStatusChange?.("error");
  });

  return socket;
}
