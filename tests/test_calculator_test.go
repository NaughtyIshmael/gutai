package main

import (
	"testing"
)

func TestIsEven_PositiveEvenNumbers(t *testing.T) {
	testCases := []struct {
		input    int
		expected bool
	}{
		{2, true},
		{4, true},
		{100, true},
		{0, true},
	}

	for _, tc := range testCases {
		result := IsEven(tc.input)
		if result != tc.expected {
			t.Errorf("IsEven(%d) = %v; want %v", tc.input, result, tc.expected)
		}
	}
}

func TestIsEven_PositiveOddNumbers(t *testing.T) {
	testCases := []struct {
		input    int
		expected bool
	}{
		{1, false},
		{3, false},
		{99, false},
	}

	for _, tc := range testCases {
		result := IsEven(tc.input)
		if result != tc.expected {
			t.Errorf("IsEven(%d) = %v; want %v", tc.input, result, tc.expected)
		}
	}
}

func TestIsEven_NegativeEvenNumbers(t *testing.T) {
	testCases := []struct {
		input    int
		expected bool
	}{
		{-2, true},
		{-4, true},
		{-100, true},
	}

	for _, tc := range testCases {
		result := IsEven(tc.input)
		if result != tc.expected {
			t.Errorf("IsEven(%d) = %v; want %v", tc.input, result, tc.expected)
		}
	}
}

func TestIsEven_NegativeOddNumbers(t *testing.T) {
	testCases := []struct {
		input    int
		expected bool
	}{
		{-1, false},
		{-3, false},
		{-99, false},
	}

	for _, tc := range testCases {
		result := IsEven(tc.input)
		if result != tc.expected {
			t.Errorf("IsEven(%d) = %v; want %v", tc.input, result, tc.expected)
		}
	}
}

func TestIsEven_BoundaryValues(t *testing.T) {
	testCases := []struct {
		input    int
		expected bool
	}{
		{0, true},
		{1, false},
		{-1, false},
		{2147483647, false},  // max int32
		{-2147483648, true}, // min int32
	}

	for _, tc := range testCases {
		result := IsEven(tc.input)
		if result != tc.expected {
			t.Errorf("IsEven(%d) = %v; want %v", tc.input, result, tc.expected)
		}
	}
}

func TestCalculatorAdd_PositiveNumbers(t *testing.T) {
	calc := NewCalculator()
	testCases := []struct {
		a, b     float64
		expected float64
	}{
		{1, 2, 3},
		{0, 0, 0},
		{100, 200, 300},
		{0.5, 0.5, 1},
	}

	for _, tc := range testCases {
		result := calc.Add(tc.a, tc.b)
		if result != tc.expected {
			t.Errorf("Add(%f, %f) = %f; want %f", tc.a, tc.b, result, tc.expected)
		}
	}
}

func TestCalculatorAdd_NegativeNumbers(t *testing.T) {
	calc := NewCalculator()
	testCases := []struct {
		a, b     float64
		expected float64
	}{
		{-1, -2, -3},
		{-100, 100, 0},
		{-0.5, -0.5, -1},
	}

	for _, tc := range testCases {
		result := calc.Add(tc.a, tc.b)
		if result != tc.expected {
			t.Errorf("Add(%f, %f) = %f; want %f", tc.a, tc.b, result, tc.expected)
		}
	}
}

func TestCalculatorAdd_BoundaryValues(t *testing.T) {
	calc := NewCalculator()
	testCases := []struct {
		a, b     float64
		expected float64
	}{
		{1.7976931348623157e+308, 0, 1.7976931348623157e+308}, // max float64
		{-1.7976931348623157e+308, 0, -1.7976931348623157e+308}, // min float64
	}

	for _, tc := range testCases {
		result := calc.Add(tc.a, tc.b)
		if result != tc.expected {
			t.Errorf("Add(%f, %f) = %f; want %f", tc.a, tc.b, result, tc.expected)
		}
	}
}

func TestCalculatorMemory_MultipleOperations(t *testing.T) {
	calc := NewCalculator()
	calc.Add(10, 5)
	calc.Add(20, 30)
	expected := 65.0

	memory := calc.GetMemory()
	if memory != expected {
		t.Errorf("GetMemory() = %f; want %f", memory, expected)
	}
}

func TestCalculatorMemory_Reset(t *testing.T) {
	calc := NewCalculator()
	calc.Add(10, 5)
	calc.ResetMemory()
	expected := 0.0

	memory := calc.GetMemory()
	if memory != expected {
		t.Errorf("GetMemory() after ResetMemory() = %f; want %f", memory, expected)
	}
}