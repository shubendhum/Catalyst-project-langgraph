import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { MessageSquare, Plus, Trash2, Edit2, Check, X } from 'lucide-react';

const ConversationSidebar = ({ 
  currentConversationId, 
  onSelectConversation, 
  onNewConversation,
  isOpen,
  onToggle 
}) => {
  const [conversations, setConversations] = useState([]);
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState('');
  const [loading, setLoading] = useState(true);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/chat/conversations?limit=50`);
      setConversations(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error loading conversations:', error);
      setLoading(false);
    }
  };

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (window.confirm('Delete this conversation?')) {
      try {
        await axios.delete(`${BACKEND_URL}/api/chat/conversations/${id}`);
        setConversations(conversations.filter(c => c.id !== id));
        if (currentConversationId === id) {
          onNewConversation();
        }
      } catch (error) {
        console.error('Error deleting conversation:', error);
      }
    }
  };

  const startEdit = (id, title, e) => {
    e.stopPropagation();
    setEditingId(id);
    setEditTitle(title);
  };

  const saveEdit = async (id, e) => {
    e.stopPropagation();
    try {
      await axios.patch(`${BACKEND_URL}/api/chat/conversations/${id}`, {
        title: editTitle
      });
      setConversations(conversations.map(c => 
        c.id === id ? { ...c, title: editTitle } : c
      ));
      setEditingId(null);
    } catch (error) {
      console.error('Error updating conversation:', error);
    }
  };

  const cancelEdit = (e) => {
    e.stopPropagation();
    setEditingId(null);
    setEditTitle('');
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    return date.toLocaleDateString();
  };

  const getConversationPreview = (conv) => {
    if (!conv.messages || conv.messages.length === 0) return 'No messages yet';
    const lastMessage = conv.messages[conv.messages.length - 1];
    const preview = lastMessage.content.substring(0, 50);
    return preview + (lastMessage.content.length > 50 ? '...' : '');
  };

  if (!isOpen) {
    return (
      <button
        onClick={onToggle}
        style={{
          position: 'fixed',
          left: '16px',
          top: '80px',
          zIndex: 1000,
          backgroundColor: '#3b82f6',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          padding: '8px 12px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
        }}
      >
        <MessageSquare size={20} />
        <span>Chats</span>
      </button>
    );
  }

  return (
    <div style={{
      width: '280px',
      height: '100vh',
      backgroundColor: '#1f2937',
      color: '#f9fafb',
      display: 'flex',
      flexDirection: 'column',
      borderRight: '1px solid #374151',
      position: 'fixed',
      left: 0,
      top: 0,
      zIndex: 999
    }}>
      {/* Header */}
      <div style={{
        padding: '16px',
        borderBottom: '1px solid #374151',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <h2 style={{ margin: 0, fontSize: '18px', fontWeight: '600' }}>Conversations</h2>
        <button
          onClick={onToggle}
          style={{
            background: 'none',
            border: 'none',
            color: '#9ca3af',
            cursor: 'pointer',
            padding: '4px'
          }}
        >
          <X size={20} />
        </button>
      </div>

      {/* New Chat Button */}
      <div style={{ padding: '16px', borderBottom: '1px solid #374151' }}>
        <button
          onClick={() => {
            onNewConversation();
            loadConversations();
          }}
          style={{
            width: '100%',
            backgroundColor: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            padding: '12px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            fontSize: '14px',
            fontWeight: '500'
          }}
        >
          <Plus size={18} />
          New Chat
        </button>
      </div>

      {/* Conversation List */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '8px'
      }}>
        {loading ? (
          <div style={{ padding: '16px', textAlign: 'center', color: '#9ca3af' }}>
            Loading...
          </div>
        ) : conversations.length === 0 ? (
          <div style={{ padding: '16px', textAlign: 'center', color: '#9ca3af' }}>
            No conversations yet
          </div>
        ) : (
          conversations.map(conv => (
            <div
              key={conv.id}
              onClick={() => onSelectConversation(conv.id)}
              style={{
                padding: '12px',
                marginBottom: '4px',
                borderRadius: '8px',
                cursor: 'pointer',
                backgroundColor: currentConversationId === conv.id ? '#374151' : 'transparent',
                transition: 'background-color 0.2s',
                display: 'flex',
                flexDirection: 'column',
                gap: '4px',
                position: 'relative'
              }}
              onMouseEnter={(e) => {
                if (currentConversationId !== conv.id) {
                  e.currentTarget.style.backgroundColor = '#2d3748';
                }
              }}
              onMouseLeave={(e) => {
                if (currentConversationId !== conv.id) {
                  e.currentTarget.style.backgroundColor = 'transparent';
                }
              }}
            >
              {editingId === conv.id ? (
                <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }} onClick={(e) => e.stopPropagation()}>
                  <input
                    type="text"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    style={{
                      flex: 1,
                      backgroundColor: '#1f2937',
                      border: '1px solid #4b5563',
                      borderRadius: '4px',
                      padding: '4px 8px',
                      color: '#f9fafb',
                      fontSize: '14px'
                    }}
                    autoFocus
                  />
                  <button
                    onClick={(e) => saveEdit(conv.id, e)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#10b981',
                      cursor: 'pointer',
                      padding: '2px'
                    }}
                  >
                    <Check size={16} />
                  </button>
                  <button
                    onClick={cancelEdit}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#ef4444',
                      cursor: 'pointer',
                      padding: '2px'
                    }}
                  >
                    <X size={16} />
                  </button>
                </div>
              ) : (
                <>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}>
                    <span style={{
                      fontSize: '14px',
                      fontWeight: '500',
                      color: '#f9fafb',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      flex: 1
                    }}>
                      {conv.title}
                    </span>
                    <div style={{ display: 'flex', gap: '4px', opacity: 0.7 }}>
                      <button
                        onClick={(e) => startEdit(conv.id, conv.title, e)}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: '#9ca3af',
                          cursor: 'pointer',
                          padding: '2px'
                        }}
                      >
                        <Edit2 size={14} />
                      </button>
                      <button
                        onClick={(e) => handleDelete(conv.id, e)}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: '#9ca3af',
                          cursor: 'pointer',
                          padding: '2px'
                        }}
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                  <div style={{
                    fontSize: '12px',
                    color: '#9ca3af',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }}>
                    {getConversationPreview(conv)}
                  </div>
                  <div style={{
                    fontSize: '11px',
                    color: '#6b7280'
                  }}>
                    {formatDate(conv.updated_at)}
                  </div>
                </>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default ConversationSidebar;
