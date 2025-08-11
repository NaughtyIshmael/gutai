package main

import (
	"errors"
	"math"
	"testing"
)

func TestNewCalculator(t *testing.T) {
	calc := NewCalculator()
	if calc == nil {
		t.Error("NewCalculator() returned nil")
	}
	if calc.memory != 0 {
		t.Errorf("Expected memory to be 0, got %f", calc.memory)
	}
}

func TestAdd(t *testing.T) {
	calc := NewCalculator()
	tests := []struct {
		a, b, expected float64
	}{
		{1, 2, 3},
		{-1, 1, 0},
		{0, 0, 0},
		{math.MaxFloat64, 0, math.MaxFloat64},
		{math.SmallestNonzeroFloat64, math.SmallestNonzeroFloat64, math.SmallestNonzeroFloat64 * 2},
	}

	for _, tt := range tests {
		result := calc.Add(tt.a, tt.b)
		if result != tt.expected {
			t.Errorf("Add(%f, %f) = %f, want %f", tt.a, tt.b, result, tt.expected)
		}
		if calc.memory != tt.expected {
			t.Errorf("Memory should be %f, got %f", tt.expected, calc.memory)
		}
	}
}

func TestSubtract(t *testing.T) {
	calc := NewCalculator()
	tests := []struct {
		a, b, expected float64
	}{
		{5, 3, 2},
		{-1, -1, 0},
		{0, 0, 0},
		{math.MaxFloat64, math.MaxFloat64, 0},
	}

	for _, tt := range tests {
		result := calc.Subtract(tt.a, tt.b)
		if result != tt.expected {
			t.Errorf("Subtract(%f, %f) = %f, want %f", tt.a, tt.b, result, tt.expected)
		}
		if calc.memory != tt.expected {
			t.Errorf("Memory should be %f, got %f", tt.expected, calc.memory)
		}
	}
}

func TestMultiply(t *testing.T) {
	calc := NewCalculator()
	tests := []struct {
		a, b, expected float64
	}{
		{2, 3, 6},
		{-1, 1, -1},
		{0, 100, 0},
		{math.MaxFloat64, 1, math.MaxFloat64},
	}

	for _, tt := range tests {
		result := calc.Multiply(tt.a, tt.b)
		if result != tt.expected {
			t.Errorf("Multiply(%f, %f) = %f, want %f", tt.a, tt.b, result, tt.expected)
		}
		if calc.memory != tt.expected {
			t.Errorf("Memory should be %f, got %f", tt.expected, calc.memory)
		}
	}
}

func TestDivide(t *testing.T) {
	calc := NewCalculator()
	tests := []struct {
		name           string
		a, b          float64
		expected       float64
		expectError    bool
		expectedErrMsg string
	}{
		{"normal division", 10, 2, 5, false, ""},
		{"divide by zero", 1, 0, 0, true, "division by zero is not allowed"},
		{"negative division", -10, 2, -5, false, ""},
		{"fraction result", 1, 2, 0.5, false, ""},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := calc.Divide(tt.a, tt.b)
			if tt.expectError {
				if err == nil {
					t.Error("Expected error but got none")
				} else if err.Error() != tt.expectedErrMsg {
					t.Errorf("Expected error message '%s', got '%s'", tt.expectedErrMsg, err.Error())
				}
			} else {
				if err != nil {
					t.Errorf("Unexpected error: %v", err)
				}
				if result != tt.expected {
					t.Errorf("Divide(%f, %f) = %f, want %f", tt.a, tt.b, result, tt.expected)
				}
				if calc.memory != tt.expected {
					t.Errorf("Memory should be %f, got %f", tt.expected, calc.memory)
				}
			}
		})
	}
}

