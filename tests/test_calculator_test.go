package main

import (
	"math"
	"testing"
)

func TestIsEven_PositiveEvenNumbers(t *testing.T) {
	tests := []struct {
		input    int
		expected bool
	}{
		{2, true},
		{4, true},
		{100, true},
		{0, true},
	}

	for _, tt := range tests {
		result := IsEven(tt.input)
		if result != tt.expected {
			t.Errorf("IsEven(%d) = %v; want %v", tt.input, result, tt.expected)
		}
	}
}

func TestIsEven_PositiveOddNumbers(t *testing.T) {
	tests := []struct {
		input    int
		expected bool
	}{
		{1, false},
		{3, false},
		{99, false},
	}

	for _, tt := range tests {
		result := IsEven(tt.input)
		if result != tt.expected {
			t.Errorf("IsEven(%d) = %v; want %v", tt.input, result, tt.expected)
		}
	}
}

func TestIsEven_NegativeEvenNumbers(t *testing.T) {
	tests := []struct {
		input    int
		expected bool
	}{
		{-2, true},
		{-4, true},
		{-100, true},
	}

	for _, tt := range tests {
		result := IsEven(tt.input)
		if result != tt.expected {
			t.Errorf("IsEven(%d) = %v; want %v", tt.input, result, tt.expected)
		}
	}
}

func TestIsEven_NegativeOddNumbers(t *testing.T) {
	tests := []struct {
		input    int
		expected bool
	}{
		{-1, false},
		{-3, false},
		{-99, false},
	}

	for _, tt := range tests {
		result := IsEven(tt.input)
		if result != tt.expected {
			t.Errorf("IsEven(%d) = %v; want %v", tt.input, result, tt.expected)
		}
	}
}

func TestIsEven_BoundaryValues(t *testing.T) {
	tests := []struct {
		input    int
		expected bool
	}{
		{math.MaxInt32 - 1, true},
		{math.MaxInt32, false},
		{math.MinInt32 + 1, false},
		{math.MinInt32, true},
	}

	for _, tt := range tests {
		result := IsEven(tt.input)
		if result != tt.expected {
			t.Errorf("IsEven(%d) = %v; want %v", tt.input, result, tt.expected)
		}
	}
}

func TestCalculatorAdd_PositiveNumbers(t *testing.T) {
	calc := NewCalculator()
	tests := []struct {
		a, b     float64
		expected float64
	}{
		{1, 2, 3},
		{0.1, 0.2, 0.3},
		{100, 200, 300},
	}

	for _, tt := range tests {
		result := calc.Add(tt.a, tt.b)
		if math.Abs(result-tt.expected) > 1e-9 {
			t.Errorf("Add(%f, %f) = %f; want %f", tt.a, tt.b, result, tt.expected)
		}
	}
}

func TestCalculatorAdd_NegativeNumbers(t *testing.T) {
	calc := NewCalculator()
	tests := []struct {
		a, b     float64
		expected float64
	}{
		{-1, -2, -3},
		{-0.1, -0.2, -0.3},
		{-100, -200, -300},
	}

	for _, tt := range tests {
		result := calc.Add(tt.a, tt.b)
		if math.Abs(result-tt.expected) > 1e-9 {
			t.Errorf("Add(%f, %f) = %f; want %f", tt.a, tt.b, result, tt.expected)
		}
	}
}

func TestCalculatorAdd_MixedNumbers(t *testing.T) {
	calc := NewCalculator()
	tests := []struct {
		a, b     float64
		expected float64
	}{
		{-1, 2, 1},
		{0.1, -0.2, -0.1},
		{100, -200, -100},
	}

	for _, tt := range tests {
		result := calc.Add(tt.a, tt.b)
		if math.Abs(result-tt.expected) > 1e-9 {
			t.Errorf("Add(%f, %f) = %f; want %f", tt.a, tt.b, result, tt.expected)
		}
	}
}

func TestCalculatorAdd_BoundaryValues(t *testing.T) {
	calc := NewCalculator()
	tests := []struct {
		a, b     float64
		expected float64
	}{
		{math.MaxFloat64, 0, math.MaxFloat64},
		{math.SmallestNonzeroFloat64, math.SmallestNonzeroFloat64, 2 * math.SmallestNonzeroFloat64},
		{-math.MaxFloat64, math.MaxFloat64, 0},
	}

	for _, tt := range tests {
		result := calc.Add(tt.a, tt.b)
		if math.Abs(result-tt.expected) > 1e-9 {
			t.Errorf("Add(%f, %f) = %f; want %f", tt.a, tt.b, result, tt.expected)
		}
	}
}

func TestCalculatorMemory_MultipleOperations(t *testing.T) {
	calc := NewCalculator()
	calc.Add(10, 5)
	calc.Add(20, 30)
	calc.Add(-5, 5)

	expected := 65.0
	result := calc.GetMemory()

	if result != expected {
		t.Errorf("GetMemory() = %f; want %f", result, expected)
	}
}

func TestCalculatorMemory_Reset(t *testing.T) {
	calc := NewCalculator()
	calc.Add(10, 5)
	calc.ResetMemory()

	expected := 0.0
	result := calc.GetMemory()

	if result != expected {
		t.Errorf("GetMemory() after ResetMemory() = %f; want %f", result, expected)
	}
}