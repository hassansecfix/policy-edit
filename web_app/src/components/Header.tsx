import { FileText } from 'lucide-react'

export function Header() {
  return (
    <header className="bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg p-6 mb-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold flex items-center justify-center gap-3">
          <FileText className="h-8 w-8" />
          Policy Automation Dashboard
        </h1>
        <p className="text-blue-100 mt-2 text-lg">
          Automated policy customization powered by Claude AI
        </p>
      </div>
    </header>
  )
}
