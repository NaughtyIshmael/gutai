package main

import (
	"errors"
	"math"
	"testing"
)

func TestNewCalculator_ReturnsNonNilInstance(t *testing.T) {
	calc := NewCalculator()
	if calc == nil {
		t.Fatal("NewCalculator() returned nil")
	}
	if calc.memory != 0 {
		t.Errorf("Expected initial memory to be 0, got %v", calc.memory)
	}
}

func TestCalculator_Add_SetsMemoryAndReturnsSum(t *testing.T) {
	calc := NewCalculator()
	tests := []struct {
		a, b, expected float64
	}{
		{1, 1, 2},
		{-1, 1, 0},
		{math.MaxFloat64, 0, math.MaxFloat64},
		{math.SmallestNonzeroFloat64, math.SmallestNonzeroFloat64, 2 * math.SmallestNonzeroFloat64},
	}
	for _, tt := range tests {
		result := calc.Add(tt.a, tt.b)
		if result != tt.expected {
			t.Errorf("Add(%v, %v) = %v; want %v", tt.a, tt.b, result, tt.expected)
		}
		if calc.memory != tt.expected {
			t.Errorf("Memory after Add(%v, %v) = %v; want %v", tt.a, tt.b, calc.memory, tt.expected)
		}
	}
}

func TestCalculator_Subtract_SetsMemoryAndReturnsDifference(t *testing.T) {
	calc := NewCalculator()
	tests := []struct {
		a, b, expected float64
	}{
		{5, 3, 2},
		{3, 5, -2},
		{0, 0, 0},
		{math.MaxFloat64, math.SmallestNonzeroFloat64, math.MaxFloat64 - math.SmallestNonzeroFloat64},
	}
	for _, tt := range tests {
		result := calc.Subtract(tt.a, tt.b)
		if result != tt.expected {
			t.Errorf("Subtract(%v, %v) = %v; want %v", tt.a, tt.b, result, tt.expected)
		}
		if calc.memory != tt.expected {
			t.Errorf("Memory after Subtract(%v, %v) = %v; want %v", tt.a, tt.b, calc.memory, tt.expected)
		}
	}
}

func TestCalculator_Multiply_SetsMemoryAndReturnsProduct(t *testing.T) {
	calc := NewCalculator()
	tests := []struct {
		a, b, expected float64
	}{
		{2, 3, 6},
		{0, 5, 0},
		{-2, 3, -6},
		{math.MaxFloat64, 1, math.MaxFloat64},
	}
	for _, tt := range tests {
		result := calc.Multiply(tt.a, tt.b)
		if result != tt.expected {
			t.Errorf("Multiply(%v, %v) = %v; want %v", tt.a, tt.b, result, tt.expected)
		}
		if calc.memory != tt.expected {
			t.Errorf("Memory after Multiply(%v, %v) = %v; want %v", tt.a, tt.b, calc.memory, tt.expected)
		}
	}
}

func TestCalculator_Divide_SetsMemoryAndReturnsQuotientOrError(t *testing.T) {
	calc := NewCalculator()
	tests := []struct {
		a, b          float64
		expected      float64
		expectingErr  bool
		expectedError error
	}{
		{10, 2, 5, false, nil},
		{10, 0, 0, true, errors.New("division by zero is not allowed")},
		{0, 10, 0, false, nil},
		{-10, 2, -5, false, nil},
	}
	for _, tt := range tests {
		result, err := calc.Divide(tt.a, tt.b)
		if tt.expectingErr {
			if err == nil {
				t.Errorf("Divide(%v, %v) expected error but got nil", tt.a, tt.b)
			} else if err.Error() != tt.expectedError.Error() {
				t.Errorf("Divide(%v, %v) error = %v; want %v", tt.a, tt.b, err, tt.expectedError)
			}
			if calc.memory != 0 {
				t.Errorf("Memory after failed Divide(%v, %v) = %v; want 0", tt.a, tt.b, calc.memory)
			}
		} else {
			if err != nil {
				t.Errorf("Divide(%v, %v) unexpected error: %v", tt.a, tt.b, err)
			}
			if result != tt.expected {
				t.Errorf("Divide(%v, %v) = %v; want %v", tt.a, tt.b, result, tt.expected)
			}
			if calc.memory != tt.expected {
				t.Errorf("Memory after Divide(%v, %v) = %v; want %v", tt.a, tt.b, calc.memory, tt.expected)
			}
		}
	}
}

