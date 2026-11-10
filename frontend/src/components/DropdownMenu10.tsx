import { useState } from "react";
import {
    User,
    Bell,
    ShieldCheck,
    CreditCard,
    Settings,
    LogOut,
    ChevronDown,
} from "lucide-react";

interface DropdownMenu10Props {
    onLogout?: () => void;
}

const accountOptions = [
    { label: "Profile", icon: User, href: "/profile" },
    { label: "Notifications", icon: Bell, href: "/notifications" },
    { label: "Security", icon: ShieldCheck, href: "/security" },
    { label: "Billing", icon: CreditCard, href: "/billing" },
    { label: "Settings", icon: Settings, href: "/settings" },
];

export default function DropdownMenu10({
    onLogout,
}: DropdownMenu10Props) {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div
            style={{
                position: "relative",
                display: "inline-block",
                fontFamily: "inherit",
            }}
        >
            <button
                type="button"
                onClick={() => setIsOpen((previous) => !previous)}
                aria-expanded={isOpen}
                aria-haspopup="true"
                style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "10px",
                    padding: "10px 16px",
                    border: "1px solid #e5e7eb",
                    borderRadius: "12px",
                    background: "#ffffff",
                    color: "#222222",
                    fontSize: "14px",
                    fontWeight: 600,
                    cursor: "pointer",
                }}
            >
                <User size={17} />
                Account
                <ChevronDown size={15} />
            </button>

            {isOpen && (
                <div
                    role="menu"
                    style={{
                        position: "absolute",
                        top: "calc(100% + 8px)",
                        right: 0,
                        width: "260px",
                        padding: "8px",
                        background: "#ffffff",
                        border: "1px solid #e5e7eb",
                        borderRadius: "14px",
                        boxShadow: "0 12px 35px rgba(0,0,0,0.10)",
                        zIndex: 1000,
                    }}
                >
                    <div
                        style={{
                            padding: "12px",
                            color: "#888888",
                            fontSize: "12px",
                            fontWeight: 700,
                        }}
                    >
                        MY ACCOUNT
                    </div>

                    {accountOptions.map((item) => {
                        const Icon = item.icon;

                        return (
                            <a
                                key={item.label}
                                href={item.href}
                                role="menuitem"
                                onClick={() => setIsOpen(false)}
                                style={{
                                    display: "flex",
                                    alignItems: "center",
                                    gap: "12px",
                                    padding: "11px 12px",
                                    borderRadius: "9px",
                                    color: "#292929",
                                    textDecoration: "none",
                                    fontSize: "14px",
                                    fontWeight: 500,
                                }}
                                onMouseEnter={(e) => {
                                    e.currentTarget.style.background = "#f5f5f5";
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.background = "transparent";
                                }}
                            >
                                <Icon size={18} color="#888888" />
                                {item.label}
                            </a>
                        );
                    })}

                    <div
                        style={{
                            height: "1px",
                            background: "#eeeeee",
                            margin: "8px 0",
                        }}
                    />

                    <button
                        type="button"
                        role="menuitem"
                        onClick={() => {
                            setIsOpen(false);
                            onLogout?.();
                        }}
                        style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "12px",
                            width: "100%",
                            padding: "11px 12px",
                            border: "none",
                            borderRadius: "9px",
                            background: "transparent",
                            color: "#ef4444",
                            fontSize: "14px",
                            fontWeight: 600,
                            cursor: "pointer",
                            textAlign: "left",
                        }}
                    >
                        <LogOut size={18} />
                        Logout
                    </button>
                </div>
            )}
        </div>
    );
}