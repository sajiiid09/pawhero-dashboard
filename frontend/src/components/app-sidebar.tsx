"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Clock3,
  LayoutDashboard,
  type LucideIcon,
  LogOut,
  PawPrint,
  ShieldCheck,
  Siren,
} from "lucide-react";

import { usePetsQuery } from "@/features/app/hooks";
import { cn } from "@/lib/utils";

type NavigationItem = {
  href?: string | null;
  label: string;
  icon: LucideIcon;
  match: (pathname: string) => boolean;
};

export function AppSidebar() {
  const pathname = usePathname();
  const { data: pets = [] } = usePetsQuery();
  const primaryPet = pets[0] ?? null;

  const navigationItems: NavigationItem[] = [
    {
      href: "/dashboard",
      label: "Dashboard",
      icon: LayoutDashboard,
      match: (value) => value === "/dashboard",
    },
    {
      href: "/pets",
      label: "Meine Tiere",
      icon: PawPrint,
      match: (value) => value.startsWith("/pets"),
    },
    {
      href: "/emergency-chain",
      label: "Notfallkette",
      icon: ShieldCheck,
      match: (value) => value.startsWith("/emergency-chain"),
    },
    {
      href: "/check-in",
      label: "Check-In",
      icon: Clock3,
      match: (value) => value.startsWith("/check-in"),
    },
    {
      href: primaryPet ? `/emergency-profile/${primaryPet.id}` : null,
      label: "Notfall-Profil",
      icon: Siren,
      match: (value) => value.startsWith("/emergency-profile"),
    },
  ];

  return (
    <aside className="w-full shrink-0 rounded-[var(--radius-panel)] bg-surface-sidebar text-white shadow-[var(--shadow-sidebar)] md:w-[278px]">
      <div className="flex h-full flex-col">
        <div className="flex items-center gap-3 px-6 pt-7 pb-6 sm:px-7">
          <div className="relative flex h-11 w-11 items-center justify-center rounded-2xl bg-white/6 ring-1 ring-white/10">
            <span className="absolute left-3 top-2.5 h-2 w-2 rounded-full bg-primary/80" />
            <span className="absolute left-5.5 top-4.5 h-2 w-2 rounded-full bg-primary/65" />
            <span className="absolute left-7.5 top-7 h-2 w-2 rounded-full bg-primary/45" />
          </div>
          <div>
            <p className="text-[1.85rem] font-extrabold tracking-[-0.06em]">Pfoten-Held</p>
          </div>
        </div>

        <nav
          aria-label="Hauptnavigation"
          className="overflow-x-auto px-5 pb-5 md:flex-1 md:overflow-visible md:px-6"
        >
          <ul className="flex min-w-max gap-3 md:min-w-0 md:flex-col">
            {navigationItems.map(({ href, label, icon: Icon, match }) => {
              const active = match(pathname);

              return (
              <li key={label}>
                {href ? (
                  <Link
                    href={href}
                    aria-current={active ? "page" : undefined}
                    className={cn(
                      "group flex items-center gap-3 rounded-[22px] border border-transparent px-4 py-3.5 text-base font-semibold text-white/68 outline-none transition hover:border-white/6 hover:bg-white/5 hover:text-white focus-visible:border-white/15 focus-visible:bg-white/6 focus-visible:text-white md:px-5",
                      active &&
                        "bg-surface-sidebar-active text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]",
                    )}
                  >
                    <Icon className={cn("h-[1.15rem] w-[1.15rem]", active ? "text-white" : "text-white/70")} />
                    <span>{label}</span>
                  </Link>
                ) : (
                  <span className="flex cursor-not-allowed items-center gap-3 rounded-[22px] px-4 py-3.5 text-base font-semibold text-white/52 md:px-5">
                    <Icon className="h-[1.15rem] w-[1.15rem] text-white/55" />
                    <span>{label}</span>
                  </span>
                )}
              </li>
            )})}
          </ul>
        </nav>

        <div className="border-t border-white/8 px-5 py-5 md:px-6 md:py-6">
          <button
            type="button"
            className="flex w-full items-center gap-3 rounded-[22px] px-4 py-3 text-left text-base font-semibold text-white/65 hover:bg-white/5 hover:text-white focus-visible:bg-white/6 focus-visible:text-white focus-visible:outline-none md:px-5"
          >
            <LogOut className="h-[1.15rem] w-[1.15rem]" />
            <span>Abmelden</span>
          </button>
        </div>
      </div>
    </aside>
  );
}
