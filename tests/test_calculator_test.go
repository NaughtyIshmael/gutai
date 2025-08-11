package main

import (
	"math"
	"testing"
)

func TestIsEven_PositiveEvenNumber(t *testing.T) {
	if !IsEven(2) {
		t.Errorf("IsEven(2) = false; want true")
	}
}

func TestIsEven_PositiveOddNumber(t *testing.T) {
	if IsEven(7) {
		t.Errorf("IsEven(7) = true; want false")
	}
}

func TestIsEven_Zero(t *testing.T) {
	if !IsEven(0) {
		t.Errorf("IsEven(0) = false; want true")
	}
}

func TestIsEven_NegativeEvenNumber(t *testing.T) {
	if !IsEven(-8) {
		t.Errorf("IsEven(-8) = false; want true")
	}
}

func TestIsEven_NegativeOddNumber(t *testing.T) {
	if IsEven(-11) {
		t.Errorf("IsEven(-11) = true; want false")
	}
}

func TestIsEven_MaxInt(t *testing.T) {
	if IsEven(int(^uint(0)>>1)) {
		t.Errorf("IsEven(MaxInt) = true; want false")
	}
}

func TestIsEven_MinInt(t *testing.T) {
	if !IsEven(-int(^uint(0)>>1)-1) {
		t.Errorf("IsEven(MinInt) = false; want true")
	}
}

func TestIsEven_BoundaryValues(t *testing.T) {
	boundaries := []int{math.MaxInt32, math.MinInt32, math.MaxInt32 - 1, math.MinInt32 + 1}
	expected := []bool{false, true, true, false}
	for i, val := range boundaries {
		if IsEven(val) != expected[i] {
			t.Errorf("IsEven(%d) = %v; want %v", val, IsEven(val), expected[i])
		}
	}
}