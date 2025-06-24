package main

import (
	"errors"
	"fmt"
	"strings"
	"time"
)

// StringUtils provides utility functions for string manipulation
type StringUtils struct{}

// NewStringUtils creates a new StringUtils instance
func NewStringUtils() *StringUtils {
	return &StringUtils{}
}

// Reverse reverses a string
func (s *StringUtils) Reverse(input string) string {
	runes := []rune(input)
	for i, j := 0, len(runes)-1; i < j; i, j = i+1, j-1 {
		runes[i], runes[j] = runes[j], runes[i]
	}
	return string(runes)
}

// IsPalindrome checks if a string is a palindrome
func (s *StringUtils) IsPalindrome(input string) bool {
	cleaned := strings.ToLower(strings.ReplaceAll(input, " ", ""))
	return cleaned == s.Reverse(cleaned)
}

// CountWords counts the number of words in a string
func (s *StringUtils) CountWords(input string) int {
	words := strings.Fields(input)
	return len(words)
}

// RemoveVowels removes all vowels from a string
func (s *StringUtils) RemoveVowels(input string) string {
	vowels := "aeiouAEIOU"
	result := ""
	for _, char := range input {
		if !strings.ContainsRune(vowels, char) {
			result += string(char)
		}
	}
	return result
}

// Logger provides simple logging functionality
type Logger struct {
	prefix string
}

// NewLogger creates a new logger with a prefix
func NewLogger(prefix string) *Logger {
	return &Logger{prefix: prefix}
}

// Info logs an info message
func (l *Logger) Info(message string) {
	fmt.Printf("[%s] INFO: %s - %s\n", l.prefix, time.Now().Format("2006-01-02 15:04:05"), message)
}

// Error logs an error message
func (l *Logger) Error(message string) {
	fmt.Printf("[%s] ERROR: %s - %s\n", l.prefix, time.Now().Format("2006-01-02 15:04:05"), message)
}

// Warning logs a warning message
func (l *Logger) Warning(message string) {
	fmt.Printf("[%s] WARNING: %s - %s\n", l.prefix, time.Now().Format("2006-01-02 15:04:05"), message)
}

// UserValidator validates user input
type UserValidator struct{}

// NewUserValidator creates a new user validator
func NewUserValidator() *UserValidator {
	return &UserValidator{}
}

// ValidateEmail checks if an email is valid (basic validation)
func (v *UserValidator) ValidateEmail(email string) error {
	if !strings.Contains(email, "@") {
		return errors.New("email must contain @ symbol")
	}
	if !strings.Contains(email, ".") {
		return errors.New("email must contain a domain")
	}
	if len(email) < 5 {
		return errors.New("email is too short")
	}
	return nil
}

// ValidatePassword checks if a password meets requirements
func (v *UserValidator) ValidatePassword(password string) error {
	if len(password) < 8 {
		return errors.New("password must be at least 8 characters long")
	}

	hasUpper := strings.ContainsAny(password, "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
	hasLower := strings.ContainsAny(password, "abcdefghijklmnopqrstuvwxyz")
	hasDigit := strings.ContainsAny(password, "0123456789")

	if !hasUpper {
		return errors.New("password must contain at least one uppercase letter")
	}
	if !hasLower {
		return errors.New("password must contain at least one lowercase letter")
	}
	if !hasDigit {
		return errors.New("password must contain at least one digit")
	}

	return nil
}

// ValidateAge checks if age is within valid range
func (v *UserValidator) ValidateAge(age int) error {
	if age < 0 {
		return errors.New("age cannot be negative")
	}
	if age > 150 {
		return errors.New("age cannot be greater than 150")
	}
	return nil
}
