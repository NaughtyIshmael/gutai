package main

import (
	"errors"
	"testing"
)

func TestNewCalculator_ReturnsCalculatorWithZeroMemory(t *testing.T) {
	calc := NewCalculator()
	if calc == nil {
		t.Fatal("NewCalculator() returned nil")
	}
	if calc.GetMemory() != 0 {
		t.Errorf("Expected memory to be 0, got %v", calc.GetMemory())
	}
}

func TestCalculator_Add_SetsMemoryAndReturnsSum(t *testing.T) {
	calc := NewCalculator()
	result := calc.Add(3, 4)
	if result != 7 {
		t.Errorf("Add(3,4) = %v; want 7", result)
	}
	if calc.GetMemory() != 7 {
		t.Errorf("Memory after Add = %v; want 7", calc.GetMemory())
	}
}

func TestCalculator_Subtract_SetsMemoryAndReturnsDifference(t *testing.T) {
	calc := NewCalculator()
	result := calc.Subtract(10, 4)
	if result != 6 {
		t.Errorf("Subtract(10,4) = %v; want 6", result)
	}
	if calc.GetMemory() != 6 {
		t.Errorf("Memory after Subtract = %v; want 6", calc.GetMemory())
	}
}

func TestCalculator_Multiply_SetsMemoryAndReturnsProduct(t *testing.T) {
	calc := NewCalculator()
	result := calc.Multiply(5, 6)
	if result != 30 {
		t.Errorf("Multiply(5,6) = %v; want 30", result)
	}
	if calc.GetMemory() != 30 {
		t.Errorf("Memory after Multiply = %v; want 30", calc.GetMemory())
	}
}

func TestCalculator_Divide_ReturnsQuotientAndSetsMemory(t *testing.T) {
	calc := NewCalculator()
	result, err := calc.Divide(20, 4)
	if err != nil {
		t.Fatalf("Divide(20,4) returned error: %v", err)
	}
	if result != 5 {
		t.Errorf("Divide(20,4) = %v; want 5", result)
	}
	if calc.GetMemory() != 5 {
		t.Errorf("Memory after Divide = %v; want 5", calc.GetMemory())
	}
}

func TestCalculator_Divide_DivisionByZeroReturnsError(t *testing.T) {
	calc := NewCalculator()
	result, err := calc.Divide(10, 0)
	if err == nil {
		t.Fatal("Expected error for division by zero, got nil")
	}
	if result != 0 {
		t.Errorf("Result for division by zero = %v; want 0", result)
	}
	expectedErr := "division by zero is not allowed"
	if err.Error() != expectedErr {
		t.Errorf("Error message = %q; want %q", err.Error(), expectedErr)
	}
}

func TestCalculator_Power_SetsMemoryAndReturnsPower(t *testing.T) {
	calc := NewCalculator()
	result := calc.Power(2, 3)
	if result != 8 {
		t.Errorf("Power(2,3) = %v; want 8", result)
	}
	if calc.GetMemory() != 8 {
		t.Errorf("Memory after Power = %v; want 8", calc.GetMemory())
	}
}

func TestCalculator_SquareRoot_ReturnsRootAndSetsMemory(t *testing.T) {
	calc := NewCalculator()
	result, err := calc.SquareRoot(25)
	if err != nil {
		t.Fatalf("SquareRoot(25) returned error: %v", err)
	}
	if result != 5 {
		t.Errorf("SquareRoot(25) = %v; want 5", result)
	}
	if calc.GetMemory() != 5 {
		t.Errorf("Memory after SquareRoot = %v; want 5", calc.GetMemory())
	}
}

func TestCalculator_SquareRoot_NegativeInputReturnsError(t *testing.T) {
	calc := NewCalculator()
	result, err := calc.SquareRoot(-4)
	if err == nil {
		t.Fatal("Expected error for square root of negative number, got nil")
	}
	if result != 0 {
		t.Errorf("Result for square root of negative number = %v; want 0", result)
	}
	expectedErr := "cannot calculate square root of negative number"
	if err.Error() != expectedErr {
		t.Errorf("Error message = %q; want %q", err.Error(), expectedErr)
	}
}

func TestCalculator_ClearMemory_ResetsMemoryToZero(t *testing.T) {
	calc := NewCalculator()
	calc.Add(10, 5)
	if calc.GetMemory() == 0 {
		t.Fatal("Memory should not be zero after Add")
	}
	calc.ClearMemory()
	if calc.GetMemory() != 0 {
		t.Errorf("Memory after ClearMemory = %v; want 0", calc.GetMemory())
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
		result, err := Factorial(tt.input)
		if err != nil {
			t.Errorf("Factorial(%d) returned error: %v", tt.input, err)
			continue
		}
		if result != tt.expected {
			t.Errorf("Factorial(%d) = %d; want %d", tt.input, result, tt.expected)
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
		t.Errorf("Error message = %q; want %q", err.Error(), expectedErr)
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
	// Since main prints to stdout, we just ensure it runs without panic
	defer func() {
		if r := recover(); r != nil {
			t.Errorf("main() panicked: %v", r)
		}
	}()
	main()
}