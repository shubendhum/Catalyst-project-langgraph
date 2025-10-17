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

type ArchitectAgent struct {
	db        *database.Database
	wsManager *websocket.Manager
	llmClient *llm.Client
}

func NewArchitectAgent(db *database.Database, wsManager *websocket.Manager, cfg *config.Config) *ArchitectAgent {
	return &ArchitectAgent{
		db:        db,
		wsManager: wsManager,
		llmClient: llm.NewClient(cfg.LLMKey, cfg.LLMProvider, cfg.LLMModel),
	}
}

func (a *ArchitectAgent) Design(taskID, plan string) (string, error) {
	a.log(taskID, "Architect", "🏗️ Designing system architecture...")

	systemPrompt := "You are a software architect. Design system architecture including data models, API endpoints, file structure, and technology choices. Be specific and detailed."
	userPrompt := "Based on this plan: " + plan + "\n\nCreate a detailed architecture design including: data models, API endpoints, file structure, component hierarchy."

	response, err := a.llmClient.SendMessage(systemPrompt, userPrompt)
	if err != nil {
		a.log(taskID, "Architect", "❌ Architecture design failed: "+err.Error())
		return "", err
	}

	a.log(taskID, "Architect", "✅ Architecture designed successfully")
	return response, nil
}

func (a *ArchitectAgent) log(taskID, agentName, message string) {
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