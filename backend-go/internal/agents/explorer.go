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

type ExplorerAgent struct {
	db        *database.Database
	wsManager *websocket.Manager
	llmClient *llm.Client
}

func NewExplorerAgent(db *database.Database, wsManager *websocket.Manager, cfg *config.Config) *ExplorerAgent {
	return &ExplorerAgent{
		db:        db,
		wsManager: wsManager,
		llmClient: llm.NewClient(cfg.LLMKey, cfg.LLMProvider, cfg.LLMModel),
	}
}

func (a *ExplorerAgent) ScanSystem(systemName, repoURL, jiraProject string) error {
	scanID := uuid.New().String()

	a.log(scanID, "Explorer", "🔍 Scanning system: "+systemName)

	// Gather system context (mocked connectors)
	context := "System: " + systemName + "\n"

	if repoURL != "" {
		a.log(scanID, "Explorer", "📂 Analyzing repository...")
		context += "Repository: " + repoURL + " (mocked analysis)\n"
	}

	if jiraProject != "" {
		a.log(scanID, "Explorer", "📋 Analyzing Jira project...")
		context += "Jira: " + jiraProject + " (mocked analysis)\n"
	}

	// AI analysis
	systemPrompt := "You are an enterprise explorer agent. Analyze existing systems read-only and provide insights, risks, and enhancement proposals. Never modify production systems."
	userPrompt := context + "\n\nProvide: 1) System brief, 2) Risk assessment, 3) Enhancement proposals. Be enterprise-safe."

	response, err := a.llmClient.SendMessage(systemPrompt, userPrompt)
	if err != nil {
		a.log(scanID, "Explorer", "❌ Scan failed: "+err.Error())
		return err
	}

	// Create scan record
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	scan := models.ExplorerScan{
		ID:         scanID,
		SystemName: systemName,
		Brief:      response[:min(len(response), 500)],
		Risks:      []string{"Data exposure risk", "Legacy dependencies"},
		Proposals:  []string{"API modernization", "Add monitoring"},
		CreatedAt:  time.Now(),
	}

	a.db.Scans.InsertOne(ctx, scan)

	a.log(scanID, "Explorer", "✅ System scan completed")
	return nil
}

func (a *ExplorerAgent) log(scanID, agentName, message string) {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	log := models.AgentLog{
		ID:        uuid.New().String(),
		TaskID:    scanID,
		AgentName: agentName,
		Message:   message,
		Timestamp: time.Now(),
	}

	a.db.Logs.InsertOne(ctx, log)
	a.wsManager.SendLog(scanID, map[string]interface{}{
		"task_id":    scanID,
		"agent_name": agentName,
		"message":    message,
		"timestamp":  log.Timestamp.Format(time.RFC3339),
	})
}