package config

import "os"

type Config struct {
	MongoURL    string
	DBName      string
	CORSOrigins string
	LLMKey      string
	LLMProvider string
	LLMModel    string
	Port        string
	Environment string
}

func LoadConfig() *Config {
	return &Config{
		MongoURL:    getEnv("MONGO_URL", "mongodb://localhost:27017"),
		DBName:      getEnv("DB_NAME", "catalyst_db"),
		CORSOrigins: getEnv("CORS_ORIGINS", "*"),
		LLMKey:      getEnv("EMERGENT_LLM_KEY", ""),
		LLMProvider: getEnv("DEFAULT_LLM_PROVIDER", "anthropic"),
		LLMModel:    getEnv("DEFAULT_LLM_MODEL", "claude-3-7-sonnet-20250219"),
		Port:        getEnv("BACKEND_PORT", "8001"),
		Environment: getEnv("ENVIRONMENT", "development"),
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}