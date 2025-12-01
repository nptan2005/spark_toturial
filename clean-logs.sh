#!/bin/bash

# ==========================
# CONFIG
# ==========================
LOG_ROOT="../logs"
DAYS_TO_KEEP=7  # giữ 7 ngày
SIZE_LIMIT_MB=2000  # ngưỡng tổng 2GB → tự clean

# ==========================
# FUNCTION: CLEAN OLD LOGS
# ==========================
echo "🔍 Cleaning logs older than $DAYS_TO_KEEP days in $LOG_ROOT"

find $LOG_ROOT -type f -name "*.log" -mtime +$DAYS_TO_KEEP -print -delete

echo "✅ Old logs cleaned."

# ==========================
# FUNCTION: CHECK SIZE
# ==========================
TOTAL_MB=$(du -sm $LOG_ROOT | awk '{print $1}')

echo "📦 Total log size: ${TOTAL_MB}MB"

if [ $TOTAL_MB -gt $SIZE_LIMIT_MB ]; then
    echo "⚠️ Total log size > ${SIZE_LIMIT_MB}MB. Auto-cleaning largest 20 files..."
    
    # Xoá file lớn nhất trước
    find $LOG_ROOT -type f -name "*.log" -printf "%s %p\n" | \
        sort -nr | head -n 20 | awk '{print $2}' | xargs rm -f
    
    echo "🧹 Large log files cleaned."
fi

echo "🎉 Done."