package main

import (
	"testing"
)

func TestCalculatorAdd(t *testing.T) {
	calc := NewCalculator()
	result := calc.Add(2, 3)
	expected := 5.0

	if result != expected {
		t.Errorf("Add(2, 3) = %f; want %f", result, expected)
	}
}

func TestCalculatorMemory(t *testing.T) {
	calc := NewCalculator()
	calc.Add(10, 5)

	memory := calc.GetMemory()
	expected := 15.0

	if memory != expected {
		t.Errorf("GetMemory() = %f; want %f", memory, expected)
	}
}

func TestIsEven(t *testing.T) {
	if !IsEven(4) {
		t.Errorf("IsEven(4) should be true")
	}

	if IsEven(3) {
		t.Errorf("IsEven(3) should be false")
	}
}
