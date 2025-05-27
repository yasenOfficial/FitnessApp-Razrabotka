#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "Running linting checks..."

# Run Black
echo -e "\n${GREEN}Running Black...${NC}"
black . --check --config lint/black.toml
BLACK_EXIT=$?

# Run Flake8
echo -e "\n${GREEN}Running Flake8...${NC}"
flake8 . --config lint/flake8.ini
FLAKE8_EXIT=$?

# Run isort
echo -e "\n${GREEN}Running isort...${NC}"
isort . --check-only --settings-file lint/isort.cfg
ISORT_EXIT=$?

# Check if any linting check failed
if [ $BLACK_EXIT -ne 0 ] || [ $FLAKE8_EXIT -ne 0 ] || [ $ISORT_EXIT -ne 0 ]; then
    echo -e "\n${RED}Linting checks failed!${NC}"
    exit 1
else
    echo -e "\n${GREEN}All linting checks passed!${NC}"
    exit 0
fi 