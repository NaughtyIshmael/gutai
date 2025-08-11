package main

import (
	"errors"
	"math"
	"testing"
)

// --- NewCalculator ---

func TestNewCalculator_InitialMemoryIsZero(t *testing.T) {
	calc := NewCalculator()
	if calc == nil {
		t.Fatal("Expected non-nil Calculator instance")
	}
	if calc.memory != 0 {
		t.Errorf("Expected initial memory to be 0, got %v", calc.memory)
	}
}

// --- ClearMemory ---

func TestClearMemory_ResetsMemoryToZero(t *testing.T) {
	calc := NewCalculator()
	calc.memory = 123.45
	calc.ClearMemory()
	if calc.memory != 0 {
		t.Errorf("Expected memory to be 0 after ClearMemory, got %v", calc.memory)
	}
}

// --- Factorial ---

func TestFactorial_NegativeInput_ReturnsError(t *testing.T) {
	_, err := Factorial(-1)
	if err == nil {
		t.Error("Expected error for negative input")
	}
}

func TestFactorial_Zero_ReturnsOne(t *testing.T) {
	result, err := Factorial(0)
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}
	if result != 1 {
		t.Errorf("Expected 1, got %d", result)
	}
}

func TestFactorial_One_ReturnsOne(t *testing.T) {
	result, err := Factorial(1)
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}
	if result != 1 {
		t.Errorf("Expected 1, got %d", result)
	}
}

func TestFactorial_SmallNumbers(t *testing.T) {
	tests := []struct {
		n        int
		expected int
	}{
		{2, 2},
		{3, 6},
		{4, 24},
		{5, 120},
		{6, 720},
	}
	for _, tt := range tests {
		result, err := Factorial(tt.n)
		if err != nil {
			t.Errorf("Unexpected error for n=%d: %v", tt.n, err)
		}
		if result != tt.expected {
			t.Errorf("Factorial(%d) = %d, want %d", tt.n, result, tt.expected)
		}
	}
}

func TestFactorial_LargeNumber(t *testing.T) {
	result, err := Factorial(10)
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
	}
	if result != 3628800 {
		t.Errorf("Expected 3628800, got %d", result)
	}
}

// --- IsEven ---

func TestIsEven_EvenNumbers(t *testing.T) {
	evens := []int{0, 2, -2, 100, -100, math.MaxInt32 - 1}
	for _, n := range evens {
		if !IsEven(n) {
			t.Errorf("IsEven(%d) = false, want true", n)
		}
	}
}

func TestIsEven_OddNumbers(t *testing.T) {
	odds := []int{1, -1, 3, -3, 101, -101, math.MaxInt32}
	for _, n := range odds {
		if IsEven(n) {
			t.Errorf("IsEven(%d) = true, want false", n)
		}
	}
}

// --- IsPrime ---

func TestIsPrime_NonPrimes(t *testing.T) {
	nonPrimes := []int{-10, -1, 0, 1, 4, 6, 8, 9, 10, 12, 15, 21, 25, 100}
	for _, n := range nonPrimes {
		if IsPrime(n) {
			t.Errorf("IsPrime(%d) = true, want false", n)
		}
	}
}

func TestIsPrime_Primes(t *testing.T) {
	primes := []int{2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 97, 101}
	for _, n := range primes {
		if !IsPrime(n) {
			t.Errorf("IsPrime(%d) = false, want true", n)
		}
	}
}

func TestIsPrime_BoundaryCases(t *testing.T) {
	if IsPrime(1) {
		t.Error("IsPrime(1) = true, want false")
	}
	if !IsPrime(2) {
		t.Error("IsPrime(2) = false, want true")
	}
	if !IsPrime(3) {
		t.Error("IsPrime(3) = false, want true")
	}
}

// --- main (smoke test) ---

func TestMainFunction_Smoke(t *testing.T) {
	// Just ensure main runs without panic
	defer func() {
		if r := recover(); r != nil {
			t.Errorf("main panicked: %v", r)
		}
	}()
	main()
}

// --- Calculator Methods ---

func TestCalculator_Add(t *testing.T) {
	calc := NewCalculator()
	tests := []struct {
		a, b     float64
		expected float64
	}{
		{1, 2, 3},
		{-1, 1, 0},
		{0, 0, 0},
		{math.MaxFloat64, 0, math.MaxFloat64},
		{math.MaxFloat64, -math.MaxFloat64, 0},
	}
	for _, tt := range tests {
		result := calc.Add(tt.a, tt.b)
		if result != tt.expected {
			t.Errorf("Add(%v, %v) = %v, want %v", tt.a, tt.b, result, tt.expected)
		}
		if calc.memory != tt.expected {
			t.Errorf("Memory after Add(%v, %v) = %v, want %v", tt.a, tt.b, calc.memory, tt.expected)
		}
	}
}

func TestCalculator_Subtract(t *testing.T) {
	calc := NewCalculator()
	tests := []struct {
		a, b     float64
		expected float64
	}{
		{5, 3, 2},
		{0, 0, 0},
		{-1, -1, 0},
		{math.MaxFloat64, math.MaxFloat64, 0},
		{math.MinInt64, 1, float64(math.MinInt64) - 1},
	}
	for _, tt := range tests {
		result := calc.Subtract(tt.a, tt.b)
		if result != tt.expected {
			t.Errorf("Subtract(%v, %v) = %v, want %v", tt.a, tt.b, result, tt.expected)
		}
		if calc.memory != tt.expected {
			t.Errorf("Memory after Subtract(%v, %v) = %v, want %v", tt.a, tt.b, calc.memory, tt.expected)
		}
	}
}

