# Makefile for agent microservice

.PHONY: setup run test clean simulate simple

# Set default Python interpreter
PYTHON = python3

# Set directories
SRC_DIR = src
DATA_DIR = data
SCRIPTS_DIR = scripts

setup:
	@echo "Setting up agent microservice..."
	@mkdir -p $(DATA_DIR)/contexts
	@mkdir -p $(DATA_DIR)/purposes
	@mkdir -p $(DATA_DIR)/templates
	@chmod +x $(SCRIPTS_DIR)/*.sh
	@echo "Setup complete!"

run:
	@echo "Starting agent microservice..."
	@$(PYTHON) $(SRC_DIR)/main.py

test:
	@echo "Running tests..."
	@$(PYTHON) -m pytest tests/

clean:
	@echo "Cleaning data directories..."
	@rm -rf $(DATA_DIR)/contexts/*
	@rm -rf $(DATA_DIR)/purposes/*
	@echo "Clean complete!"

simulate:
	@echo "Running request simulation..."
	@$(SCRIPTS_DIR)/run_simulation.sh

simple:
	@echo "Running simplified simulation..."
	@$(SCRIPTS_DIR)/run_simple_simulation.sh 