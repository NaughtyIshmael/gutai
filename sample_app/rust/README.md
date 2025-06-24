# GUTAI Rust Sample Application

This is a sample Rust application that demonstrates basic Rust programming concepts and provides minimal but comprehensive test coverage for the GUTAI project.

## Features

The application consists of three main modules:

### Calculator (`src/calculator.rs`)

- Basic arithmetic operations (add, subtract, multiply, divide)
- Advanced operations (power, square root)
- Error handling for edge cases (division by zero, negative square roots)

### Task Manager (`src/task_manager.rs`)

- Task creation and management
- Task completion tracking
- Task removal and filtering
- Comprehensive task statistics

### Utils (`src/utils.rs`)

- String formatting and manipulation
- Email validation
- Word frequency analysis
- Mathematical utilities (Fibonacci, GCD, LCM)
- Text processing functions

## Building and Running

### Prerequisites

- Rust (latest stable version)
- Cargo (comes with Rust)

### Build the application

```bash
cargo build
```

### Run the application

```bash
cargo run
```

### Run tests

```bash
cargo test
```

### Run tests with output

```bash
cargo test -- --nocapture
```

### Run tests in verbose mode

```bash
cargo test --verbose
```

## Project Structure

```
src/
├── main.rs           # Main application entry point
├── calculator.rs     # Calculator module with arithmetic operations
├── task_manager.rs   # Task management functionality
└── utils.rs          # Utility functions and helpers
```

## Test Coverage

Each module includes comprehensive unit tests covering:

- Normal operation cases
- Edge cases and error conditions
- Input validation
- State management
- Mathematical accuracy

The tests can be run individually:

```bash
cargo test calculator::tests
cargo test task_manager::tests
cargo test utils::tests
```

## Example Usage

```rust
use calculator::Calculator;
use task_manager::TaskManager;
use utils::format_output;

let calc = Calculator::new();
let result = calc.add(10.0, 5.0);

let mut tasks = TaskManager::new();
let task_id = tasks.add_task("Sample task".to_string());
tasks.complete_task(task_id);

println!("{}", format_output("Tasks completed", &tasks.completed_count().to_string()));
```

## CI/CD Integration

This sample application is designed to work with GUTAI's automated testing and coverage analysis. The tests are structured to provide meaningful coverage data and can be easily integrated into GitHub Actions workflows.