func TestCalculator_Multiply(t *testing.T) {
	calc := NewCalculator()
	tests := []struct {
		a, b     float64
		expected float64
	}{
		{2, 3, 6},
		{0, 100, 0},
		{-2, 3, -6},
		{math.MaxFloat64, 0, 0},
	}
	for _, tt := range tests {
		result := calc.Multiply(tt.a, tt.b)
		if result != tt.expected {
			t.Errorf("Multiply(%v, %v) = %v, want %v", tt.a, tt.b, result, tt.expected)
		}
		if calc.memory != tt.expected {
			t.Errorf("Memory after Multiply(%v, %v) = %v, want %v", tt.a, tt.b, calc.memory, tt.expected)
		}
	}
}

func TestCalculator_Divide_NormalCases(t *testing.T) {
	calc := NewCalculator()
	tests := []struct {
		a, b     float64
		expected float64
	}{
		{6, 3, 2},
		{0, 1, 0},
		{-6, 3, -2},
		{math.MaxFloat64, 1, math.MaxFloat64},
	}
	for _, tt := range tests {
		result, err := calc.Divide(tt.a, tt.b)
		if err != nil {
			t.Errorf("Divide(%v, %v) unexpected error: %v", tt.a, tt.b, err)
		}
		if result != tt.expected {
			t.Errorf("Divide(%v, %v) = %v, want %v", tt.a, tt.b, result, tt.expected)
		}
		if calc.memory != tt.expected {
			t.Errorf("Memory after Divide(%v, %v) = %v, want %v", tt.a, tt.b, calc.memory, tt.expected)
		}
	}
}

func TestCalculator_Divide_ByZero(t *testing.T) {
	calc := NewCalculator()
	_, err := calc.Divide(1, 0)
	if err == nil {
		t.Error("Expected error for division by zero")
	}
	if !errors.Is(err, errors.New("division by zero is not allowed")) && err.Error() != "division by zero is not allowed" {
		t.Errorf("Unexpected error message: %v", err)
	}
}

func TestCalculator_Power(t *testing.T) {
	calc := NewCalculator()
	tests := []struct {
		a, b     float64
		expected float64
	}{
		{2, 3, 8},
		{5, 0, 1},
		{0, 5, 0},
		{2, -2, 0.25},
		{-2, 3, -8},
	}
	for _, tt := range tests {
		result := calc.Power(tt.a, tt.b)
		if math.Abs(result-tt.expected) > 1e-9 {
			t.Errorf("Power(%v, %v) = %v, want %v", tt.a, tt.b, result, tt.expected)
		}
		if math.Abs(calc.memory-tt.expected) > 1e-9 {
			t.Errorf("Memory after Power(%v, %v) = %v, want %v", tt.a, tt.b, calc.memory, tt.expected)
		}
	}
}

func TestCalculator_SquareRoot_Positive(t *testing.T) {
	calc := NewCalculator()
	tests := []struct {
		a        float64
		expected float64
	}{
		{4, 2},
		{0, 0},
		{9, 3},
		{1, 1},
	}
	for _, tt := range tests {
		result, err := calc.SquareRoot(tt.a)
		if err != nil {
			t.Errorf("SquareRoot(%v) unexpected error: %v", tt.a, err)
		}
		if math.Abs(result-tt.expected) > 1e-9 {
			t.Errorf("SquareRoot(%v) = %v, want %v", tt.a, result, tt.expected)
		}
		if math.Abs(calc.memory-tt.expected) > 1e-9 {
			t.Errorf("Memory after SquareRoot(%v) = %v, want %v", tt.a, calc.memory, tt.expected)
		}
	}
}

func TestCalculator_SquareRoot_Negative(t *testing.T) {
	calc := NewCalculator()
	_, err := calc.SquareRoot(-4)
	if err == nil {
		t.Error("Expected error for negative input to SquareRoot")
	}
	if !errors.Is(err, errors.New("cannot calculate square root of negative number")) && err.Error() != "cannot calculate square root of negative number" {
		t.Errorf("Unexpected error message: %v", err)
	}
}

func TestCalculator_GetMemory(t *testing.T) {
	calc := NewCalculator()
	calc.memory = 42.5
	if calc.GetMemory() != 42.5 {
		t.Errorf("GetMemory() = %v, want 42.5", calc.GetMemory())
	}
}

func TestCalculator_Memory_AfterOperations(t *testing.T) {
	calc := NewCalculator()
	calc.Add(1, 2)
	if calc.GetMemory() != 3 {
		t.Errorf("Memory after Add = %v, want 3", calc.GetMemory())
	}
	calc.Subtract(10, 5)
	if calc.GetMemory() != 5 {
		t.Errorf("Memory after Subtract = %v, want 5", calc.GetMemory())
	}
	calc.Multiply(2, 3)
	if calc.GetMemory() != 6 {
		t.Errorf("Memory after Multiply = %v, want 6", calc.GetMemory())
	}
	calc.Power(2, 4)
	if calc.GetMemory() != 16 {
		t.Errorf("Memory after Power = %v, want 16", calc.GetMemory())
	}
	calc.ClearMemory()
	if calc.GetMemory() != 0 {
		t.Errorf("Memory after ClearMemory = %v, want 0", calc.GetMemory())
	}
}