/**
 * 自定义 React Hooks
 * 提供通用功能和最佳实践
 */

import { useState, useEffect, useCallback, useRef, useMemo } from 'react';

// ==================== 异步操作 Hook ====================

/**
 * 异步操作 Hook
 * @param asyncFunction - 异步函数
 * @returns { data, loading, error, execute, reset }
 *
 * @example
 * const { data, loading, error, execute } = useAsync(fetchData);
 */
export function useAsync<T, P extends any[] = []>(
  asyncFunction: (...args: P) => Promise<T>
) {
  const [state, setState] = useState<{
    data: T | null;
    loading: boolean;
    error: string | null;
  }>({
    data: null,
    loading: false,
    error: null,
  });

  const execute = useCallback(
    async (...args: P): Promise<T | null> => {
      setState(prev => ({ ...prev, loading: true, error: null }));

      try {
        const result = await asyncFunction(...args);
        setState({ data: result, loading: false, error: null });
        return result;
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'An error occurred';
        setState(prev => ({ ...prev, loading: false, error: errorMessage }));
        return null;
      }
    },
    [asyncFunction]
  );

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return {
    ...state,
    execute,
    reset,
  };
}

// ==================== 定时刷新 Hook ====================

/**
 * 定时刷新 Hook
 * @param callback - 回调函数
 * @param interval - 刷新间隔（毫秒）
 * @param immediate - 是否立即执行
 *
 * @example
 * useRefresh(() => fetchData(), 5000);
 */
export function useRefresh(
  callback: () => void | Promise<void>,
  interval: number | null,
  immediate: boolean = true
) {
  const savedCallback = useRef(callback);

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    if (interval === null) return;

    const tick = async () => {
      await savedCallback.current();
    };

    if (immediate) {
      tick();
    }

    const id = setInterval(tick, interval);
    return () => clearInterval(id);
  }, [interval, immediate]);
}

// ==================== 防抖 Hook ====================

/**
 * 防抖 Hook
 * @param value - 需要防抖的值
 * @param delay - 延迟时间（毫秒）
 *
 * @example
 * const debouncedSearchTerm = useDebounce(searchTerm, 500);
 */
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

// ==================== 节流 Hook ====================

/**
 * 节流 Hook
 * @param value - 需要节流的值
 * @param interval - 节流间隔（毫秒）
 *
 * @example
 * const throttledValue = useThrottle(scrollPosition, 100);
 */
export function useThrottle<T>(value: T, interval: number): T {
  const [throttledValue, setThrottledValue] = useState<T>(value);
  const lastExecuted = useRef<number>(Date.now());

  useEffect(() => {
    const handler = setTimeout(() => {
      const now = Date.now();
      const timeSinceLastExecution = now - lastExecuted.current;

      if (timeSinceLastExecution >= interval) {
        setThrottledValue(value);
        lastExecuted.current = now;
      }
    }, interval - (Date.now() - lastExecuted.current));

    return () => {
      clearTimeout(handler);
    };
  }, [value, interval]);

  return throttledValue;
}

// ==================== 本地存储 Hook ====================

/**
 * 本地存储 Hook
 * @param key - 存储键名
 * @param initialValue - 初始值
 *
 * @example
 * const [user, setUser] = useLocalStorage('user', { name: 'Guest' });
 */
export function useLocalStorage<T>(
  key: string,
  initialValue: T
): [T, (value: T | ((prev: T) => T)) => void, () => void] {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  const setValue = useCallback(
    (value: T | ((prev: T) => T)) => {
      try {
        const valueToStore = value instanceof Function ? value(storedValue) : value;
        setStoredValue(valueToStore);
        window.localStorage.setItem(key, JSON.stringify(valueToStore));
      } catch (error) {
        console.warn(`Error setting localStorage key "${key}":`, error);
      }
    },
    [key, storedValue]
  );

  const removeValue = useCallback(() => {
    try {
      window.localStorage.removeItem(key);
      setStoredValue(initialValue);
    } catch (error) {
      console.warn(`Error removing localStorage key "${key}":`, error);
    }
  }, [key, initialValue]);

  return [storedValue, setValue, removeValue];
}

// ==================== 会话存储 Hook ====================

/**
 * 会话存储 Hook
 * @param key - 存储键名
 * @param initialValue - 初始值
 *
 * @example
 * const [token, setToken] = useSessionStorage('token', '');
 */
