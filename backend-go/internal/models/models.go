package models

import (
	"time"
)

type Project struct {
	ID          string    `json:"id" bson:"id"`
	Name        string    `json:"name" bson:"name" binding:"required"`
	Description string    `json:"description" bson:"description"`
	Status      string    `json:"status" bson:"status"`
	CreatedAt   time.Time `json:"created_at" bson:"created_at"`
}

type Task struct {
	ID         string                 `json:"id" bson:"id"`
	ProjectID  string                 `json:"project_id" bson:"project_id" binding:"required"`
	Prompt     string                 `json:"prompt" bson:"prompt" binding:"required"`
	GraphState map[string]string      `json:"graph_state" bson:"graph_state"`
	Status     string                 `json:"status" bson:"status"`
	Cost       float64                `json:"cost" bson:"cost"`
	CreatedAt  time.Time              `json:"created_at" bson:"created_at"`
}

type AgentLog struct {
	ID        string    `json:"id" bson:"id"`
	TaskID    string    `json:"task_id" bson:"task_id"`
	AgentName string    `json:"agent_name" bson:"agent_name"`
	Message   string    `json:"message" bson:"message"`
	Timestamp time.Time `json:"timestamp" bson:"timestamp"`
}

type Deployment struct {
	ID        string    `json:"id" bson:"id"`
	TaskID    string    `json:"task_id" bson:"task_id"`
	URL       string    `json:"url" bson:"url"`
	CommitSHA string    `json:"commit_sha" bson:"commit_sha"`
	Cost      float64   `json:"cost" bson:"cost"`
	Report    string    `json:"report" bson:"report"`
	CreatedAt time.Time `json:"created_at" bson:"created_at"`
}

type ExplorerScan struct {
	ID         string    `json:"id" bson:"id"`
	SystemName string    `json:"system_name" bson:"system_name" binding:"required"`
	Brief      string    `json:"brief" bson:"brief"`
	Risks      []string  `json:"risks" bson:"risks"`
	Proposals  []string  `json:"proposals" bson:"proposals"`
	CreatedAt  time.Time `json:"created_at" bson:"created_at"`
}

type ProjectCreate struct {
	Name        string `json:"name" binding:"required"`
	Description string `json:"description"`
}

type TaskCreate struct {
	ProjectID string `json:"project_id" binding:"required"`
	Prompt    string `json:"prompt" binding:"required"`
}

type ExplorerScanCreate struct {
	SystemName  string `json:"system_name" binding:"required"`
	RepoURL     string `json:"repo_url"`
	JiraProject string `json:"jira_project"`
}