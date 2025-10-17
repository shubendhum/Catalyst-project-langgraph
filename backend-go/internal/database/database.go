package database

import (
	"context"
	"time"

	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

type Database struct {
	Client   *mongo.Client
	DB       *mongo.Database
	Projects *mongo.Collection
	Tasks    *mongo.Collection
	Logs     *mongo.Collection
	Deploys  *mongo.Collection
	Scans    *mongo.Collection
}

func Connect(mongoURL, dbName string) (*Database, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	client, err := mongo.Connect(ctx, options.Client().ApplyURI(mongoURL))
	if err != nil {
		return nil, err
	}

	// Ping the database
	if err := client.Ping(ctx, nil); err != nil {
		return nil, err
	}

	db := client.Database(dbName)

	return &Database{
		Client:   client,
		DB:       db,
		Projects: db.Collection("projects"),
		Tasks:    db.Collection("tasks"),
		Logs:     db.Collection("agent_logs"),
		Deploys:  db.Collection("deployments"),
		Scans:    db.Collection("explorer_scans"),
	}, nil
}

func (d *Database) Disconnect() error {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	return d.Client.Disconnect(ctx)
}