
import { useState, type FormEvent } from "react";
import { useAuth } from "../../context/AuthContext";
import { motion, type Variants } from "motion/react";
import {
    ArrowRight,
    ArrowUpRight,
    ChevronLeft,
} from "lucide-react";
import "./Auth7.css";

interface Auth7Props {
    onLoginClick?: () => void;
}

const GoogleIcon = () => (
    <svg viewBox="0 0 24 24" width="19" height="19">
        <path
            fill="#4285F4"
            d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.1 5.1 0 0 1-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
        />
        <path
            fill="#34A853"
            d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.16v2.84C3.99 20.53 7.7 23 12 23z"
        />
        <path
            fill="#FBBC05"
            d="M5.84 14.09a6.96 6.96 0 0 1 0-4.18V7.07H2.16a11 11 0 0 0 0 9.86z"
        />
        <path
            fill="#EA4335"
            d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.16 7.07l3.68 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
        />
    </svg>
);

const AppleIcon = () => (
    <svg viewBox="0 0 24 24" width="19" height="19" fill="currentColor">
        <path d="M17.05 12.54c.02 2.11 1.85 2.81 1.87 2.82-.02.05-.29 1-.96 1.98-.58.85-1.18 1.7-2.13 1.72-.93.02-1.23-.55-2.3-.55-1.06 0-1.4.53-2.27.57-.91.03-1.6-.92-2.18-1.77-1.19-1.72-2.1-4.86-.88-6.99.6-1.06 1.68-1.73 2.85-1.75.89-.02 1.73.6 2.27.6.53 0 1.53-.74 2.58-.63.44.02 1.67.18 2.46 1.33-.06.04-1.47.86-1.31 2.67zM15.35 6.77c.48-.58.8-1.38.71-2.18-.69.03-1.53.46-2.03 1.04-.44.51-.82 1.32-.72 2.09.77.06 1.56-.39 2.04-.95z" />
    </svg>
);

const PhoneIcon = () => (
    <svg
        viewBox="0 0 24 24"
        width="19"
        height="19"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
    >
        <rect x="6" y="2" width="12" height="20" rx="2" />
        <path d="M11 18h2" />
    </svg>
);

const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.06,
            delayChildren: 0.08,
        },
    },
};

const itemVariants: Variants = {
    hidden: { opacity: 0, y: 10 },
    visible: {
        opacity: 1,
        y: 0,
        transition: { duration: 0.3 },
    },
};

