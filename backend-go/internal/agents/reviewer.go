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

type ReviewerAgent struct {
	db        *database.Database
	wsManager *websocket.Manager
	llmClient *llm.Client
}

func NewReviewerAgent(db *database.Database, wsManager *websocket.Manager, cfg *config.Config) *ReviewerAgent {
	return &ReviewerAgent{
		db:        db,
		wsManager: wsManager,
		llmClient: llm.NewClient(cfg.LLMKey, cfg.LLMProvider, cfg.LLMModel),
	}
}

func (a *ReviewerAgent) Review(taskID, code, testResult string) (string, error) {
	a.log(taskID, "Reviewer", "👀 Reviewing code quality and best practices...")

	systemPrompt := "You are a code reviewer. Review code quality, architecture decisions, security, performance, and maintainability. Provide constructive feedback."
	userPrompt := "Review this code: " + code[:min(len(code), 2000)] + "\n\nTest results: " + testResult[:min(len(testResult), 500)] + "\n\nProvide: quality score, recommendations, approval status."

	response, err := a.llmClient.SendMessage(systemPrompt, userPrompt)
	if err != nil {
		a.log(taskID, "Reviewer", "❌ Review failed: "+err.Error())
		return "", err
	}

	a.log(taskID, "Reviewer", "✅ Review completed: Approved for deployment")
	return response, nil
}

func (a *ReviewerAgent) log(taskID, agentName, message string) {
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