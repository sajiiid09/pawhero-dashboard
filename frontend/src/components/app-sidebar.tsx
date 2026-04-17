"use client";

import { motion } from "framer-motion";
import {
  Clock3,
  LayoutDashboard,
  type LucideIcon,
  LogOut,
  PawPrint,
  ShieldCheck,
  Siren,
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { useAuth } from "@/features/auth/auth-context";
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
  const router = useRouter();
  const { logout, user } = useAuth();
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

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <aside className="w-full shrink-0 rounded-[var(--radius-panel)] bg-surface-sidebar text-white shadow-[var(--shadow-sidebar)] transition-all duration-500 ease-out md:sticky md:top-[var(--shell-inset)] md:flex md:h-[calc(100dvh-(var(--shell-inset)*2))] md:w-[278px] md:flex-col md:self-start md:overflow-hidden">
      <div className="flex h-full flex-col">
        {/* Brand / Logo Area */}
        <div className="flex items-center gap-3 px-6 pt-7 pb-6 sm:px-7">
          <div className="relative flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-white/5 ring-1 ring-white/10 shadow-[inset_0_1px_0_rgba(255,255,255,0.1)] transition-transform duration-300 hover:scale-105">
            <Image
              src="/logo.png"
              alt="Pfoten-Held Logo"
              width={32}
              height={32}
              className="h-10 w-10 object-cover"
              priority
            />
          </div>
          <div className="min-w-0">
            <p className="truncate text-[1.85rem] font-extrabold tracking-[-0.06em] text-white drop-shadow-sm">
              Pfoten-Held
            </p>
            {user && (
              <p className="truncate text-xs font-medium text-white/50 transition-colors hover:text-white/70">
                {user.displayName}
              </p>
            )}
          </div>
        </div>

        {/* Navigation */}
        <nav
          aria-label="Hauptnavigation"
          className="scrollbar-hide overflow-x-auto px-5 pb-5 md:flex-1 md:overflow-y-auto md:overflow-x-hidden md:px-6"
        >
          <ul className="flex min-w-max gap-2 md:min-w-0 md:flex-col">
            {navigationItems.map(({ href, label, icon: Icon, match }) => {
              const active = match(pathname);

              return (
                <li key={label} className="relative">
                  {/* Fluid Active Background Pill */}
                  {active && (
                    <motion.div
                      layoutId="sidebar-active-pill"
                      className="absolute inset-0 rounded-[22px] bg-surface-sidebar-active shadow-[inset_0_1px_0_rgba(255,255,255,0.06),0_2px_8px_rgba(0,0,0,0.15)]"
                      initial={false}
                      transition={{
                        type: "spring",
                        stiffness: 400,
                        damping: 30,
                      }}
                    />
                  )}

                  {href ? (
                    <Link
                      href={href}
                      aria-current={active ? "page" : undefined}
                      className={cn(
                        "group relative z-10 flex items-center gap-3 rounded-[22px] border border-transparent px-4 py-3.5 text-base font-semibold outline-none transition-colors duration-200 md:px-5",
                        active
                          ? "text-white"
                          : "text-white/60 hover:border-white/10 hover:bg-white/5 hover:text-white focus-visible:border-white/15 focus-visible:bg-white/10 focus-visible:text-white"
                      )}
                    >
                      <Icon
                        className={cn(
                          "h-[1.15rem] w-[1.15rem] transition-transform duration-300 ease-out",
                          active ? "text-white" : "text-white/60 group-hover:scale-110 group-hover:text-white/90"
                        )}
                      />
                      <span>{label}</span>
                    </Link>
                  ) : (
                    <span className="relative z-10 flex cursor-not-allowed items-center gap-3 rounded-[22px] px-4 py-3.5 text-base font-semibold text-white/30 md:px-5">
                      <Icon className="h-[1.15rem] w-[1.15rem] text-white/30" />
                      <span>{label}</span>
                    </span>
                  )}
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Footer Area */}
        <div className="border-t border-white/10 px-5 py-5 transition-colors duration-300 md:px-6 md:py-6">
          <button
            type="button"
            onClick={handleLogout}
            className="group flex w-full items-center gap-3 rounded-[22px] border border-transparent px-4 py-3 text-left text-base font-semibold text-white/60 transition-all duration-200 hover:border-white/10 hover:bg-white/5 hover:text-white focus-visible:bg-white/10 focus-visible:text-white focus-visible:outline-none md:px-5"
          >
            <LogOut className="h-[1.15rem] w-[1.15rem] transition-transform duration-300 ease-out group-hover:translate-x-1 group-hover:text-white/90" />
            <span>Abmelden</span>
          </button>
        </div>
      </div>
    </aside>
  );
}
