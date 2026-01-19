/**
 * 检查所有组件文件的导入完整性
 * 确保所有使用的工具函数都已正确导入
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const componentsDir = path.join(__dirname, '../components');
const utilsDir = path.join(__dirname, '../utils');

// 从 utils/format.ts 提取所有导出的函数
function getExportedFunctions(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const exports = [];
  const exportRegex = /^export\s+(?:function|const)\s+(\w+)/gm;
  let match;
  while ((match = exportRegex.exec(content)) !== null) {
    exports.push(match[1]);
  }
  return exports;
}

// 检查组件文件中使用的函数
function checkComponentImports(componentPath) {
  const content = fs.readFileSync(componentPath, 'utf-8');
  const filename = path.basename(componentPath);
  const issues = [];

  // 获取所有可用的工具函数
  const formatFunctions = getExportedFunctions(path.join(utilsDir, 'format.ts'));
  
  // 检查是否使用了工具函数但未导入
  formatFunctions.forEach(funcName => {
    // 检查是否在代码中使用了该函数
    const usageRegex = new RegExp(`\\b${funcName}\\s*\\(`, 'g');
    const isUsed = usageRegex.test(content);
    
    if (isUsed) {
      // 检查是否已导入
      const importRegex = new RegExp(`import.*\\b${funcName}\\b.*from.*['"]\\.\\./utils/format['"]`, 'g');
      const isImported = importRegex.test(content);
      
      // 检查是否有本地定义（应该使用导入的版本）
      const localDefRegex = new RegExp(`(?:const|function)\\s+${funcName}\\s*=`, 'g');
      const hasLocalDef = localDefRegex.test(content);
      
      if (!isImported && !hasLocalDef) {
        issues.push({
          type: 'missing_import',
          function: funcName,
          message: `Function ${funcName} is used but not imported from utils/format`
        });
      } else if (hasLocalDef) {
        issues.push({
          type: 'local_definition',
          function: funcName,
          message: `Function ${funcName} is defined locally but should use imported version from utils/format`
        });
      }
    }
  });

  return issues;
}

// 主函数
function main() {
  const componentFiles = fs.readdirSync(componentsDir)
    .filter(file => file.endsWith('.tsx') || file.endsWith('.ts'))
    .map(file => path.join(componentsDir, file));

  console.log('Checking component imports...\n');
  
  let totalIssues = 0;
  componentFiles.forEach(file => {
    const issues = checkComponentImports(file);
    if (issues.length > 0) {
      console.log(`\n${path.basename(file)}:`);
      issues.forEach(issue => {
        console.log(`  [${issue.type}] ${issue.message}`);
        totalIssues++;
      });
    }
  });

  if (totalIssues === 0) {
    console.log('✓ All imports are correct!');
    process.exit(0);
  } else {
    console.log(`\n✗ Found ${totalIssues} issue(s)`);
    process.exit(1);
  }
}

main();
