
import React from "react";
import {
    ArrowRight,
    Anchor,
    ShieldCheck,
    BrainCircuit,
    Activity,
    Ship,
    Globe2,
    CheckCircle2,
    Menu,
} from "lucide-react";
import Contact5Section from "./Contact5";
import { ThemeToggleButton } from "./workspace/ThemeToggleButton";
import "./PublicLanding.css";

interface PublicLandingProps {
    onLogin: () => void;
    onRegister: () => void;
    onNavigate: (page: "overview" | "copilot" | "risk" | "payments" | "shipments") => void;
}

const PublicLanding: React.FC<PublicLandingProps> = ({
    onLogin,
    onRegister,
    onNavigate,
}) => {
    return (
        <main className="light-landing">
            {/* NAVIGATION */}
            <header className="lp-header">
                <a href="#home" className="lp-brand">
                    <span className="lp-brand-icon"><Anchor size={21} /></span>
                    <span className="lp-brand-name">FreightPilot</span>
                </a>

                <nav className="lp-nav">
                    <a href="#about">About</a>
                    <a href="#solutions">Solutions</a>
                    <a href="#services">Services</a>
                    <a href="#contact">Contact</a>
                </nav>

                <div className="lp-nav-actions">
                    <ThemeToggleButton compact />
                    <button className="lp-login" onClick={onLogin}>Sign in</button>
                    <button className="lp-primary-btn lp-nav-cta" onClick={onRegister}>
                        Get started <ArrowRight size={16} />
                    </button>
                </div>

                <button
                    className="lp-mobile-menu"
                    aria-label="Open navigation"
                    onClick={() => document.querySelector(".lp-nav")?.classList.toggle("lp-nav-open")}
                >
                    <Menu />
                </button>
            </header>

            {/* HERO */}
            <section className="lp-hero" id="home">
                <div className="lp-hero-copy">
                    <div className="lp-eyebrow">
                        <span className="lp-eyebrow-dot" />
                        SMARTER GLOBAL LOGISTICS
                    </div>

                    <h1>
                        Navigate the future of
                        <span> global logistics.</span>
                    </h1>

                    <p>
                        Move your freight with greater visibility, smarter decisions
                        and complete control. One connected platform for modern
                        maritime operations.
                    </p>

                    <div className="lp-hero-actions">
                        <button className="lp-primary-btn" onClick={onRegister}>
                            Explore Platform <ArrowRight size={17} />
                        </button>

                        <a href="#about" className="lp-secondary-btn">
                            Discover more <ArrowRight size={16} />
                        </a>
                    </div>

                    <div className="lp-trust-points">
                        <span><CheckCircle2 /> Shipment visibility</span>
                        <span><CheckCircle2 /> AI-powered intelligence</span>
                        <span><CheckCircle2 /> Risk management</span>
                    </div>
                </div>

                <div className="lp-hero-visual">
                    <div className="lp-video-container">
                        <video
                            className="lp-yacht-video"
                            autoPlay
                            muted
                            loop
                            playsInline
                            preload="auto"
                            poster="/images/yacht-poster.png"
                        >
                            <source src="/videos/yacht-motion.mp4" type="video/mp4" />
                            Your browser does not support video playback.
                        </video>

                        <div className="lp-video-label">
                            <span /> GLOBAL MARITIME MOVEMENT
                        </div>
                    </div>

                    <div className="lp-floating-card">
                        <div className="lp-floating-icon"><Globe2 /></div>
                        <div>
                            <strong>Connected globally</strong>
                            <span>One unified workspace</span>
                        </div>
                    </div>
                </div>

                <div className="lp-hero-bottom">
                    <span>INTELLIGENT LOGISTICS</span>
                    <span>VISIBILITY · CONTROL · CONFIDENCE</span>
                </div>
            </section>

            {/* INTRODUCTION */}
            <section className="lp-about" id="about">
                <div className="lp-about-label">
                    <span className="lp-section-kicker">A NEW WAY FORWARD</span>
                    <span className="lp-about-line" />
                </div>

                <div className="lp-about-content">
                    <h2>
                        Move beyond traditional
                        <span> freight management.</span>
                    </h2>

                    <p>
                        Logistics should not be complicated. Bring shipment planning,
                        carrier comparisons, intelligent risk assessment and payment
                        visibility together in one straightforward experience.
                    </p>

                    <button
                        className="lp-text-link"
                        onClick={() => onNavigate("overview")}
                    >
                        Explore your workspace <ArrowRight size={17} />
                    </button>
                </div>
            </section>

            {/* SOLUTIONS */}
            <section className="lp-solutions" id="solutions">
                <div className="lp-section-heading">
                    <div>
                        <span className="lp-section-kicker">WHAT WE OFFER</span>
                        <h2>Everything you need.<br /><span>Nothing you don't.</span></h2>
                    </div>
                    <p>
                        Practical tools designed to make freight operations
                        clearer, more predictable and easier to manage.
                    </p>
                </div>

                <div className="lp-solution-grid">
                    <article className="lp-solution-card">
                        <div className="lp-solution-icon"><Ship /></div>
                        <span className="lp-card-number">01</span>
                        <h3>Shipment Visibility</h3>
                        <p>
                            Keep shipment details, milestones and delivery information
                            organised in one place.
                        </p>
                        <button onClick={() => onNavigate("shipments")}>
                            Explore <ArrowRight />
                        </button>
                    </article>

                    <article className="lp-solution-card">
                        <div className="lp-solution-icon"><BrainCircuit /></div>
                        <span className="lp-card-number">02</span>
                        <h3>AI Intelligence</h3>
                        <p>
                            Use AI-assisted analysis to understand freight information
                            and support better decisions.
                        </p>
                        <button onClick={() => onNavigate("copilot")}>
                            Explore <ArrowRight />
                        </button>
                    </article>

                    <article className="lp-solution-card">
                        <div className="lp-solution-icon"><ShieldCheck /></div>
                        <span className="lp-card-number">03</span>
                        <h3>Risk Management</h3>
                        <p>
                            Identify pricing anomalies, transit concerns and
                            operational risks before committing.
                        </p>
                        <button onClick={() => onNavigate("risk")}>
                            Explore <ArrowRight />
                        </button>
                    </article>

                    <article className="lp-solution-card">
                        <div className="lp-solution-icon"><Activity /></div>
                        <span className="lp-card-number">04</span>
                        <h3>Smart Analytics</h3>
                        <p>
                            Understand shipment activity, costs and operational
                            performance through clear insights.
                        </p>
                        <button onClick={() => onNavigate("overview")}>
                            Explore <ArrowRight />
                        </button>
                    </article>
                </div>
            </section>

            {/* SERVICES */}
            <section className="lp-services" id="services">
                <div className="lp-services-visual">
                    <div className="lp-services-image">
                        <img
                            src="/images/yacht-poster.png"
                            alt="Yacht sailing across open water"
                            loading="lazy"
                        />
                    </div>
                    <div className="lp-image-caption">
                        <span>BUILT FOR MODERN MARITIME OPERATIONS</span>
                    </div>
                </div>

                <div className="lp-services-copy">
                    <span className="lp-section-kicker">OUR APPROACH</span>
                    <h2>From planning<br />to <span>delivery.</span></h2>
                    <p>
                        Every shipment involves important decisions. Manage the
                        journey with a connected workflow that helps you plan,
                        compare, evaluate and monitor.
                    </p>

                    <div className="lp-service-list">
                        <div><CheckCircle2 /><span>Shipment creation and management</span></div>
                        <div><CheckCircle2 /><span>Carrier quote comparison</span></div>
                        <div><CheckCircle2 /><span>AI-assisted risk evaluation</span></div>
                        <div><CheckCircle2 /><span>Payment and shipment records</span></div>
                    </div>

                    <button className="lp-primary-btn" onClick={onRegister}>
                        Get started <ArrowRight size={17} />
                    </button>
                </div>
            </section>

            {/* CONTACT */}
            <div id="contact">
                <Contact5Section />
            </div>

            {/* FOOTER */}
            <footer className="lp-footer">
                <a href="#home" className="lp-brand">
                    <span className="lp-brand-icon"><Anchor size={19} /></span>
                    <span className="lp-brand-name">FreightPilot</span>
                </a>

                <p>Intelligent logistics. Better possibilities.</p>

                <span>© {new Date().getFullYear()} All rights reserved.</span>
            </footer>
        </main>
    );
};

export default PublicLanding;
