package main

import (
	"math"
	"testing"
)

func TestIsEven_PositiveEvenNumbers(t *testing.T) {
	testCases := []struct {
		input    int
		expected bool
	}{
		{0, true},
		{2, true},
		{10, true},
		{100, true},
		{1000, true},
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
		{11, false},
		{101, false},
		{1001, false},
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
		{-10, true},
		{-100, true},
		{-1000, true},
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
		{-11, false},
		{-101, false},
		{-1001, false},
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
		{math.MaxInt32 - 1, true},
		{math.MaxInt32, false},
		{math.MinInt32 + 1, false},
		{math.MinInt32, true},
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
		{1, 1, 2},
		{10, 20, 30},
		{0.5, 0.5, 1},
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
		{-10, -20, -30},
		{-0.5, -0.5, -1},
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
		{10, -20, -10},
		{-0.5, 0.5, 0},
		{100, -200, -100},
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
		{math.MaxFloat64, 0, math.MaxFloat64},
		{math.SmallestNonzeroFloat64, math.SmallestNonzeroFloat64, 2 * math.SmallestNonzeroFloat64},
		{-math.MaxFloat64, -math.MaxFloat64, -2 * math.MaxFloat64},
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
		t.Errorf("GetMemory() after Reset = %f; want %f", result, expected)
	}
}