export function useSessionStorage<T>(
  key: string,
  initialValue: T
): [T, (value: T | ((prev: T) => T)) => void] {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.sessionStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.warn(`Error reading sessionStorage key "${key}":`, error);
      return initialValue;
    }
  });

  const setValue = useCallback(
    (value: T | ((prev: T) => T)) => {
      try {
        const valueToStore = value instanceof Function ? value(storedValue) : value;
        setStoredValue(valueToStore);
        window.sessionStorage.setItem(key, JSON.stringify(valueToStore));
      } catch (error) {
        console.warn(`Error setting sessionStorage key "${key}":`, error);
      }
    },
    [key, storedValue]
  );

  return [storedValue, setValue];
}

// ==================== 窗口大小 Hook ====================

/**
 * 窗口大小 Hook
 *
 * @example
 * const { width, height } = useWindowSize();
 */
export function useWindowSize() {
  const [windowSize, setWindowSize] = useState<{
    width: number | undefined;
    height: number | undefined;
  }>({
    width: undefined,
    height: undefined,
  });

  useEffect(() => {
    function handleResize() {
      setWindowSize({
        width: window.innerWidth,
        height: window.innerHeight,
      });
    }

    handleResize();
    window.addEventListener('resize', handleResize);

    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return windowSize;
}

// ==================== 在线状态 Hook ====================

/**
 * 在线状态 Hook
 *
 * @example
 * const isOnline = useOnline();
 */
export function useOnline(): boolean {
  const [isOnline, setIsOnline] = useState<boolean>(
    typeof navigator !== 'undefined' ? navigator.onLine : true
  );

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return isOnline;
}

// ==================== 点击外部 Hook ====================

/**
 * 点击外部 Hook
 * @param handler - 点击外部的回调函数
 *
 * @example
 * const ref = useClickOutside(() => setOpen(false));
 */
export function useClickOutside<T extends HTMLElement = any>(
  handler: () => void
): React.RefObject<T> {
  const ref = useRef<T>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        handler();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [handler]);

  return ref;
}

// ==================== 上次值 Hook ====================

/**
 * 上次值 Hook
 * @param value - 当前值
 *
 * @example
 * const prevCount = usePrevious(count);
 */
export function usePrevious<T>(value: T): T | undefined {
  const ref = useRef<T>();

  useEffect(() => {
    ref.current = value;
  }, [value]);

  return ref.current;
}

// ==================== 挂载状态 Hook ====================

/**
 * 挂载状态 Hook
 * 用于判断组件是否已挂载
 *
 * @example
 * const isMounted = useIsMounted();
 * useEffect(() => {
 *   if (isMounted()) {
 *     // 仅在组件挂载后执行
 *   }
 * });
 */
export function useIsMounted(): () => boolean {
  const isMounted = useRef(false);

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  return useCallback(() => isMounted.current, []);
}

// ==================== 复制到剪贴板 Hook ====================

/**
 * 复制到剪贴板 Hook
 *
 * @example
 * const { copy, copied } = useClipboard();
 * <button onClick={() => copy('Hello')}>Copy</button>
 */
export function useClipboard(text?: string) {
  const [copied, setCopied] = useState(false);

  const copy = useCallback(
    async (textToCopy?: string) => {
      const text = textToCopy;
      if (!text) return;

      try {
        await navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      } catch (error) {
        console.warn('Failed to copy text:', error);
        setCopied(false);
      }
    },
    [text]
  );

  return { copy, copied };
}

// ==================== 页面可见性 Hook ====================

/**
 * 页面可见性 Hook
 *
 * @example
 * const isVisible = usePageVisibility();
 */
export function usePageVisibility(): boolean {
  const [isVisible, setIsVisible] = useState<boolean>(
    typeof document !== 'undefined' ? !document.hidden : true
  );

  useEffect(() => {
    const handleVisibilityChange = () => {
      setIsVisible(!document.hidden);
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  return isVisible;
}

// ==================== 媒体查询 Hook ====================

/**
 * 媒体查询 Hook
 * @param query - 媒体查询字符串
 *
 * @example
 * const isMobile = useMediaQuery('(max-width: 768px)');
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      return window.matchMedia(query).matches;
    }
    return false;
  });

  useEffect(() => {
    const mediaQuery = window.matchMedia(query);
    const handler = (event: MediaQueryListEvent) => {
      setMatches(event.matches);
    };

    // 现代浏览器
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handler);
      return () => mediaQuery.removeEventListener('change', handler);
    }
    // 旧浏览器
    else {
      mediaQuery.addListener(handler);
      return () => mediaQuery.removeListener(handler);
    }
  }, [query]);

  return matches;
}
