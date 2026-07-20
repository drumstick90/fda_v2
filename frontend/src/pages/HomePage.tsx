import { Link } from 'react-router-dom'
import { Search, Layers, TrendingUp, Pill } from 'lucide-react'

const workflows = [
  {
    title: 'Find a drug label',
    description: 'Search by generic or brand name.',
    href: '/search',
    icon: Search,
    primary: true,
  },
  {
    title: 'Compare a drug list',
    description: 'Run batch searches and export CSV.',
    href: '/batch',
    icon: Layers,
  },
  {
    title: 'Review label history',
    description: 'See versions, formulations, and indication changes.',
    href: '/label-analysis',
    icon: TrendingUp,
  },
  {
    title: 'Search by indication',
    description: 'Find labeled drugs for a condition.',
    href: '/indication-search',
    icon: Pill,
  },
]

export function HomePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold text-gray-900">FDA label search</h1>
        <p className="mt-2 max-w-2xl text-gray-600">
          Choose a workflow. The app fetches live OpenFDA label data and keeps AI summaries optional.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {workflows.map((workflow) => {
          const Icon = workflow.icon

          return (
            <Link
              key={workflow.href}
              to={workflow.href}
              className={`group rounded-lg border bg-white p-5 shadow-sm transition hover:border-primary-300 hover:shadow ${
                workflow.primary ? 'border-primary-200' : 'border-gray-200'
              }`}
            >
              <div className="flex items-start gap-4">
                <div
                  className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-md ${
                    workflow.primary ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="font-semibold text-gray-900 group-hover:text-primary-700">
                    {workflow.title}
                  </h2>
                  <p className="mt-1 text-sm text-gray-600">{workflow.description}</p>
                </div>
              </div>
            </Link>
          )
        })}
      </div>
    </div>
  )
}
