'use client';

import Link from 'next/link';
import { cn, getSeverityColor, getStatusColor, timeAgo } from '@/lib/utils';
import type { Incident } from '@/types';

interface IncidentListProps {
  incidents: Incident[];
  showRegion?: boolean;
}

export default function IncidentList({ incidents, showRegion = true }: IncidentListProps) {
  if (incidents.length === 0) {
    return (
      <div className="rounded-lg bg-white p-6 text-center text-gray-500">
        No incidents found
      </div>
    );
  }

  return (
    <div className="rounded-lg bg-white shadow overflow-hidden">
      <ul className="divide-y divide-gray-200">
        {incidents.map((incident) => (
          <li key={incident.id}>
            <Link
              href={`/incidents/${incident.id}`}
              className="block hover:bg-gray-50 transition-colors"
            >
              <div className="px-4 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span
                      className={cn(
                        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
                        getSeverityColor(incident.severity)
                      )}
                    >
                      {incident.severity.toUpperCase()}
                    </span>
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {incident.title}
                    </p>
                  </div>
                  <span
                    className={cn(
                      'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
                      getStatusColor(incident.status)
                    )}
                  >
                    {incident.status.replace('_', ' ')}
                  </span>
                </div>
                <div className="mt-2 flex items-center justify-between text-sm text-gray-500">
                  <div className="flex items-center gap-4">
                    <span>{incident.service}</span>
                    {showRegion && (
                      <span className="capitalize">{incident.region}</span>
                    )}
                  </div>
                  <span>{timeAgo(incident.created_at)}</span>
                </div>
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
