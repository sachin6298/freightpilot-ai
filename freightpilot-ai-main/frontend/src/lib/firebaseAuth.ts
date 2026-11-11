import { initializeApp, getApp, getApps } from "firebase/app";
import {
  getAuth,
  signInWithPhoneNumber,
  RecaptchaVerifier,
  ConfirmationResult,
  UserCredential,
} from "firebase/auth";

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID,
};

const requiredConfig = [
  firebaseConfig.apiKey,
  firebaseConfig.authDomain,
  firebaseConfig.projectId,
  firebaseConfig.messagingSenderId,
  firebaseConfig.appId,
];

if (requiredConfig.some((value) => !value)) {
  throw new Error("Firebase configuration is incomplete. Check frontend environment variables.");
}

const app = getApps().length ? getApp() : initializeApp(firebaseConfig);
export const auth = getAuth(app);

export interface PhoneAuthResult {
  verificationId: string;
  confirmationResult: ConfirmationResult;
}

export interface VerifiedPhoneResult {
  idToken: string;
  phoneNumber: string;
  uid: string;
}

/**
 * Initialize reCAPTCHA verifier for Firebase Phone Auth
 * @param containerId - DOM element ID for invisible reCAPTCHA
 * @returns RecaptchaVerifier instance
 */
export function createRecaptchaVerifier(containerId: string = "recaptcha-container"): RecaptchaVerifier {
  const container = document.getElementById(containerId);
  if (!container) {
    // Create invisible reCAPTCHA container if it doesn't exist
    const newContainer = document.createElement("div");
    newContainer.id = containerId;
    newContainer.style.display = "none";
    document.body.appendChild(newContainer);
  }

  return new RecaptchaVerifier(auth, containerId, {
    size: "invisible",
    callback: () => {
      // reCAPTCHA solved, allow signInWithPhoneNumber
    },
    "expired-callback": () => {
      // reCAPTCHA expired, user needs to try again
    },
  });
}

/**
 * Send OTP via Firebase Phone Authentication
 * @param phoneNumber - E.164 format phone number (e.g., +15551234567)
 * @param recaptchaVerifier - RecaptchaVerifier instance
 * @returns Promise with verification ID and confirmation result
 */
export async function sendPhoneOtp(
  phoneNumber: string,
  recaptchaVerifier: RecaptchaVerifier
): Promise<PhoneAuthResult> {
  // Validate phone number format
  if (!/^\+[1-9]\d{7,14}$/.test(phoneNumber)) {
    throw new Error("Invalid phone number format. Use E.164 format (e.g., +15551234567).");
  }

  try {
    const confirmationResult = await signInWithPhoneNumber(auth, phoneNumber, recaptchaVerifier);
    return {
      verificationId: confirmationResult.verificationId,
      confirmationResult,
    };
  } catch (error: unknown) {
    const err = error as Error & { code?: string };
    if (err.code === "auth/invalid-phone-number") {
      throw new Error("Invalid phone number format.");
    }
    if (err.code === "auth/missing-phone-number") {
      throw new Error("Phone number is required.");
    }
    if (err.code === "auth/quota-exceeded") {
      throw new Error("SMS quota exceeded. Please try again later.");
    }
    if (err.code === "auth/captcha-check-failed") {
      throw new Error("reCAPTCHA verification failed. Please try again.");
    }
    throw new Error(err.message || "Failed to send OTP. Please try again.");
  }
}

/**
 * Verify OTP and get Firebase ID token
 * @param confirmationResult - ConfirmationResult from sendPhoneOtp
 * @param otp - 6-digit OTP code
 * @returns Promise with ID token and phone number
 */
export async function verifyPhoneOtp(
  confirmationResult: ConfirmationResult,
  otp: string
): Promise<VerifiedPhoneResult> {
  if (!/^\d{6}$/.test(otp)) {
    throw new Error("Invalid OTP format. Must be 6 digits.");
  }

  try {
    const userCredential: UserCredential = await confirmationResult.confirm(otp);
    const idToken = await userCredential.user.getIdToken();

    return {
      idToken,
      phoneNumber: userCredential.user.phoneNumber || "",
      uid: userCredential.user.uid,
    };
  } catch (error: unknown) {
    const err = error as Error & { code?: string };
    if (err.code === "auth/invalid-verification-code") {
      throw new Error("Invalid verification code. Please check and try again.");
    }
    if (err.code === "auth/code-expired") {
      throw new Error("Verification code has expired. Please request a new one.");
    }
    if (err.code === "auth/session-expired") {
      throw new Error("Session expired. Please request a new code.");
    }
    throw new Error(err.message || "Failed to verify OTP. Please try again.");
  }
}

/**
 * Sign in with Firebase Phone Auth credential (for linking accounts)
 * @param phoneNumber - E.164 format phone number
 * @param otp - 6-digit OTP code
 * @param recaptchaVerifier - RecaptchaVerifier instance
 * @returns Promise with ID token and phone number
 */
export async function signInWithPhoneAuth(
  phoneNumber: string,
  otp: string,
  recaptchaVerifier: RecaptchaVerifier
): Promise<VerifiedPhoneResult> {
  const { confirmationResult } = await sendPhoneOtp(phoneNumber, recaptchaVerifier);
  return verifyPhoneOtp(confirmationResult, otp);
}

/**
 * Clean up reCAPTCHA verifier
 * @param recaptchaVerifier - RecaptchaVerifier instance to clean up
 */
export function cleanupRecaptchaVerifier(recaptchaVerifier: RecaptchaVerifier | null): void {
  if (recaptchaVerifier) {
    recaptchaVerifier.clear();
  }
}

/**
 * Get current user's ID token (for already authenticated users)
 * @returns Promise with ID token or null
 */
export async function getCurrentUserIdToken(): Promise<string | null> {
  const user = auth.currentUser;
  if (!user) return null;
  return user.getIdToken();
}

/**
 * Link phone number to current authenticated user
 * @param phoneNumber - E.164 format phone number
 * @param otp - 6-digit OTP code
 * @param recaptchaVerifier - RecaptchaVerifier instance
 * @returns Promise with ID token
 */
export async function linkPhoneNumber(
  phoneNumber: string,
  otp: string,
  recaptchaVerifier: RecaptchaVerifier
): Promise<string> {
  const user = auth.currentUser;
  if (!user) {
    throw new Error("No authenticated user to link phone number.");
  }

  const { confirmationResult } = await sendPhoneOtp(phoneNumber, recaptchaVerifier);
  await confirmationResult.confirm(otp);

  return user.getIdToken();
}

export default app;