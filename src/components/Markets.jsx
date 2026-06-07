import { useAuth } from '../contexts/AuthContext';
import MarketsHub from './markets/MarketsHub';
import MarketsComingSoon from './markets/MarketsComingSoon';

/**
 * Markets tab — developer preview only; everyone else sees coming soon.
 * Developer access: DEVELOPER_EMAILS on backend → is_developer from subscription-status API.
 */
function Markets() {
  const { isDeveloper, hasCheckedDeveloperStatus } = useAuth();

  // Default to coming soon until we confirm developer (avoids flashing WIP UI to regular users).
  if (!hasCheckedDeveloperStatus || !isDeveloper) {
    return <MarketsComingSoon />;
  }

  return <MarketsHub />;
}

export default Markets;
