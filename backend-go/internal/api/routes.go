package api

import (
	"context"
	"net/http"
	"time"

	"github.com/catalyst/backend/internal/agents"
	"github.com/catalyst/backend/internal/config"
	"github.com/catalyst/backend/internal/database"
	"github.com/catalyst/backend/internal/models"
	"github.com/catalyst/backend/internal/orchestrator"
	"github.com/catalyst/backend/internal/websocket"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo/options"
)

func SetupRoutes(router *gin.Engine, db *database.Database, wsManager *websocket.Manager, cfg *config.Config) {
	api := router.Group("/api")

	// Projects
	api.POST("/projects", createProject(db))
	api.GET("/projects", listProjects(db))
	api.GET("/projects/:id", getProject(db))

	// Tasks
	api.POST("/tasks", createTask(db, wsManager, cfg))
	api.GET("/tasks", listTasks(db))
	api.GET("/tasks/:id", getTask(db))

	// Logs
	api.GET("/logs/:taskId", getLogs(db))

	// Deployments
	api.GET("/deployments/:taskId", getDeployment(db))

	// Explorer
	api.POST("/explorer/scan", createExplorerScan(db, wsManager, cfg))
	api.GET("/explorer/scans", listExplorerScans(db))
}

func createProject(db *database.Database) gin.HandlerFunc {
	return func(c *gin.Context) {
		var req models.ProjectCreate
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		project := models.Project{
			ID:          uuid.New().String(),
			Name:        req.Name,
			Description: req.Description,
			Status:      "active",
			CreatedAt:   time.Now(),
		}

		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()

		if _, err := db.Projects.InsertOne(ctx, project); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}

		c.JSON(http.StatusOK, project)
	}
}

func listProjects(db *database.Database) gin.HandlerFunc {
	return func(c *gin.Context) {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()

		cursor, err := db.Projects.Find(ctx, bson.M{})
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		defer cursor.Close(ctx)

		var projects []models.Project
		if err := cursor.All(ctx, &projects); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}

		if projects == nil {
			projects = []models.Project{}
		}

		c.JSON(http.StatusOK, projects)
	}
}

func getProject(db *database.Database) gin.HandlerFunc {
	return func(c *gin.Context) {
		id := c.Param("id")

		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()

		var project models.Project
		if err := db.Projects.FindOne(ctx, bson.M{"id": id}).Decode(&project); err != nil {
			c.JSON(http.StatusNotFound, gin.H{"error": "Project not found"})
			return
		}

		c.JSON(http.StatusOK, project)
	}
}

func createTask(db *database.Database, wsManager *websocket.Manager, cfg *config.Config) gin.HandlerFunc {
	return func(c *gin.Context) {
		var req models.TaskCreate
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		task := models.Task{
			ID:         uuid.New().String(),
			ProjectID:  req.ProjectID,
			Prompt:     req.Prompt,
			GraphState: make(map[string]string),
			Status:     "pending",
			Cost:       0,
			CreatedAt:  time.Now(),
		}

		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()

		if _, err := db.Tasks.InsertOne(ctx, task); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}

		// Start task execution in background
		go orchestrator.ExecuteTask(db, wsManager, cfg, task.ID, task.Prompt, task.ProjectID)

		c.JSON(http.StatusOK, task)
	}
}

func listTasks(db *database.Database) gin.HandlerFunc {
	return func(c *gin.Context) {
		projectID := c.Query("project_id")

		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()

		filter := bson.M{}
		if projectID != "" {
			filter["project_id"] = projectID
		}

		cursor, err := db.Tasks.Find(ctx, filter)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		defer cursor.Close(ctx)

		var tasks []models.Task
		if err := cursor.All(ctx, &tasks); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}

		if tasks == nil {
			tasks = []models.Task{}
		}

		c.JSON(http.StatusOK, tasks)
	}
}

func getTask(db *database.Database) gin.HandlerFunc {
	return func(c *gin.Context) {
		id := c.Param("id")

		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()

		var task models.Task
		if err := db.Tasks.FindOne(ctx, bson.M{"id": id}).Decode(&task); err != nil {
			c.JSON(http.StatusNotFound, gin.H{"error": "Task not found"})
			return
		}

		c.JSON(http.StatusOK, task)
	}
}

func getLogs(db *database.Database) gin.HandlerFunc {
	return func(c *gin.Context) {
		taskID := c.Param("taskId")

		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()

		opts := options.Find().SetSort(bson.D{{"timestamp", 1}})
		cursor, err := db.Logs.Find(ctx, bson.M{"task_id": taskID}, opts)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		defer cursor.Close(ctx)

		var logs []models.AgentLog
		if err := cursor.All(ctx, &logs); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}

		if logs == nil {
			logs = []models.AgentLog{}
		}

		c.JSON(http.StatusOK, logs)
	}
}

func getDeployment(db *database.Database) gin.HandlerFunc {
	return func(c *gin.Context) {
		taskID := c.Param("taskId")

		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()

		var deployment models.Deployment
		if err := db.Deploys.FindOne(ctx, bson.M{"task_id": taskID}).Decode(&deployment); err != nil {
			c.JSON(http.StatusNotFound, gin.H{"error": "Deployment not found"})
			return
		}

		c.JSON(http.StatusOK, deployment)
	}
}

func createExplorerScan(db *database.Database, wsManager *websocket.Manager, cfg *config.Config) gin.HandlerFunc {
	return func(c *gin.Context) {
		var req models.ExplorerScanCreate
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		// Create scan in background
		go func() {
			explorer := agents.NewExplorerAgent(db, wsManager, cfg)
			explorer.ScanSystem(req.SystemName, req.RepoURL, req.JiraProject)
		}()

		// Return immediate response
		scan := models.ExplorerScan{
			ID:         uuid.New().String(),
			SystemName: req.SystemName,
			Brief:      "Scan initiated...",
			Risks:      []string{},
			Proposals:  []string{},
			CreatedAt:  time.Now(),
		}

		c.JSON(http.StatusOK, scan)
	}
}

func listExplorerScans(db *database.Database) gin.HandlerFunc {
	return func(c *gin.Context) {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()

		cursor, err := db.Scans.Find(ctx, bson.M{})
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		defer cursor.Close(ctx)

		var scans []models.ExplorerScan
		if err := cursor.All(ctx, &scans); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}

		if scans == nil {
			scans = []models.ExplorerScan{}
		}

		c.JSON(http.StatusOK, scans)
	}
}