export default function Auth7({ onLoginClick }: Auth7Props) {
    const auth = useAuth();
    const [phoneMode, setPhoneMode] = useState(false);
    const [otpSent, setOtpSent] = useState(false);
    const [phone, setPhone] = useState("");
    const [otp, setOtp] = useState("");
    const [terms, setTerms] = useState(false);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");

    const execute = async (action: () => Promise<void>) => {
        setBusy(true);
        setError("");

        try {
            await action();
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "Authentication failed. Please try again."
            );
        } finally {
            setBusy(false);
        }
    };

    const handleEmailSubmit = async (
        e: FormEvent<HTMLFormElement>
    ) => {
        e.preventDefault();

        if (!terms) {
            setError("Please accept the Terms and Privacy Policy.");
            return;
        }

        await execute(async () => {
            const formData = new FormData(e.currentTarget);
            await auth.registerBuyer({
                email: String(formData.get("email") || ""),
                password: String(formData.get("password") || ""),
                company_name: String(formData.get("name") || ""),
                contact_person: undefined,
                phone_number: undefined,
            });
        });
    };

    const sendOtp = async () => {
        if (!phone.trim()) {
            setError("Please enter your mobile number.");
            return;
        }

        await execute(async () => {
            await auth.verifyFirebasePhone("dummy", phone.trim()); // Will be replaced with real flow
            setOtpSent(true);
        });
    };

    const verifyOtp = async () => {
        if (!otp.trim()) {
            setError("Please enter your OTP.");
            return;
        }

        await execute(async () => {
            // Use verifyAccountPhone from backend - but we need phone number from context
            // For now, we'll mark as verified since the flow goes through AuthContext
            await auth.refreshUser();
        });
    };

    const handleGoogleSignIn = async () => {
        await execute(async () => {
            // Google OAuth would typically open a flow; for now we use login
            // The actual Google ID sign-in is handled in App.tsx AuthModal
            // Here we'll try to get the current user or show error
            if (!auth.user) {
                setError("Google sign-in not fully configured. Please use email login or contact support.");
            }
        });
    };

    const handleAppleSignIn = async () => {
        await execute(async () => {
            if (!auth.user) {
                setError("Apple sign-in not fully configured. Please use email login or contact support.");
            }
        });
    };

    return (
        <main className="fp-auth fp-auth-register">
            <a href="/" className="fp-brand">
                FREIGHT<span>PILOT</span>
            </a>

            <section className="fp-auth-left">
                <div className="fp-form-wrapper">
                    <motion.div
                        variants={containerVariants}
                        initial="hidden"
                        animate="visible"
                        className="fp-form-content"
                    >
                        <motion.div
                            variants={itemVariants}
                            className="fp-heading"
                        >
                            <div className="fp-eyebrow">
                                CREATE YOUR ACCOUNT
                            </div>

                            <h1>
                                {phoneMode
                                    ? "Phone verification"
                                    : "Create your account"}
                            </h1>

                            <p>
                                {phoneMode
                                    ? "Verify your mobile number to continue."
                                    : "Your logistics workspace starts here."}
                            </p>
                        </motion.div>

                        {!phoneMode && (
                            <motion.div
                                variants={itemVariants}
                                className="fp-social"
                            >
                                <button
                                    type="button"
                                    disabled={busy}
                                    onClick={handleGoogleSignIn}
                                    className="fp-social-button"
                                >
                                    <GoogleIcon />
                                    <span>Google</span>
                                </button>

                                <button
                                    type="button"
                                    disabled={busy}
                                    onClick={handleAppleSignIn}
                                    className="fp-social-button"
                                >
                                    <AppleIcon />
                                    <span>Apple</span>
                                </button>

                                <button
                                    type="button"
                                    disabled={busy}
                                    onClick={() => {
                                        setPhoneMode(true);
                                        setError("");
                                    }}
                                    className="fp-social-button fp-phone-button"
                                >
                                    <PhoneIcon />
                                    <span>Continue with Phone</span>
                                </button>
                            </motion.div>
                        )}

                        {!phoneMode && (
                            <motion.div
                                variants={itemVariants}
                                className="fp-divider"
                            >
                                <span />
                                <small>OR CONTINUE WITH EMAIL</small>
                                <span />
                            </motion.div>
                        )}

                        {!phoneMode ? (
                            <motion.form
                                variants={itemVariants}
                                onSubmit={handleEmailSubmit}
                                className="fp-email-form"
                            >
                                <div className="fp-field">
                                    <label htmlFor="fp-name">Full name</label>
                                    <input
                                        id="fp-name"
                                        name="name"
                                        type="text"
                                        autoComplete="name"
                                        required
                                        placeholder="Enter your full name"
                                        className="fp-input"
                                    />
                                </div>

                                <div className="fp-field">
                                    <label htmlFor="fp-email">Email address</label>
                                    <input
                                        id="fp-email"
                                        name="email"
                                        type="email"
                                        autoComplete="email"
                                        required
                                        placeholder="name@example.com"
                                        className="fp-input"
                                    />
                                </div>

                                <div className="fp-field">
                                    <label htmlFor="fp-password">Password</label>
                                    <input
                                        id="fp-password"
                                        name="password"
                                        type="password"
                                        autoComplete="new-password"
                                        minLength={8}
                                        required
                                        placeholder="Minimum 8 characters"
                                        className="fp-input"
                                    />
                                </div>

                                <label className="fp-terms">
                                    <input
                                        type="checkbox"
                                        checked={terms}
                                        onChange={(e) => setTerms(e.target.checked)}
                                    />
                                    <span>
                                        I agree to the Terms of Service and Privacy Policy.
                                    </span>
                                </label>

                                <button
                                    type="submit"
                                    disabled={busy}
                                    className="fp-primary-button"
                                >
                                    {busy ? "Creating account..." : "Create account"}
                                    {!busy && <ArrowUpRight size={17} />}
                                </button>
                            </motion.form>
                        ) : (
                            <motion.div
                                variants={itemVariants}
                                className="fp-phone-form"
                            >
                                {!otpSent ? (
                                    <>
                                        <div className="fp-field">
                                            <label htmlFor="fp-phone">
                                                Mobile number
                                            </label>

                                            <input
                                                id="fp-phone"
                                                type="tel"
                                                autoComplete="tel"
                                                value={phone}
                                                onChange={(e) => setPhone(e.target.value)}
                                                placeholder="+91 9876543210"
                                                className="fp-input"
                                            />
                                        </div>

                                        <div id="recaptcha-container" />

                                        <button
                                            type="button"
                                            disabled={busy}
                                            onClick={sendOtp}
                                            className="fp-primary-button"
                                        >
                                            {busy ? "Sending OTP..." : "Send verification code"}
                                            {!busy && <ArrowRight size={17} />}
                                        </button>
                                    </>
                                ) : (
                                    <>
                                        <p className="fp-phone-description">
                                            Enter the verification code sent to {phone}.
                                        </p>

                                        <input
                                            type="text"
                                            inputMode="numeric"
                                            autoComplete="one-time-code"
                                            maxLength={6}
                                            value={otp}
                                            onChange={(e) =>
                                                setOtp(
                                                    e.target.value.replace(/\D/g, "").slice(0, 6)
                                                )
                                            }
                                            placeholder="Enter 6-digit OTP"
                                            className="fp-input fp-otp-input"
                                        />

                                        <button
                                            type="button"
                                            disabled={busy || otp.length !== 6}
                                            onClick={verifyOtp}
                                            className="fp-primary-button"
                                        >
                                            {busy ? "Verifying..." : "Verify and sign in"}
                                            {!busy && <ArrowRight size={17} />}
                                        </button>

                                        <button
                                            type="button"
                                            onClick={() => {
                                                setOtpSent(false);
                                                setOtp("");
                                                setError("");
                                            }}
                                            className="fp-text-button"
                                        >
                                            Change phone number
                                        </button>
                                    </>
                                )}

                                <button
                                    type="button"
                                    onClick={() => {
                                        setPhoneMode(false);
                                        setOtpSent(false);
                                        setOtp("");
                                        setPhone("");
                                        setError("");
                                    }}
                                    className="fp-text-button"
                                >
                                    <ChevronLeft size={14} />
                                    Back to registration
                                </button>
                            </motion.div>
                        )}

                        {error && (
                            <p role="alert" className="fp-error">
                                {error}
                            </p>
                        )}

                        <motion.div
                            variants={itemVariants}
                            className="fp-login"
                        >
                            Already have an account?{" "}
                            <button type="button" onClick={() => onLoginClick?.()}>
                                Log in
                            </button>
                        </motion.div>
                    </motion.div>
                </div>
            </section>
        </main>
    );
}
