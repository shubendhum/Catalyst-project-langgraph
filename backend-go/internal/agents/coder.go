package agents

import (
	"context"
	"time"

	"github.com/catalyst/backend/internal/config"
	"github.com/catalyst/backend/internal/database"
	"github.com/catalyst/backend/internal/llm"
	"github.com/catalyst/backend/internal/models"
	"github.com/catalyst/backend/internal/websocket"
	"github.com/google/uuid"
)

type CoderAgent struct {
	db        *database.Database
	wsManager *websocket.Manager
	llmClient *llm.Client
}

func NewCoderAgent(db *database.Database, wsManager *websocket.Manager, cfg *config.Config) *CoderAgent {
	return &CoderAgent{
		db:        db,
		wsManager: wsManager,
		llmClient: llm.NewClient(cfg.LLMKey, cfg.LLMProvider, cfg.LLMModel),
	}
}

func (a *CoderAgent) Code(taskID, architecture, feedback string) (string, error) {
	if feedback != "" {
		a.log(taskID, "Coder", "🔄 Fixing code based on feedback...")
	} else {
		a.log(taskID, "Coder", "💻 Writing code implementation...")
	}

	systemPrompt := "You are a coding agent. Write clean, production-ready code based on architecture specifications. Include error handling, comments, and follow best practices."
	userPrompt := "Architecture: " + architecture
	if feedback != "" {
		userPrompt += "\n\nFeedback from tests/review: " + feedback
	}
	userPrompt += "\n\nGenerate complete code implementation. Provide file paths and code content."

	response, err := a.llmClient.SendMessage(systemPrompt, userPrompt)
	if err != nil {
		a.log(taskID, "Coder", "❌ Coding failed: "+err.Error())
		return "", err
	}

	a.log(taskID, "Coder", "✅ Code generated successfully")
	return response, nil
}

func (a *CoderAgent) log(taskID, agentName, message string) {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	log := models.AgentLog{
		ID:        uuid.New().String(),
		TaskID:    taskID,
		AgentName: agentName,
		Message:   message,
		Timestamp: time.Now(),
	}

	a.db.Logs.InsertOne(ctx, log)
	a.wsManager.SendLog(taskID, map[string]interface{}{
		"task_id":    taskID,
		"agent_name": agentName,
		"message":    message,
		"timestamp":  log.Timestamp.Format(time.RFC3339),
	})
}