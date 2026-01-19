#!/usr/bin/env node

/**
 * 自动修复脚本 - 空值安全
 *
 * 使用方法:
 * node scripts/fix-null-safety.js
 *
 * 这个脚本会自动扫描并修复常见的空值安全问题
 */

const fs = require('fs');
const path = require('path');

// 要扫描的目录
const directories = [
  path.join(__dirname, '../components'),
  path.join(__dirname, '../services'),
];

// 常见的空值不安全模式
const patterns = [
  // .toFixed() 调用
  {
    pattern: /(\w+)\.toFixed\((\d+)\)/g,
    replacement: 'safeToFixed($1, $2)',
    import: "import { safeToFixed } from '../utils/format';",
    message: '.toFixed() 调用',
  },
  // .toLocaleString() 调用
  {
    pattern: /(\w+)\.toLocaleString\(\)/g,
    replacement: '($1 || 0).toLocaleString()',
    message: '.toLocaleString() 调用',
  },
  // 直接访问 undefined/null 属性
  {
    pattern: /(\w+)\.map\(/g,
    check: (match) => {
      // 检查是否有数组检查
      return !match.includes('?.') && !match.includes('length > 0');
    },
    replacement: '($1 || []).map(',
    message: '数组 map 前未检查',
  },
  // 数组索引访问
  {
    pattern: /(\w+)\[0\]/g,
    replacement: '($1 || [])[0]',
    message: '数组索引访问未检查',
  },
];

// 文件统计
let totalFiles = 0;
let modifiedFiles = 0;
let totalFixes = 0;

/**
 * 扫描并修复文件
 */
function scanAndFixFile(filePath) {
  try {
    let content = fs.readFileSync(filePath, 'utf-8');
    let modified = false;
    let fileFixes = 0;

    // 检查是否有安全导入
    const hasSafeImport = content.includes('safeToFixed') ||
                         content.includes('safeCurrency') ||
                         content.includes('safePercent');

    patterns.forEach(({ pattern, replacement, import, message }) => {
      const matches = content.match(pattern);
      if (matches) {
        const before = content;

        // 应用替换
        content = content.replace(pattern, replacement);

        // 如果需要添加导入
        if (import && !hasSafeImport) {
          // 在最后一个 import 后添加
          const importMatch = content.match(/^import .+;$/gm);
          if (importMatch) {
            const lastImport = importMatch[importMatch.length - 1];
            const importIndex = content.lastIndexOf(lastImport);
            content = content.slice(0, importIndex + lastImport.length) +
                      '\n' + import +
                      content.slice(importIndex + lastImport.length);
          }
        }

        if (content !== before) {
          modified = true;
          fileFixes += matches.length;
          console.log(`  ✓ 修复 ${message} (${matches.length} 处)`);
        }
      }
    });

    if (modified) {
      // 备份原文件
      fs.writeFileSync(filePath + '.bak', content, 'utf-8');

      // 写入修复后的文件
      fs.writeFileSync(filePath, content, 'utf-8');

      modifiedFiles++;
      totalFixes += fileFixes;

      console.log(`\n✅ 已修复: ${path.relative(process.cwd(), filePath)} (${fileFixes} 处修复)`);
    }

    totalFiles++;
  } catch (error) {
    console.error(`❌ 错误处理文件 ${filePath}:`, error.message);
  }
}

/**
 * 递归扫描目录
 */
function scanDirectory(dir) {
  const files = fs.readdirSync(dir);

  files.forEach((file) => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);

    if (stat.isDirectory()) {
      // 跳过 node_modules 和 .git
      if (file !== 'node_modules' && file !== '.git' && file !== 'dist') {
        scanDirectory(filePath);
      }
    } else if (file.match(/\.(tsx?|jsx?)$/)) {
      // 只处理 TypeScript/JavaScript 文件
      scanAndFixFile(filePath);
    }
  });
}

/**
 * 主函数
 */
function main() {
  console.log('🔍 开始扫描文件...\n');

  directories.forEach((dir) => {
    if (fs.existsSync(dir)) {
      console.log(`\n📂 扫描目录: ${path.relative(process.cwd(), dir)}`);
      scanDirectory(dir);
    } else {
      console.warn(`⚠️  目录不存在: ${dir}`);
    }
  });

  console.log('\n' + '='.repeat(50));
  console.log('📊 扫描完成!');
  console.log(`   总文件数: ${totalFiles}`);
  console.log(`   修改文件: ${modifiedFiles}`);
  console.log(`   总修复数: ${totalFixes}`);
  console.log('='.repeat(50));

  if (modifiedFiles > 0) {
    console.log('\n💡 提示:');
    console.log('   - 原文件已备份为 .bak 文件');
    console.log('   - 请仔细检查修改后的文件');
    console.log('   - 运行测试确保功能正常');
    console.log('   - 如果有问题，可以从 .bak 文件恢复');
  }
}

// 运行脚本
if (require.main === module) {
  main();
}

module.exports = { scanAndFixFile, scanDirectory };
