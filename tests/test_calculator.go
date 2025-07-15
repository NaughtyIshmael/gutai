package main

import (
	"errors"
	"testing"
)

func TestNewCalculator_ReturnsNonNilInstance(t *testing.T) {
	calc := NewCalculator()
	if calc == nil {
		t.Fatal("Expected NewCalculator to return a non-nil instance")
	}
	if calc.memory != 0 {
		t.Errorf("Expected initial memory to be 0, got %v", calc.memory)
	}
}

func TestCalculator_Add_SetsMemoryAndReturnsSum(t *testing.T) {
	calc := NewCalculator()
	result := calc.Add(3, 4)
	if result != 7 {
		t.Errorf("Add(3,4) = %v; want 7", result)
	}
	if calc.memory != 7 {
		t.Errorf("Memory after Add should be 7, got %v", calc.memory)
	}
}

func TestCalculator_Subtract_SetsMemoryAndReturnsDifference(t *testing.T) {
	calc := NewCalculator()
	result := calc.Subtract(10, 4)
	if result != 6 {
		t.Errorf("Subtract(10,4) = %v; want 6", result)
	}
	if calc.memory != 6 {
		t.Errorf("Memory after Subtract should be 6, got %v", calc.memory)
	}
}

func TestCalculator_Multiply_SetsMemoryAndReturnsProduct(t *testing.T) {
	calc := NewCalculator()
	result := calc.Multiply(5, 6)
	if result != 30 {
		t.Errorf("Multiply(5,6) = %v; want 30", result)
	}
	if calc.memory != 30 {
		t.Errorf("Memory after Multiply should be 30, got %v", calc.memory)
	}
}

func TestCalculator_Divide_SetsMemoryAndReturnsQuotient(t *testing.T) {
	calc := NewCalculator()
	result, err := calc.Divide(20, 4)
	if err != nil {
		t.Fatalf("Divide(20,4) returned unexpected error: %v", err)
	}
	if result != 5 {
		t.Errorf("Divide(20,4) = %v; want 5", result)
	}
	if calc.memory != 5 {
		t.Errorf("Memory after Divide should be 5, got %v", calc.memory)
	}
}

func TestCalculator_Divide_ByZeroReturnsError(t *testing.T) {
	calc := NewCalculator()
	result, err := calc.Divide(10, 0)
	if err == nil {
		t.Fatal("Expected error when dividing by zero, got nil")
	}
	if result != 0 {
		t.Errorf("Expected result to be 0 on division by zero, got %v", result)
	}
	expectedErr := "division by zero is not allowed"
	if err.Error() != expectedErr {
		t.Errorf("Expected error message %q, got %q", expectedErr, err.Error())
	}
}

func TestCalculator_Power_SetsMemoryAndReturnsPower(t *testing.T) {
	calc := NewCalculator()
	result := calc.Power(2, 3)
	if result != 8 {
		t.Errorf("Power(2,3) = %v; want 8", result)
	}
	if calc.memory != 8 {
		t.Errorf("Memory after Power should be 8, got %v", calc.memory)
	}
}

func TestCalculator_SquareRoot_PositiveNumber(t *testing.T) {
	calc := NewCalculator()
	result, err := calc.SquareRoot(25)
	if err != nil {
		t.Fatalf("SquareRoot(25) returned unexpected error: %v", err)
	}
	if result != 5 {
		t.Errorf("SquareRoot(25) = %v; want 5", result)
	}
	if calc.memory != 5 {
		t.Errorf("Memory after SquareRoot should be 5, got %v", calc.memory)
	}
}

func TestCalculator_SquareRoot_Zero(t *testing.T) {
	calc := NewCalculator()
	result, err := calc.SquareRoot(0)
	if err != nil {
		t.Fatalf("SquareRoot(0) returned unexpected error: %v", err)
	}
	if result != 0 {
		t.Errorf("SquareRoot(0) = %v; want 0", result)
	}
	if calc.memory != 0 {
		t.Errorf("Memory after SquareRoot should be 0, got %v", calc.memory)
	}
}

