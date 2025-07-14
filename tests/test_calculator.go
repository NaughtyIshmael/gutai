package main

import (
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

func TestCalculator_Add(t *testing.T) {
	tests := []struct {
		name     string
		a, b     float64
		expected float64
	}{
		{"positive numbers", 2, 3, 5},
		{"negative numbers", -2, -3, -5},
		{"mixed numbers", -2, 3, 1},
		{"zero values", 0, 0, 0},
		{"large numbers", 1e10, 2e10, 3e10},
	}

	calc := NewCalculator()
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := calc.Add(tt.a, tt.b)
			if result != tt.expected {
				t.Errorf("Add(%f, %f) = %f, want %f", tt.a, tt.b, result, tt.expected)
			}
			if calc.memory != result {
				t.Errorf("Memory not updated correctly, got %f, want %f", calc.memory, result)
			}
		})
	}
}

func TestCalculator_Subtract(t *testing.T) {
	tests := []struct {
		name     string
		a, b     float64
		expected float64
	}{
		{"positive numbers", 5, 3, 2},
		{"negative numbers", -5, -3, -2},
		{"mixed numbers", -5, 3, -8},
		{"zero values", 0, 0, 0},
		{"large numbers", 2e10, 1e10, 1e10},
	}

	calc := NewCalculator()
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := calc.Subtract(tt.a, tt.b)
			if result != tt.expected {
				t.Errorf("Subtract(%f, %f) = %f, want %f", tt.a, tt.b, result, tt.expected)
			}
			if calc.memory != result {
				t.Errorf("Memory not updated correctly, got %f, want %f", calc.memory, result)
			}
		})
	}
}

func TestCalculator_Multiply(t *testing.T) {
	tests := []struct {
		name     string
		a, b     float64
		expected float64
	}{
		{"positive numbers", 2, 3, 6},
		{"negative numbers", -2, -3, 6},
		{"mixed numbers", -2, 3, -6},
		{"zero values", 0, 0, 0},
		{"large numbers", 1e10, 2e10, 2e20},
	}

	calc := NewCalculator()
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := calc.Multiply(tt.a, tt.b)
			if result != tt.expected {
				t.Errorf("Multiply(%f, %f) = %f, want %f", tt.a, tt.b, result, tt.expected)
			}
			if calc.memory != result {
				t.Errorf("Memory not updated correctly, got %f, want %f", calc.memory, result)
			}
		})
	}
}

func TestCalculator_Divide(t *testing.T) {
	tests := []struct {
		name        string
		a, b        float64
		expected    float64
		expectError bool
	}{
		{"positive numbers", 6, 3, 2, false},
		{"negative numbers", -6, -3, 2, false},
		{"mixed numbers", -6, 3, -2, false},
		{"division by zero", 6, 0, 0, true},
		{"large numbers", 2e20, 1e10, 2e10, false},
	}

	calc := NewCalculator()
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := calc.Divide(tt.a, tt.b)
			if tt.expectError {
				if err == nil {
					t.Error("Expected error but got none")
				}
			} else {
				if err != nil {
					t.Errorf("Unexpected error: %v", err)
				}
				if result != tt.expected {
					t.Errorf("Divide(%f, %f) = %f, want %f", tt.a, tt.b, result, tt.expected)
				}
				if calc.memory != result {
					t.Errorf("Memory not updated correctly, got %f, want %f", calc.memory, result)
				}
			}
		})
	}
}

func TestCalculator_Power(t *testing.T) {
	tests := []struct {
		name     string
		a, b     float64
		expected float64
	}{
		{"positive exponents", 2, 3, 8},
		{"negative exponents", 2, -3, 0.125},
		{"zero exponent", 5, 0, 1},
		{"fractional exponents", 4, 0.5, 2},
		{"large exponents", 2, 10, 1024},
	}

	calc := NewCalculator()
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := calc.Power(tt.a, tt.b)
			if math.Abs(result-tt.expected) > 1e-9 {
				t.Errorf("Power(%f, %f) = %f, want %f", tt.a, tt.b, result, tt.expected)
			}
			if calc.memory != result {
				t.Errorf("Memory not updated correctly, got %f, want %f", calc.memory, result)
			}
		})
	}
}

func TestCalculator_SquareRoot(t *testing.T) {
	tests := []struct {
		name        string
		a           float64
		expected    float64
		expectError bool
	}{
		{"positive number", 16, 4, false},
		{"zero", 0, 0, false},
		{"negative number", -16, 0, true},
		{"irrational result", 2, math.Sqrt(2), false},
	}

	calc := NewCalculator()
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := calc.SquareRoot(tt.a)
			if tt.expectError {
				if err == nil {
					t.Error("Expected error but got none")
				}
			} else {
				if err != nil {
					t.Errorf("Unexpected error: %v", err)
				}
				if math.Abs(result-tt.expected) > 1e-9 {
					t.Errorf("SquareRoot(%f) = %f, want %f", tt.a, result, tt.expected)
				}
				if calc.memory != result {
					t.Errorf("Memory not updated correctly, got %f, want %f", calc.memory, result)
				}
			}
		})
	}
}

func TestCalculator_GetMemory(t *testing.T) {
	calc := NewCalculator()
	if calc.GetMemory() != 0 {
		t.Error("Initial memory should be 0")
	}

	calc.Add(5, 3)
	if calc.GetMemory() != 8 {
		t.Error("Memory should be updated after operation")
	}
}

func TestCalculator_ClearMemory(t *testing.T) {
	calc := NewCalculator()
	calc.Add(5, 3)
	calc.ClearMemory()
	if calc.memory != 0 {
		t.Error("Memory should be cleared to 0")
	}
}

func TestIsEven(t *testing.T) {
	tests := []struct {
		name     string
		n        int
		expected bool
	}{
		{"even positive", 4, true},
		{"odd positive", 5, false},
		{"even negative", -4, true},
		{"odd negative", -5, false},
		{"zero", 0, true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := IsEven(tt.n)
			if result != tt.expected {
				t.Errorf("IsEven(%d) = %t, want %t", tt.n, result, tt.expected)
			}
		})
	}
}

func TestFactorial(t *testing.T) {
	tests := []struct {
		name        string
		n           int
		expected    int
		expectError bool
	}{
		{"factorial of 0", 0, 1, false},
		{"factorial of 1", 1, 1, false},
		{"factorial of 5", 5, 120, false},
		{"factorial of 10", 10, 3628800, false},
		{"negative number", -5, 0, true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := Factorial(tt.n)
			if tt.expectError {
				if err == nil {
					t.Error("Expected error but got none")
				}
			} else {
				if err != nil {
					t.Errorf("Unexpected error: %v", err)
				}
				if result != tt.expected {
					t.Errorf("Factorial(%d) = %d, want %d", tt.n, result, tt.expected)
				}
			}
		})
	}
}

func TestIsPrime(t *testing.T) {
	tests := []struct {
		name     string
		n        int
		expected bool
	}{
		{"small prime", 2, true},
		{"small non-prime", 4, false},
		{"large prime", 997, true},
		{"large non-prime", 1000, false},
		{"negative number", -7, false},
		{"zero", 0, false},
		{"one", 1, false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := IsPrime(tt.n)
			if result != tt.expected {
				t.Errorf("IsPrime(%d) = %t, want %t", tt.n, result, tt.expected)
			}
		})
	}
}