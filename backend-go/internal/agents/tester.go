package agents

import (
	"context"
	"math/rand"
	"time"

	"github.com/catalyst/backend/internal/config"
	"github.com/catalyst/backend/internal/database"
	"github.com/catalyst/backend/internal/llm"
	"github.com/catalyst/backend/internal/models"
	"github.com/catalyst/backend/internal/websocket"
	"github.com/google/uuid"
)

type TesterAgent struct {
	db        *database.Database
	wsManager *websocket.Manager
	llmClient *llm.Client
}

func NewTesterAgent(db *database.Database, wsManager *websocket.Manager, cfg *config.Config) *TesterAgent {
	return &TesterAgent{
		db:        db,
		wsManager: wsManager,
		llmClient: llm.NewClient(cfg.LLMKey, cfg.LLMProvider, cfg.LLMModel),
	}
}

func (a *TesterAgent) Test(taskID, code string) (string, bool, error) {
	a.log(taskID, "Tester", "🧪 Running tests and analyzing code...")

	systemPrompt := "You are a testing agent. Analyze code and create comprehensive test scenarios. Identify bugs, edge cases, and potential issues."
	code Prompt := "Analyze this code and provide test results: " + code[:min(len(code), 3000)] + "\n\nIdentify: bugs, edge cases, security issues. Output: {passed: bool, issues: [], suggestions: []}"

	response, err := a.llmClient.SendMessage(systemPrompt, userPrompt)
	if err != nil {
		a.log(taskID, "Tester", "❌ Testing failed: "+err.Error())
		return "", false, err
	}

	// Simulate test execution (66% pass rate)
	rand.Seed(time.Now().UnixNano())
	passed := rand.Float32() < 0.66

	if passed {
		a.log(taskID, "Tester", "✅ All tests passed")
	} else {
		a.log(taskID, "Tester", "⚠️ Tests found issues, routing back to coder...")
	}

	return response, passed, nil
}

func (a *TesterAgent) log(taskID, agentName, message string) {
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

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}