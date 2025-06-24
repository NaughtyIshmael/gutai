# Golang Sample Application

This is a sample Golang application designed to test GUTAI's test generation capabilities for Go projects.

## Structure

The application consists of several modules:

### 1. Calculator (`calculator.go`)

A comprehensive calculator with the following features:

- Basic arithmetic operations (add, subtract, multiply, divide)
- Advanced operations (power, square root)
- Memory functionality
- Utility functions (factorial, prime checking, even number checking)

### 2. String Utilities (`utils.go`)

String manipulation and validation utilities:

- **StringUtils**: String operations (reverse, palindrome check, word count, etc.)
- **Logger**: Simple logging with timestamps
- **UserValidator**: Email, password, and age validation

### 3. Task Manager (`task_manager.go`)

A complete task management system:

- Create, read, update, delete tasks
- Task completion tracking
- Due date management
- Priority sorting
- JSON import/export
- Statistics (completion rate, overdue tasks)

## Features for Testing

This application provides various scenarios for unit test generation:

1. **Error Handling**: Functions that return errors (division by zero, negative square roots, etc.)
2. **Edge Cases**: Boundary conditions (empty strings, zero values, negative numbers)
3. **Data Structures**: Complex types with multiple fields and methods
4. **Business Logic**: Real-world functionality like task management
5. **Input Validation**: Email, password, and age validation
6. **Algorithms**: Prime checking, factorial calculation, string manipulation

## Running the Application

```bash
cd sample_app/golang
go run .
```

## Expected Test Coverage Areas

GUTAI should be able to generate tests for:

- ✅ **Unit tests** for individual functions
- ✅ **Error condition tests** for functions that can fail
- ✅ **Boundary value tests** for edge cases
- ✅ **Integration tests** for complex workflows
- ✅ **Struct method tests** for object-oriented functionality
- ✅ **JSON serialization/deserialization tests**
- ✅ **Validation logic tests**

This sample provides a realistic codebase that mirrors common Go development patterns and should challenge GUTAI to generate comprehensive, meaningful unit tests.
