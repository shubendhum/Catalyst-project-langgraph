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

type PlannerAgent struct {
	db        *database.Database
	wsManager *websocket.Manager
	llmClient *llm.Client
}

func NewPlannerAgent(db *database.Database, wsManager *websocket.Manager, cfg *config.Config) *PlannerAgent {
	return &PlannerAgent{
		db:        db,
		wsManager: wsManager,
		llmClient: llm.NewClient(cfg.LLMKey, cfg.LLMProvider, cfg.LLMModel),
	}
}

func (a *PlannerAgent) Plan(taskID, prompt string) (string, error) {
	a.log(taskID, "Planner", "🧠 Analyzing requirements and creating development plan...")

	systemPrompt := "You are a planning agent. Analyze user requirements and create a structured development plan with phases and tasks. Output JSON format with: {phases: [{name, tasks: []}], tech_stack: {}, requirements: []}"
	userPrompt := "Create a detailed development plan for: " + prompt + "\n\nProvide a structured JSON plan."

	response, err := a.llmClient.SendMessage(systemPrompt, userPrompt)
	if err != nil {
		a.log(taskID, "Planner", "❌ Planning failed: "+err.Error())
		return "", err
	}

	a.log(taskID, "Planner", "✅ Plan created successfully")
	return response, nil
}

func (a *PlannerAgent) log(taskID, agentName, message string) {
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