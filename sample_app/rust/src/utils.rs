/// Utility functions for the sample application
use std::collections::HashMap;

/// Formats output with a label and value
pub fn format_output(label: &str, value: &str) -> String {
    format!("{}: {}", label, value)
}

/// Validates an email address (simple validation)
pub fn is_valid_email(email: &str) -> bool {
    if email.len() <= 5 {
        return false;
    }

    let at_count = email.matches('@').count();
    if at_count != 1 {
        return false;
    }

    let parts: Vec<&str> = email.split('@').collect();
    if parts.len() != 2 || parts[0].is_empty() || parts[1].is_empty() {
        return false;
    }

    let domain = parts[1];
    domain.contains('.') && !domain.starts_with('.') && !domain.ends_with('.')
}

/// Capitalizes the first letter of a string
pub fn capitalize_first(s: &str) -> String {
    match s.chars().next() {
        None => String::new(),
        Some(first) => first.to_uppercase().collect::<String>() + &s[1..],
    }
}

/// Counts word frequency in a text
pub fn word_frequency(text: &str) -> HashMap<String, usize> {
    let mut frequency = HashMap::new();

    for word in text.split_whitespace() {
        let word = word
            .to_lowercase()
            .chars()
            .filter(|c| c.is_alphabetic())
            .collect::<String>();

        if !word.is_empty() {
            *frequency.entry(word).or_insert(0) += 1;
        }
    }

    frequency
}

/// Reverses a string
pub fn reverse_string(s: &str) -> String {
    s.chars().rev().collect()
}

/// Checks if a string is a palindrome
pub fn is_palindrome(s: &str) -> bool {
    let cleaned: String = s
        .chars()
        .filter(|c| c.is_alphanumeric())
        .map(|c| c.to_lowercase().next().unwrap())
        .collect();

    cleaned == reverse_string(&cleaned)
}

/// Calculates the Fibonacci number at position n
pub fn fibonacci(n: u32) -> u64 {
    match n {
        0 => 0,
        1 => 1,
        _ => {
            let mut a = 0;
            let mut b = 1;
            for _ in 2..=n {
                let temp = a + b;
                a = b;
                b = temp;
            }
            b
        }
    }
}

/// Finds the greatest common divisor of two numbers
pub fn gcd(mut a: u64, mut b: u64) -> u64 {
    while b != 0 {
        let temp = b;
        b = a % b;
        a = temp;
    }
    a
}

/// Finds the least common multiple of two numbers
pub fn lcm(a: u64, b: u64) -> u64 {
    if a == 0 || b == 0 {
        0
    } else {
        (a * b) / gcd(a, b)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_format_output() {
        let result = format_output("Test", "Value");
        assert_eq!(result, "Test: Value");
    }

    #[test]
    fn test_is_valid_email() {
        assert!(is_valid_email("test@example.com"));
        assert!(is_valid_email("user.name@domain.co.uk"));
        assert!(!is_valid_email("invalid.email"));
        assert!(!is_valid_email("@domain.com"));
        assert!(!is_valid_email("user@"));
        assert!(!is_valid_email(""));
    }

    #[test]
    fn test_capitalize_first() {
        assert_eq!(capitalize_first("hello"), "Hello");
        assert_eq!(capitalize_first("WORLD"), "WORLD");
        assert_eq!(capitalize_first("a"), "A");
        assert_eq!(capitalize_first(""), "");
    }
}
