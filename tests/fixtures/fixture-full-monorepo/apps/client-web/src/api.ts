// Import from a declared dependency (should be deduplicated in inference)
import { RuntimeApiClient } from '../../runtime-api-a/src/client';

export function fetchData() {
  const client = new RuntimeApiClient();
  return client.getData();
}
