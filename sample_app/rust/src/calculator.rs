/// A simple calculator with basic arithmetic operations
pub struct Calculator;

impl Calculator {
    /// Creates a new Calculator instance
    pub fn new() -> Self {
        Calculator
    }

    /// Adds two numbers
    pub fn add(&self, a: f64, b: f64) -> f64 {
        a + b
    }

    /// Subtracts two numbers
    pub fn subtract(&self, a: f64, b: f64) -> f64 {
        a - b
    }

    /// Multiplies two numbers
    pub fn multiply(&self, a: f64, b: f64) -> f64 {
        a * b
    }

    /// Divides two numbers
    /// Returns None if dividing by zero
    pub fn divide(&self, a: f64, b: f64) -> Option<f64> {
        if b == 0.0 {
            None
        } else {
            Some(a / b)
        }
    }

    /// Calculates power of a number
    pub fn power(&self, base: f64, exponent: f64) -> f64 {
        base.powf(exponent)
    }

    /// Calculates square root
    /// Returns None for negative numbers
    pub fn sqrt(&self, x: f64) -> Option<f64> {
        if x < 0.0 {
            None
        } else {
            Some(x.sqrt())
        }
    }
}

impl Default for Calculator {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_add() {
        let calc = Calculator::new();
        assert_eq!(calc.add(2.0, 3.0), 5.0);
        assert_eq!(calc.add(-1.0, 1.0), 0.0);
        assert_eq!(calc.add(0.0, 0.0), 0.0);
    }

    #[test]
    fn test_subtract() {
        let calc = Calculator::new();
        assert_eq!(calc.subtract(5.0, 3.0), 2.0);
        assert_eq!(calc.subtract(1.0, 1.0), 0.0);
        assert_eq!(calc.subtract(0.0, 5.0), -5.0);
    }

    #[test]
    fn test_multiply() {
        let calc = Calculator::new();
        assert_eq!(calc.multiply(3.0, 4.0), 12.0);
        assert_eq!(calc.multiply(-2.0, 3.0), -6.0);
        assert_eq!(calc.multiply(0.0, 100.0), 0.0);
    }

    #[test]
    fn test_divide() {
        let calc = Calculator::new();
        assert_eq!(calc.divide(10.0, 2.0), Some(5.0));
        assert_eq!(calc.divide(7.0, 2.0), Some(3.5));
        assert_eq!(calc.divide(5.0, 0.0), None);
    }

    #[test]
    fn test_power() {
        let calc = Calculator::new();
        assert_eq!(calc.power(2.0, 3.0), 8.0);
        assert_eq!(calc.power(5.0, 0.0), 1.0);
        assert_eq!(calc.power(10.0, 2.0), 100.0);
    }

    #[test]
    fn test_default() {
        let calc = Calculator::default();
        assert_eq!(calc.add(1.0, 2.0), 3.0);
    }
}
