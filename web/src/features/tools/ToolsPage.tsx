import React, { useState } from "react";
import { Wrench, CheckCircle2, ShieldAlert, AlertCircle, ChevronDown, ChevronRight, Search } from "lucide-react";
import { Badge } from "../../components/Badge";

interface ToolLogEntry {
  id: string;
  tool_name: string;
  sender_masked: string;
  status: "ok" | "requires_user_confirmation" | "error";
  timestamp: string;
  arguments: Record<string, any>;
  result: Record<string, any>;
}

const MOCK_TOOL_LOGS: ToolLogEntry[] = [
  {
    id: "log_1",
    tool_name: "check_order_status",
    sender_masked: "+44 (791) ••••• 4310",
    status: "ok",
    timestamp: "10 mins ago",
    arguments: { order_id: "ORD-1029" },
    result: { status: "In Transit", carrier: "FedEx", tracking: "TRK983726154" },
  },
  {
    id: "log_2",
    tool_name: "cancel_order",
    sender_masked: "+1 (415) ••••• 7762",
    status: "requires_user_confirmation",
    timestamp: "45 mins ago",
    arguments: { order_id: "ORD-2045", reason: "Customer request" },
    result: { status: "requires_user_confirmation", message: "Sensitive action requires user confirmation" },
  },
  {
    id: "log_3",
    tool_name: "schedule_appointment",
    sender_masked: "+61 (400) ••••• 9134",
    status: "ok",
    timestamp: "6 hours ago",
    arguments: { date: "Tomorrow", time_slot: "10:00 AM", topic: "General Inquiry" },
    result: { status: "confirmed", appointment_id: "APT-8821" },
  },
  {
    id: "log_4",
    tool_name: "calculate_shipping_quote",
    sender_masked: "+1 (555) ••••• 2281",
    status: "ok",
    timestamp: "1 day ago",
    arguments: { postal_code: "90210", weight_kg: 2.5 },
    result: { estimated_cost_usd: 9.74, delivery_window: "2-4 business days" },
  },
];

export const ToolsPage: React.FC = () => {
  const [logs] = useState<ToolLogEntry[]>(MOCK_TOOL_LOGS);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const filtered = logs.filter(
    (l) =>
      l.tool_name.toLowerCase().includes(search.toLowerCase()) ||
      l.sender_masked.includes(search)
  );

  return (
    <div className="flex h-full w-full flex-col overflow-y-auto p-4 md:p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <Wrench className="h-6 w-6 text-primary" />
          <span>Claude Tool Execution Audit Log</span>
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Review business tool calls executed by Claude, parameters passed, and confirmation gates.
        </p>
      </div>

      <div className="relative max-w-md">
        <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Filter by tool name or phone..."
          className="w-full rounded-xl border border-input bg-card pl-9 pr-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
        />
      </div>

      {/* Logs Table */}
      <div className="rounded-2xl border border-border bg-card overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-border bg-muted/40 text-xs font-semibold text-muted-foreground">
              <tr>
                <th className="py-3 px-4">Tool Name</th>
                <th className="py-3 px-4">User Phone</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Time</th>
                <th className="py-3 px-4 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {filtered.map((log) => {
                const isExpanded = expandedId === log.id;
                return (
                  <React.Fragment key={log.id}>
                    <tr
                      onClick={() => setExpandedId(isExpanded ? null : log.id)}
                      className="cursor-pointer hover:bg-accent/40 transition-colors"
                    >
                      <td className="py-3.5 px-4 font-mono font-medium text-xs">
                        {log.tool_name}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-xs text-muted-foreground">
                        {log.sender_masked}
                      </td>
                      <td className="py-3.5 px-4">
                        {log.status === "ok" && (
                          <Badge variant="success" className="gap-1 text-[10px]">
                            <CheckCircle2 className="h-3 w-3" /> Executed
                          </Badge>
                        )}
                        {log.status === "requires_user_confirmation" && (
                          <Badge variant="warning" className="gap-1 text-[10px]">
                            <ShieldAlert className="h-3 w-3" /> Gated Confirmation
                          </Badge>
                        )}
                        {log.status === "error" && (
                          <Badge variant="destructive" className="gap-1 text-[10px]">
                            <AlertCircle className="h-3 w-3" /> Error
                          </Badge>
                        )}
                      </td>
                      <td className="py-3.5 px-4 text-xs text-muted-foreground">
                        {log.timestamp}
                      </td>
                      <td className="py-3.5 px-4 text-right text-muted-foreground">
                        {isExpanded ? (
                          <ChevronDown className="h-4 w-4 inline-block" />
                        ) : (
                          <ChevronRight className="h-4 w-4 inline-block" />
                        )}
                      </td>
                    </tr>

                    {isExpanded && (
                      <tr className="bg-muted/10">
                        <td colSpan={5} className="p-4 border-t border-border/40 font-mono text-xs">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                              <p className="font-semibold text-muted-foreground mb-1">Invocation Arguments:</p>
                              <pre className="p-3 rounded-xl bg-card border border-border overflow-x-auto text-[11px]">
                                {JSON.stringify(log.arguments, null, 2)}
                              </pre>
                            </div>
                            <div>
                              <p className="font-semibold text-muted-foreground mb-1">Execution Response:</p>
                              <pre className="p-3 rounded-xl bg-card border border-border overflow-x-auto text-[11px]">
                                {JSON.stringify(log.result, null, 2)}
                              </pre>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
