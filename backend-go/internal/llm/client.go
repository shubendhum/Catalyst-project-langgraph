package llm

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

type Client struct {
	APIKey   string
	Provider string
	Model    string
}

type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

func NewClient(apiKey, provider, model string) *Client {
	return &Client{
		APIKey:   apiKey,
		Provider: provider,
		Model:    model,
	}
}

func (c *Client) SendMessage(systemPrompt, userPrompt string) (string, error) {
	if c.Provider == "anthropic" {
		return c.callClaude(systemPrompt, userPrompt)
	}
	return "", fmt.Errorf("unsupported provider: %s", c.Provider)
}

func (c *Client) callClaude(systemPrompt, userPrompt string) (string, error) {
	url := "https://api.anthropic.com/v1/messages"

	reqBody := map[string]interface{}{
		"model":      c.Model,
		"max_tokens": 4096,
		"system":     systemPrompt,
		"messages": []Message{
			{Role: "user", Content: userPrompt},
		},
	}

	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return "", err
	}

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return "", err
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("x-api-key", c.APIKey)
	req.Header.Set("anthropic-version", "2023-06-01")

	client := &http.Client{Timeout: 60 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("API error: %s", string(body))
	}

	var result map[string]interface{}
	if err := json.Unmarshal(body, &result); err != nil {
		return "", err
	}

	if content, ok := result["content"].([]interface{}); ok && len(content) > 0 {
		if textBlock, ok := content[0].(map[string]interface{}); ok {
			if text, ok := textBlock["text"].(string); ok {
				return text, nil
			}
		}
	}

	return "", fmt.Errorf("unexpected response format")
}