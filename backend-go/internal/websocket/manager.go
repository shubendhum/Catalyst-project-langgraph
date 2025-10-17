package websocket

import (
	"encoding/json"
	"net/http"
	"sync"

	"github.com/gorilla/websocket"
	logger "github.com/sirupsen/logrus"
)

type Manager struct {
	connections map[string]*websocket.Conn
	mu          sync.RWMutex
	upgrader    websocket.Upgrader
}

func NewManager() *Manager {
	return &Manager{
		connections: make(map[string]*websocket.Conn),
		upgrader: websocket.Upgrader{
			CheckOrigin: func(r *http.Request) bool {
				return true // Allow all origins (configure for production)
			},
		},
	}
}

func (m *Manager) HandleWebSocket(w http.ResponseWriter, r *http.Request, taskID string) {
	conn, err := m.upgrader.Upgrade(w, r, nil)
	if err != nil {
		logger.Errorf("Failed to upgrade connection: %v", err)
		return
	}

	m.mu.Lock()
	m.connections[taskID] = conn
	m.mu.Unlock()

	logger.Infof("WebSocket connected for task: %s", taskID)

	// Read messages (ping/pong)
	for {
		_, _, err := conn.ReadMessage()
		if err != nil {
			m.mu.Lock()
			delete(m.connections, taskID)
			m.mu.Unlock()
			conn.Close()
			logger.Infof("WebSocket disconnected for task: %s", taskID)
			break
		}
	}
}

func (m *Manager) SendLog(taskID string, logData map[string]interface{}) {
	m.mu.RLock()
	conn, exists := m.connections[taskID]
	m.mu.RUnlock()

	if !exists {
		return
	}

	data, err := json.Marshal(logData)
	if err != nil {
		logger.Errorf("Failed to marshal log: %v", err)
		return
	}

	if err := conn.WriteMessage(websocket.TextMessage, data); err != nil {
		logger.Errorf("Failed to send log: %v", err)
		m.mu.Lock()
		delete(m.connections, taskID)
		m.mu.Unlock()
	}
}