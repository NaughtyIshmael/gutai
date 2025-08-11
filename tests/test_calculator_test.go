package main

import (
	"testing"
)

func TestIsEven_PositiveEvenNumbers(t *testing.T) {
	testCases := []struct {
		input    int
		expected bool
	}{
		{0, true},
		{2, true},
		{100, true},
		{1000000, true},
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
		{101, false},
		{1000001, false},
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
		{-0, true},
		{-2, true},
		{-100, true},
		{-1000000, true},
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
		{-101, false},
		{-1000001, false},
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
		{2147483647, false}, // max int32
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
		{0, 0, 0},
		{1, 1, 2},
		{1.5, 2.5, 4},
		{100, 200, 300},
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
		{-1, -1, -2},
		{-1.5, -2.5, -4},
		{-100, -200, -300},
	}

	for _, tc := range testCases {
		result := calc.Add(tc.a, tc.b)
		if result != tc.expected {
			t.Errorf("Add(%f, %f) = %f; want %f", tc.a, tc.b, result, tc.expected)
		}
	}
}

func TestCalculatorAdd_MixedNumbers(t *testing.T) {
	calc := NewCalculator()
	testCases := []struct {
		a, b     float64
		expected float64
	}{
		{-1, 1, 0},
		{1.5, -2.5, -1},
		{100, -50, 50},
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
	calc.Add(20, 5)
	calc.Add(-5, 5)

	expected := 40.0
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