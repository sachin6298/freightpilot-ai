import {
    Mail,
    Headset,
    MapPin,
    ArrowUpRight,
    type LucideIcon,
} from "lucide-react";

import "./Contact5.css";

interface ContactMethod {
    id: string;
    icon: LucideIcon;
    title: string;
    description: string;
    details: string;
    href?: string;
}

interface Contact5Props {
    badge?: string;
    heading: string;
    description?: string;
    contactMethods: ContactMethod[];
    footerText?: string;
}

function Contact5({
    badge,
    heading,
    description,
    contactMethods,
    footerText,
}: Contact5Props) {
    return (
        <section className="fp-contact" id="contact">
            <div className="fp-contact-container">

                <div className="fp-contact-header">
                    {badge && (
                        <span className="fp-contact-badge">
                            <span className="fp-contact-badge-dot" />
                            {badge}
                        </span>
                    )}

                    <h2>{heading}</h2>

                    {description && (
                        <p className="fp-contact-description">
                            {description}
                        </p>
                    )}
                </div>

                <div className="fp-contact-grid">
                    {contactMethods.map((method) => {
                        const Icon = method.icon;

                        return (
                            <article
                                className="fp-contact-card"
                                key={method.id}
                            >
                                <div className="fp-contact-icon">
                                    <Icon size={25} strokeWidth={1.8} />
                                </div>

                                <h3>{method.title}</h3>

                                <p className="fp-contact-card-description">
                                    {method.description}
                                </p>

                                {method.href ? (
                                    <a
                                        href={method.href}
                                        className="fp-contact-detail"
                                    >
                                        {method.details}
                                        <ArrowUpRight size={17} />
                                    </a>
                                ) : (
                                    <p className="fp-contact-detail">
                                        {method.details}
                                    </p>
                                )}
                            </article>
                        );
                    })}
                </div>

                {footerText && (
                    <div className="fp-contact-footer">
                        {footerText}
                    </div>
                )}

            </div>
        </section>
    );
}

export default function Contact5Section() {
    const supportEmail = import.meta.env.VITE_SUPPORT_EMAIL?.trim();
    const emailHref = supportEmail ? `mailto:${supportEmail}` : undefined;
    return (
        <Contact5
            badge="Get in Touch"
            heading="Let's build something great together"
            description="Have questions about our platform, partnerships, or product features? Our team is here to support you every step of the way."
            contactMethods={[
                {
                    id: "email",
                    icon: Mail,
                    title: "Email Us",
                    description:
                        "Send us your questions and our team will get back to you.",
                    details: supportEmail || "Support email not configured",
                    href: emailHref,
                },
                {
                    id: "support",
                    icon: Headset,
                    title: "Live Support",
                    description:
                        "Talk to our team for assistance with your logistics operations.",
                    details: supportEmail || "Support email not configured",
                    href: emailHref,
                },
                {
                    id: "office",
                    icon: MapPin,
                    title: "Our Location",
                    description:
                        "Connect with our team.",
                    details: "India",
                },
            ]}
            footerText="We're committed to delivering reliable support, intelligent solutions, and a seamless logistics experience."
        />
    );
}