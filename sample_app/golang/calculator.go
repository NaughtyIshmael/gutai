package main

import (
	"errors"
	"fmt"
	"math"
)

// Calculator provides basic mathematical operations
type Calculator struct {
	memory float64
}

// NewCalculator creates a new calculator instance
func NewCalculator() *Calculator {
	return &Calculator{memory: 0}
}

// Add performs addition of two numbers
func (c *Calculator) Add(a, b float64) float64 {
	result := a + b
	c.memory = result
	return result
}

// Subtract performs subtraction of two numbers
func (c *Calculator) Subtract(a, b float64) float64 {
	result := a - b
	c.memory = result
	return result
}

// Multiply performs multiplication of two numbers
func (c *Calculator) Multiply(a, b float64) float64 {
	result := a * b
	c.memory = result
	return result
}

// Divide performs division of two numbers
func (c *Calculator) Divide(a, b float64) (float64, error) {
	if b == 0 {
		return 0, errors.New("division by zero is not allowed")
	}
	result := a / b
	c.memory = result
	return result, nil
}

// Power calculates a to the power of b
func (c *Calculator) Power(a, b float64) float64 {
	result := math.Pow(a, b)
	c.memory = result
	return result
}

// SquareRoot calculates the square root of a number
func (c *Calculator) SquareRoot(a float64) (float64, error) {
	if a < 0 {
		return 0, errors.New("cannot calculate square root of negative number")
	}
	result := math.Sqrt(a)
	c.memory = result
	return result, nil
}

// GetMemory returns the last calculated result
func (c *Calculator) GetMemory() float64 {
	return c.memory
}

// ClearMemory resets the memory to zero
func (c *Calculator) ClearMemory() {
	c.memory = 0
}

// IsEven checks if a number is even
func IsEven(n int) bool {
	return n%2 == 0
}

// Factorial calculates the factorial of a number
func Factorial(n int) (int, error) {
	if n < 0 {
		return 0, errors.New("factorial is not defined for negative numbers")
	}
	if n == 0 || n == 1 {
		return 1, nil
	}

	result := 1
	for i := 2; i <= n; i++ {
		result *= i
	}
	return result, nil
}

// IsPrime checks if a number is prime
func IsPrime(n int) bool {
	if n <= 1 {
		return false
	}
	if n <= 3 {
		return true
	}
	if n%2 == 0 || n%3 == 0 {
		return false
	}

	for i := 5; i*i <= n; i += 6 {
		if n%i == 0 || n%(i+2) == 0 {
			return false
		}
	}
	return true
}

func main() {
	calc := NewCalculator()

	fmt.Println("=== Calculator Demo ===")

	// Basic operations
	fmt.Printf("5 + 3 = %.2f\n", calc.Add(5, 3))
	fmt.Printf("10 - 4 = %.2f\n", calc.Subtract(10, 4))
	fmt.Printf("6 * 7 = %.2f\n", calc.Multiply(6, 7))

	if result, err := calc.Divide(15, 3); err == nil {
		fmt.Printf("15 / 3 = %.2f\n", result)
	}

	fmt.Printf("2^8 = %.2f\n", calc.Power(2, 8))

	if result, err := calc.SquareRoot(16); err == nil {
		fmt.Printf("√16 = %.2f\n", result)
	}

	fmt.Printf("Memory: %.2f\n", calc.GetMemory())

	// Utility functions
	fmt.Printf("Is 42 even? %t\n", IsEven(42))
	fmt.Printf("Is 17 prime? %t\n", IsPrime(17))

	if fact, err := Factorial(5); err == nil {
		fmt.Printf("5! = %d\n", fact)
	}
}
