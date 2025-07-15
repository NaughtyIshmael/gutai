package main

import (
	"testing"
)

func TestIsEven_PositiveEvenNumber_ReturnsTrue(t *testing.T) {
	if !IsEven(2) {
		t.Errorf("IsEven(2) = false; want true")
	}
}

func TestIsEven_PositiveOddNumber_ReturnsFalse(t *testing.T) {
	if IsEven(3) {
		t.Errorf("IsEven(3) = true; want false")
	}
}

func TestIsEven_Zero_ReturnsTrue(t *testing.T) {
	if !IsEven(0) {
		t.Errorf("IsEven(0) = false; want true")
	}
}

func TestIsEven_NegativeEvenNumber_ReturnsTrue(t *testing.T) {
	if !IsEven(-4) {
		t.Errorf("IsEven(-4) = false; want true")
	}
}

func TestIsEven_NegativeOddNumber_ReturnsFalse(t *testing.T) {
	if IsEven(-5) {
		t.Errorf("IsEven(-5) = true; want false")
	}
}