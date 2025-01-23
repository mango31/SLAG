// Logout
export const logout = createAsyncThunk("auth/logout", async () => {
  clearAuthData();
  // Clear any other auth-related data in localStorage
  const authKeys = Object.keys(localStorage).filter(
    (key) =>
      key.startsWith("auth_") ||
      key.includes("token") ||
      key.includes("user") ||
      key.includes("wallet")
  );
  authKeys.forEach((key) => localStorage.removeItem(key));
  return null;
});
