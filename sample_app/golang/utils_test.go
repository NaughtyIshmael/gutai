package main

import (
	"testing"
)

func TestStringUtilsReverse(t *testing.T) {
	utils := NewStringUtils()
	result := utils.Reverse("hello")
	expected := "olleh"

	if result != expected {
		t.Errorf("Reverse('hello') = %s; want %s", result, expected)
	}
}

func TestUserValidatorValidateEmail(t *testing.T) {
	validator := NewUserValidator()

	// Test valid email
	err := validator.ValidateEmail("test@example.com")
	if err != nil {
		t.Errorf("ValidateEmail('test@example.com') should not return error, got: %v", err)
	}
}
