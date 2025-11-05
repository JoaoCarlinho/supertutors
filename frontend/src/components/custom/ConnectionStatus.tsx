import { useValues, useActions } from 'kea';
import { conversationLogic, type ConnectionStatus as ConnectionStatusType } from '../../logic/conversationLogic';
import { Button } from '../ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '../ui/tooltip';

/**
 * ConnectionStatus Component
 *
 * Displays WebSocket connection status with visual indicator:
 * - Green dot: Connected
 * - Yellow dot: Connecting
 * - Red dot: Disconnected
 *
 * Includes tooltip with connection details and manual reconnect button
 */
export function ConnectionStatus() {
  const { connectionStatus, connectionError } = useValues(conversationLogic);
  const { reconnect } = useActions(conversationLogic);

  const statusConfig: Record<ConnectionStatusType, { color: string; label: string; ariaLabel: string }> = {
    connected: {
      color: 'bg-green-500',
      label: 'Connected',
      ariaLabel: 'Connection status: Connected',
    },
    connecting: {
      color: 'bg-yellow-500 animate-pulse',
      label: 'Connecting...',
      ariaLabel: 'Connection status: Connecting',
    },
    disconnected: {
      color: 'bg-red-500',
      label: 'Disconnected',
      ariaLabel: 'Connection status: Disconnected',
    },
  };

  const config = statusConfig[connectionStatus as ConnectionStatusType];

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div
            className="fixed top-4 right-4 z-50 flex items-center gap-2 px-3 py-2 bg-white dark:bg-gray-800 rounded-lg shadow-md border border-gray-200 dark:border-gray-700"
            role="status"
            aria-label={config.ariaLabel}
          >
            <div className={`w-3 h-3 rounded-full ${config.color}`} />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {config.label}
            </span>
          </div>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="max-w-xs">
          <div className="space-y-2">
            <p className="font-semibold">Connection Status</p>
            <p className="text-sm">
              Status: <span className="font-medium">{config.label}</span>
            </p>
            {connectionError && (
              <p className="text-sm text-red-500">
                Error: {connectionError}
              </p>
            )}
            {connectionStatus === 'disconnected' && (
              <Button
                onClick={reconnect}
                variant="outline"
                size="sm"
                className="w-full mt-2"
              >
                Reconnect
              </Button>
            )}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
