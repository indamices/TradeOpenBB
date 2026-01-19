/**
 * 安全工具函数库
 * 防止空值、数组越界、类型错误等运行时错误
 */

/**
 * 安全的对象属性访问
 * @example safeAccess(obj, 'a.b.c', 'default')
 */
export function safeAccess<T>(
  obj: any,
  path: string,
  defaultValue: T
): T {
  const keys = path.split('.');
  let result = obj;

  for (const key of keys) {
    if (result == null) {
      return defaultValue;
    }
    result = result[key];
  }

  return result !== undefined && result !== null ? result : defaultValue;
}

/**
 * 安全的数组访问
 * @example safeArrayAccess([1, 2, 3], 5, 0) // returns 0
 */
export function safeArrayAccess<T>(
  arr: T[] | undefined | null,
  index: number,
  defaultValue: T
): T {
  if (!arr || !Array.isArray(arr) || index < 0 || index >= arr.length) {
    return defaultValue;
  }
  return arr[index];
}

/**
 * 安全的数组长度检查
 */
export function safeArrayLength(arr: any[] | undefined | null): number {
  return Array.isArray(arr) ? arr.length : 0;
}

/**
 * 安全的数组操作 - map
 */
export function safeArrayMap<T, U>(
  arr: T[] | undefined | null,
  mapper: (item: T, index: number) => U,
  defaultValue: U[] = []
): U[] {
  if (!Array.isArray(arr)) {
    return defaultValue;
  }
  try {
    return arr.map(mapper);
  } catch (e) {
    console.warn('safeArrayMap error:', e);
    return defaultValue;
  }
}

/**
 * 安全的数组操作 - filter
 */
export function safeArrayFilter<T>(
  arr: T[] | undefined | null,
  predicate: (item: T, index: number) => boolean,
  defaultValue: T[] = []
): T[] {
  if (!Array.isArray(arr)) {
    return defaultValue;
  }
  try {
    return arr.filter(predicate);
  } catch (e) {
    console.warn('safeArrayFilter error:', e);
    return defaultValue;
  }
}

/**
 * 安全的数组操作 - some
 */
export function safeArraySome<T>(
  arr: T[] | undefined | null,
  predicate: (item: T, index: number) => boolean,
  defaultValue: boolean = false
): boolean {
  if (!Array.isArray(arr) || arr.length === 0) {
    return defaultValue;
  }
  try {
    return arr.some(predicate);
  } catch (e) {
    console.warn('safeArraySome error:', e);
    return defaultValue;
  }
}

/**
 * 安全的数值计算
 */
export function safeNumber(
  value: any,
  defaultValue: number = 0
): number {
  if (typeof value === 'number' && !Number.isNaN(value)) {
    return value;
  }
  const parsed = Number(value);
  return !Number.isNaN(parsed) ? parsed : defaultValue;
}

/**
 * 安全的数值运算 - 加法
 */
export function safeAdd(a: any, b: any, defaultValue: number = 0): number {
  const numA = safeNumber(a, 0);
  const numB = safeNumber(b, 0);
  return numA + numB || defaultValue;
}

/**
 * 安全的数值运算 - 乘法
 */
export function safeMultiply(a: any, b: any, defaultValue: number = 0): number {
  const numA = safeNumber(a, 0);
  const numB = safeNumber(b, 0);
  return numA * numB || defaultValue;
}

/**
 * 安全的数值比较
 */
export function safeCompare(
  a: any,
  b: any,
  operator: '>' | '<' | '>=' | '<=' | '===' | '!==',
  defaultValue: boolean = false
): boolean {
  try {
    const numA = safeNumber(a);
    const numB = safeNumber(b);

    switch (operator) {
      case '>': return numA > numB;
      case '<': return numA < numB;
      case '>=': return numA >= numB;
      case '<=': return numA <= numB;
      case '===': return numA === numB;
      case '!==': return numA !== numB;
      default: return defaultValue;
    }
  } catch (e) {
    console.warn('safeCompare error:', e);
    return defaultValue;
  }
}

/**
 * 安全的条件渲染
 */
export function safeRender<T>(
  condition: any,
  component: T,
  defaultValue: T = null as any
): T {
  return condition ? component : defaultValue;
}

/**
 * 安全的字符串操作 - toLowerCase
 */
export function safeLowerCase(str: string | undefined | null): string {
  if (typeof str !== 'string') {
    return '';
  }
  try {
    return str.toLowerCase();
  } catch (e) {
    return '';
  }
}

/**
 * 安全的字符串操作 - includes
 */
export function safeStringIncludes(
  str: string | undefined | null,
  searchStr: string,
  defaultValue: boolean = false
): boolean {
  if (typeof str !== 'string' || typeof searchStr !== 'string') {
    return defaultValue;
  }
  try {
    return str.toLowerCase().includes(searchStr.toLowerCase());
  } catch (e) {
    return defaultValue;
  }
}

/**
 * 安全的字符串分割
 */
export function safeSplit(
  str: string | undefined | null,
  separator: string = ',',
  defaultValue: string[] = []
): string[] {
  if (typeof str !== 'string') {
    return defaultValue;
  }
  try {
    return str.split(separator).map(s => s.trim()).filter(s => s);
  } catch (e) {
    return defaultValue;
  }
}

/**
 * 安全的日期格式化
 */
export function safeFormatDate(
  date: string | Date | undefined | null,
  locale: string = 'en-US',
  options: Intl.DateTimeFormatOptions = {},
  defaultValue: string = ''
): string {
  try {
    if (!date) return defaultValue;
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    if (isNaN(dateObj.getTime())) return defaultValue;
    return dateObj.toLocaleDateString(locale, options);
  } catch (e) {
    console.warn('safeFormatDate error:', e);
    return defaultValue;
  }
}

/**
 * 安全的 Promise.all 包装
 */
export async function safePromiseAll<T>(
  promises: Promise<T>[],
  defaultValue: T[] = []
): Promise<T[]> {
  try {
    return await Promise.all(promises);
  } catch (e) {
    console.warn('safePromiseAll error:', e);
    return defaultValue;
  }
}

/**
 * 防抖函数
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;

  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      timeout = null;
      func(...args);
    };

    if (timeout) {
      clearTimeout(timeout);
    }
    timeout = setTimeout(later, wait);
  };
}

/**
 * 节流函数
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;

  return function executedFunction(...args: Parameters<T>) {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}
