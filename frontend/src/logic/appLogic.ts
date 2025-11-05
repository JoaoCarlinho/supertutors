import { kea } from 'kea';

// Basic appLogic store - will be expanded in future stories
// Type generation with kea-typegen will be configured when more complex logic is added
export const appLogic = kea({
  actions: () => ({
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    setAppReady: (ready: any) => ({ ready }),
  }),
  reducers: () => ({
    appReady: [
      false,
      {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        setAppReady: (_state: any, { ready }: any) => ready,
      },
    ],
  }),
});
