#!/bin/bash
# 快速代码扫描脚本 - Code Review Quick Scan
# 用途: 快速发现常见代码问题

echo "=========================================="
echo "🔍 代码审查快速扫描 - Quick Scan"
echo "=========================================="
echo ""

PROJECT_ROOT=$(pwd)
RESULTS_FILE="$PROJECT_ROOT/scan-results.txt"
echo "扫描结果将保存到: $RESULTS_FILE"
echo "" > "$RESULTS_FILE"

# 颜色定义
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

scan_count=0
issue_count=0

# 扫描函数
scan() {
    local pattern=$1
    local description=$2
    local severity=$3
    local include_pattern=$4
    
    scan_count=$((scan_count + 1))
    echo "[$scan_count] 扫描: $description"
    
    results=$(grep -r "$pattern" "$PROJECT_ROOT" --include="$include_pattern" 2>/dev/null | grep -v "node_modules\|dist\|.git\|scan-results")
    local count=$(echo "$results" | grep -c "^" || echo "0")
    
    if [ "$count" -gt 0 ]; then
        echo "   ${RED}发现 $count 处${NC}"
        echo "$results" >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
        issue_count=$((issue_count + count))
    else
        echo "   ${GREEN}✓ 未发现${NC}"
    fi
    echo ""
}

# ==================== 硬编码路径扫描 ====================
echo "🔴 扫描硬编码路径..."
scan "c:\\Users\|/home/" "Windows/Linux 绝对路径" "P0" "*.py"
scan "localhost" "localhost 硬编码" "P1" "*.py"
scan "127\.0\.0\.1" "127.0.0.1 硬编码" "P0" "*.py"

# ==================== 调试代码扫描 ====================
echo "🔴 扫描调试代码遗留..."
scan "console\.log\|console\.debug" "console.log/debug" "P1" "*.tsx"
scan "print(" "print() 调试" "P1" "*.py"
scan "#region agent log" "Agent 调试日志" "P0" "*.py"

# ==================== 类型安全扫描 ====================
echo "🟡 扫描类型安全问题..."
scan "as any" "TypeScript as any" "P1" "*.tsx"
scan ": any" "TypeScript any 类型" "P2" "*.tsx"

# ==================== 错误处理扫描 ====================
echo "🟡 扫描错误处理..."
scan "except: pass\|except.*:" "空 except 块" "P1" "*.py"
scan "catch.*{}" "空 catch 块" "P1" "*.tsx"
scan "\.catch(()=>{})" "空 catch 回调" "P1" "*.tsx"

# ==================== 代码质量扫描 ====================
echo "🟢 扫描代码质量问题..."
scan "parseInt([^,]*)" "parseInt 缺少基数" "P2" "*.tsx"
scan "parseFloat([^,]*)" "parseFloat 缺少基数" "P2" "*.tsx"
scan "\.join\(" "数组 join 缺少空值检查" "P2" "*.tsx"

# ==================== 汇总报告 ====================
echo "=========================================="
echo "📊 扫描汇总"
echo "=========================================="
echo "扫描项目数: $scan_count"
echo "发现问题数: ${RED}$issue_count${NC}"
echo ""

if [ "$issue_count" -gt 0 ]; then
    echo "详细结果已保存到: $RESULTS_FILE"
    echo ""
    echo "前10个问题预览:"
    echo "----------------------------------------"
    head -20 "$RESULTS_FILE"
    echo ""
    echo "建议: 运行 'detailed-scan.sh' 查看完整分析"
else
    echo "${GREEN}✓ 未发现明显问题！${GREEN}"
fi

echo ""
echo "完成时间: $(date '+%Y-%m-%d %H:%M:%S')"
