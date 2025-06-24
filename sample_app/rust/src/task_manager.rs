/// A simple task management structure
#[derive(Debug, Clone, PartialEq)]
pub struct Task {
    pub id: usize,
    pub description: String,
    pub completed: bool,
}

impl Task {
    /// Creates a new task
    pub fn new(id: usize, description: String) -> Self {
        Task {
            id,
            description,
            completed: false,
        }
    }

    /// Marks the task as completed
    pub fn complete(&mut self) {
        self.completed = true;
    }

    /// Checks if the task is completed
    pub fn is_completed(&self) -> bool {
        self.completed
    }
}

/// A task manager to handle multiple tasks
pub struct TaskManager {
    tasks: Vec<Task>,
    next_id: usize,
}

impl TaskManager {
    /// Creates a new empty TaskManager
    pub fn new() -> Self {
        TaskManager {
            tasks: Vec::new(),
            next_id: 1,
        }
    }

    /// Adds a new task
    pub fn add_task(&mut self, description: String) -> usize {
        let task = Task::new(self.next_id, description);
        let id = task.id;
        self.tasks.push(task);
        self.next_id += 1;
        id
    }

    /// Completes a task by ID
    pub fn complete_task(&mut self, id: usize) -> bool {
        if let Some(task) = self.tasks.iter_mut().find(|t| t.id == id) {
            task.complete();
            true
        } else {
            false
        }
    }

    /// Gets the total number of tasks
    pub fn task_count(&self) -> usize {
        self.tasks.len()
    }

    /// Gets the number of completed tasks
    pub fn completed_count(&self) -> usize {
        self.tasks.iter().filter(|t| t.is_completed()).count()
    }

    /// Gets the number of pending tasks
    pub fn pending_count(&self) -> usize {
        self.task_count() - self.completed_count()
    }

    /// Gets all tasks
    pub fn get_tasks(&self) -> &Vec<Task> {
        &self.tasks
    }

    /// Gets a task by ID
    pub fn get_task(&self, id: usize) -> Option<&Task> {
        self.tasks.iter().find(|t| t.id == id)
    }

    /// Removes a task by ID
    pub fn remove_task(&mut self, id: usize) -> bool {
        if let Some(pos) = self.tasks.iter().position(|t| t.id == id) {
            self.tasks.remove(pos);
            true
        } else {
            false
        }
    }

    /// Clears all completed tasks
    pub fn clear_completed(&mut self) {
        self.tasks.retain(|t| !t.is_completed());
    }
}

impl Default for TaskManager {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_task_creation() {
        let task = Task::new(1, "Test task".to_string());
        assert_eq!(task.id, 1);
        assert_eq!(task.description, "Test task");
        assert!(!task.is_completed());
    }

    #[test]
    fn test_task_completion() {
        let mut task = Task::new(1, "Test task".to_string());
        assert!(!task.is_completed());
        task.complete();
        assert!(task.is_completed());
    }

    #[test]
    fn test_task_manager_creation() {
        let manager = TaskManager::new();
        assert_eq!(manager.task_count(), 0);
        assert_eq!(manager.completed_count(), 0);
        assert_eq!(manager.pending_count(), 0);
    }

    #[test]
    fn test_default() {
        let manager = TaskManager::default();
        assert_eq!(manager.task_count(), 0);
    }
}
