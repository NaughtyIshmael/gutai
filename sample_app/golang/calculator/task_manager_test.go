package main

import (
	"testing"
	"time"
)

func TestTaskManagerAddTask(t *testing.T) {
	tm := NewTaskManager()
	dueDate := time.Now().Add(24 * time.Hour)

	task := tm.AddTask("Test Task", "A test task", dueDate)

	if task.ID != 1 {
		t.Errorf("First task ID should be 1, got %d", task.ID)
	}

	if task.Title != "Test Task" {
		t.Errorf("Task title should be 'Test Task', got '%s'", task.Title)
	}
}

func TestTaskManagerGetTaskCount(t *testing.T) {
	tm := NewTaskManager()

	count := tm.GetTaskCount()
	if count != 0 {
		t.Errorf("New task manager should have 0 tasks, got %d", count)
	}

	tm.AddTask("Task 1", "Description", time.Now())
	count = tm.GetTaskCount()
	if count != 1 {
		t.Errorf("After adding one task, count should be 1, got %d", count)
	}
}
