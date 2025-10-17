package orchestrator

import (
	"context"
	"time"

	"github.com/catalyst/backend/internal/agents"
	"github.com/catalyst/backend/internal/config"
	"github.com/catalyst/backend/internal/database"
	"github.com/catalyst/backend/internal/websocket"
	"go.mongodb.org/mongo-driver/bson"
	logger "github.com/sirupsen/logrus"
)

func ExecuteTask(db *database.Database, wsManager *websocket.Manager, cfg *config.Config, taskID, prompt, projectID string) {
	defer func() {
		if r := recover(); r != nil {
			logger.Errorf("Task execution panic: %v", r)
			updateTaskStatus(db, taskID, "failed", nil)
		}
	}()

	// Update task status to running
	updateTaskStatus(db, taskID, "running", nil)

	// Phase 1: Planning
	planner := agents.NewPlannerAgent(db, wsManager, cfg)
	plan, err := planner.Plan(taskID, prompt)
	if err != nil {
		logger.Errorf("Planner failed: %v", err)
		updateTaskStatus(db, taskID, "failed", nil)
		return
	}
	updateGraphState(db, taskID, "planner", "completed")
	time.Sleep(1 * time.Second)

	// Phase 2: Architecture
	architect := agents.NewArchitectAgent(db, wsManager, cfg)
	architecture, err := architect.Design(taskID, plan)
	if err != nil {
		logger.Errorf("Architect failed: %v", err)
		updateTaskStatus(db, taskID, "failed", nil)
		return
	}
	updateGraphState(db, taskID, "architect", "completed")
	time.Sleep(1 * time.Second)

	// Phase 3-4: Coding with Testing Loop
	coder := agents.NewCoderAgent(db, wsManager, cfg)
	tester := agents.NewTesterAgent(db, wsManager, cfg)

	var code string
	var testResult string
	testPassed := false
	maxRetries := 2

	for attempt := 0; attempt < maxRetries; attempt++ {
		if attempt == 0 {
			code, err = coder.Code(taskID, architecture, "")
		} else {
			code, err = coder.Code(taskID, architecture, testResult)
		}

		if err != nil {
			logger.Errorf("Coder failed: %v", err)
			updateTaskStatus(db, taskID, "failed", nil)
			return
		}
		updateGraphState(db, taskID, "coder", "completed")
		time.Sleep(1 * time.Second)

		testResult, testPassed, err = tester.Test(taskID, code)
		if err != nil {
			logger.Errorf("Tester failed: %v", err)
			updateTaskStatus(db, taskID, "failed", nil)
			return
		}
		updateGraphState(db, taskID, "tester", "completed")

		if testPassed {
			break
		} else if attempt < maxRetries-1 {
			updateGraphState(db, taskID, "coder", "reworking")
			time.Sleep(1 * time.Second)
		}
	}

	if !testPassed {
		logger.Error("Tests failed after max retries")
		updateTaskStatus(db, taskID, "failed", nil)
		return
	}

	time.Sleep(1 * time.Second)

	// Phase 5: Review
	reviewer := agents.NewReviewerAgent(db, wsManager, cfg)
	_, err = reviewer.Review(taskID, code, testResult)
	if err != nil {
		logger.Errorf("Reviewer failed: %v", err)
		updateTaskStatus(db, taskID, "failed", nil)
		return
	}
	updateGraphState(db, taskID, "reviewer", "completed")
	time.Sleep(1 * time.Second)

	// Phase 6: Deployment
	deployer := agents.NewDeployerAgent(db, wsManager, cfg)
	_, _, err = deployer.Deploy(taskID, code, projectID)
	if err != nil {
		logger.Errorf("Deployer failed: %v", err)
		updateTaskStatus(db, taskID, "failed", nil)
		return
	}
	updateGraphState(db, taskID, "deployer", "completed")

	// Mark task as completed
	updateTaskStatusWithCost(db, taskID, "completed", 0.85)
}

func updateTaskStatus(db *database.Database, taskID, status string, graphState map[string]string) {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	update := bson.M{"status": status}
	if graphState != nil {
		update["graph_state"] = graphState
	}

	db.Tasks.UpdateOne(ctx, bson.M{"id": taskID}, bson.M{"$set": update})
}

func updateTaskStatusWithCost(db *database.Database, taskID, status string, cost float64) {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	db.Tasks.UpdateOne(ctx, bson.M{"id": taskID}, bson.M{"$set": bson.M{"status": status, "cost": cost}})
}

func updateGraphState(db *database.Database, taskID, node, status string) {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Get current task
	var task struct {
		GraphState map[string]string `bson:"graph_state"`
	}

	if err := db.Tasks.FindOne(ctx, bson.M{"id": taskID}).Decode(&task); err != nil {
		return
	}

	if task.GraphState == nil {
		task.GraphState = make(map[string]string)
	}

	task.GraphState[node] = status

	db.Tasks.UpdateOne(ctx, bson.M{"id": taskID}, bson.M{"$set": bson.M{"graph_state": task.GraphState}})
}
