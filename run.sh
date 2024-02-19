#!/bin/bash

# Step 1: Ensure the script is executed from the project directory
if [ ! -f requirements.txt ]; then
    echo "requirements.txt not found. Please run this script from the project root directory."
    exit 1
fi

# Step 2: Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Step 3: Ask for OpenAI API Key
echo "Please enter your OpenAI API key:"
read OPENAI_API_KEY

# Step 4: Create or update the .env file with the OpenAI API key
echo "OPENAI_API_KEY=${OPENAI_API_KEY}" > .env

# Step 5: Run the server
echo "Starting the server..."
python src/client.py
