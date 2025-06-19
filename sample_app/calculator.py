"""
Sample calculator module for testing GUTAI E2E workflow.
This module intentionally has incomplete test coverage to demonstrate
the AI-powered test generation capability.
"""


class Calculator:
    """A simple calculator class with various mathematical operations."""

    def __init__(self):
        self.history = []

    def add(self, a, b):
        """Add two numbers."""
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result

    def subtract(self, a, b):
        """Subtract b from a."""
        result = a - b
        self.history.append(f"{a} - {b} = {result}")
        return result

    def multiply(self, a, b):
        """Multiply two numbers."""
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result

    def divide(self, a, b):
        """Divide a by b."""
        if b == 0:
            raise ValueError("Division by zero is not allowed")
        result = a / b
        self.history.append(f"{a} / {b} = {result}")
        return result

    def power(self, base, exponent):
        """Calculate base raised to the power of exponent."""
        result = base**exponent
        self.history.append(f"{base} ^ {exponent} = {result}")
        return result

    def square_root(self, number):
        """Calculate square root of a number."""
        if number < 0:
            raise ValueError("Cannot calculate square root of negative number")
        result = number**0.5
        self.history.append(f"√{number} = {result}")
        return result

    def factorial(self, n):
        """Calculate factorial of n."""
        if n < 0:
            raise ValueError("Factorial is not defined for negative numbers")
        if n == 0 or n == 1:
            return 1
        result = 1
        for i in range(2, n + 1):
            result *= i
        self.history.append(f"{n}! = {result}")
        return result

    def get_history(self):
        """Get calculation history."""
        return self.history.copy()

    def clear_history(self):
        """Clear calculation history."""
        self.history.clear()


def fibonacci(n):
    """Generate the nth Fibonacci number."""
    if n < 0:
        raise ValueError("Fibonacci is not defined for negative numbers")
    if n == 0:
        return 0
    if n == 1:
        return 1

    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def is_prime(number):
    """Check if a number is prime."""
    if number < 2:
        return False
    if number == 2:
        return True
    if number % 2 == 0:
        return False

    for i in range(3, int(number**0.5) + 1, 2):
        if number % i == 0:
            return False
    return True


def gcd(a, b):
    """Calculate the Greatest Common Divisor of two numbers."""
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


class StatisticsCalculator:
    """A class for statistical calculations."""

    @staticmethod
    def mean(numbers):
        """Calculate the arithmetic mean of a list of numbers."""
        if not numbers:
            raise ValueError("Cannot calculate mean of empty list")
        return sum(numbers) / len(numbers)

    @staticmethod
    def median(numbers):
        """Calculate the median of a list of numbers."""
        if not numbers:
            raise ValueError("Cannot calculate median of empty list")
        sorted_numbers = sorted(numbers)
        n = len(sorted_numbers)
        if n % 2 == 0:
            return (sorted_numbers[n // 2 - 1] + sorted_numbers[n // 2]) / 2
        else:
            return sorted_numbers[n // 2]

    @staticmethod
    def mode(numbers):
        """Calculate the mode of a list of numbers."""
        if not numbers:
            raise ValueError("Cannot calculate mode of empty list")

        frequency = {}
        for num in numbers:
            frequency[num] = frequency.get(num, 0) + 1

        max_count = max(frequency.values())
        modes = [num for num, count in frequency.items() if count == max_count]
        return modes[0] if len(modes) == 1 else modes
