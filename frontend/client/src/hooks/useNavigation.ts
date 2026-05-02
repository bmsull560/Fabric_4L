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

interface NavigateToFunction {
  (state: RouteState, params?: NavigationParams, options?: NavigationOptions): void;
  (path: string, options?: NavigationOptions): void;
}

export function useNavigation() {
  const navigate = useNavigate();
  const location = useLocation();

  const navigateTo: NavigateToFunction = (
    stateOrPath: RouteState | string,
    paramsOrOptions?: NavigationParams | NavigationOptions,
    options?: NavigationOptions
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
      const path = getStatePath(state, params);
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
    navigateTo('intelligence', { accountId, tab });

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
