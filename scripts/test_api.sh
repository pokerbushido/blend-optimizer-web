#!/bin/bash

# Script di test completo API backend
# Usage: ./test_api.sh

set -e

API_URL="${API_URL:-http://localhost:8000}"
USERNAME="${USERNAME:-admin}"
PASSWORD="${PASSWORD:-changeme123}"

echo "========================================="
echo "🧪 Testing Blend Optimizer API"
echo "========================================="
echo "API URL: $API_URL"
echo "User: $USERNAME"
echo ""

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "⚠️  jq is not installed. Installing..."
    echo "On macOS: brew install jq"
    echo "On Linux: sudo apt-get install jq"
    exit 1
fi

# 1. Health Check
echo "📊 1. Health Check"
echo "GET $API_URL/health"
HEALTH=$(curl -s "$API_URL/health")
echo "$HEALTH" | jq
if [ "$(echo "$HEALTH" | jq -r .status)" != "healthy" ]; then
    echo "❌ Health check failed!"
    exit 1
fi
echo "✅ Health check passed"
echo ""

# 2. Login
echo "🔐 2. Login Admin"
echo "POST $API_URL/api/auth/login"
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$USERNAME&password=$PASSWORD")

TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r .access_token)

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
    echo "❌ Login failed!"
    echo "$LOGIN_RESPONSE" | jq
    exit 1
fi

echo "Token obtained: ${TOKEN:0:50}..."
echo "✅ Login successful"
echo ""

# 3. Get Current User
echo "👤 3. Get Current User"
echo "GET $API_URL/api/auth/me"
USER_INFO=$(curl -s -X GET "$API_URL/api/auth/me" \
  -H "Authorization: Bearer $TOKEN")
echo "$USER_INFO" | jq
USERNAME_CHECK=$(echo "$USER_INFO" | jq -r .username)
if [ "$USERNAME_CHECK" != "$USERNAME" ]; then
    echo "❌ User verification failed!"
    exit 1
fi
echo "✅ User verified: $USERNAME_CHECK"
echo ""

# 4. Inventory Stats
echo "📦 4. Inventory Stats"
echo "GET $API_URL/api/inventory/stats"
STATS=$(curl -s -X GET "$API_URL/api/inventory/stats" \
  -H "Authorization: Bearer $TOKEN")
echo "$STATS" | jq
TOTAL_LOTS=$(echo "$STATS" | jq -r .total_lots)
echo "Total lots in inventory: $TOTAL_LOTS"
echo "✅ Inventory stats retrieved"
echo ""

# 5. List Lots
echo "📋 5. List Inventory Lots (first 5)"
echo "GET $API_URL/api/inventory/lots?limit=5"
LOTS=$(curl -s -X GET "$API_URL/api/inventory/lots?limit=5" \
  -H "Authorization: Bearer $TOKEN")
echo "$LOTS" | jq
echo "✅ Inventory lots listed"
echo ""

# 6. List Users (Admin only)
echo "👥 6. List Users (Admin only)"
echo "GET $API_URL/api/users/"
USERS=$(curl -s -X GET "$API_URL/api/users/" \
  -H "Authorization: Bearer $TOKEN")
echo "$USERS" | jq
echo "✅ Users listed"
echo ""

# 7. Test CSV Upload (if test file exists)
if [ -f "test_inventory.csv" ]; then
    echo "📤 7. Upload Test Inventory CSV"
    echo "POST $API_URL/api/inventory/upload"
    UPLOAD=$(curl -s -X POST "$API_URL/api/inventory/upload" \
      -H "Authorization: Bearer $TOKEN" \
      -F "file=@test_inventory.csv" \
      -F "notes=Test upload from script")
    echo "$UPLOAD" | jq
    echo "✅ CSV uploaded successfully"
    echo ""
else
    echo "⏭️  7. Skipping CSV upload (test_inventory.csv not found)"
    echo ""
fi

# 8. Test Optimization (only if inventory has lots)
if [ "$TOTAL_LOTS" -gt 0 ]; then
    echo "🎯 8. Test Blend Optimization"
    echo "POST $API_URL/api/optimize/blend"

    OPTIMIZE_REQUEST='{
      "target_dc": 80.0,
      "target_fp": 650.0,
      "total_kg": 100.0,
      "num_solutions": 2,
      "exclude_raw_materials": true
    }'

    OPTIMIZE_RESULT=$(curl -s -X POST "$API_URL/api/optimize/blend" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d "$OPTIMIZE_REQUEST")

    echo "$OPTIMIZE_RESULT" | jq

    REQUEST_ID=$(echo "$OPTIMIZE_RESULT" | jq -r .request_id)

    if [ "$REQUEST_ID" != "null" ] && [ -n "$REQUEST_ID" ]; then
        echo "✅ Optimization completed"
        echo "Request ID: $REQUEST_ID"

        # Test Excel download
        echo ""
        echo "📥 9. Download Optimization Excel"
        echo "GET $API_URL/api/optimize/$REQUEST_ID/excel"

        curl -s -X GET "$API_URL/api/optimize/$REQUEST_ID/excel" \
          -H "Authorization: Bearer $TOKEN" \
          -o "test_result_$(date +%Y%m%d_%H%M%S).xlsx"

        if [ -f "test_result_"*.xlsx ]; then
            echo "✅ Excel downloaded successfully"
            ls -lh test_result_*.xlsx | tail -1
        else
            echo "❌ Excel download failed"
        fi
    else
        echo "⚠️  Optimization returned no results (might be expected if inventory is empty)"
        echo "$OPTIMIZE_RESULT" | jq .detail
    fi
else
    echo "⏭️  8-9. Skipping optimization tests (inventory is empty)"
fi

echo ""
echo "========================================="
echo "✅ ALL TESTS COMPLETED SUCCESSFULLY!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Upload your inventory CSV via API or web interface"
echo "2. Request blend optimizations"
echo "3. Download Excel results"
echo ""
echo "API Documentation: $API_URL/docs"
echo "========================================="
