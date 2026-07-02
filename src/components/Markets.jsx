import MarketsHub from './markets/MarketsHub';

/**
 * Markets tab — now available to all users.
 * (Previously developer-gated via isDeveloper; kept MarketsComingSoon in repo for future gating.)
 */
function Markets() {
  return <MarketsHub />;
}

export default Markets;