func TestPower(t *testing.T) {
	calc := NewCalculator()
	tests := []struct {
		a, b, expected float64
	}{
		{2, 3, 8},
		{5, 0, 1},
		{0, 5, 0},
		{2, -1, 0.5},
	}

	for _, tt := range tests {
		result := calc.Power(tt.a, tt.b)
		if result != tt.expected {
			t.Errorf("Power(%f, %f) = %f, want %f", tt.a, tt.b, result, tt.expected)
		}
		if calc.memory != tt.expected {
			t.Errorf("Memory should be %f, got %f", tt.expected, calc.memory)
		}
	}
}

func TestSquareRoot(t *testing.T) {
	calc := NewCalculator()
	tests := []struct {
		name           string
		input          float64
		expected       float64
		expectError    bool
		expectedErrMsg string
	}{
		{"positive number", 16, 4, false, ""},
		{"zero", 0, 0, false, ""},
		{"negative number", -1, 0, true, "cannot calculate square root of negative number"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := calc.SquareRoot(tt.input)
			if tt.expectError {
				if err == nil {
					t.Error("Expected error but got none")
				} else if err.Error() != tt.expectedErrMsg {
					t.Errorf("Expected error message '%s', got '%s'", tt.expectedErrMsg, err.Error())
				}
			} else {
				if err != nil {
					t.Errorf("Unexpected error: %v", err)
				}
				if result != tt.expected {
					t.Errorf("SquareRoot(%f) = %f, want %f", tt.input, result, tt.expected)
				}
				if calc.memory != tt.expected {
					t.Errorf("Memory should be %f, got %f", tt.expected, calc.memory)
				}
			}
		})
	}
}

func TestGetMemory(t *testing.T) {
	calc := NewCalculator()
	if calc.GetMemory() != 0 {
		t.Errorf("Expected initial memory to be 0, got %f", calc.GetMemory())
	}

	calc.Add(1, 2)
	if calc.GetMemory() != 3 {
		t.Errorf("Expected memory to be 3, got %f", calc.GetMemory())
	}
}

func TestClearMemory(t *testing.T) {
	calc := NewCalculator()
	calc.Add(1, 2)
	calc.ClearMemory()
	if calc.memory != 0 {
		t.Errorf("Expected memory to be 0 after ClearMemory, got %f", calc.memory)
	}
}

func TestIsEven(t *testing.T) {
	tests := []struct {
		input    int
		expected bool
	}{
		{2, true},
		{3, false},
		{0, true},
		{-2, true},
		{-3, false},
	}

	for _, tt := range tests {
		result := IsEven(tt.input)
		if result != tt.expected {
			t.Errorf("IsEven(%d) = %t, want %t", tt.input, result, tt.expected)
		}
	}
}

func TestFactorial(t *testing.T) {
	tests := []struct {
		name           string
		input          int
		expected       int
		expectError    bool
		expectedErrMsg string
	}{
		{"factorial of 0", 0, 1, false, ""},
		{"factorial of 1", 1, 1, false, ""},
		{"factorial of 5", 5, 120, false, ""},
		{"negative input", -1, 0, true, "factorial is not defined for negative numbers"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := Factorial(tt.input)
			if tt.expectError {
				if err == nil {
					t.Error("Expected error but got none")
				} else if err.Error() != tt.expectedErrMsg {
					t.Errorf("Expected error message '%s', got '%s'", tt.expectedErrMsg, err.Error())
				}
			} else {
				if err != nil {
					t.Errorf("Unexpected error: %v", err)
				}
				if result != tt.expected {
					t.Errorf("Factorial(%d) = %d, want %d", tt.input, result, tt.expected)
				}
			}
		})
	}
}

func TestIsPrime(t *testing.T) {
	tests := []struct {
		input    int
		expected bool
	}{
		{2, true},
		{3, true},
		{4, false},
		{5, true},
		{1, false},
		{0, false},
		{-1, false},
		{997, true},
		{100, false},
	}

	for _, tt := range tests {
		result := IsPrime(tt.input)
		if result != tt.expected {
			t.Errorf("IsPrime(%d) = %t, want %t", tt.input, result, tt.expected)
		}
	}
}