func TestCalculator_SquareRoot_NegativeNumberReturnsError(t *testing.T) {
	calc := NewCalculator()
	result, err := calc.SquareRoot(-4)
	if err == nil {
		t.Fatal("Expected error when calculating square root of negative number, got nil")
	}
	if result != 0 {
		t.Errorf("Expected result to be 0 on error, got %v", result)
	}
	expectedErr := "cannot calculate square root of negative number"
	if err.Error() != expectedErr {
		t.Errorf("Expected error message %q, got %q", expectedErr, err.Error())
	}
}

func TestCalculator_GetMemory_ReturnsLastResult(t *testing.T) {
	calc := NewCalculator()
	calc.memory = 42.5
	got := calc.GetMemory()
	if got != 42.5 {
		t.Errorf("GetMemory() = %v; want 42.5", got)
	}
}

func TestCalculator_ClearMemory_ResetsMemoryToZero(t *testing.T) {
	calc := NewCalculator()
	calc.memory = 100
	calc.ClearMemory()
	if calc.memory != 0 {
		t.Errorf("ClearMemory() did not reset memory to 0, got %v", calc.memory)
	}
}

func TestIsEven_ReturnsTrueForEvenNumbers(t *testing.T) {
	evenNumbers := []int{0, 2, 4, 100, -2, -100}
	for _, n := range evenNumbers {
		if !IsEven(n) {
			t.Errorf("IsEven(%d) = false; want true", n)
		}
	}
}

func TestIsEven_ReturnsFalseForOddNumbers(t *testing.T) {
	oddNumbers := []int{1, 3, 5, 101, -1, -99}
	for _, n := range oddNumbers {
		if IsEven(n) {
			t.Errorf("IsEven(%d) = true; want false", n)
		}
	}
}

func TestFactorial_ReturnsCorrectFactorialForValidInput(t *testing.T) {
	tests := []struct {
		input    int
		expected int
	}{
		{0, 1},
		{1, 1},
		{2, 2},
		{3, 6},
		{5, 120},
		{7, 5040},
	}
	for _, tt := range tests {
		got, err := Factorial(tt.input)
		if err != nil {
			t.Errorf("Factorial(%d) returned unexpected error: %v", tt.input, err)
		}
		if got != tt.expected {
			t.Errorf("Factorial(%d) = %d; want %d", tt.input, got, tt.expected)
		}
	}
}

func TestFactorial_NegativeInputReturnsError(t *testing.T) {
	_, err := Factorial(-1)
	if err == nil {
		t.Fatal("Expected error for negative input to Factorial, got nil")
	}
	expectedErr := "factorial is not defined for negative numbers"
	if err.Error() != expectedErr {
		t.Errorf("Expected error message %q, got %q", expectedErr, err.Error())
	}
}

func TestIsPrime_ReturnsFalseForNonPrimes(t *testing.T) {
	nonPrimes := []int{-10, -1, 0, 1, 4, 6, 8, 9, 10, 12, 15, 20, 25, 100}
	for _, n := range nonPrimes {
		if IsPrime(n) {
			t.Errorf("IsPrime(%d) = true; want false", n)
		}
	}
}

func TestIsPrime_ReturnsTrueForPrimes(t *testing.T) {
	primes := []int{2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47}
	for _, n := range primes {
		if !IsPrime(n) {
			t.Errorf("IsPrime(%d) = false; want true", n)
		}
	}
}

func TestIsPrime_BoundaryValues(t *testing.T) {
	// Test boundary values around small primes
	if IsPrime(1) {
		t.Error("IsPrime(1) = true; want false")
	}
	if !IsPrime(2) {
		t.Error("IsPrime(2) = false; want true")
	}
	if !IsPrime(3) {
		t.Error("IsPrime(3) = false; want true")
	}
	if IsPrime(4) {
		t.Error("IsPrime(4) = true; want false")
	}
}

func TestMainFunction_ExecutesWithoutPanic(t *testing.T) {
	// We just call main to ensure it runs without panic.
	// Output is not captured here.
	defer func() {
		if r := recover(); r != nil {
			t.Errorf("main() panicked: %v", r)
		}
	}()
	main()
}