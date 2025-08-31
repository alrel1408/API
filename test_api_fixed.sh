#!/bin/bash

# Test script untuk VPN API
# Pastikan API berfungsi dengan baik setelah perbaikan

API_KEY="3PWhU2T4_JDoy-iSZBGdVOp9yrlbv1oKkYtW8SsmJF0"
BASE_URL="http://localhost:7777"

echo "=== Testing VPN API Endpoints ==="
echo "API Key: ${API_KEY:0:10}..."
echo "Base URL: $BASE_URL"
echo ""

# Test 1: Server Info
echo "1. Testing /api/v1/info..."
response=$(curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/api/v1/info")
if [[ $response == *"status"*"success"* ]]; then
    echo "   ✅ SUCCESS: Server info retrieved"
else
    echo "   ❌ FAILED: $response"
fi
echo ""

# Test 2: Account Stats
echo "2. Testing /api/v1/accounts/stats..."
response=$(curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/api/v1/accounts/stats")
if [[ $response == *"status"*"success"* ]]; then
    echo "   ✅ SUCCESS: Account stats retrieved"
else
    echo "   ❌ FAILED: $response"
fi
echo ""

# Test 3: Accounts List
echo "3. Testing /api/v1/accounts/list..."
response=$(curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/api/v1/accounts/list")
if [[ $response == *"status"*"success"* ]]; then
    echo "   ✅ SUCCESS: Accounts list retrieved"
else
    echo "   ❌ FAILED: $response"
fi
echo ""

# Test 4: SSH List
echo "4. Testing /api/v1/ssh/list..."
response=$(curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/api/v1/ssh/list")
if [[ $response == *"status"*"success"* ]]; then
    echo "   ✅ SUCCESS: SSH list retrieved"
else
    echo "   ❌ FAILED: $response"
fi
echo ""

# Test 5: Trojan List
echo "5. Testing /api/v1/trojan/list..."
response=$(curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/api/v1/trojan/list")
if [[ $response == *"status"*"success"* ]]; then
    echo "   ✅ SUCCESS: Trojan list retrieved"
else
    echo "   ❌ FAILED: $response"
fi
echo ""

echo "=== API Test Completed ==="
echo "Jika semua test berhasil, API berfungsi dengan baik!"
