module github.com/catalyst/backend

go 1.21

require (
	// Web Framework
	github.com/gin-gonic/gin v1.9.1
	github.com/gin-contrib/cors v1.5.0
	
	// MongoDB Driver
	go.mongodb.org/mongo-driver v1.13.1
	
	// WebSocket
	github.com/gorilla/websocket v1.5.1
	
	// Configuration
	github.com/joho/godotenv v1.5.1
	
	// LLM Integration
	github.com/sashabaranov/go-openai v1.20.2
	
	// HTTP Client
	github.com/go-resty/resty/v2 v2.11.0
	
	// UUID
	github.com/google/uuid v1.5.0
	
	// JSON
	github.com/tidwall/gjson v1.17.0
	
	// Logging
	github.com/sirupsen/logrus v1.9.3
	
	// Validation
	github.com/go-playground/validator/v10 v10.16.0
)