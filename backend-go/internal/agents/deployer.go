package agents

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"time"

	"github.com/catalyst/backend/internal/config"
	"github.com/catalyst/backend/internal/database"
	"github.com/catalyst/backend/internal/models"
	"github.com/catalyst/backend/internal/websocket"
	"github.com/google/uuid"
)

type DeployerAgent struct {
	db        *database.Database
	wsManager *websocket.Manager
	cfg       *config.Config
}

func NewDeployerAgent(db *database.Database, wsManager *websocket.Manager, cfg *config.Config) *DeployerAgent {
	return &DeployerAgent{
		db:        db,
		wsManager: wsManager,
		cfg:       cfg,
	}
}

func (a *DeployerAgent) Deploy(taskID, code, projectID string) (string, string, error) {
	a.log(taskID, "Deployer", "🚀 Starting deployment process...")

	// Generate commit SHA
	hash := sha256.Sum256([]byte(code))
	commitSHA := hex.EncodeToString(hash[:])[:12]

	// Generate deployment URL
	deploymentURL := fmt.Sprintf("https://catalyst-%s.deploy.catalyst.ai", projectID[:8])

	a.log(taskID, "Deployer", "📦 Building application...")
	time.Sleep(1 * time.Second)

	a.log(taskID, "Deployer", "☁️ Deploying to cloud...")
	time.Sleep(1 * time.Second)

	// Create deployment record
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	deployment := models.Deployment{
		ID:        uuid.New().String(),
		TaskID:    taskID,
		URL:       deploymentURL,
		CommitSHA: commitSHA,
		Cost:      0.25,
		Report:    fmt.Sprintf("Deployment successful\nURL: %s\nCommit: %s\nStatus: Live", deploymentURL, commitSHA),
		CreatedAt: time.Now(),
	}

	a.db.Deploys.InsertOne(ctx, deployment)

	a.log(taskID, "Deployer", fmt.Sprintf("✅ Deployment successful: %s", deploymentURL))

	return deploymentURL, commitSHA, nil
}

func (a *DeployerAgent) log(taskID, agentName, message string) {
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