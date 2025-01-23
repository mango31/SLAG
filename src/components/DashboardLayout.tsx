import React, { useEffect } from "react";
import { useRouter } from "next/router";
import { useDispatch } from "react-redux";
import { disconnectWallet } from "../redux/walletSlice";
import { signOut } from "../redux/authSlice";
import { logout } from "../redux/authSlice";

const DashboardLayout: React.FC = () => {
  const router = useRouter();
  const dispatch = useDispatch();

  const handleSignOut = async () => {
    try {
      // If user was signed in with wallet, disconnect it first
      if (authMethod === "wallet") {
        await dispatch(disconnectWallet()).unwrap();
      }
      // Then dispatch logout action
      await dispatch(logout()).unwrap();
      router.push("/dashboard/create");
    } catch (error) {
      console.error("Error signing out:", error);
    }
  };

  useEffect(() => {
    // Cleanup function
    return () => {
      // Handle any cleanup tasks if needed
    };
  }, []);

  return <div>{/* Render your component content here */}</div>;
};

export default DashboardLayout;
