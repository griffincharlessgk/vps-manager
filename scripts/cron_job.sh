#!/bin/bash

# VPS Manager Cron Job Script
# Tác giả: VPS Manager System
# Mô tả: Script để thực hiện các tác vụ định kỳ thay thế cho scheduler

# Cấu hình
BASE_URL="http://localhost:5000"
LOG_FILE="/home/ubuntu/vps-manager/logs/cron_job.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Hàm ghi log
log_message() {
    echo "[$TIMESTAMP] $1" >> "$LOG_FILE"
}

# Hàm gọi API endpoint
call_api() {
    local endpoint="$1"
    local description="$2"
    
    log_message "Starting: $description"
    
    response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" -eq 200 ]; then
        log_message "Success: $description - $body"
        return 0
    else
        log_message "Error: $description - HTTP $http_code - $body"
        return 1
    fi
}

# Hàm kiểm tra server có chạy không
check_server() {
    if ! curl -s "$BASE_URL/me" > /dev/null 2>&1; then
        log_message "ERROR: VPS Manager server is not running at $BASE_URL"
        exit 1
    fi
}

# Main execution
log_message "=== VPS Manager Cron Job Started ==="

# Kiểm tra server
check_server

# Lấy tham số từ command line
case "${1:-all}" in
    "zingproxy-sync")
        log_message "Running ZingProxy sync only"
        call_api "/api/sync-zingproxy-proxies" "ZingProxy Proxy Sync"
        ;;
    
    "zingproxy-update")
        log_message "Running ZingProxy account update only"
        call_api "/api/update-zingproxy-accounts" "ZingProxy Account Update"
        ;;
    
    "bitlaunch-apis")
        log_message "Running BitLaunch API update only"
        call_api "/api/update-bitlaunch-apis" "BitLaunch API Update"
        ;;
    
    "bitlaunch-vps")
        log_message "Running BitLaunch VPS update only"
        call_api "/api/update-bitlaunch-vps" "BitLaunch VPS Update"
        ;;
    
    "cloudfly-apis")
        log_message "Running CloudFly API update only"
        call_api "/api/update-cloudfly-apis" "CloudFly API Update"
        ;;
    
    "cloudfly-vps")
        log_message "Running CloudFly VPS update only"
        call_api "/api/update-cloudfly-vps" "CloudFly VPS Update"
        ;;
    
    "notifications")
        log_message "Running notifications only"
        call_api "/api/send-expiry-notifications" "Expiry Notifications"
        call_api "/api/send-account-details" "Account Details"
        ;;
    
    "daily")
        log_message "Running daily tasks"
        call_api "/api/sync-zingproxy-proxies" "ZingProxy Proxy Sync"
        call_api "/api/update-bitlaunch-apis" "BitLaunch API Update"
        call_api "/api/update-bitlaunch-vps" "BitLaunch VPS Update"
        call_api "/api/update-zingproxy-accounts" "ZingProxy Account Update"
        call_api "/api/update-cloudfly-apis" "CloudFly API Update"
        call_api "/api/update-cloudfly-vps" "CloudFly VPS Update"
        call_api "/api/send-expiry-notifications" "Expiry Notifications"
        call_api "/api/send-account-details" "Account Details"
        ;;
    
    "weekly")
        log_message "Running weekly tasks"
        call_api "/api/send-weekly-report" "Weekly Report"
        ;;
    
    "all")
        log_message "Running all tasks"
        call_api "/api/sync-zingproxy-proxies" "ZingProxy Proxy Sync"
        call_api "/api/update-bitlaunch-apis" "BitLaunch API Update"
        call_api "/api/update-bitlaunch-vps" "BitLaunch VPS Update"
        call_api "/api/update-zingproxy-accounts" "ZingProxy Account Update"
        call_api "/api/update-cloudfly-apis" "CloudFly API Update"
        call_api "/api/update-cloudfly-vps" "CloudFly VPS Update"
        call_api "/api/send-expiry-notifications" "Expiry Notifications"
        call_api "/api/send-account-details" "Account Details"
        ;;
    
    *)
        echo "Usage: $0 [task]"
        echo ""
        echo "Available tasks:"
        echo "  zingproxy-sync    - Sync ZingProxy proxies only"
        echo "  zingproxy-update  - Update ZingProxy accounts only"
        echo "  bitlaunch-apis    - Update BitLaunch APIs only"
        echo "  bitlaunch-vps     - Update BitLaunch VPS only"
        echo "  cloudfly-apis     - Update CloudFly APIs only"
        echo "  cloudfly-vps      - Update CloudFly VPS only"
        echo "  notifications     - Send notifications only"
        echo "  daily            - Run daily tasks"
        echo "  weekly           - Run weekly tasks"
        echo "  all              - Run all tasks (default)"
        echo ""
        echo "Examples:"
        echo "  $0 daily          # Run daily tasks"
        echo "  $0 notifications  # Send notifications only"
        echo "  $0 zingproxy-sync # Sync ZingProxy only"
        exit 1
        ;;
esac

log_message "=== VPS Manager Cron Job Completed ==="
