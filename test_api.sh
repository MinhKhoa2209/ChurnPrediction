#!/bin/bash

# Test script to verify API endpoints

echo "Testing API endpoints..."
echo ""

# Test health endpoint
echo "1. Testing health endpoint..."
curl -s http://localhost:8000/health | jq .
echo ""

# Test users endpoint (requires authentication)
echo "2. Testing users endpoint (should return 401 without auth)..."
curl -s -w "\nHTTP Status: %{http_code}\n" http://localhost:8000/api/v1/users
echo ""

echo "Done!"
