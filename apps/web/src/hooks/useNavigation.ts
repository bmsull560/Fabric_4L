/**
 * useNavigation — Wrapper hook for centralized navigation service
 * Replaces direct useNavigate() with state-based navigation per CONTRACT.md §2.6
 */
import { useNavigate, useLocation, type NavigateOptions, type To } from 'react-router-dom';
import { getStatePath, type RouteState, type NavigationParams } from '@/navigation/navigationService';

interface NavigationOptions extends Omit<NavigateOptions, 'state'> {
  replace?: boolean;
  state?: Record<string, unknown>;
}

interface StateNavigationOptions extends NavigationOptions {
  query?: Record<string, string | number | undefined>;
}

interface NavigateToFunction {
  (state: RouteState, params?: NavigationParams, options?: StateNavigationOptions): void;
  (path: string, options?: NavigationOptions): void;
}

export function useNavigation() {
  const navigate = useNavigate();
  const location = useLocation();

  const buildQueryString = (query?: Record<string, string | number | undefined>): string => {
    if (!query) return '';
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined) {
        params.append(key, String(value));
      }
    }
    const queryString = params.toString();
    return queryString ? `?${queryString}` : '';
  };

  const navigateTo: NavigateToFunction = (
    stateOrPath: RouteState | string,
    paramsOrOptions?: NavigationParams | NavigationOptions,
    options?: StateNavigationOptions
  ) => {
    if (typeof stateOrPath === 'string' && stateOrPath.startsWith('/')) {
      // Direct path navigation (backward compat)
      const opts = paramsOrOptions as NavigationOptions | undefined;
      navigate(stateOrPath, opts);
    } else {
      // State-based navigation
      const state = stateOrPath as RouteState;
      const params = paramsOrOptions as NavigationParams | undefined;
      const opts = options;
      let path = getStatePath(state, params);
      if (opts?.query) {
        path += buildQueryString(opts.query);
      }
      navigate(path, opts);
    }
  };

  const goBack = () => navigate(-1);
  const goForward = () => navigate(1);

  const navigateToLogin = (redirect?: string) => {
    if (redirect) {
      navigate(`/login?redirect=${encodeURIComponent(redirect)}`);
    } else {
      navigateTo('login');
    }
  };

  const navigateToHome = () => navigateTo('home');

  const navigateToAccount = (accountId: string) =>
    navigateTo('account-detail', { accountId });

  const navigateToIntelligence = (accountId: string, tab?: string) =>
    navigateTo('intelligence-signals', { accountId, tab });

  return {
    navigate,
    navigateTo,
    goBack,
    goForward,
    navigateToLogin,
    navigateToHome,
    navigateToAccount,
    navigateToIntelligence,
    location,
  };
}
