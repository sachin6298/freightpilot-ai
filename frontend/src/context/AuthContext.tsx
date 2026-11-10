import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react";
import { setAuthToken, getAuthToken, fetchCurrentUser, login as apiLogin, registerBuyer as apiRegisterBuyer, registerSeller as apiRegisterSeller } from "../api";
import { verifyFirebasePhone, linkFirebasePhone } from "../api";
import type { UserProfile, AuthResponse } from "../types";

interface AuthContextType {
  user: UserProfile | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  registerBuyer: (data: { email: string; password: string; company_name?: string; contact_person?: string; phone_number?: string }) => Promise<void>;
  registerSeller: (data: { email: string; password: string; business_name: string; business_address: string; country: string; contact_person: string; contact_phone: string; registration_number?: string }) => Promise<void>;
  logout: () => void;
  verifyFirebasePhone: (idToken: string, phoneNumber: string) => Promise<void>;
  linkFirebasePhone: (idToken: string, phoneNumber: string) => Promise<void>;
  refreshUser: () => Promise<void>;
  error: string | null;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => setError(null), []);

  const refreshUser = useCallback(async () => {
    const token = getAuthToken();
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const userData = await fetchCurrentUser();
      setUser(userData);
    } catch {
      // Token may be expired - clear it
      setAuthToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const handleAuthResponse = useCallback(async (response: AuthResponse) => {
    setAuthToken(response.access_token);
    const userData = await fetchCurrentUser();
    setUser(userData);
    setError(null);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setError(null);
    setLoading(true);
    try {
      const response = await apiLogin(email, password);
      await handleAuthResponse(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed. Please try again.");
      setLoading(false);
      throw err;
    }
  }, [handleAuthResponse]);

  const registerBuyer = useCallback(async (data: { email: string; password: string; company_name?: string; contact_person?: string; phone_number?: string }) => {
    setError(null);
    setLoading(true);
    try {
      const response = await apiRegisterBuyer(data);
      await handleAuthResponse(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed. Please try again.");
      setLoading(false);
      throw err;
    }
  }, [handleAuthResponse]);

  const registerSeller = useCallback(async (data: { email: string; password: string; business_name: string; business_address: string; country: string; contact_person: string; contact_phone: string; registration_number?: string }) => {
    setError(null);
    setLoading(true);
    try {
      const response = await apiRegisterSeller(data);
      await handleAuthResponse(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed. Please try again.");
      setLoading(false);
      throw err;
    }
  }, [handleAuthResponse]);

  const logout = useCallback(() => {
    setAuthToken(null);
    setUser(null);
    setError(null);
    window.location.href = "/login";
  }, []);

  const handleFirebasePhone = useCallback(async (idToken: string, phoneNumber: string) => {
    setError(null);
    setLoading(true);
    try {
      const response = await verifyFirebasePhone(idToken, phoneNumber);
      await handleAuthResponse(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Phone verification failed. Please try again.");
      setLoading(false);
      throw err;
    }
  }, [handleAuthResponse]);

  const handleLinkFirebasePhone = useCallback(async (idToken: string, phoneNumber: string) => {
    setError(null);
    setLoading(true);
    try {
      const updatedUser = await linkFirebasePhone(idToken, phoneNumber);
      setUser(updatedUser);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to link phone number. Please try again.");
      setLoading(false);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      login,
      registerBuyer,
      registerSeller,
      logout,
      verifyFirebasePhone: handleFirebasePhone,
      linkFirebasePhone: handleLinkFirebasePhone,
      refreshUser,
      error,
      clearError,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}