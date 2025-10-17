package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/catalyst/backend/internal/api"
	"github.com/catalyst/backend/internal/config"
	"github.com/catalyst/backend/internal/database"
	"github.com/catalyst/backend/internal/websocket"
	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
	logger "github.com/sirupsen/logrus"
)

func main() {
	// Load environment variables
	if err := godotenv.Load(".env"); err != nil {
		logger.Warn("No .env file found")
	}

	// Initialize logger
	logger.SetFormatter(&logger.JSONFormatter{})
	logger.SetOutput(os.Stdout)
	logLevel := os.Getenv("LOG_LEVEL")
	if logLevel == "DEBUG" {
		logger.SetLevel(logger.DebugLevel)
	} else {
		logger.SetLevel(logger.InfoLevel)
	}

	logger.Info("Starting Catalyst Backend (Go)...")

	// Load configuration
	cfg := config.LoadConfig()

	// Connect to MongoDB
	db, err := database.Connect(cfg.MongoURL, cfg.DBName)
	if err != nil {
		logger.Fatalf("Failed to connect to MongoDB: %v", err)
	}
	defer db.Disconnect()

	logger.Info("Connected to MongoDB")

	// Initialize WebSocket manager
	wsManager := websocket.NewManager()

	// Setup Gin router
	if cfg.Environment == "production" {
		gin.SetMode(gin.ReleaseMode)
	}
	router := gin.Default()

	// CORS configuration
	corsConfig := cors.DefaultConfig()
	if cfg.CORSOrigins == "*" {
		corsConfig.AllowAllOrigins = true
	} else {
		corsConfig.AllowOrigins = []string{cfg.CORSOrigins}
	}
	corsConfig.AllowMethods = []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"}
	corsConfig.AllowHeaders = []string{"Origin", "Content-Type", "Authorization"}
	router.Use(cors.New(corsConfig))

	// Health check endpoint
	router.GET("/api", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"message": "Catalyst AI Platform API (Go)",
			"version": "1.0.0",
		})
	})

	// Setup API routes
	api.SetupRoutes(router, db, wsManager, cfg)

	// WebSocket endpoint
	router.GET("/ws/:taskId", func(c *gin.Context) {
		taskID := c.Param("taskId")
		wsManager.HandleWebSocket(c.Writer, c.Request, taskID)
	})

	// Start server
	port := cfg.Port
	if port == "" {
		port = "8001"
	}

	srv := &http.Server{
		Addr:           ":" + port,
		Handler:        router,
		ReadTimeout:    10 * time.Second,
		WriteTimeout:   10 * time.Second,
		MaxHeaderBytes: 1 << 20,
	}

	// Graceful shutdown
	go func() {
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Fatalf("Failed to start server: %v", err)
		}
	}()

	logger.Infof("Server started on port %s", port)

	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	logger.Info("Shutting down server...")

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		logger.Fatalf("Server forced to shutdown: %v", err)
	}

	logger.Info("Server exited")
}