func TestCalculator_Power_SetsMemoryAndReturnsPower(t *testing.T) {
	calc := NewCalculator()
	tests := []struct {
		a, b, expected float64
	}{
		{2, 3, 8},
		{5, 0, 1},
		{2, -2, 0.25},
		{0, 5, 0},
		{0, 0, 1}, // math.Pow(0,0) returns 1
	}
	for _, tt := range tests {
		result := calc.Power(tt.a, tt.b)
		if result != tt.expected {
			t.Errorf("Power(%v, %v) = %v; want %v", tt.a, tt.b, result, tt.expected)
		}
		if calc.memory != tt.expected {
			t.Errorf("Memory after Power(%v, %v) = %v; want %v", tt.a, tt.b, calc.memory, tt.expected)
		}
	}
}

func TestCalculator_SquareRoot_ReturnsResultOrErrorAndSetsMemory(t *testing.T) {
	calc := NewCalculator()
	tests := []struct {
		input         float64
		expected      float64
		expectingErr  bool
		expectedError error
	}{
		{16, 4, false, nil},
		{0, 0, false, nil},
		{1, 1, false, nil},
		{-1, 0, true, errors.New("cannot calculate square root of negative number")},
	}
	for _, tt := range tests {
		result, err := calc.SquareRoot(tt.input)
		if tt.expectingErr {
			if err == nil {
				t.Errorf("SquareRoot(%v) expected error but got nil", tt.input)
			} else if err.Error() != tt.expectedError.Error() {
				t.Errorf("SquareRoot(%v) error = %v; want %v", tt.input, err, tt.expectedError)
			}
			if calc.memory != 0 {
				t.Errorf("Memory after failed SquareRoot(%v) = %v; want 0", tt.input, calc.memory)
			}
		} else {
			if err != nil {
				t.Errorf("SquareRoot(%v) unexpected error: %v", tt.input, err)
			}
			if result != tt.expected {
				t.Errorf("SquareRoot(%v) = %v; want %v", tt.input, result, tt.expected)
			}
			if calc.memory != tt.expected {
				t.Errorf("Memory after SquareRoot(%v) = %v; want %v", tt.input, calc.memory, tt.expected)
			}
		}
	}
}

func TestCalculator_GetMemory_ReturnsLastResult(t *testing.T) {
	calc := NewCalculator()
	if mem := calc.GetMemory(); mem != 0 {
		t.Errorf("Initial memory = %v; want 0", mem)
	}
	calc.memory = 123.456
	if mem := calc.GetMemory(); mem != 123.456 {
		t.Errorf("GetMemory() = %v; want 123.456", mem)
	}
}

func TestCalculator_ClearMemory_ResetsMemoryToZero(t *testing.T) {
	calc := NewCalculator()
	calc.memory = 100
	calc.ClearMemory()
	if calc.memory != 0 {
		t.Errorf("Memory after ClearMemory() = %v; want 0", calc.memory)
	}
}

func TestIsEven_ReturnsTrueForEvenNumbersAndFalseForOdd(t *testing.T) {
	tests := []struct {
		input    int
		expected bool
	}{
		{0, true},
		{1, false},
		{2, true},
		{-2, true},
		{-3, false},
		{999999, false},
		{1000000, true},
	}
	for _, tt := range tests {
		result := IsEven(tt.input)
		if result != tt.expected {
			t.Errorf("IsEven(%v) = %v; want %v", tt.input, result, tt.expected)
		}
	}
}

func TestFactorial_ReturnsCorrectFactorialOrError(t *testing.T) {
	tests := []struct {
		input         int
		expected      int
		expectingErr  bool
		expectedError error
	}{
		{-1, 0, true, errors.New("factorial is not defined for negative numbers")},
		{0, 1, false, nil},
		{1, 1, false, nil},
		{2, 2, false, nil},
		{5, 120, false, nil},
		{10, 3628800, false, nil},
	}
	for _, tt := range tests {
		result, err := Factorial(tt.input)
		if tt.expectingErr {
			if err == nil {
				t.Errorf("Factorial(%v) expected error but got nil", tt.input)
			} else if err.Error() != tt.expectedError.Error() {
				t.Errorf("Factorial(%v) error = %v; want %v", tt.input, err, tt.expectedError)
			}
		} else {
			if err != nil {
				t.Errorf("Factorial(%v) unexpected error: %v", tt.input, err)
			}
			if result != tt.expected {
				t.Errorf("Factorial(%v) = %v; want %v", tt.input, result, tt.expected)
			}
		}
	}
}

func TestIsPrime_ReturnsTrueForPrimesAndFalseForNonPrimes(t *testing.T) {
	tests := []struct {
		input    int
		expected bool
	}{
		{-10, false},
		{0, false},
		{1, false},
		{2, true},
		{3, true},
		{4, false},
		{5, true},
		{9, false},
		{11, true},
		{25, false},
		{29, true},
		{97, true},
		{100, false},
		{7919, true}, // large prime
	}
	for _, tt := range tests {
		result := IsPrime(tt.input)
		if result != tt.expected {
			t.Errorf("IsPrime(%v) = %v; want %v", tt.input, result, tt.expected)
		}
	}
}