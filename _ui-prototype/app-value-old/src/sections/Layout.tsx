import { Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  LayoutDashboard, GitFork, FlaskConical, Database, Calculator, FileText,
  Plus, Search, Bell, UserCircle, ChevronRight, CheckCircle2, Circle
} from "lucide-react";

const steps = [
  { path: "/", label: "Discovery" },
  { path: "/hypotheses", label: "Hypotheses" },
  { path: "/driver-tree", label: "Driver Tree" },
  { path: "/evidence", label: "Evidence" },
  { path: "/calculator", label: "Calculator" },
  { path: "/value-case", label: "Value Case" },
];

const sidebarItems = [
  { icon: LayoutDashboard, label: "Discovery Hub", path: "/" },
  { icon: FlaskConical, label: "Hypothesis Canvas", path: "/hypotheses" },
  { icon: GitFork, label: "Driver Tree Builder", path: "/driver-tree" },
  { icon: Database, label: "Evidence Library", path: "/evidence" },
  { icon: Calculator, label: "Value Calculator", path: "/calculator" },
  { icon: FileText, label: "Value Case Builder", path: "/value-case" },
];

export default function Layout() {
  const location = useLocation();
  const navigate = useNavigate();
  const currentPath = location.pathname;
  const currentStep = steps.findIndex((s) => s.path === currentPath);

  return (
    <div className="flex h-screen bg-[#f4f5f7] overflow-hidden">
      {/* LEFT SIDEBAR */}
      <aside className="w-60 bg-white border-r border-gray-200 flex flex-col shrink-0">
        <div className="px-5 py-4 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-[#2d8a6e] flex items-center justify-center">
              <GitFork className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-gray-900 leading-tight">Value Fabric</h1>
              <p className="text-[10px] text-gray-400 leading-tight">Value Modeling Platform</p>
            </div>
          </div>
        </div>

        <div className="px-4 pt-3 pb-2">
          <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg border border-gray-200">
            <Search className="w-4 h-4 text-gray-400" />
            <span className="text-xs text-gray-400">Search models...</span>
          </div>
        </div>

        <div className="px-4 pb-3">
          <button className="w-full flex items-center justify-center gap-2 py-2 bg-[#2d8a6e] text-white rounded-lg text-sm font-medium hover:bg-[#257a5e] transition-colors">
            <Plus className="w-4 h-4" />
            New Value Model
          </button>
        </div>

        <nav className="flex-1 px-3 space-y-0.5 overflow-y-auto">
          <p className="px-3 pt-3 pb-1 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">Workflow</p>
          {sidebarItems.map((item) => {
            const isActive = currentPath === item.path;
            return (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive
                    ? "bg-[#eaf5f1] text-[#2d8a6e] font-semibold"
                    : "text-gray-600 hover:bg-gray-50"
                }`}
              >
                <item.icon className="w-4 h-4 shrink-0" />
                <span className="text-left">{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="px-4 py-3 border-t border-gray-100">
          <div className="flex items-center gap-2">
            <UserCircle className="w-8 h-8 text-gray-400" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">Sarah Chen</p>
              <p className="text-[10px] text-gray-400">Value Engineer</p>
            </div>
          </div>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <header className="bg-white border-b border-gray-200 px-6 py-3">
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
            <span className="font-medium text-gray-700">Allego</span>
            <ChevronRight className="w-3.5 h-3.5 text-gray-400" />
            <span className="font-medium text-gray-700">Medtronic Value Model</span>
            <ChevronRight className="w-3.5 h-3.5 text-gray-400" />
            <span className="text-gray-400">Medical Device Sales Enablement</span>
            <div className="ml-auto flex items-center gap-3">
              <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium">
                Stage {currentStep >= 0 ? currentStep + 1 : 1} — {steps[currentStep >= 0 ? currentStep : 0]?.label}
              </span>
              <Bell className="w-5 h-5 text-gray-400 cursor-pointer hover:text-gray-600" />
            </div>
          </div>

          <div className="flex items-center gap-1">
            {steps.map((step, i) => {
              const isActive = i === currentStep;
              const isCompleted = i < currentStep;
              return (
                <button
                  key={step.path}
                  onClick={() => navigate(step.path)}
                  className="flex-1 flex items-center gap-1.5 py-1.5 px-2 rounded-md transition-colors"
                >
                  {isCompleted ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                  ) : isActive ? (
                    <Circle className="w-4 h-4 text-[#2d8a6e] shrink-0" />
                  ) : (
                    <Circle className="w-4 h-4 text-gray-300 shrink-0" />
                  )}
                  <span className={`text-xs font-medium ${isActive ? "text-[#2d8a6e]" : isCompleted ? "text-emerald-600" : "text-gray-400"}`}>
                    {step.label}
                  </span>
                  {i < steps.length - 1 && <ChevronRight className="w-3 h-3 text-gray-300 ml-auto shrink-0" />}
                </button>
              );
            })}
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
