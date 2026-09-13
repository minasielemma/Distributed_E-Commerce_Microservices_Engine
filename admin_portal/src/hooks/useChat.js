import { useState, useEffect, useCallback, useRef } from 'react';
import { chatService, mediaService } from '../services/apiServices';
import { useWebSocket } from './useWebSocket';

export const extractRoomId = (target) => {
  if (!target) return null;
  if (typeof target === 'string' || typeof target === 'number') return String(target);
  if (typeof target === 'object') {
    if (target.room_id) return extractRoomId(target.room_id);
    if (target.room) return extractRoomId(target.room);
    if (target.id) return extractRoomId(target.id);
  }
  return null;
};

export const useChat = (roomId, options = {}) => {
  const { onNewMessage } = options;
  const [room, setRoom] = useState(null);
  const [messages, setMessages] = useState([]);
  const [participants, setParticipants] = useState([]);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState(null);

  const fetchRoom = useCallback(async () => {
    if (!roomId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await chatService.getRoom(roomId);
      const fetchedRoomId = extractRoomId(res.data);
      if (fetchedRoomId && String(roomId) !== String(fetchedRoomId)) {
        return; // Guard against race conditions when user switches rooms quickly
      }
      setRoom(res.data);
      const msgs = res.data?.messages || [];
      setMessages(msgs);
      setParticipants(res.data?.participants || []);
      setHasMore(msgs.length >= 20);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load chat room');
    } finally {
      setLoading(false);
    }
  }, [roomId]);

  useEffect(() => {
    setMessages([]);
    setRoom(null);
    setParticipants([]);
    fetchRoom();
  }, [roomId, fetchRoom]);

  const handleWebSocketMessage = useCallback((evt) => {
    const type = evt.type;
    const data = evt.data || evt;

    const msgRoomId = extractRoomId(data?.room_id || data?.room || evt?.room_id || evt?.room);
    if (msgRoomId && roomId && String(msgRoomId) !== String(roomId)) {
      if ((type === 'new_message' || type === 'chat_message') && onNewMessage) {
        onNewMessage(data.id ? data : evt);
      }
      return;
    }

    if (type === 'new_message' || type === 'chat_message') {
      const newMsg = data.id ? { ...data } : { ...evt };

      const newMsgRoomId = extractRoomId(newMsg.room_id || newMsg.room);
      if (newMsgRoomId && roomId && String(newMsgRoomId) !== String(roomId)) {
        if (onNewMessage) onNewMessage(newMsg);
        return;
      }

      if (!newMsg.room && !newMsg.room_id && roomId) {
        newMsg.room = roomId;
        newMsg.room_id = roomId;
      }
      setMessages((prev) => {
        if (prev.some((m) => String(m.id) === String(newMsg.id))) return prev;

        const currentUserId = localStorage.getItem('user_id') || localStorage.getItem('userId');
        const isFromSelf = newMsg.sender_id && currentUserId && String(newMsg.sender_id) === String(currentUserId);

        if (isFromSelf) {
          const optIdx = prev.findIndex((m) => String(m.id).startsWith('optimistic_') && m.content === newMsg.content);
          if (optIdx !== -1) {
            const updated = [...prev];
            updated[optIdx] = newMsg;
            return updated;
          }
        }

        return [...prev, newMsg];
      });
      setRoom((prev) => (prev ? { ...prev, last_message_at: newMsg.created_at } : null));
      if (onNewMessage) {
        onNewMessage(newMsg);
      }
    } else if (type === 'message_history') {
      const historyRoomId = extractRoomId(data?.room_id || data?.room || data?.messages?.[0]?.room_id || data?.messages?.[0]?.room);
      if (historyRoomId && roomId && String(historyRoomId) !== String(roomId)) {
        return;
      }
      const historyMsgs = data.messages || [];
      setMessages((prev) => {
        const existingIds = new Set(prev.map((m) => String(m.id)));
        const filtered = historyMsgs.filter((m) => !existingIds.has(String(m.id)));
        return [...filtered, ...prev];
      });
      setHasMore(!!data.has_more);
      setLoadingMore(false);
    } else if (type === 'delivery_receipt') {
      const receiptRoomId = extractRoomId(data?.room_id || data?.room);
      if (receiptRoomId && roomId && String(receiptRoomId) !== String(roomId)) {
        return;
      }
      const { message_ids, user_id } = data;
      const targetSet = new Set((message_ids || []).map((id) => String(id).toLowerCase()));
      setMessages((prev) =>
        prev.map((msg) => {
          const mId = String(msg.id).toLowerCase();
          if (targetSet.size > 0) {
            if (targetSet.has(mId) && msg.recipient_status !== 'READ') {
              return { ...msg, recipient_status: 'DELIVERED' };
            }
          } else if (String(msg.sender_id).toLowerCase() !== String(user_id).toLowerCase() && msg.recipient_status !== 'READ') {
            return { ...msg, recipient_status: 'DELIVERED' };
          }
          return msg;
        })
      );
    } else if (type === 'read_receipt') {
      const receiptRoomId = extractRoomId(data?.room_id || data?.room);
      if (receiptRoomId && roomId && String(receiptRoomId) !== String(roomId)) {
        return;
      }
      const { message_ids, user_id } = data;
      const targetSet = new Set((message_ids || []).map((id) => String(id).toLowerCase()));
      setMessages((prev) =>
        prev.map((msg) => {
          const mId = String(msg.id).toLowerCase();
          if (targetSet.size > 0) {
            if (targetSet.has(mId)) {
              return { ...msg, recipient_status: 'READ' };
            }
          } else if (String(msg.sender_id).toLowerCase() !== String(user_id).toLowerCase()) {
            return { ...msg, recipient_status: 'READ' };
          }
          return msg;
        })
      );
    } else if (type === 'reaction_update') {
      const reactionRoomId = extractRoomId(data?.room_id || data?.room);
      if (reactionRoomId && roomId && String(reactionRoomId) !== String(roomId)) {
        return;
      }
      const { message_id, user_id, user_name, emoji, action } = data;
      setMessages((prev) =>
        prev.map((msg) => {
          if (String(msg.id) !== String(message_id)) return msg;
          let reactions = (msg.reactions || []).map((r) => ({
            ...r,
            users: [...(r.users || [])],
          }));
          const groupIdx = reactions.findIndex((r) => r.emoji === emoji);

          if (action === 'ADDED') {
            if (groupIdx !== -1) {
              const group = reactions[groupIdx];
              if (!group.users.some((u) => String(u.user_id) === String(user_id))) {
                reactions[groupIdx] = {
                  ...group,
                  count: group.count + 1,
                  users: [...group.users, { user_id, user_name }],
                };
              }
            } else {
              reactions.push({ emoji, count: 1, users: [{ user_id, user_name }] });
            }
          } else if (action === 'REMOVED') {
            if (groupIdx !== -1) {
              const group = reactions[groupIdx];
              const updatedUsers = group.users.filter((u) => String(u.user_id) !== String(user_id));
              const updatedCount = Math.max(0, group.count - 1);
              if (updatedCount === 0 || updatedUsers.length === 0) {
                reactions.splice(groupIdx, 1);
              } else {
                reactions[groupIdx] = {
                  ...group,
                  count: updatedCount,
                  users: updatedUsers,
                };
              }
            }
          }
          return { ...msg, reactions };
        })
      );
    }
  }, [roomId, onNewMessage]);

  const { isConnected, sendMessage: wsSend } = useWebSocket(
    roomId ? `/ws/chat/room/${roomId}/` : null,
    {
      enabled: !!roomId,
      onMessage: handleWebSocketMessage,
    }
  );

  useEffect(() => {
    if (!isConnected) return;
    const timer = setInterval(() => {
      wsSend({ action: 'heartbeat', payload: {} });
    }, 120000);
    return () => clearInterval(timer);
  }, [isConnected, wsSend]);

  const sendMessage = async (content, fileObj = null) => {
    if (!roomId) return;
    const currentUserId = localStorage.getItem('user_id') || localStorage.getItem('userId');
    const currentUsername = localStorage.getItem('username') || 'Me';

    const tempId = `optimistic_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
    const tempMsg = {
      id: tempId,
      room: roomId,
      room_id: roomId,
      sender_id: currentUserId,
      sender_name: currentUsername,
      content: content.trim(),
      message_type: fileObj ? 'FILE' : 'TEXT',
      created_at: new Date().toISOString(),
      recipient_status: 'SENT',
      is_optimistic: true,
    };

    setMessages((prev) => [...prev, tempMsg]);

    try {
      let media_file_id = null;

      if (fileObj) {
        const formData = new FormData();
        formData.append('file', fileObj);
        formData.append('visibility', 'SHARED');
        participants.forEach((p) => {
          if (p.user_id) {
            formData.append('shared_with_users', String(p.user_id));
          }
        });
        const uploadRes = await mediaService.uploadFile(formData);
        media_file_id = uploadRes.data?.id || uploadRes.data?.file_id;
      }

      let sentViaWs = false;
      if (isConnected) {
        sentViaWs = wsSend({
          action: 'send_message',
          payload: {
            content: content.trim(),
            media_file_id,
          },
        });
      }

      if (!sentViaWs) {
        const res = await chatService.sendMessage(roomId, { content: content.trim(), media_file_id });
        const sentMsg = res.data;
        setMessages((prev) => {
          const optIdx = prev.findIndex((m) => m.id === tempId);
          if (optIdx !== -1) {
            const updated = [...prev];
            updated[optIdx] = sentMsg;
            return updated;
          }
          if (prev.some((m) => m.id === sentMsg.id)) return prev;
          return [...prev, sentMsg];
        });
        return sentMsg;
      }
      return tempMsg;
    } catch (err) {
      setMessages((prev) => prev.filter((m) => m.id !== tempId));
      throw err;
    }
  };

  const fetchMoreMessages = useCallback(async () => {
    if (!roomId || messages.length === 0 || loadingMore) return;
    const oldestId = messages[0].id;
    setLoadingMore(true);

    let safetyTimer = null;

    try {
      if (isConnected) {
        wsSend({
          action: 'fetch_messages',
          payload: {
            before_id: oldestId,
            limit: 25,
          },
        });
        safetyTimer = setTimeout(() => {
          setLoadingMore(false);
        }, 8000);
      } else {
        const res = await chatService.getMessages(roomId, { before_id: oldestId, limit: 25 });
        const historyMsgs = Array.isArray(res.data) ? res.data : (res.data?.results || res.data?.messages || []);
        setMessages((prev) => {
          const existingIds = new Set(prev.map((m) => m.id));
          const filtered = historyMsgs.filter((m) => !existingIds.has(m.id));
          return [...filtered, ...prev];
        });
        setHasMore(historyMsgs.length >= 25);
        setLoadingMore(false);
      }
    } catch (err) {
      console.error('Failed to load older messages:', err);
      setLoadingMore(false);
      if (safetyTimer) clearTimeout(safetyTimer);
    }
  }, [roomId, messages, loadingMore, isConnected, wsSend]);

  const confirmDelivery = useCallback((messageIds = []) => {
    if (!roomId) return;
    const validIds = messageIds.filter((id) => id && !String(id).startsWith('optimistic_'));
    if (validIds.length === 0) return;
    if (isConnected) {
      wsSend({
        action: 'confirm_delivery',
        payload: { message_ids: validIds },
      });
    } else {
      chatService.markDelivered(roomId, { message_ids: validIds }).catch(() => {});
    }
  }, [roomId, isConnected, wsSend]);

  const markRead = useCallback((messageIds = []) => {
    if (!roomId) return;
    const validIds = messageIds.filter((id) => id && !String(id).startsWith('optimistic_'));
    if (validIds.length === 0) return;
    if (isConnected) {
      wsSend({
        action: 'mark_read',
        payload: { message_ids: validIds },
      });
    } else {
      chatService.markRead(roomId, { message_ids: validIds }).catch(() => {});
    }
    window.dispatchEvent(new CustomEvent('chat_unread_updated'));
  }, [roomId, isConnected, wsSend]);

  useEffect(() => {
    if (!roomId || !messages.length) return;
    const currentUserId = localStorage.getItem('user_id') || localStorage.getItem('userId');
    const unreadMsgs = messages.filter((m) => {
      const isOptimistic = String(m.id).startsWith('optimistic_');
      const isFromOther = !currentUserId || String(m.sender_id).toLowerCase() !== String(currentUserId).toLowerCase();
      return !isOptimistic && isFromOther && m.recipient_status !== 'READ';
    });
    if (unreadMsgs.length > 0) {
      const ids = unreadMsgs.map((m) => m.id);
      confirmDelivery(ids);
      markRead(ids);
    }
  }, [roomId, messages, isConnected, confirmDelivery, markRead]);

  const toggleReaction = useCallback(async (messageId, emoji) => {
    if (!roomId || !messageId) return;
    const sentWS = isConnected && wsSend({
      action: 'toggle_reaction',
      payload: { message_id: messageId, emoji },
    });
    if (!sentWS) {
      try {
        await chatService.toggleReaction(roomId, { message_id: messageId, emoji });
      } catch (err) {
        console.error('Failed to toggle reaction:', err);
      }
    }
  }, [roomId, isConnected, wsSend]);

  const addParticipant = async (username, userName = '', role = 'MEMBER') => {
    if (!roomId) return;
    try {
      const res = await chatService.addParticipant(roomId, { username, user_id: username, user_name: userName, role });
      await fetchRoom();
      return res.data;
    } catch (err) {
      throw err;
    }
  };

  const removeParticipant = async (userId) => {
    if (!roomId) return;
    try {
      const res = await chatService.removeParticipant(roomId, userId);
      await fetchRoom();
      return res.data;
    } catch (err) {
      throw err;
    }
  };

  return {
    room,
    messages,
    participants,
    loading,
    loadingMore,
    error,
    isConnected,
    hasMore,
    sendMessage,
    fetchMoreMessages,
    markRead,
    toggleReaction,
    addParticipant,
    removeParticipant,
    refresh: fetchRoom,
  };
};
