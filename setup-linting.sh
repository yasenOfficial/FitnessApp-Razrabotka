#!/bin/bash

# Install Python development dependencies
pip install -r requirements-dev.txt

# Install Node.js dependencies
npm install

# Initialize pre-commit
pre-commit install

# Run initial formatting
echo "Running initial code formatting..."
black .
isort .
npm run lint:fix
npm run format

echo "Linting setup complete! Your code will now be automatically formatted before commits."
echo "You can also run these commands manually:"
echo "  Python:"
echo "    - flake8 . (check style)"
echo "    - black . (format code)"
echo "    - isort . (sort imports)"
echo "  JavaScript:"
echo "    - npm run lint (check style)"
echo "    - npm run lint:fix (fix style issues)"
echo "    - npm run format (format code)" 