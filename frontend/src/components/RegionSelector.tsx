'use client';

import { Fragment } from 'react';
import { Listbox, Transition } from '@headlessui/react';
import { CheckIcon, ChevronUpDownIcon, GlobeAltIcon } from '@heroicons/react/24/outline';
import { cn } from '@/lib/utils';

const regions = [
  { id: null, name: 'All Regions', flag: '🌍' },
  { id: 'india', name: 'India', flag: '🇮🇳' },
  { id: 'china', name: 'China', flag: '🇨🇳' },
  { id: 'usa', name: 'USA', flag: '🇺🇸' },
];

interface RegionSelectorProps {
  value: string | null;
  onChange: (value: string | null) => void;
}

export default function RegionSelector({ value, onChange }: RegionSelectorProps) {
  const selected = regions.find((r) => r.id === value) || regions[0];

  return (
    <Listbox value={value} onChange={onChange}>
      <div className="relative">
        <Listbox.Button className="relative w-full cursor-pointer rounded-lg bg-white py-2 pl-3 pr-10 text-left shadow-sm border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 sm:text-sm">
          <span className="flex items-center gap-2">
            <span>{selected.flag}</span>
            <span className="block truncate">{selected.name}</span>
          </span>
          <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
            <ChevronUpDownIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
          </span>
        </Listbox.Button>
        <Transition
          as={Fragment}
          leave="transition ease-in duration-100"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <Listbox.Options className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm">
            {regions.map((region) => (
              <Listbox.Option
                key={region.id ?? 'all'}
                value={region.id}
                className={({ active }) =>
                  cn(
                    'relative cursor-pointer select-none py-2 pl-10 pr-4',
                    active ? 'bg-primary-100 text-primary-900' : 'text-gray-900'
                  )
                }
              >
                {({ selected }) => (
                  <>
                    <span className="flex items-center gap-2">
                      <span>{region.flag}</span>
                      <span className={cn('block truncate', selected && 'font-medium')}>
                        {region.name}
                      </span>
                    </span>
                    {selected && (
                      <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-primary-600">
                        <CheckIcon className="h-5 w-5" aria-hidden="true" />
                      </span>
                    )}
                  </>
                )}
              </Listbox.Option>
            ))}
          </Listbox.Options>
        </Transition>
      </div>
    </Listbox>
  );
}
