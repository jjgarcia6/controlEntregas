import {
  Building2,
  ClipboardList,
  CreditCard,
  FileBarChart,
  FileText,
  FileUp,
  LayoutDashboard,
  Package,
  ShieldCheck,
  GitBranch,
  Truck,
  Users,
} from "lucide-react";
import { useLocation, Link } from "react-router-dom";

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";

interface NavItem {
  label: string;
  icon: React.ElementType;
  href: string;
  roles: string[];
}

const navItems: NavItem[] = [
  {
    label: "Dashboard",
    icon: LayoutDashboard,
    href: "/dashboard",
    roles: ["admin", "operador", "lectura"],
  },
  {
    label: "Usuarios",
    icon: Users,
    href: "/usuarios",
    roles: ["admin"],
  },
  {
    label: "Bancos",
    icon: Building2,
    href: "/bancos",
    roles: ["admin", "operador"],
  },
  {
    label: "Ingreso XML",
    icon: FileUp,
    href: "/xml/ingreso",
    roles: ["admin", "operador"],
  },
  {
    label: "Pendientes XML",
    icon: ClipboardList,
    href: "/xml/pendientes",
    roles: ["admin", "operador"],
  },
  {
    label: "Lista XML",
    icon: FileText,
    href: "/xml/lista",
    roles: ["admin", "operador", "lectura"],
  },
  {
    label: "Kardex",
    icon: Package,
    href: "/kardex",
    roles: ["admin", "operador", "lectura"],
  },
  {
    label: "Entregas",
    icon: Truck,
    href: "/entregas",
    roles: ["admin", "operador", "lectura"],
  },
  {
    label: "Pagos",
    icon: CreditCard,
    href: "/pagos",
    roles: ["admin", "operador"],
  },
  {
    label: "Reportes",
    icon: FileBarChart,
    href: "/reportes",
    roles: ["admin", "operador", "lectura"],
  },
  {
    label: "Trazabilidad",
    icon: GitBranch,
    href: "/trazabilidad",
    roles: ["admin", "operador", "lectura"],
  },
  {
    label: "Auditoría",
    icon: ShieldCheck,
    href: "/auditoria",
    roles: ["admin"],
  },
];

interface AppSidebarProps {
  rol?: string;
}

export function AppSidebar({ rol = "" }: AppSidebarProps) {
  const location = useLocation();

  const visibleItems = navItems.filter(
    (item) => rol === "" || item.roles.includes(rol),
  );

  return (
    <Sidebar>
      <SidebarHeader className="p-4">
        <span className="font-semibold text-base">Control de Entregas</span>
      </SidebarHeader>
      <SidebarContent>
        <SidebarMenu>
          {visibleItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname.startsWith(item.href);
            return (
              <SidebarMenuItem key={item.href}>
                <SidebarMenuButton asChild isActive={isActive}>
                  <Link to={item.href}>
                    <Icon className="h-4 w-4" />
                    <span>{item.label}</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            );
          })}
        </SidebarMenu>
      </SidebarContent>
      <SidebarFooter />
    </Sidebar>
  );
}
