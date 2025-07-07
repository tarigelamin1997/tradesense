import * as React from "react";
import { Login1 } from "./login-1";

const DemoOne = () => {
  return (
    <Login1 
      heading="Welcome to TradeSense"
      logo={{
        url: "https://tradesense.com",
        src: "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=400&h=100&fit=crop&crop=center",
        alt: "TradeSense Logo",
        title: "TradeSense",
      }}
      buttonText="Sign In"
      googleText="Continue with Google"
      signupText="Don't have an account?"
      signupUrl="/register"
    />
  );
};

export { DemoOne }; 