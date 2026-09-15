import React, { useState, useEffect, useLayoutEffect, useRef, useContext, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { chatService, orderService, authService } from '../services/apiServices';
import { useChat, extractRoomId } from '../hooks/useChat';
import { usePresence } from '../hooks/usePresence';
import { AuthContext } from '../context/AuthContext';
import {
  MessageSquare,
  Send,
  User,
  Search,
  Plus,
  Wifi,
  WifiOff,
  Package,
  Paperclip,
  FileText,
  Download,
  UserPlus,
  Users,
  X,
  Check,
  CheckCheck,
  Smile,
  Sparkles,
  ExternalLink,
  ChevronLeft,
} from 'lucide-react';

const EMOJI_OPTIONS = ['👍', '❤️', '🔥', '😂', '🎉', '😮'];

const MediaAttachmentViewer = ({ roomId, fileId, isMe, fileNameHint }) => {
  const [blobUrl, setBlobUrl] = useState(null);
  const [isImage, setIsImage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState(false);
  const [fileName, setFileName] = useState(fileNameHint || 'Attached File');

  useEffect(() => {
    let active = true;
    let createdUrl = null;

    const fetchAttachmentInfo = async () => {
      setLoading(true);
      setError(false);
      try {
        const res = await chatService.downloadRoomFile(roomId, fileId);
        if (!active) return;
        const blob = res.data;
        const contentType = blob.type || res.headers['content-type'] || '';

        const disposition = res.headers['content-disposition'];
        if (disposition && disposition.includes('filename=')) {
          const matched = disposition.match(/filename="?([^";]+)"?/);
          if (matched && matched[1]) {
            setFileName(matched[1]);
          }
        }

        const isImg = contentType.startsWith('image/') || 
                      /\.(jpg|jpeg|png|gif|webp|svg|bmp)$/i.test(fileName);

        setIsImage(isImg);
        createdUrl = URL.createObjectURL(blob);
        setBlobUrl(createdUrl);
      } catch (err) {
        if (active) setError(true);
      } finally {
        if (active) setLoading(false);
      }
    };

    if (roomId && fileId) {
      fetchAttachmentInfo();
    }

    return () => {
      active = false;
      if (createdUrl) URL.revokeObjectURL(createdUrl);
    };
  }, [roomId, fileId, fileNameHint]);

  const handleDownload = async () => {
    setDownloading(true);
    try {
      if (blobUrl) {
        const a = document.createElement('a');
        a.href = blobUrl;
        a.download = fileName || `file_${String(fileId).substring(0, 8)}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
      } else {
        const res = await chatService.downloadRoomFile(roomId, fileId);
        const blob = res.data;
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName || `file_${String(fileId).substring(0, 8)}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error('Failed to download file:', err);
    } finally {
      setDownloading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-2.5 bg-black/20 border border-[#D5D9D9] rounded-xl flex items-center gap-2 text-xs text-[#565959] animate-pulse">
        <FileText size={16} className="animate-spin text-[#007185]" />
        <span>Loading attachment...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-2.5 bg-rose-950/40 border border-[#B12704] rounded-xl flex items-center justify-between text-xs text-[#B12704]">
        <span className="flex items-center gap-1.5 truncate">
          <FileText size={16} /> File Unavailable
        </span>
        <button
          type="button"
          onClick={handleDownload}
          className="px-2 py-1 bg-rose-500/20 hover:bg-rose-500/30 rounded text-[11px] font-semibold text-rose-200"
        >
          Download
        </button>
      </div>
    );
  }

  if (isImage && blobUrl) {
    return (
      <div className="mt-1 space-y-1">
        <div className="relative group/img overflow-hidden rounded-xl border border-[#D5D9D9] bg-black/40 inline-block">
          <img
            src={blobUrl}
            alt={fileName}
            className="max-h-60 sm:max-h-72 w-auto max-w-full object-contain rounded-xl transition-transform hover:scale-[1.01] cursor-pointer"
            onClick={() => window.open(blobUrl, '_blank')}
          />
          <div className="absolute inset-0 bg-black/40 opacity-0 group-hover/img:opacity-100 transition-opacity flex items-center justify-center gap-2">
            <button
              type="button"
              onClick={() => window.open(blobUrl, '_blank')}
              className="p-2 rounded-full bg-white/20 hover:bg-white/30 text-[#111] backdrop-blur-md transition-all"
              title="Open Full Image"
            >
              <ExternalLink size={16} />
            </button>
            <button
              type="button"
              onClick={handleDownload}
              className="p-2 rounded-full bg-amazon-orange hover:bg-amazon-orange/90 text-[#111] backdrop-blur-md transition-all"
              title="Download Image"
            >
              <Download size={16} />
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`p-2.5 rounded-xl border flex items-center justify-between gap-3 ${
      isMe 
        ? 'bg-[#F0F2F2] border-[#D5D9D9] text-[#111]' 
        : 'bg-[#F0F2F2] border-[#D5D9D9] text-[#111]'
    }`}>
      <div className="flex items-center gap-2.5 min-w-0">
        <div className="p-2 rounded-lg bg-amazon-orange/20 border border-[#D5D9D9] text-[#007185] shrink-0">
          <FileText size={18} />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-xs font-bold truncate text-[#111]" title={fileName}>
            {fileName}
          </p>
          <p className="text-[10px] text-[#565959]/80 font-mono">
            Secure Shared File
          </p>
        </div>
      </div>

      <button
        type="button"
        onClick={handleDownload}
        disabled={downloading}
        className="px-2.5 py-1.5 rounded-lg bg-amazon-orange/20 hover:bg-amazon-orange/90/30 border border-amazon-orange/40 text-[#007185] hover:text-[#111] text-xs font-semibold transition-all flex items-center gap-1.5 shrink-0"
        title="Secure Download with Token Header"
      >
        <Download size={14} className={downloading ? 'animate-bounce' : ''} />
        <span>{downloading ? 'Downloading...' : 'Download'}</span>
      </button>
    </div>
  );
};

export const ChatPage = () => {
  const { user } = useContext(AuthContext);
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const initialOrderId = queryParams.get('orderId');
  const [rooms, setRooms] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [search, setSearch] = useState('');
  const [loadingList, setLoadingList] = useState(true);
  const [inputMsg, setInputMsg] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [sending, setSending] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showAddUserModal, setShowAddUserModal] = useState(false);
  const [modalError, setModalError] = useState('');
  const [activeEmojiPickerMsgId, setActiveEmojiPickerMsgId] = useState(null);

  // Shops/Tenants list for special product requests
  const [shops, setShops] = useState([]);
  const [selectedShop, setSelectedShop] = useState('');
  const [loadingShops, setLoadingShops] = useState(false);

  // Orders list for dropdown picker
  const [orders, setOrders] = useState([]);
  const [loadingOrders, setLoadingOrders] = useState(false);

  // New room modal inputs
  const [newRoomName, setNewRoomName] = useState('');
  const [newRoomType, setNewRoomType] = useState('ORDER_SUPPORT');
  const [selectedOrder, setSelectedOrder] = useState('');
  const [initialMessage, setInitialMessage] = useState('');

  // Add participant inputs
  const [addUserId, setAddUserId] = useState('');
  const [addUserName, setAddUserName] = useState('');
  const [addUserRole, setAddUserRole] = useState('MEMBER');

  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  const { presenceMap, queryPresence } = usePresence();

  const fetchRooms = useCallback(async () => {
    setLoadingList(true);
    try {
      const res = await chatService.getRooms();
      const list = Array.isArray(res.data) ? res.data : (res.data?.results || []);
      setRooms(list);
      if (list.length > 0 && !selectedId) {
        setSelectedId(list[0].id);
      }
    } catch (err) {
      console.error('Failed to fetch chat rooms:', err);
    } finally {
      setLoadingList(false);
    }
  }, [selectedId]);
  const messagesViewportRef = useRef(null);
  const scrollStateRef = useRef(null);
  const isInitialLoadRef = useRef(true);

  const updateRoomLastMessage = useCallback((targetRoomId, newMsg) => {
    const rId = extractRoomId(targetRoomId);
    if (!rId || !newMsg) return;
    setRooms((prevRooms) => {
      const idx = prevRooms.findIndex((r) => String(r.id) === String(rId));
      if (idx === -1) {
        chatService.getRooms().then(res => {
          const list = Array.isArray(res.data) ? res.data : (res.data?.results || []);
          setRooms(list);
        }).catch(() => {});
        return prevRooms;
      }
      const updated = [...prevRooms];
      const targetRoom = { ...updated[idx] };
      const msgContent = newMsg.content || (newMsg.media_file_id ? '[Attachment]' : 'New message');

      targetRoom.last_message = {
        id: newMsg.id,
        content: msgContent,
        sender_name: newMsg.sender_name,
        sender_id: newMsg.sender_id,
        created_at: newMsg.created_at || new Date().toISOString(),
      };
      targetRoom.last_message_at = newMsg.created_at || new Date().toISOString();

      if (String(rId) === String(selectedId)) {
        targetRoom.unread_count = 0;
      } else if (typeof newMsg.unread_count === 'number') {
        targetRoom.unread_count = newMsg.unread_count;
      } else if (String(newMsg.sender_id) !== String(user?.id)) {
        targetRoom.unread_count = (targetRoom.unread_count || 0) + 1;
      }

      // Move updated room to top of list
      updated.splice(idx, 1);
      return [targetRoom, ...updated];
    });
  }, [selectedId, user]);

  const handleNewMessage = useCallback((newMsg) => {
    const targetRoomId = extractRoomId(newMsg?.room_id || newMsg?.room);
    if (targetRoomId) {
      updateRoomLastMessage(targetRoomId, newMsg);
    }
  }, [updateRoomLastMessage]);

  const {
    room,
    messages,
    participants,
    loading: loadingChat,
    loadingMore,
    isConnected,
    hasMore,
    sendMessage,
    fetchMoreMessages,
    toggleReaction,
    addParticipant,
    removeParticipant,
    refresh,
  } = useChat(selectedId, { onNewMessage: handleNewMessage });

  useEffect(() => {
    const handleNotif = (e) => {
      const notif = e.detail;
      if (notif?.notification_type === 'CHAT' || notif?.metadata?.room_id) {
        const targetRoomId = notif.metadata?.room_id;
        if (targetRoomId) {
          updateRoomLastMessage(targetRoomId, {
            room: targetRoomId,
            room_id: targetRoomId,
            id: notif.metadata?.message_id,
            content: notif.metadata?.content || notif.message || notif.body,
            sender_name: notif.metadata?.sender_name,
            created_at: notif.metadata?.created_at || notif.created_at || new Date().toISOString(),
          });
        } else {
          fetchRooms();
        }
      }
    };

    const handleRoomCreated = () => {
      fetchRooms();
    };

    const handleRoomUpdated = (e) => {
      const data = e.detail;
      if (data?.room_id) {
        if (data.last_message) {
          updateRoomLastMessage(data.room_id, {
            room: data.room_id,
            room_id: data.room_id,
            id: data.last_message.id,
            content: data.last_message.content,
            sender_name: data.last_message.sender_name,
            sender_id: data.last_message.sender_id,
            created_at: data.last_message.created_at || data.last_message_at,
            unread_count: data.unread_count,
          });
        } else if (typeof data.unread_count === 'number') {
          const rId = extractRoomId(data.room_id);
          setRooms((prevRooms) =>
            prevRooms.map((r) => {
              if (String(r.id) === String(rId)) {
                return {
                  ...r,
                  unread_count: String(rId) === String(selectedId) ? 0 : data.unread_count,
                };
              }
              return r;
            })
          );
        }
      } else {
        fetchRooms();
      }
    };

    const handleUnreadUpdated = (e) => {
      const data = e.detail;
      if (data?.room_id && typeof data.unread_count === 'number') {
        const rId = extractRoomId(data.room_id);
        setRooms((prevRooms) =>
          prevRooms.map((r) => {
            if (String(r.id) === String(rId)) {
              return {
                ...r,
                unread_count: String(rId) === String(selectedId) ? 0 : data.unread_count,
              };
            }
            return r;
          })
        );
      }
    };

    window.addEventListener('notification_received', handleNotif);
    window.addEventListener('chat_room_created', handleRoomCreated);
    window.addEventListener('chat_room_updated', handleRoomUpdated);
    window.addEventListener('chat_unread_updated', handleUnreadUpdated);
    return () => {
      window.removeEventListener('notification_received', handleNotif);
      window.removeEventListener('chat_room_created', handleRoomCreated);
      window.removeEventListener('chat_room_updated', handleRoomUpdated);
      window.removeEventListener('chat_unread_updated', handleUnreadUpdated);
    };
  }, [updateRoomLastMessage, fetchRooms, selectedId]);

  useEffect(() => {
    fetchRooms().then(() => {
      if (initialOrderId) {
        setModalError('');
        setShowCreateModal(true);
        setNewRoomType('ORDER_SUPPORT');
        setSelectedOrder(initialOrderId);
        setNewRoomName(`Order Support #${String(initialOrderId).substring(0, 8)}`);
        fetchOrdersForPicker();
        fetchShopsForPicker();
      }
    });
  }, [initialOrderId]);

  useEffect(() => {
    isInitialLoadRef.current = true;
  }, [selectedId]);

  const scrollToBottom = () => {
    requestAnimationFrame(() => {
      if (messagesViewportRef.current) {
        messagesViewportRef.current.scrollTop = messagesViewportRef.current.scrollHeight;
      }
    });
  };

  useEffect(() => {
    if (messages.length > 0) {
      scrollToBottom();
      if (isInitialLoadRef.current) {
        isInitialLoadRef.current = false;
      }
    }
  }, [messages]);

  useLayoutEffect(() => {
    if (scrollStateRef.current && messagesViewportRef.current) {
      const container = messagesViewportRef.current;
      const heightDiff = container.scrollHeight - scrollStateRef.current.scrollHeight;
      container.scrollTop = scrollStateRef.current.scrollTop + heightDiff;
      scrollStateRef.current = null;
    }
  }, [messages]);

  const handleScroll = (e) => {
    const container = e.target;
    if (container.scrollTop <= 40 && hasMore && !loadingMore) {
      scrollStateRef.current = {
        scrollHeight: container.scrollHeight,
        scrollTop: container.scrollTop,
      };
      fetchMoreMessages();
    }
  };

  useEffect(() => {
    if (participants && participants.length > 0) {
      participants.forEach((p) => {
        if (p.user_id && p.user_id !== user?.id) {
          queryPresence(p.user_id);
        }
      });
    }
  }, [participants, user, queryPresence]);



  const fetchShopsForPicker = async () => {
    setLoadingShops(true);
    try {
      const res = await authService.getTenants().catch(() => null);
      if (res && res.data) {
        const list = Array.isArray(res.data) ? res.data : (res.data?.results || []);
        setShops(list);
      }
    } catch (err) {
      console.error('Failed to fetch shops:', err);
    } finally {
      setLoadingShops(false);
    }
  };

  const fetchOrdersForPicker = async () => {
    setLoadingOrders(true);
    try {
      const res = await orderService.getOrders().catch(() => null);
      if (res && res.data) {
        const orderList = Array.isArray(res.data) ? res.data : (res.data.results || []);
        setOrders(orderList);
      }
    } catch (err) {
      console.error('Failed to load orders for picker:', err);
    } finally {
      setLoadingOrders(false);
    }
  };

  const openCreateModal = () => {
    setModalError('');
    setShowCreateModal(true);
    fetchOrdersForPicker();
    fetchShopsForPicker();
  };

  const applyTemplate = (templateType) => {
    if (templateType === 'SPECIAL_REQUEST') {
      setNewRoomType('ORDER_SUPPORT');
      setNewRoomName('Special Product Request');
      setInitialMessage('Hello! I would like to inquire about a custom/special product request for your store.');
    } else if (templateType === 'ORDER_SUPPORT') {
      setNewRoomType('ORDER_SUPPORT');
      setNewRoomName('Order Support Ticket');
      setInitialMessage('Hello, I need assistance with an order.');
    } else if (templateType === 'PAYMENT') {
      setNewRoomType('DIRECT');
      setNewRoomName('Billing & Payment Inquiry');
      setInitialMessage('Hello, I have a question regarding billing/invoices.');
    } else if (templateType === 'PRODUCT') {
      setNewRoomType('DIRECT');
      setNewRoomName('Product Information & Return');
      setInitialMessage('Hello, I would like to inquire about a product or return.');
    } else if (templateType === 'TEAM') {
      setNewRoomType('GROUP');
      setNewRoomName('Operations & Store Team Chat');
      setInitialMessage('Team chat initialized.');
    }
  };

  const handleOrderSelect = (orderId) => {
    setSelectedOrder(orderId);
    if (orderId) {
      const ord = orders.find((o) => String(o.id) === String(orderId));
      const shortId = String(orderId).substring(0, 8);
      const name = ord ? `Order Support #${shortId} (${ord.status})` : `Order Support #${shortId}`;
      setNewRoomName(name);
      if (!initialMessage) {
        setInitialMessage(`Hello, starting support chat for Order #${shortId}.`);
      }
    }
  };

  const handleCreateRoom = async (e) => {
    e.preventDefault();
    setModalError('');
    if (!newRoomName.trim()) {
      setModalError('Please enter a room name.');
      return;
    }
    try {
      const res = await chatService.createRoom({
        name: newRoomName.trim(),
        room_type: newRoomType,
        tenant_id: selectedShop ? selectedShop : null,
        order_id: selectedOrder ? selectedOrder : null,
        initial_message: initialMessage.trim(),
      });
      setShowCreateModal(false);
      setNewRoomName('');
      setSelectedOrder('');
      setInitialMessage('');
      await fetchRooms();
      if (res.data?.id) {
        setSelectedId(res.data.id);
      }
    } catch (err) {
      const msg = err.response?.data?.error || err.response?.data?.detail || err.message || 'Failed to create chat room.';
      setModalError(msg);
    }
  };

  const handleAddParticipant = async (e) => {
    e.preventDefault();
    setModalError('');
    if (!addUserId.trim()) {
      setModalError('Username or User ID is required.');
      return;
    }
    try {
      await addParticipant(addUserId.trim(), addUserName.trim(), addUserRole);
      setShowAddUserModal(false);
      setAddUserId('');
      setAddUserName('');
    } catch (err) {
      setModalError(err.response?.data?.error || 'Failed to add participant.');
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputMsg.trim() && !selectedFile) return;

    const currentText = inputMsg.trim();
    const hasFile = !!selectedFile;

    setSending(true);
    try {
      const sentMsg = await sendMessage(inputMsg, selectedFile);
      setInputMsg('');
      setSelectedFile(null);

      const targetRoomId = sentMsg?.room || sentMsg?.room_id || selectedId;
      updateRoomLastMessage(targetRoomId, sentMsg || {
        room: selectedId,
        content: currentText || (hasFile ? '[Attachment]' : 'New message'),
        sender_name: user?.username || 'Me',
        sender_id: user?.id,
        created_at: new Date().toISOString(),
      });

      setTimeout(() => {
        scrollToBottom();
      }, 50);
    } catch (err) {
      console.error('Failed to send message:', err);
    } finally {
      setSending(false);
    }
  };

  const [showMobileChatRoom, setShowMobileChatRoom] = useState(false);

  const filteredRooms = rooms.filter((r) =>
    (r.name || '').toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="w-full h-[calc(100vh-6rem)] flex flex-col p-3 sm:p-4 md:p-6 overflow-hidden">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 shrink-0 mb-3 sm:mb-4">
        <div>
          <h1 className="text-xl sm:text-2xl md:text-3xl font-extrabold text-[#111] tracking-tight flex items-center gap-2 sm:gap-3">
            <MessageSquare className="text-[#007185] w-6 h-6 sm:w-7 sm:h-7" /> Real-Time Live Messaging
          </h1>
          <p className="text-[#565959] text-xs mt-0.5">
            Action-based WebSocket protocol • Multi-participant threads • Reactions & Delivery Status
          </p>
        </div>

        <button
          onClick={openCreateModal}
          className="btn-primary text-xs flex items-center gap-2 shadow-lg shadow-sm shrink-0"
        >
          <Plus size={16} /> New Chat Room
        </button>
      </div>

      {/* Main Chat Layout Container */}
      <div className="bg-white border border-[#D5D9D9] rounded-lg flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-4 overflow-hidden shadow-2xl">
        {/* Left Sidebar: Rooms List */}
        <div className={`lg:col-span-1 border-r border-[#D5D9D9] flex flex-col h-full overflow-hidden bg-[#F0F2F2] ${showMobileChatRoom ? 'hidden lg:flex' : 'flex'}`}>
          <div className="p-3 sm:p-4 border-b border-[#D5D9D9] space-y-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[#565959]" size={14} />
              <input
                type="text"
                placeholder="Filter rooms..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-white border border-[#D5D9D9] rounded-xl pl-9 pr-3 py-2 text-xs text-[#111] placeholder-slate-500 focus:outline-none focus:border-amazon-orange"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto custom-scrollbar divide-y divide-white/5">
            {loadingList ? (
              <div className="p-6 text-center text-xs text-[#565959]">Loading rooms...</div>
            ) : filteredRooms.length === 0 ? (
              <div className="p-6 text-center text-xs text-[#565959]">No chat rooms found.</div>
            ) : (
              filteredRooms.map((r) => {
                const isSelected = r.id === selectedId;
                const unread = r.unread_count || 0;
                const previewContent = r.last_message?.sender_name 
                  ? `${r.last_message.sender_name}: ${r.last_message.content || '[Attachment]'}`
                  : (r.last_message?.content || (r.last_message?.media_file_id ? '[Attachment]' : 'No messages yet'));

                return (
                  <div
                    key={r.id}
                    onClick={() => {
                      setSelectedId(r.id);
                      setShowMobileChatRoom(true);
                      setRooms(prev => prev.map(roomItem => roomItem.id === r.id ? { ...roomItem, unread_count: 0 } : roomItem));
                    }}
                    className={`p-3.5 sm:p-4 cursor-pointer transition-all flex items-start gap-3 ${
                      isSelected
                        ? 'bg-[#F0F2F2] border-l-4 border-amazon-orange'
                        : 'hover:bg-[#F3F3F3]'
                    }`}
                  >
                    <div className="w-9 h-9 rounded-xl bg-amazon-orange/20 text-[#007185] flex items-center justify-center font-bold text-xs shrink-0 relative">
                      {r.room_type === 'ORDER_SUPPORT' ? (
                        <Package size={18} />
                      ) : r.room_type === 'GROUP' ? (
                        <Users size={18} />
                      ) : (
                        <User size={18} />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-1">
                        <h4 className="text-xs font-bold text-[#111] truncate">{r.name}</h4>
                        <div className="flex items-center gap-1.5 shrink-0">
                          {r.last_message_at && (
                            <span className="text-[10px] text-[#565959] font-medium">
                              {new Date(r.last_message_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                          )}
                          {unread > 0 && (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-amazon-orange text-[#111]">
                              {unread}
                            </span>
                          )}
                        </div>
                      </div>
                      <p className="text-[11px] text-[#565959] truncate mt-0.5">
                        {previewContent}
                      </p>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right Pane: Active Chat Room */}
        <div className={`lg:col-span-3 flex flex-col h-full min-h-0 overflow-hidden bg-white ${!showMobileChatRoom ? 'hidden lg:flex' : 'flex'}`}>
          {selectedId && room ? (
            <>
              {/* Room Header */}
              <div className="p-3 sm:p-4 bg-white border-b border-[#D5D9D9] flex items-center justify-between shrink-0">
                <div className="flex items-center gap-2 sm:gap-3 min-w-0">
                  <button
                    onClick={() => setShowMobileChatRoom(false)}
                    className="lg:hidden p-1.5 rounded-lg bg-gray-100 text-gray-700 hover:bg-gray-200 shrink-0"
                    title="Back to Chat Rooms"
                  >
                    <ChevronLeft size={18} />
                  </button>
                  <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-2xl bg-[#F0F2F2] text-[#007185] flex items-center justify-center font-black shrink-0">
                    {room.room_type === 'ORDER_SUPPORT' ? (
                      <Package size={20} />
                    ) : room.room_type === 'GROUP' ? (
                      <Users size={20} />
                    ) : (
                      <User size={20} />
                    )}
                  </div>
                  <div className="min-w-0">
                    <h3 className="text-xs sm:text-sm font-extrabold text-[#111] flex items-center gap-2 truncate">
                      {room.name}
                    </h3>
                    <div className="flex items-center gap-2 mt-0.5 text-[10px] sm:text-[11px] text-[#565959]">
                      {isConnected ? (
                        <span className="text-emerald-400 inline-flex items-center gap-1 font-bold">
                          <Wifi size={12} /> Connected Live
                        </span>
                      ) : (
                        <span className="text-amber-400 inline-flex items-center gap-1">
                          <WifiOff size={12} /> Reconnecting...
                        </span>
                      )}
                      <span>•</span>
                      <span>{participants.length} Members</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => { setModalError(''); setShowAddUserModal(true); }}
                    className="px-3 py-1.5 rounded-xl bg-amazon-orange/10 hover:bg-amazon-orange/90/20 border border-[#D5D9D9] text-[#007185] text-xs font-bold transition-all flex items-center gap-1.5"
                  >
                    <UserPlus size={14} /> Add User
                  </button>
                </div>
              </div>

              {/* Participants Bar */}
              <div className="px-4 py-2 bg-[#F0F2F2] border-b border-[#D5D9D9] flex items-center gap-2 overflow-x-auto custom-scrollbar shrink-0 text-[11px]">
                <span className="text-[#565959] font-bold uppercase text-[9px]">Members:</span>
                {participants.map((p) => {
                  const presence = presenceMap[p.user_id] || { status: 'offline' };
                  const isOnline = presence.status === 'online';
                  return (
                    <span
                      key={p.id}
                      className="px-2.5 py-0.5 rounded-full bg-[#F3F3F3] border border-[#D5D9D9] text-[#565959] flex items-center gap-1.5"
                    >
                      <span
                        className={`w-2 h-2 rounded-full ${
                          isOnline ? 'bg-emerald-400 shadow-sm shadow-emerald-400/50' : 'bg-slate-600'
                        }`}
                        title={isOnline ? 'Online' : 'Offline'}
                      />
                      <span className="font-semibold">{p.user_name || `User-${String(p.user_id).substring(0, 4)}`}</span>
                      <span className="text-[9px] text-[#007185] font-mono">({p.role})</span>
                      {p.user_id !== user?.id && (
                        <button
                          onClick={() => removeParticipant(p.user_id)}
                          className="text-[#565959] hover:text-rose-400 ml-0.5"
                          title="Remove Participant"
                        >
                          <X size={10} />
                        </button>
                      )}
                    </span>
                  );
                })}
              </div>

              {/* Messages Viewport */}
              <div
                ref={messagesViewportRef}
                onScroll={handleScroll}
                className="flex-1 min-h-0 p-6 overflow-y-auto custom-scrollbar space-y-4 bg-[#F0F2F2]"
              >
                {loadingMore && (
                  <div className="text-center py-2 text-xs text-[#007185] font-bold flex items-center justify-center gap-2">
                    <span className="w-4 h-4 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
                    Fetching older messages...
                  </div>
                )}
                {messages.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-xs text-[#565959]">
                    No messages yet in this room.
                  </div>
                ) : (
                  messages.map((msg) => {
                    const currentUserId = String(
                      user?.user_id ||
                      user?.id ||
                      user?.pk ||
                      localStorage.getItem('user_id') ||
                      localStorage.getItem('userId') ||
                      ''
                    ).toLowerCase();

                    const currentUsername = String(
                      user?.username ||
                      user?.email ||
                      localStorage.getItem('username') ||
                      ''
                    ).toLowerCase();

                    const msgSenderId = String(
                      msg.sender_id ||
                      msg.sender?.id ||
                      msg.sender ||
                      ''
                    ).toLowerCase();

                    const msgSenderName = String(msg.sender_name || '').toLowerCase();

                    const isMe = Boolean(
                      msg.is_optimistic ||
                      msgSenderName === 'me' ||
                      msgSenderName === 'you' ||
                      (currentUserId && msgSenderId && currentUserId === msgSenderId) ||
                      (currentUsername && msgSenderName && currentUsername === msgSenderName)
                    );
                    const isSystem = msg.message_type === 'SYSTEM';

                    if (isSystem) {
                      return (
                        <div key={msg.id} className="text-center my-2">
                          <span className="px-3 py-1 rounded-full bg-[#F0F2F2] border border-slate-700/50 text-[#565959] text-xs font-medium">
                            {msg.content}
                          </span>
                        </div>
                      );
                    }

                    const recStatus = msg.recipient_status || 'SENT';

                    return (
                      <div
                        key={msg.id}
                        className={`flex flex-col ${isMe ? 'items-end ml-auto' : 'items-start mr-auto'} group relative w-full`}
                      >
                        <div className={`flex items-center gap-2 mb-1 ${isMe ? 'flex-row-reverse text-right' : 'flex-row text-left'}`}>
                          <span className={`text-xs font-bold ${isMe ? 'text-[#007185]' : 'text-[#565959]'}`}>
                            {isMe ? 'You' : (msg.sender_name || 'User')} {msg.sender_role ? `(${msg.sender_role})` : ''}
                          </span>
                          <span className="text-[10px] text-slate-500 font-mono">
                            {new Date(msg.created_at).toLocaleTimeString([], {
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </span>
                        </div>

                        {/* Message Bubble Container */}
                        <div className={`relative flex items-center gap-2 ${isMe ? 'flex-row-reverse' : 'flex-row'} max-w-[85%] sm:max-w-md`}>
                          {/* Emoji Picker Trigger (on hover) */}
                          <div className="relative opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                            <button
                              type="button"
                              onClick={() => setActiveEmojiPickerMsgId(activeEmojiPickerMsgId === msg.id ? null : msg.id)}
                              className="p-1 rounded-full bg-[#F0F2F2] hover:bg-slate-700 text-[#565959] hover:text-[#111] transition-all text-xs"
                              title="React with Emoji"
                            >
                              <Smile size={14} />
                            </button>
                            {activeEmojiPickerMsgId === msg.id && (
                              <div className={`absolute z-30 bottom-full mb-1.5 px-2 py-1 bg-white border border-[#D5D9D9] rounded-2xl flex items-center gap-1.5 shadow-2xl whitespace-nowrap ${isMe ? 'right-0' : 'left-0'}`}>
                                {EMOJI_OPTIONS.map((e) => (
                                  <button
                                    key={e}
                                    type="button"
                                    onClick={() => {
                                      toggleReaction(msg.id, e);
                                      setActiveEmojiPickerMsgId(null);
                                    }}
                                    className="hover:scale-125 transition-transform text-sm p-1"
                                  >
                                    {e}
                                  </button>
                                ))}
                              </div>
                            )}
                          </div>

                          <div
                            className={`p-3.5 rounded-2xl text-sm leading-relaxed space-y-2 relative ${
                              isMe
                                ? 'bg-amazon-orange text-[#111] rounded-tr-none shadow-lg shadow-indigo-600/25 ml-auto'
                                : 'bg-white border border-[#D5D9D9] text-[#111] rounded-tl-none mr-auto'
                            }`}
                          >
                            {msg.content && <div className="break-words">{msg.content}</div>}

                            {/* Media File Attachment */}
                            {msg.media_file_id && (
                              <MediaAttachmentViewer
                                roomId={selectedId}
                                fileId={msg.media_file_id}
                                isMe={isMe}
                                fileNameHint={msg.content && msg.content !== 'FILE' ? msg.content : null}
                              />
                            )}

                            {/* Delivery & Read Receipts Icon */}
                            {isMe && (
                              <div className="flex justify-end items-center text-[10px] text-[#007185]/80 gap-1 mt-1">
                                {recStatus === 'READ' ? (
                                  <CheckCheck size={14} className="text-emerald-300" title="Read" />
                                ) : recStatus === 'DELIVERED' ? (
                                  <CheckCheck size={14} className="text-[#007185]" title="Delivered" />
                                ) : (
                                  <Check size={14} className="text-[#007185]/70" title="Sent" />
                                )}
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Reaction Badges Below Message */}
                        {msg.reactions && msg.reactions.length > 0 && (
                          <div className={`flex flex-wrap gap-1 mt-1.5 ${isMe ? 'justify-end' : 'justify-start'}`}>
                            {msg.reactions.map((r) => (
                              <button
                                key={r.emoji}
                                onClick={() => toggleReaction(msg.id, r.emoji)}
                                className="px-2 py-0.5 rounded-full bg-[#F0F2F2] border border-[#D5D9D9] text-[11px] text-[#565959] flex items-center gap-1 hover:bg-slate-700 transition-all"
                              >
                                <span>{r.emoji}</span>
                                <span className="font-bold text-[10px]">{r.count}</span>
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input Bar */}
              <div className="p-4 bg-white border-t border-[#D5D9D9] flex flex-col gap-2 shrink-0 mt-auto">
                {selectedFile && (
                  <div className="px-3 py-1.5 bg-[#F0F2F2] border border-[#D5D9D9] rounded-xl flex items-center justify-between text-xs text-[#007185]">
                    <span className="flex items-center gap-2 truncate">
                      <Paperclip size={14} /> {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
                    </span>
                    <button
                      type="button"
                      onClick={() => setSelectedFile(null)}
                      className="text-[#565959] hover:text-[#111]"
                    >
                      <X size={14} />
                    </button>
                  </div>
                )}

                <form onSubmit={handleSend} className="flex items-center gap-2">
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={(e) => setSelectedFile(e.target.files[0] || null)}
                    className="hidden"
                  />
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="p-3 rounded-xl bg-[#F3F3F3] hover:bg-[#F0F2F2] text-[#565959] border border-[#D5D9D9] transition-all"
                    title="Attach file via Media Service"
                  >
                    <Paperclip size={16} />
                  </button>

                  <input
                    type="text"
                    placeholder="Type your message..."
                    value={inputMsg}
                    onChange={(e) => setInputMsg(e.target.value)}
                    className="flex-1 px-4 py-3 bg-white border border-[#D5D9D9] rounded-xl text-xs text-[#111] placeholder-slate-500 focus:outline-none focus:border-amazon-orange"
                  />

                  <button
                    type="submit"
                    disabled={sending || (!inputMsg.trim() && !selectedFile)}
                    className="px-5 py-3 rounded-xl bg-amazon-orange hover:bg-amazon-orange/90 disabled:opacity-50 text-[#111] font-bold text-xs transition-all shadow-lg shadow-sm flex items-center gap-2"
                  >
                    <Send size={14} /> {sending ? 'Sending...' : 'Send'}
                  </button>
                </form>
              </div>
            </>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-[#565959] gap-3 p-8">
              <MessageSquare size={48} className="text-slate-700" />
              <p className="text-sm font-semibold">Select a chat room or create a new one</p>
              <button
                onClick={openCreateModal}
                className="mt-2 px-4 py-2 rounded-xl bg-amazon-orange text-[#111] text-xs font-bold shadow-lg shadow-sm"
              >
                + Create Chat Room
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Modal: User-Friendly Chat Room Creation */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-[#D5D9D9] rounded-2xl w-full max-w-lg p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-black text-[#111] flex items-center gap-2">
                <Sparkles className="text-[#007185]" size={20} /> Quick-Start Chat Room
              </h2>
              <button onClick={() => setShowCreateModal(false)} className="text-[#565959] hover:text-[#111]">
                <X size={18} />
              </button>
            </div>

            {modalError && (
              <div className="p-3 rounded-xl bg-[#FFF] border border-[#B12704] text-[#B12704] text-xs font-semibold">
                {modalError}
              </div>
            )}

            {/* Quick Templates */}
            <div>
              <label className="block text-xs font-bold text-[#565959] mb-2">Preset Templates:</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => applyTemplate('SPECIAL_REQUEST')}
                  className="p-2.5 rounded-xl bg-[#FFF] hover:bg-[#F0F2F2] border border-[#D5D9D9] hover:border-amber-500/60 text-left transition-all col-span-2"
                >
                  <p className="text-xs font-black text-[#111] flex items-center gap-1.5">
                    ✨ Special Product Request (Ask Shop Owner)
                  </p>
                  <p className="text-[10px] text-[#565959]">Directly contact merchant/shop owner for custom requests</p>
                </button>

                <button
                  type="button"
                  onClick={() => applyTemplate('ORDER_SUPPORT')}
                  className="p-2.5 rounded-xl bg-[#F3F3F3] hover:bg-[#F0F2F2] border border-[#D5D9D9] hover:border-amazon-orange/40 text-left transition-all"
                >
                  <p className="text-xs font-bold text-[#111]">🛒 Order Support</p>
                  <p className="text-[10px] text-[#565959]">Link to customer order</p>
                </button>

                <button
                  type="button"
                  onClick={() => applyTemplate('PAYMENT')}
                  className="p-2.5 rounded-xl bg-[#F3F3F3] hover:bg-purple-600/20 border border-[#D5D9D9] hover:border-purple-500/40 text-left transition-all"
                >
                  <p className="text-xs font-bold text-[#111]">💳 Payment Inquiry</p>
                  <p className="text-[10px] text-[#565959]">Billing & Invoices</p>
                </button>
              </div>
            </div>

            <form onSubmit={handleCreateRoom} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-[#565959] mb-1">Target Shop / Merchant (Required for Special Requests)</label>
                {loadingShops ? (
                  <div className="text-xs text-[#565959] py-1">Loading available shops...</div>
                ) : (
                  <select
                    value={selectedShop}
                    onChange={(e) => setSelectedShop(e.target.value)}
                    className="w-full px-3 py-2.5 bg-white border border-[#D5D9D9] rounded-xl text-xs text-[#111] focus:outline-none focus:border-amazon-orange"
                  >
                    <option value="">-- Pick Target Shop --</option>
                    {shops.map((s) => (
                      <option key={s.id} value={s.id}>
                        🏪 {s.name} ({s.domain || 'Main Store'})
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div>
                <label className="block text-xs font-bold text-[#565959] mb-1">Room Type</label>
                <select
                  value={newRoomType}
                  onChange={(e) => setNewRoomType(e.target.value)}
                  className="w-full px-3 py-2.5 bg-white border border-[#D5D9D9] rounded-xl text-xs text-[#111] focus:outline-none focus:border-amazon-orange"
                >
                  <option value="ORDER_SUPPORT">🛒 Order / Special Request (Linked to Shop)</option>
                  <option value="DIRECT">💬 Direct Customer Support</option>
                  <option value="GROUP">👥 Store Group Channel</option>
                </select>
              </div>

              {newRoomType === 'ORDER_SUPPORT' && (
                <div>
                  <label className="block text-xs font-bold text-[#565959] mb-1">Link to Store Order (Optional)</label>
                  {loadingOrders ? (
                    <div className="text-xs text-[#565959] py-1">Loading recent orders...</div>
                  ) : (
                    <select
                      value={selectedOrder}
                      onChange={(e) => handleOrderSelect(e.target.value)}
                      className="w-full px-3 py-2.5 bg-white border border-[#D5D9D9] rounded-xl text-xs text-[#111] focus:outline-none focus:border-amazon-orange"
                    >
                      <option value="">-- Pick an Order --</option>
                      {orders.map((o) => (
                        <option key={o.id} value={o.id}>
                          Order #{String(o.id).substring(0, 8)} - ${o.total_amount || '0.00'} [{o.status || 'CREATED'}]
                        </option>
                      ))}
                    </select>
                  )}
                </div>
              )}

              <div>
                <label className="block text-xs font-bold text-[#565959] mb-1">Room Display Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Order Support #1002"
                  value={newRoomName}
                  onChange={(e) => setNewRoomName(e.target.value)}
                  className="w-full px-3 py-2.5 bg-white border border-[#D5D9D9] rounded-xl text-xs text-[#111] focus:outline-none focus:border-amazon-orange"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-[#565959] mb-1">Initial Greeting Message (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. Hello, welcome to customer support!"
                  value={initialMessage}
                  onChange={(e) => setInitialMessage(e.target.value)}
                  className="w-full px-3 py-2.5 bg-white border border-[#D5D9D9] rounded-xl text-xs text-[#111] focus:outline-none focus:border-amazon-orange"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-[#D5D9D9]">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 bg-[#F3F3F3] hover:bg-[#F0F2F2] text-[#565959] font-bold text-xs rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 btn-buy-now text-[#111] font-extrabold text-xs rounded-xl shadow-lg shadow-sm"
                >
                  Create & Launch Thread
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Add Participant */}
      {showAddUserModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-[#D5D9D9] rounded-2xl w-full max-w-md p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-black text-[#111] flex items-center gap-2">
                <UserPlus className="text-[#007185]" size={20} /> Add Room Participant
              </h2>
              <button onClick={() => setShowAddUserModal(false)} className="text-[#565959] hover:text-[#111]">
                <X size={18} />
              </button>
            </div>

            {modalError && (
              <div className="p-3 rounded-xl bg-[#FFF] border border-[#B12704] text-[#B12704] text-xs font-semibold">
                {modalError}
              </div>
            )}

            <form onSubmit={handleAddParticipant} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-[#565959] mb-1">Username (or User ID)</label>
                <input
                  type="text"
                  required
                  placeholder="Enter Username (e.g. john_doe)"
                  value={addUserId}
                  onChange={(e) => setAddUserId(e.target.value)}
                  className="w-full px-3 py-2.5 bg-white border border-[#D5D9D9] rounded-xl text-xs text-[#111] focus:outline-none focus:border-amazon-orange font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-[#565959] mb-1">Participant Display Name (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. Support Specialist"
                  value={addUserName}
                  onChange={(e) => setAddUserName(e.target.value)}
                  className="w-full px-3 py-2.5 bg-white border border-[#D5D9D9] rounded-xl text-xs text-[#111] focus:outline-none focus:border-amazon-orange"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-[#565959] mb-1">Participant Role</label>
                <select
                  value={addUserRole}
                  onChange={(e) => setAddUserRole(e.target.value)}
                  className="w-full px-3 py-2.5 bg-white border border-[#D5D9D9] rounded-xl text-xs text-[#111] focus:outline-none focus:border-amazon-orange"
                >
                  <option value="MEMBER">Member / Participant</option>
                  <option value="ADMIN">Room Moderator</option>
                </select>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-[#D5D9D9]">
                <button
                  type="button"
                  onClick={() => setShowAddUserModal(false)}
                  className="px-4 py-2 bg-[#F3F3F3] hover:bg-[#F0F2F2] text-[#565959] font-bold text-xs rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-amazon-orange hover:bg-amazon-orange/90 text-[#111] font-bold text-xs rounded-xl shadow-lg shadow-sm"
                >
                  Add Participant
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
