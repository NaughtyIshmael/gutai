package main

import (
	"encoding/json"
	"errors"
	"sort"
	"time"
)

// Task represents a simple task with ID, title, and completion status
type Task struct {
	ID          int       `json:"id"`
	Title       string    `json:"title"`
	Description string    `json:"description"`
	Completed   bool      `json:"completed"`
	CreatedAt   time.Time `json:"created_at"`
	DueDate     time.Time `json:"due_date"`
}

// TaskManager manages a collection of tasks
type TaskManager struct {
	tasks  []Task
	nextID int
}

// NewTaskManager creates a new task manager
func NewTaskManager() *TaskManager {
	return &TaskManager{
		tasks:  make([]Task, 0),
		nextID: 1,
	}
}

// AddTask adds a new task to the manager
func (tm *TaskManager) AddTask(title, description string, dueDate time.Time) *Task {
	task := Task{
		ID:          tm.nextID,
		Title:       title,
		Description: description,
		Completed:   false,
		CreatedAt:   time.Now(),
		DueDate:     dueDate,
	}

	tm.tasks = append(tm.tasks, task)
	tm.nextID++

	return &task
}

// GetTask retrieves a task by ID
func (tm *TaskManager) GetTask(id int) (*Task, error) {
	for i := range tm.tasks {
		if tm.tasks[i].ID == id {
			return &tm.tasks[i], nil
		}
	}
	return nil, errors.New("task not found")
}

// GetAllTasks returns all tasks
func (tm *TaskManager) GetAllTasks() []Task {
	return tm.tasks
}

// GetCompletedTasks returns only completed tasks
func (tm *TaskManager) GetCompletedTasks() []Task {
	var completed []Task
	for _, task := range tm.tasks {
		if task.Completed {
			completed = append(completed, task)
		}
	}
	return completed
}

// GetPendingTasks returns only pending tasks
func (tm *TaskManager) GetPendingTasks() []Task {
	var pending []Task
	for _, task := range tm.tasks {
		if !task.Completed {
			pending = append(pending, task)
		}
	}
	return pending
}

// CompleteTask marks a task as completed
func (tm *TaskManager) CompleteTask(id int) error {
	for i := range tm.tasks {
		if tm.tasks[i].ID == id {
			tm.tasks[i].Completed = true
			return nil
		}
	}
	return errors.New("task not found")
}

// DeleteTask removes a task from the manager
func (tm *TaskManager) DeleteTask(id int) error {
	for i, task := range tm.tasks {
		if task.ID == id {
			tm.tasks = append(tm.tasks[:i], tm.tasks[i+1:]...)
			return nil
		}
	}
	return errors.New("task not found")
}

// GetOverdueTasks returns tasks that are past their due date
func (tm *TaskManager) GetOverdueTasks() []Task {
	var overdue []Task
	now := time.Now()

	for _, task := range tm.tasks {
		if !task.Completed && task.DueDate.Before(now) {
			overdue = append(overdue, task)
		}
	}
	return overdue
}

// GetTasksByPriority returns tasks sorted by due date (earliest first)
func (tm *TaskManager) GetTasksByPriority() []Task {
	tasksCopy := make([]Task, len(tm.tasks))
	copy(tasksCopy, tm.tasks)

	sort.Slice(tasksCopy, func(i, j int) bool {
		return tasksCopy[i].DueDate.Before(tasksCopy[j].DueDate)
	})

	return tasksCopy
}

// GetTaskCount returns the total number of tasks
func (tm *TaskManager) GetTaskCount() int {
	return len(tm.tasks)
}

// GetCompletionRate returns the percentage of completed tasks
func (tm *TaskManager) GetCompletionRate() float64 {
	if len(tm.tasks) == 0 {
		return 0.0
	}

	completed := 0
	for _, task := range tm.tasks {
		if task.Completed {
			completed++
		}
	}

	return float64(completed) / float64(len(tm.tasks)) * 100.0
}

// ExportToJSON exports all tasks to JSON format
func (tm *TaskManager) ExportToJSON() (string, error) {
	data, err := json.MarshalIndent(tm.tasks, "", "  ")
	if err != nil {
		return "", err
	}
	return string(data), nil
}

// ImportFromJSON imports tasks from JSON format
func (tm *TaskManager) ImportFromJSON(jsonData string) error {
	var tasks []Task
	err := json.Unmarshal([]byte(jsonData), &tasks)
	if err != nil {
		return err
	}

	tm.tasks = tasks

	// Update nextID to avoid conflicts
	maxID := 0
	for _, task := range tasks {
		if task.ID > maxID {
			maxID = task.ID
		}
	}
	tm.nextID = maxID + 1

	return nil
}
