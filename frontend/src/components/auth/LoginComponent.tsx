import { useState, useEffect } from "react";
import { useAuth } from "@/hooks/useAuth";
import { useDispatch, useSelector } from "react-redux";
import {
  connectWallet,
  disconnectWallet,
  checkWalletAvailability,
} from "@/store/slices/web3Slice";
import type { AppDispatch, RootState } from "@/store";

export function LoginComponent() {
  const dispatch = useDispatch<AppDispatch>();
  const {
    signIn,
    signOut,
    error: authError,
    isLoading: authLoading,
  } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const {
    connected,
    publicKey,
    isLoading: web3Loading,
    error: web3Error,
    isAvailable,
  } = useSelector((state: RootState) => state.web3);

  // Check wallet availability on mount
  useEffect(() => {
    dispatch(checkWalletAvailability());
  }, [dispatch]);

  // Traditional login
  const handleTraditionalLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await signIn({ email, password });
    } catch (error) {
      console.error("Traditional login failed:", error);
    }
  };

  // Web3 login with Phantom wallet
  const handleWeb3Login = async () => {
    try {
      const walletResult = await dispatch(connectWallet()).unwrap();
      if (walletResult.publicKey) {
        await signIn({ web3_wallet: walletResult.publicKey });
      }
    } catch (error) {
      console.error("Web3 login failed:", error);
    }
  };

  // Handle wallet disconnect
  const handleDisconnect = async () => {
    try {
      await dispatch(disconnectWallet()).unwrap();
      signOut();
    } catch (error) {
      console.error("Disconnect failed:", error);
    }
  };

  const isLoading = authLoading || web3Loading;
  const error = authError || web3Error;

  return (
    <div className="flex flex-col space-y-4 p-6">
      {/* Traditional Login Form */}
      {!connected && (
        <form onSubmit={handleTraditionalLogin} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium">
              Email
            </label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
              required
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium">
              Password
            </label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
              required
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {isLoading ? "Signing in..." : "Sign in"}
          </button>
        </form>
      )}

      {/* Web3 Section */}
      {!connected && (
        <>
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">
                Or continue with
              </span>
            </div>
          </div>

          <button
            onClick={handleWeb3Login}
            disabled={isLoading || !isAvailable}
            className="w-full bg-purple-600 text-white py-2 px-4 rounded-md hover:bg-purple-700 disabled:opacity-50"
          >
            {isLoading
              ? "Connecting..."
              : !isAvailable
              ? "Phantom Wallet Not Found"
              : "Connect Phantom Wallet"}
          </button>
        </>
      )}

      {/* Connected Wallet Info */}
      {connected && publicKey && (
        <div className="space-y-4">
          <div className="p-4 bg-gray-50 rounded-md">
            <p className="text-sm text-gray-600">Connected Wallet</p>
            <p className="text-sm font-mono mt-1">{`${publicKey.slice(
              0,
              4
            )}...${publicKey.slice(-4)}`}</p>
          </div>
          <button
            onClick={handleDisconnect}
            className="w-full bg-red-600 text-white py-2 px-4 rounded-md hover:bg-red-700"
          >
            Disconnect Wallet
          </button>
        </div>
      )}

      {/* Error Display */}
      {error && <div className="text-red-600 text-sm mt-2">{error}</div>}
    </div>
  );
}
